"""Question generation service using OpenAI for intelligent quiz creation"""

import json
import logging
import time
import asyncio
from typing import List, Dict, Tuple, Optional, Any, Literal
from uuid import uuid4

import openai
from app.core.config import get_settings
from app.services.retrieval import HybridRanker
from app.db.session import get_db_pool

from .question_templates import QuestionTemplates, QuestionType, DifficultyLevel
from .difficulty_assessor import DifficultyAssessor, ContentAnalysis

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """Generates quiz questions from document chunks using OpenAI"""
    
    def __init__(self):
        self.settings = get_settings()
        self.templates = QuestionTemplates()
        self.difficulty_assessor = DifficultyAssessor()
        self.hybrid_ranker = HybridRanker()
        
        # Initialize OpenAI client
        if not self.settings.openai_api_key:
            logger.warning("OpenAI API key not configured - question generation will fail")
    
    async def generate_questions_from_document(
        self,
        document_id: str,
        user_id: str,
        question_count: int,
        question_types: List[QuestionType],
        difficulty: DifficultyLevel = "medium",
        focus_sections: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate questions from document chunks
        
        Args:
            document_id: UUID of document to generate questions from
            user_id: UUID of user requesting questions (for RLS)
            question_count: Number of questions to generate
            question_types: Types of questions to generate
            difficulty: Target difficulty level
            focus_sections: Optional specific sections to focus on
            
        Returns:
            List of generated question dictionaries
        """
        start_time = time.time()
        
        logger.info(
            "Starting question generation",
            extra={
                "document_id": document_id,
                "user_id": user_id,
                "question_count": question_count,
                "question_types": question_types,
                "difficulty": difficulty
            }
        )
        
        try:
            # Step 1: Select optimal chunks for question generation
            selected_chunks = await self._select_content_chunks(
                document_id, user_id, question_count, focus_sections
            )
            
            if not selected_chunks:
                logger.warning("No suitable chunks found for question generation")
                return []
            
            # Step 2: Analyze chunks for difficulty and question potential
            chunk_analyses = []
            for chunk in selected_chunks:
                analysis = self.difficulty_assessor.analyze_content_chunk(
                    chunk["content"], chunk
                )
                chunk_analyses.append((chunk, analysis))
            
            # Step 3: Plan question distribution across types and difficulties
            question_distribution = self._plan_question_distribution(
                question_count, question_types, difficulty, chunk_analyses
            )
            
            # Step 4: Generate questions in batches
            all_questions = []
            for question_type, type_count in question_distribution["by_type"].items():
                if type_count > 0:
                    type_questions = await self._generate_questions_by_type(
                        chunk_analyses, question_type, type_count, difficulty
                    )
                    all_questions.extend(type_questions)
            
            # Step 5: Validate and enhance generated questions
            validated_questions = await self._validate_and_enhance_questions(
                all_questions, chunk_analyses
            )
            
            # Step 6: Final selection and ranking
            final_questions = self._select_best_questions(
                validated_questions, question_count
            )
            
            generation_time = time.time() - start_time
            
            logger.info(
                "Question generation completed",
                extra={
                    "questions_generated": len(final_questions),
                    "generation_time": generation_time,
                    "chunks_used": len(selected_chunks)
                }
            )
            
            return final_questions
            
        except Exception as e:
            logger.error(
                "Question generation failed",
                extra={"error": str(e), "document_id": document_id},
                exc_info=True
            )
            raise Exception(f"Failed to generate questions: {str(e)}")
    
    async def _select_content_chunks(
        self,
        document_id: str,
        user_id: str,
        question_count: int,
        focus_sections: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Select optimal chunks for question generation
        
        Strategy:
        1. Get chunks spread across document sections
        2. Prioritize information-dense chunks
        3. Ensure variety in content types
        4. Consider focus sections if provided
        """
        pool = await get_db_pool()
        
        async with pool.acquire() as conn:
            # Base query for chunks with content
            base_query = """
                SELECT 
                    c.id,
                    c.content,
                    c.page_number,
                    c.section_title,
                    c.token_count,
                    c.metadata
                FROM public.chunks c
                JOIN public.documents d ON d.id = c.document_id
                WHERE d.id = $1 AND d.owner_id = $2
                    AND length(c.content) > 100  -- Minimum content length
            """
            
            # Add section filtering if requested
            if focus_sections:
                placeholders = ",".join(f"${i+3}" for i in range(len(focus_sections)))
                base_query += f" AND c.section_title = ANY(ARRAY[{placeholders}])"
                chunk_rows = await conn.fetch(base_query, document_id, user_id, *focus_sections)
            else:
                base_query += " ORDER BY c.page_number, c.id"
                chunk_rows = await conn.fetch(base_query, document_id, user_id)
        
        if not chunk_rows:
            return []
        
        # Convert to dictionaries and analyze
        chunks = [dict(row) for row in chunk_rows]
        
        # Strategy: Select diverse, information-rich chunks
        selected_chunks = self._select_diverse_chunks(chunks, question_count * 2)  # Get 2x for better options
        
        logger.debug(
            f"Selected {len(selected_chunks)} chunks from {len(chunks)} available chunks"
        )
        
        return selected_chunks
    
    def _select_diverse_chunks(self, chunks: List[Dict], target_count: int) -> List[Dict]:
        """
        Select diverse chunks across document sections
        
        Strategy:
        1. Group by section
        2. Select from different sections
        3. Prioritize information density
        4. Ensure minimum content quality
        """
        if len(chunks) <= target_count:
            return chunks
        
        # Group by section
        sections = {}
        for chunk in chunks:
            section = chunk.get("section_title", "Unknown")
            if section not in sections:
                sections[section] = []
            sections[section].append(chunk)
        
        selected = []
        section_keys = list(sections.keys())
        
        # Round-robin selection from sections
        while len(selected) < target_count and any(sections.values()):
            for section_key in section_keys:
                if len(selected) >= target_count:
                    break
                    
                if sections[section_key]:
                    # Select best chunk from this section (by content length as proxy for info density)
                    best_chunk = max(
                        sections[section_key],
                        key=lambda x: len(x.get("content", ""))
                    )
                    selected.append(best_chunk)
                    sections[section_key].remove(best_chunk)
        
        return selected
    
    def _plan_question_distribution(
        self,
        question_count: int,
        question_types: List[QuestionType],
        target_difficulty: DifficultyLevel,
        chunk_analyses: List[Tuple[Dict, ContentAnalysis]]
    ) -> Dict[str, Any]:
        """Plan optimal distribution of questions across types and difficulties"""
        
        # Get difficulty distribution recommendation
        difficulty_dist = self.difficulty_assessor.recommend_question_distribution(
            [analysis for _, analysis in chunk_analyses],
            question_count,
            target_difficulty
        )
        
        # Distribute across question types
        type_distribution = {}
        remaining_questions = question_count
        
        for i, qtype in enumerate(question_types):
            if i == len(question_types) - 1:  # Last type gets remainder
                type_distribution[qtype] = remaining_questions
            else:
                # Roughly equal distribution, with slight preferences
                type_preferences = {
                    "multiple_choice": 0.4,
                    "true_false": 0.3,
                    "short_answer": 0.3
                }
                
                type_count = max(1, round(question_count * type_preferences.get(qtype, 0.33)))
                type_count = min(type_count, remaining_questions - (len(question_types) - i - 1))
                type_distribution[qtype] = type_count
                remaining_questions -= type_count
        
        return {
            "by_difficulty": difficulty_dist,
            "by_type": type_distribution,
            "total": question_count
        }
    
    async def _generate_questions_by_type(
        self,
        chunk_analyses: List[Tuple[Dict, ContentAnalysis]],
        question_type: QuestionType,
        question_count: int,
        target_difficulty: DifficultyLevel
    ) -> List[Dict[str, Any]]:
        """Generate questions of a specific type"""
        
        # Select best chunks for this question type
        suitable_chunks = self._select_chunks_for_question_type(
            chunk_analyses, question_type, question_count
        )
        
        if not suitable_chunks:
            logger.warning(f"No suitable chunks found for {question_type} questions")
            return []
        
        # Generate questions in batches (to avoid token limits)
        batch_size = min(3, question_count)  # Generate up to 3 questions per API call
        all_questions = []
        
        for i in range(0, question_count, batch_size):
            batch_count = min(batch_size, question_count - i)
            chunk_idx = i % len(suitable_chunks)  # Cycle through chunks
            chunk, analysis = suitable_chunks[chunk_idx]
            
            try:
                batch_questions = await self._generate_question_batch(
                    chunk, question_type, batch_count, target_difficulty
                )
                all_questions.extend(batch_questions)
                
                # Small delay between API calls
                if i + batch_size < question_count:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.warning(f"Failed to generate batch: {e}")
                continue
        
        return all_questions
    
    def _select_chunks_for_question_type(
        self,
        chunk_analyses: List[Tuple[Dict, ContentAnalysis]],
        question_type: QuestionType,
        needed_count: int
    ) -> List[Tuple[Dict, ContentAnalysis]]:
        """Select chunks most suitable for a specific question type"""
        
        # Score chunks based on suitability for question type
        scored_chunks = []
        for chunk, analysis in chunk_analyses:
            score = self._calculate_chunk_suitability(analysis, question_type)
            scored_chunks.append((score, chunk, analysis))
        
        # Sort by suitability score and return top chunks
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        # Return at least needed_count chunks, but not more than available
        selected_count = min(max(needed_count, 2), len(scored_chunks))
        return [(chunk, analysis) for _, chunk, analysis in scored_chunks[:selected_count]]
    
    def _calculate_chunk_suitability(self, analysis: ContentAnalysis, question_type: QuestionType) -> float:
        """Calculate how suitable a chunk is for generating a specific question type"""
        
        suitability_factors = {
            "multiple_choice": {
                "factual_statements": 0.4,
                "key_concepts": 0.3,
                "technical_terms": 0.2,
                "complexity": 0.1
            },
            "true_false": {
                "factual_statements": 0.5,
                "technical_terms": 0.3,
                "key_concepts": 0.2
            },
            "short_answer": {
                "relationships": 0.3,
                "key_concepts": 0.3,
                "complexity": 0.2,
                "factual_statements": 0.2
            }
        }
        
        factors = suitability_factors.get(question_type, suitability_factors["multiple_choice"])
        
        score = 0.0
        score += factors.get("factual_statements", 0) * min(1.0, len(analysis.factual_statements) / 5)
        score += factors.get("key_concepts", 0) * min(1.0, len(analysis.key_concepts) / 3)
        score += factors.get("technical_terms", 0) * min(1.0, len(analysis.technical_terms) / 5)
        score += factors.get("relationships", 0) * min(1.0, len(analysis.relationships) / 3)
        score += factors.get("complexity", 0) * analysis.complexity_score
        
        return score
    
    async def _generate_question_batch(
        self,
        chunk: Dict[str, Any],
        question_type: QuestionType,
        question_count: int,
        difficulty: DifficultyLevel
    ) -> List[Dict[str, Any]]:
        """Generate a batch of questions from a single chunk"""
        
        # Build the prompt
        prompt = self.templates.get_generation_prompt(
            question_type=question_type,
            difficulty=difficulty,
            chunk_content=chunk["content"],
            question_count=question_count,
            document_title=chunk.get("document_title", "Document")
        )
        
        # Call OpenAI API
        try:
            client = openai.AsyncOpenAI(api_key=self.settings.openai_api_key)
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # Some creativity, but not too much
                max_tokens=2000,
                response_format={"type": "json_object"} if question_count > 1 else None
            )
            
            response_text = response.choices[0].message.content
            
            # Parse response
            questions = self._parse_question_response(
                response_text, chunk, question_type, difficulty
            )
            
            logger.debug(
                f"Generated {len(questions)} {question_type} questions from chunk",
                extra={"chunk_id": chunk.get("id"), "difficulty": difficulty}
            )
            
            return questions
            
        except Exception as e:
            logger.error(f"OpenAI API error during question generation: {e}")
            raise Exception(f"Question generation API call failed: {str(e)}")
    
    def _parse_question_response(
        self,
        response_text: str,
        source_chunk: Dict[str, Any],
        question_type: QuestionType,
        expected_difficulty: DifficultyLevel
    ) -> List[Dict[str, Any]]:
        """Parse OpenAI response into question dictionaries"""
        
        try:
            # Try to parse as JSON array
            if response_text.strip().startswith("["):
                questions_data = json.loads(response_text)
            else:
                # Try to extract JSON from response
                json_match = re.search(r'\\[.*\\]', response_text, re.DOTALL)
                if json_match:
                    questions_data = json.loads(json_match.group())
                else:
                    # Single question response
                    questions_data = [json.loads(response_text)]
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse question response JSON: {e}")
            logger.debug(f"Response text: {response_text}")
            return []
        
        # Convert to standard format
        questions = []
        for i, q_data in enumerate(questions_data):
            try:
                question = {
                    "id": f"q_{uuid4().hex[:8]}",
                    "type": question_type,
                    "question": q_data.get("question", "").strip(),
                    "options": q_data.get("options"),
                    "correct_answer": q_data.get("correct_answer", "").strip(),
                    "explanation": q_data.get("explanation", "").strip(),
                    "difficulty": q_data.get("difficulty", expected_difficulty),
                    "source_chunk_id": source_chunk.get("id"),
                    "source_reference": q_data.get("source_reference", ""),
                    "page_number": source_chunk.get("page_number"),
                    "section_title": source_chunk.get("section_title"),
                    "generated_at": time.time(),
                    "quality_score": 0.0  # Will be set during validation
                }
                
                # Validate essential fields
                if question["question"] and question["correct_answer"]:
                    questions.append(question)
                else:
                    logger.warning(f"Skipping incomplete question: {q_data}")
                    
            except Exception as e:
                logger.warning(f"Error processing question {i}: {e}")
                continue
        
        return questions
    
    async def _validate_and_enhance_questions(
        self,
        questions: List[Dict[str, Any]],
        chunk_analyses: List[Tuple[Dict, ContentAnalysis]]
    ) -> List[Dict[str, Any]]:
        """Validate generated questions and enhance with quality scores"""
        
        validated_questions = []
        
        for question in questions:
            try:
                # Basic validation
                if not self._is_valid_question(question):
                    continue
                
                # Calculate quality score
                quality_score = self._calculate_question_quality(question, chunk_analyses)
                question["quality_score"] = quality_score
                
                # Enhance with additional metadata
                question = self._enhance_question_metadata(question)
                
                validated_questions.append(question)
                
            except Exception as e:
                logger.warning(f"Error validating question: {e}")
                continue
        
        logger.debug(f"Validated {len(validated_questions)} out of {len(questions)} questions")
        return validated_questions
    
    def _is_valid_question(self, question: Dict[str, Any]) -> bool:
        """Validate that a question meets basic quality requirements"""
        
        # Check required fields
        required_fields = ["question", "correct_answer", "type"]
        for field in required_fields:
            if not question.get(field):
                logger.debug(f"Question missing required field: {field}")
                return False
        
        # Check question length
        question_text = question["question"]
        if len(question_text) < 10 or len(question_text) > 500:
            logger.debug(f"Question length invalid: {len(question_text)}")
            return False
        
        # Type-specific validation
        question_type = question["type"]
        
        if question_type == "multiple_choice":
            options = question.get("options", [])
            if not isinstance(options, list) or len(options) < 2:
                logger.debug("Multiple choice question needs at least 2 options")
                return False
            
            correct_answer = question["correct_answer"]
            if correct_answer not in options:
                # Try to match by partial string
                matches = [opt for opt in options if correct_answer.lower() in opt.lower()]
                if not matches:
                    logger.debug("Correct answer not found in options")
                    return False
        
        elif question_type == "true_false":
            correct_answer = question["correct_answer"].lower()
            if correct_answer not in ["true", "false"]:
                logger.debug(f"True/false answer must be 'true' or 'false', got: {correct_answer}")
                return False
        
        return True
    
    def _calculate_question_quality(
        self,
        question: Dict[str, Any],
        chunk_analyses: List[Tuple[Dict, ContentAnalysis]]
    ) -> float:
        """Calculate quality score for a question"""
        
        quality_factors = {
            "clarity": 0.25,
            "difficulty_appropriateness": 0.20,
            "source_relevance": 0.20,
            "answer_correctness": 0.15,
            "explanation_quality": 0.10,
            "uniqueness": 0.10
        }
        
        scores = {}
        
        # Clarity (based on question structure and language)
        scores["clarity"] = self._assess_question_clarity(question)
        
        # Difficulty appropriateness (compared to expected)
        scores["difficulty_appropriateness"] = self._assess_difficulty_appropriateness(question)
        
        # Source relevance (how well question relates to source content)
        scores["source_relevance"] = self._assess_source_relevance(question, chunk_analyses)
        
        # Answer correctness (basic checks)
        scores["answer_correctness"] = self._assess_answer_correctness(question)
        
        # Explanation quality
        scores["explanation_quality"] = self._assess_explanation_quality(question)
        
        # Uniqueness (avoid repetitive questions)
        scores["uniqueness"] = 0.8  # Placeholder - could implement similarity checking
        
        # Calculate weighted score
        total_score = sum(
            quality_factors[factor] * scores[factor]
            for factor in quality_factors
        )
        
        return min(1.0, total_score)
    
    def _assess_question_clarity(self, question: Dict[str, Any]) -> float:
        """Assess clarity of question text"""
        question_text = question["question"]
        
        clarity_score = 0.7  # Base score
        
        # Bonus for clear question words
        question_starters = ["what", "how", "why", "when", "where", "which", "who"]
        if any(question_text.lower().startswith(starter) for starter in question_starters):
            clarity_score += 0.1
        
        # Bonus for appropriate length
        word_count = len(question_text.split())
        if 5 <= word_count <= 20:
            clarity_score += 0.1
        
        # Penalty for unclear language
        unclear_indicators = ["uh", "um", "maybe", "perhaps", "might be"]
        if any(indicator in question_text.lower() for indicator in unclear_indicators):
            clarity_score -= 0.2
        
        return min(1.0, clarity_score)
    
    def _assess_difficulty_appropriateness(self, question: Dict[str, Any]) -> float:
        """Assess if question difficulty matches expectations"""
        expected_difficulty = question.get("difficulty", "medium")
        
        # Use difficulty assessor to analyze actual difficulty
        actual_difficulty, _ = self.difficulty_assessor.assess_question_difficulty(
            question["question"],
            question["type"],
            question["correct_answer"],
            question.get("source_reference", ""),
            question.get("explanation", "")
        )
        
        # Score based on match
        if actual_difficulty == expected_difficulty:
            return 1.0
        elif abs(["easy", "medium", "hard"].index(actual_difficulty) - 
                 ["easy", "medium", "hard"].index(expected_difficulty)) == 1:
            return 0.7
        else:
            return 0.4
    
    def _assess_source_relevance(
        self,
        question: Dict[str, Any],
        chunk_analyses: List[Tuple[Dict, ContentAnalysis]]
    ) -> float:
        """Assess how well question relates to source content"""
        
        source_chunk_id = question.get("source_chunk_id")
        if not source_chunk_id:
            return 0.5
        
        # Find the source chunk
        source_chunk = None
        for chunk, _ in chunk_analyses:
            if chunk.get("id") == source_chunk_id:
                source_chunk = chunk
                break
        
        if not source_chunk:
            return 0.5
        
        # Check overlap between question and source content
        question_words = set(question["question"].lower().split())
        source_words = set(source_chunk["content"].lower().split())
        
        # Remove common words
        common_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "for", "of", "with", "by"}
        question_words -= common_words
        source_words -= common_words
        
        if not question_words:
            return 0.5
        
        # Calculate relevance based on word overlap
        overlap = len(question_words & source_words) / len(question_words)
        return min(1.0, overlap * 1.5)  # Scale up since some overlap is expected
    
    def _assess_answer_correctness(self, question: Dict[str, Any]) -> float:
        """Basic assessment of answer correctness"""
        
        # This is a basic check - more sophisticated validation would require
        # actual verification against the source content
        
        answer = question["correct_answer"]
        question_type = question["type"]
        
        if question_type == "true_false":
            return 1.0 if answer.lower() in ["true", "false"] else 0.0
        
        elif question_type == "multiple_choice":
            options = question.get("options", [])
            if answer in options:
                return 1.0
            # Check partial matches
            matches = [opt for opt in options if answer.lower() in opt.lower()]
            return 0.8 if matches else 0.3
        
        elif question_type == "short_answer":
            # Basic length and content checks
            if 3 <= len(answer.split()) <= 50:
                return 0.8
            else:
                return 0.5
        
        return 0.7  # Default moderate score
    
    def _assess_explanation_quality(self, question: Dict[str, Any]) -> float:
        """Assess quality of question explanation"""
        
        explanation = question.get("explanation", "")
        if not explanation:
            return 0.3
        
        quality_score = 0.5  # Base score for having an explanation
        
        # Bonus for appropriate length
        word_count = len(explanation.split())
        if 10 <= word_count <= 100:
            quality_score += 0.2
        
        # Bonus for references to source
        if "text" in explanation.lower() or "document" in explanation.lower():
            quality_score += 0.2
        
        # Bonus for explanatory language
        explanatory_words = ["because", "since", "due to", "explains", "indicates", "shows"]
        if any(word in explanation.lower() for word in explanatory_words):
            quality_score += 0.1
        
        return min(1.0, quality_score)
    
    def _enhance_question_metadata(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Add additional metadata to question"""
        
        question["metadata"] = {
            "word_count": len(question["question"].split()),
            "estimated_time_seconds": self._estimate_question_time(question),
            "cognitive_level": self._determine_cognitive_level(question),
            "topics": self._extract_question_topics(question)
        }
        
        return question
    
    def _estimate_question_time(self, question: Dict[str, Any]) -> int:
        """Estimate time needed to answer question"""
        
        base_times = {
            "multiple_choice": 30,
            "true_false": 15,
            "short_answer": 60
        }
        
        base_time = base_times.get(question["type"], 30)
        
        # Adjust for difficulty
        difficulty_multipliers = {
            "easy": 0.8,
            "medium": 1.0,
            "hard": 1.5
        }
        
        multiplier = difficulty_multipliers.get(question.get("difficulty", "medium"), 1.0)
        
        # Adjust for question length
        word_count = len(question["question"].split())
        if word_count > 15:
            multiplier *= 1.2
        
        return int(base_time * multiplier)
    
    def _determine_cognitive_level(self, question: Dict[str, Any]) -> str:
        """Determine Bloom's taxonomy level for question"""
        
        question_text = question["question"].lower()
        
        cognitive_indicators = {
            "remember": ["what", "when", "where", "who", "define", "list", "identify"],
            "understand": ["explain", "describe", "summarize", "interpret", "classify"],
            "apply": ["apply", "demonstrate", "calculate", "solve", "use", "show"],
            "analyze": ["analyze", "examine", "compare", "contrast", "categorize"],
            "evaluate": ["evaluate", "assess", "judge", "critique", "justify"],
            "create": ["create", "design", "develop", "formulate", "propose"]
        }
        
        level_scores = {}
        for level, indicators in cognitive_indicators.items():
            score = sum(1 for indicator in indicators if indicator in question_text)
            level_scores[level] = score
        
        if level_scores and max(level_scores.values()) > 0:
            return max(level_scores, key=level_scores.get)
        else:
            return "understand"  # Default level
    
    def _extract_question_topics(self, question: Dict[str, Any]) -> List[str]:
        """Extract main topics from question"""
        
        question_text = question["question"]
        
        # Simple topic extraction (could be enhanced with NLP)
        topics = []
        
        # Look for capitalized words (potential proper nouns/topics)
        import re
        capitalized_words = re.findall(r'\\b[A-Z][a-z]+\\b', question_text)
        topics.extend(capitalized_words)
        
        # Look for technical terms from source
        source_ref = question.get("source_reference", "")
        if source_ref:
            # Extract potential topics from source reference
            technical_terms = re.findall(r'\\b[a-z]+(?:ing|tion|ment|ness)\\b', source_ref.lower())
            topics.extend(technical_terms)
        
        # Remove duplicates and limit
        topics = list(set(topics))[:5]
        
        return topics
    
    def _select_best_questions(
        self,
        questions: List[Dict[str, Any]],
        target_count: int
    ) -> List[Dict[str, Any]]:
        """Select the best questions from generated set"""
        
        if len(questions) <= target_count:
            return questions
        
        # Sort by quality score
        questions.sort(key=lambda q: q.get("quality_score", 0), reverse=True)
        
        # Select top questions while ensuring diversity
        selected = []
        used_sources = set()
        
        for question in questions:
            if len(selected) >= target_count:
                break
            
            # Prefer questions from different sources for diversity
            source_id = question.get("source_chunk_id")
            if source_id not in used_sources or len(selected) < target_count // 2:
                selected.append(question)
                if source_id:
                    used_sources.add(source_id)
        
        # Fill remaining slots if needed
        for question in questions:
            if len(selected) >= target_count:
                break
            if question not in selected:
                selected.append(question)
        
        return selected[:target_count]


async def test_question_generator():
    """Test question generation functionality"""
    generator = QuestionGenerator()
    
    # Mock chunk data for testing
    mock_chunks = [
        {
            "id": "test-chunk-1",
            "content": "Machine learning is a subset of artificial intelligence that enables computers to learn from data without explicit programming. Cross-validation techniques are used to validate model performance.",
            "page_number": 1,
            "section_title": "Introduction to ML"
        }
    ]
    
    try:
        # Test question generation (would need actual OpenAI API key)
        print("✓ Question generator initialized")
        print(f"✓ Templates loaded: {len(generator.templates.templates)}")
        print(f"✓ Difficulty assessor ready")
        
        # Test chunk selection logic
        selected = generator._select_diverse_chunks(mock_chunks * 5, 3)
        print(f"✓ Chunk selection: {len(selected)} chunks selected")
        
        return generator
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_question_generator())
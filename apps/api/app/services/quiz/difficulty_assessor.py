"""Difficulty assessment for quiz questions and content chunks"""

import logging
import re
from typing import Dict, List, Tuple, Optional, Literal
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DifficultyLevel = Literal["easy", "medium", "hard"]


@dataclass 
class DifficultyFactors:
    """Factors that contribute to question difficulty"""
    cognitive_level: str  # bloom's taxonomy level
    concept_complexity: float  # 0.0-1.0
    vocabulary_complexity: float  # 0.0-1.0
    reasoning_required: float  # 0.0-1.0
    context_dependency: float  # 0.0-1.0
    prior_knowledge_needed: float  # 0.0-1.0


@dataclass
class ContentAnalysis:
    """Analysis of content chunk for question generation"""
    key_concepts: List[str]
    technical_terms: List[str]
    factual_statements: List[str]
    relationships: List[Tuple[str, str]]
    complexity_score: float
    information_density: float
    question_potential: Dict[DifficultyLevel, float]


class DifficultyAssessor:
    """Assesses and predicts difficulty levels for questions and content"""
    
    def __init__(self):
        self.bloom_levels = {
            "remember": 1,     # recall facts, terms, concepts
            "understand": 2,   # explain ideas, concepts
            "apply": 3,        # use information in new situations
            "analyze": 4,      # draw connections among ideas
            "evaluate": 5,     # justify a stand or decision
            "create": 6        # produce new or original work
        }
        
        self.cognitive_keywords = {
            "remember": ["what", "when", "where", "who", "define", "list", "identify", "recall", "state"],
            "understand": ["explain", "describe", "summarize", "interpret", "classify", "compare"],
            "apply": ["apply", "demonstrate", "calculate", "solve", "use", "show", "implement"],
            "analyze": ["analyze", "examine", "investigate", "categorize", "differentiate", "relate"],
            "evaluate": ["evaluate", "assess", "judge", "critique", "defend", "justify", "argue"],
            "create": ["create", "design", "develop", "formulate", "propose", "construct", "generate"]
        }
        
        self.technical_indicators = [
            # Academic/scientific terms
            r'\b(?:hypothesis|methodology|analysis|evaluation|implementation|optimization)\b',
            # Mathematical/statistical terms  
            r'\b(?:algorithm|coefficient|correlation|regression|probability|statistics)\b',
            # Technical jargon
            r'\b(?:framework|architecture|paradigm|infrastructure|scalability)\b',
            # Complex connectors
            r'\b(?:furthermore|nevertheless|consequently|alternatively|specifically)\b'
        ]
        
    def assess_question_difficulty(
        self,
        question: str,
        question_type: str,
        answer: str,
        context: str,
        explanation: str = ""
    ) -> Tuple[DifficultyLevel, DifficultyFactors]:
        """
        Assess difficulty of a generated question
        
        Args:
            question: Question text
            question_type: Type of question (multiple_choice, true_false, short_answer)
            answer: Correct answer
            context: Source content
            explanation: Answer explanation
            
        Returns:
            Tuple of difficulty level and contributing factors
        """
        factors = DifficultyFactors(
            cognitive_level=self._assess_cognitive_level(question, explanation),
            concept_complexity=self._assess_concept_complexity(question, answer, context),
            vocabulary_complexity=self._assess_vocabulary_complexity(question + " " + answer),
            reasoning_required=self._assess_reasoning_requirement(question, question_type, explanation),
            context_dependency=self._assess_context_dependency(question, context),
            prior_knowledge_needed=self._assess_prior_knowledge(question, context)
        )
        
        difficulty = self._calculate_overall_difficulty(factors)
        
        logger.debug(
            "Question difficulty assessed",
            extra={
                "question": question[:50] + "...",
                "difficulty": difficulty,
                "cognitive_level": factors.cognitive_level,
                "complexity": factors.concept_complexity
            }
        )
        
        return difficulty, factors
    
    def analyze_content_chunk(self, chunk_content: str, chunk_metadata: Dict = None) -> ContentAnalysis:
        """
        Analyze content chunk for question generation potential
        
        Args:
            chunk_content: Text content of chunk
            chunk_metadata: Optional metadata (page, section, etc.)
            
        Returns:
            Content analysis with difficulty assessments
        """
        # Extract key concepts and terms
        key_concepts = self._extract_key_concepts(chunk_content)
        technical_terms = self._extract_technical_terms(chunk_content)
        factual_statements = self._extract_factual_statements(chunk_content)
        relationships = self._extract_relationships(chunk_content)
        
        # Calculate complexity metrics
        complexity_score = self._calculate_content_complexity(
            chunk_content, technical_terms, key_concepts
        )
        information_density = self._calculate_information_density(chunk_content)
        
        # Assess question generation potential by difficulty
        question_potential = {
            "easy": self._assess_easy_question_potential(factual_statements, technical_terms),
            "medium": self._assess_medium_question_potential(key_concepts, relationships),
            "hard": self._assess_hard_question_potential(relationships, complexity_score)
        }
        
        return ContentAnalysis(
            key_concepts=key_concepts,
            technical_terms=technical_terms,
            factual_statements=factual_statements,
            relationships=relationships,
            complexity_score=complexity_score,
            information_density=information_density,
            question_potential=question_potential
        )
    
    def recommend_question_distribution(
        self, 
        content_analyses: List[ContentAnalysis],
        total_questions: int,
        preferred_difficulty: DifficultyLevel = "medium"
    ) -> Dict[DifficultyLevel, int]:
        """
        Recommend optimal distribution of question difficulties
        
        Args:
            content_analyses: Analysis results for content chunks
            total_questions: Total number of questions to generate
            preferred_difficulty: User's preferred difficulty level
            
        Returns:
            Recommended number of questions per difficulty level
        """
        # Calculate average potential by difficulty
        avg_potential = {
            "easy": sum(analysis.question_potential["easy"] for analysis in content_analyses) / len(content_analyses),
            "medium": sum(analysis.question_potential["medium"] for analysis in content_analyses) / len(content_analyses),
            "hard": sum(analysis.question_potential["hard"] for analysis in content_analyses) / len(content_analyses)
        }
        
        # Base distribution strategies
        distributions = {
            "easy": {"easy": 0.6, "medium": 0.3, "hard": 0.1},
            "medium": {"easy": 0.3, "medium": 0.5, "hard": 0.2},
            "hard": {"easy": 0.2, "medium": 0.3, "hard": 0.5}
        }
        
        base_dist = distributions[preferred_difficulty]
        
        # Adjust based on content potential
        adjusted_dist = {}
        for difficulty in ["easy", "medium", "hard"]:
            # Scale base distribution by content potential
            adjusted_dist[difficulty] = base_dist[difficulty] * (0.5 + avg_potential[difficulty])
        
        # Normalize to sum to 1.0
        total_weight = sum(adjusted_dist.values())
        for difficulty in adjusted_dist:
            adjusted_dist[difficulty] /= total_weight
        
        # Convert to actual question counts
        question_counts = {}
        remaining_questions = total_questions
        
        for difficulty in ["easy", "medium", "hard"]:
            if difficulty == "hard":  # Last one gets remainder
                question_counts[difficulty] = remaining_questions
            else:
                count = round(adjusted_dist[difficulty] * total_questions)
                question_counts[difficulty] = max(1, count)  # At least 1
                remaining_questions -= count
        
        return question_counts
    
    def _assess_cognitive_level(self, question: str, explanation: str) -> str:
        """Determine Bloom's taxonomy level from question and explanation"""
        text = (question + " " + explanation).lower()
        
        # Score each cognitive level
        level_scores = {}
        for level, keywords in self.cognitive_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            level_scores[level] = score
        
        # Return highest scoring level, or "understand" as default
        if not level_scores or max(level_scores.values()) == 0:
            return "understand"
        
        return max(level_scores.items(), key=lambda x: x[1])[0]
    
    def _assess_concept_complexity(self, question: str, answer: str, context: str) -> float:
        """Assess conceptual complexity based on abstract vs concrete concepts"""
        text = question + " " + answer
        
        # Count abstract concepts
        abstract_indicators = [
            r'\b(?:concept|theory|principle|framework|paradigm|approach)\b',
            r'\b(?:relationship|correlation|implication|significance)\b',
            r'\b(?:factor|aspect|element|component|characteristic)\b'
        ]
        
        abstract_count = sum(
            len(re.findall(pattern, text, re.IGNORECASE)) 
            for pattern in abstract_indicators
        )
        
        # Count concrete facts
        concrete_indicators = [
            r'\b(?:number|amount|size|weight|length|time|date)\b',
            r'\b(?:name|title|location|person|place|organization)\b',
            r'\b\d+(?:\.\d+)?(?:%|percent|degrees?|years?|months?)\b'
        ]
        
        concrete_count = sum(
            len(re.findall(pattern, text, re.IGNORECASE))
            for pattern in concrete_indicators
        )
        
        # Calculate complexity ratio
        total_indicators = abstract_count + concrete_count
        if total_indicators == 0:
            return 0.5  # Medium complexity by default
        
        return min(1.0, abstract_count / total_indicators)
    
    def _assess_vocabulary_complexity(self, text: str) -> float:
        """Assess vocabulary complexity using syllable count and technical terms"""
        words = re.findall(r'\b\w+\b', text.lower())
        if not words:
            return 0.0
        
        # Count technical terms
        technical_count = sum(
            len(re.findall(pattern, text, re.IGNORECASE)) 
            for pattern in self.technical_indicators
        )
        
        # Estimate syllable complexity (rough approximation)
        long_words = [w for w in words if len(w) > 6]  # Words with 6+ characters
        
        # Calculate complexity score
        vocab_complexity = (
            (technical_count / len(words)) * 0.6 +
            (len(long_words) / len(words)) * 0.4
        )
        
        return min(1.0, vocab_complexity)
    
    def _assess_reasoning_requirement(self, question: str, question_type: str, explanation: str) -> float:
        """Assess how much reasoning is required to answer the question"""
        text = (question + " " + explanation).lower()
        
        # Reasoning indicators
        reasoning_indicators = [
            r'\b(?:why|how|explain|analyze|compare|evaluate|justify)\b',
            r'\b(?:because|therefore|consequently|however|although)\b',
            r'\b(?:relationship|connection|difference|similarity)\b',
            r'\b(?:implication|result|outcome|effect|impact)\b'
        ]
        
        reasoning_count = sum(
            len(re.findall(pattern, text, re.IGNORECASE))
            for pattern in reasoning_indicators
        )
        
        # Question type baseline
        type_baseline = {
            "multiple_choice": 0.3,
            "true_false": 0.2,
            "short_answer": 0.5
        }
        
        base_reasoning = type_baseline.get(question_type, 0.3)
        reasoning_bonus = min(0.4, reasoning_count * 0.1)
        
        return min(1.0, base_reasoning + reasoning_bonus)
    
    def _assess_context_dependency(self, question: str, context: str) -> float:
        """Assess how much the question depends on the specific context"""
        # Find question words that appear in context
        question_words = set(re.findall(r'\b\w+\b', question.lower()))
        context_words = set(re.findall(r'\b\w+\b', context.lower()))
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        question_words -= common_words
        context_words -= common_words
        
        if not question_words:
            return 0.5
        
        # Calculate overlap
        overlap = len(question_words & context_words) / len(question_words)
        
        return min(1.0, overlap)
    
    def _assess_prior_knowledge(self, question: str, context: str) -> float:
        """Assess how much prior knowledge is needed beyond the context"""
        text = question.lower()
        
        # Indicators of prior knowledge requirements
        prior_knowledge_indicators = [
            r'\b(?:typically|generally|commonly|usually|often)\b',
            r'\b(?:traditional|conventional|standard|normal)\b',
            r'\b(?:similar|different|unlike|compared to)\b',
            r'\b(?:field|domain|discipline|industry)\b'
        ]
        
        prior_knowledge_count = sum(
            len(re.findall(pattern, text, re.IGNORECASE))
            for pattern in prior_knowledge_indicators
        )
        
        return min(1.0, prior_knowledge_count * 0.2)
    
    def _calculate_overall_difficulty(self, factors: DifficultyFactors) -> DifficultyLevel:
        """Calculate overall difficulty from individual factors"""
        # Weighted combination of factors
        weights = {
            "cognitive_level": 0.25,
            "concept_complexity": 0.2,
            "vocabulary_complexity": 0.15,
            "reasoning_required": 0.2,
            "context_dependency": 0.1,
            "prior_knowledge_needed": 0.1
        }
        
        # Convert cognitive level to numeric score
        cognitive_score = self.bloom_levels.get(factors.cognitive_level, 2) / 6.0
        
        # Calculate weighted score
        overall_score = (
            weights["cognitive_level"] * cognitive_score +
            weights["concept_complexity"] * factors.concept_complexity +
            weights["vocabulary_complexity"] * factors.vocabulary_complexity +
            weights["reasoning_required"] * factors.reasoning_required +
            weights["context_dependency"] * factors.context_dependency +
            weights["prior_knowledge_needed"] * factors.prior_knowledge_needed
        )
        
        # Convert to difficulty level
        if overall_score < 0.4:
            return "easy"
        elif overall_score < 0.7:
            return "medium"
        else:
            return "hard"
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        # Look for noun phrases and technical terms
        concept_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Title case phrases
            r'\b(?:method|approach|technique|strategy|process|system)\b',
            r'\b(?:analysis|evaluation|assessment|measurement|calculation)\b'
        ]
        
        concepts = []
        for pattern in concept_patterns:
            concepts.extend(re.findall(pattern, text))
        
        return list(set(concepts))[:10]  # Limit to top 10
    
    def _extract_technical_terms(self, text: str) -> List[str]:
        """Extract technical terms from text"""
        technical_terms = []
        
        # Use predefined patterns
        for pattern in self.technical_indicators:
            technical_terms.extend(re.findall(pattern, text, re.IGNORECASE))
        
        # Add domain-specific terms (extend as needed)
        domain_patterns = [
            r'\b(?:algorithm|neural|network|learning|training|model)\b',
            r'\b(?:data|dataset|feature|parameter|variable|metric)\b',
            r'\b(?:performance|accuracy|precision|recall|validation)\b'
        ]
        
        for pattern in domain_patterns:
            technical_terms.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return list(set(technical_terms))[:15]  # Limit to top 15
    
    def _extract_factual_statements(self, text: str) -> List[str]:
        """Extract factual statements from text"""
        # Simple sentence splitting - could be enhanced with NLP
        sentences = re.split(r'[.!?]+', text)
        
        factual_indicators = [
            r'\b(?:is|are|was|were|has|have|had)\b',
            r'\b(?:shows?|demonstrates?|indicates?|reveals?)\b',
            r'\b(?:found|discovered|observed|noted|reported)\b',
            r'\b\d+(?:\.\d+)?(?:%|percent|times|fold)\b'
        ]
        
        factual_statements = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Reasonable minimum length
                for pattern in factual_indicators:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        factual_statements.append(sentence)
                        break
        
        return factual_statements[:20]  # Limit to top 20
    
    def _extract_relationships(self, text: str) -> List[Tuple[str, str]]:
        """Extract relationships between concepts"""
        relationship_patterns = [
            (r'([A-Za-z ]+)\s+(?:leads to|causes|results in)\s+([A-Za-z ]+)', 'causes'),
            (r'([A-Za-z ]+)\s+(?:is related to|correlates with)\s+([A-Za-z ]+)', 'related_to'),
            (r'([A-Za-z ]+)\s+(?:differs from|contrasts with)\s+([A-Za-z ]+)', 'differs_from'),
        ]
        
        relationships = []
        for pattern, relation_type in relationship_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                relationships.append((match[0].strip(), match[1].strip()))
        
        return relationships[:10]  # Limit to top 10
    
    def _calculate_content_complexity(self, text: str, technical_terms: List[str], key_concepts: List[str]) -> float:
        """Calculate overall content complexity score"""
        word_count = len(re.findall(r'\b\w+\b', text))
        if word_count == 0:
            return 0.0
        
        # Factors contributing to complexity
        technical_density = len(technical_terms) / word_count
        concept_density = len(key_concepts) / word_count
        avg_word_length = sum(len(word) for word in re.findall(r'\b\w+\b', text)) / word_count
        sentence_count = len(re.split(r'[.!?]+', text))
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Weighted complexity score
        complexity = (
            technical_density * 0.3 +
            concept_density * 0.2 +
            (avg_word_length - 4) / 10 * 0.2 +  # Normalize around 4-letter words
            min(avg_sentence_length / 20, 1.0) * 0.3  # Cap at 20 words per sentence
        )
        
        return min(1.0, complexity)
    
    def _calculate_information_density(self, text: str) -> float:
        """Calculate information density of content"""
        # Count informative elements
        informative_patterns = [
            r'\b\d+(?:\.\d+)?(?:%|percent|degrees?|years?|months?)\b',  # Numbers with units
            r'\b(?:Figure|Table|Section|Chapter)\s+\d+\b',  # References
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Proper nouns/titles
            r'\([^)]+\)',  # Parenthetical information
        ]
        
        total_informative = sum(
            len(re.findall(pattern, text))
            for pattern in informative_patterns
        )
        
        word_count = len(re.findall(r'\b\w+\b', text))
        return min(1.0, total_informative / max(word_count, 1))
    
    def _assess_easy_question_potential(self, factual_statements: List[str], technical_terms: List[str]) -> float:
        """Assess potential for generating easy questions"""
        return min(1.0, (len(factual_statements) * 0.1) + (len(technical_terms) * 0.05))
    
    def _assess_medium_question_potential(self, key_concepts: List[str], relationships: List[Tuple[str, str]]) -> float:
        """Assess potential for generating medium questions"""
        return min(1.0, (len(key_concepts) * 0.08) + (len(relationships) * 0.15))
    
    def _assess_hard_question_potential(self, relationships: List[Tuple[str, str]], complexity_score: float) -> float:
        """Assess potential for generating hard questions"""
        return min(1.0, (len(relationships) * 0.1) + (complexity_score * 0.8))


def test_difficulty_assessor():
    """Test difficulty assessment functionality"""
    assessor = DifficultyAssessor()
    
    # Test question difficulty assessment
    sample_question = "Analyze the implications of the proposed methodology for real-world applications"
    sample_answer = "The methodology has significant implications for industrial automation and decision support systems"
    sample_context = "The research demonstrates novel algorithmic improvements that address scalability and accuracy limitations"
    
    difficulty, factors = assessor.assess_question_difficulty(
        sample_question, "short_answer", sample_answer, sample_context
    )
    
    print(f"✓ Question difficulty assessed: {difficulty}")
    print(f"✓ Cognitive level: {factors.cognitive_level}")
    print(f"✓ Concept complexity: {factors.concept_complexity:.2f}")
    
    # Test content analysis
    sample_content = """
    Machine learning algorithms enable computers to learn patterns from data without explicit programming.
    Cross-validation techniques and statistical significance testing were employed to validate results.
    The proposed approach demonstrates a 15% improvement in accuracy compared to baseline methods.
    Applications include industrial automation, data processing pipelines, and real-time decision support systems.
    """
    
    analysis = assessor.analyze_content_chunk(sample_content)
    print(f"✓ Content analyzed - complexity: {analysis.complexity_score:.2f}")
    print(f"✓ Key concepts found: {len(analysis.key_concepts)}")
    print(f"✓ Technical terms: {len(analysis.technical_terms)}")
    
    # Test question distribution recommendation
    distribution = assessor.recommend_question_distribution([analysis], 10, "medium")
    print(f"✓ Question distribution: {distribution}")
    
    return assessor


if __name__ == "__main__":
    test_difficulty_assessor()
"""Question evaluation and scoring service for quiz answers"""

import logging
import re
import time
from typing import Dict, List, Tuple, Optional, Any, Literal
from dataclasses import dataclass
from difflib import SequenceMatcher

from app.services.embeddings import generate_embeddings

logger = logging.getLogger(__name__)

QuestionType = Literal["multiple_choice", "true_false", "short_answer"]


@dataclass
class EvaluationResult:
    """Result of answer evaluation"""
    is_correct: bool
    score: float  # 0.0 to 1.0
    max_score: float
    feedback: str
    detailed_feedback: Dict[str, Any]
    evaluation_method: str
    processing_time: float


@dataclass
class AnswerAnalysis:
    """Analysis of user answer"""
    normalized_answer: str
    key_terms: List[str]
    semantic_similarity: Optional[float] = None
    keyword_matches: List[str] = None
    partial_credit_factors: Dict[str, float] = None


class QuestionEvaluator:
    """Evaluates quiz answers and provides detailed feedback"""
    
    def __init__(self):
        self.similarity_threshold = 0.75  # For semantic similarity
        self.keyword_match_threshold = 0.6  # For keyword-based scoring
        self.partial_credit_enabled = True
        
        # Common correct answer patterns
        self.true_patterns = [
            "true", "yes", "correct", "right", "accurate", "valid"
        ]
        self.false_patterns = [
            "false", "no", "incorrect", "wrong", "inaccurate", "invalid"
        ]
        
        # Stop words for keyword extraction
        self.stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", 
            "for", "of", "with", "by", "is", "are", "was", "were", "be",
            "been", "being", "have", "has", "had", "will", "would", "could",
            "should", "may", "might", "can", "do", "does", "did", "get",
            "got", "go", "going", "went", "come", "came", "take", "took"
        }
    
    async def evaluate_answer(
        self,
        question: Dict[str, Any],
        user_answer: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        Evaluate a user's answer to a quiz question
        
        Args:
            question: Question data including type, correct answer, etc.
            user_answer: User's submitted answer
            context: Optional additional context for evaluation
            
        Returns:
            EvaluationResult with score, feedback, and analysis
        """
        start_time = time.time()
        
        question_type = question.get("type", "multiple_choice")
        correct_answer = question.get("correct_answer", "")
        
        logger.debug(
            "Evaluating answer",
            extra={
                "question_id": question.get("id"),
                "question_type": question_type,
                "user_answer_length": len(user_answer)
            }
        )
        
        try:
            # Route to appropriate evaluation method
            if question_type == "multiple_choice":
                result = await self._evaluate_multiple_choice(question, user_answer)
            elif question_type == "true_false":
                result = await self._evaluate_true_false(question, user_answer)
            elif question_type == "short_answer":
                result = await self._evaluate_short_answer(question, user_answer, context)
            else:
                raise ValueError(f"Unsupported question type: {question_type}")
            
            # Add processing time
            result.processing_time = time.time() - start_time
            
            logger.info(
                "Answer evaluated",
                extra={
                    "question_id": question.get("id"),
                    "is_correct": result.is_correct,
                    "score": result.score,
                    "processing_time": result.processing_time
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Answer evaluation failed",
                extra={
                    "question_id": question.get("id"),
                    "error": str(e)
                },
                exc_info=True
            )
            
            # Return error result
            return EvaluationResult(
                is_correct=False,
                score=0.0,
                max_score=1.0,
                feedback="Unable to evaluate answer due to system error.",
                detailed_feedback={"error": str(e)},
                evaluation_method="error",
                processing_time=time.time() - start_time
            )
    
    async def _evaluate_multiple_choice(
        self,
        question: Dict[str, Any],
        user_answer: str
    ) -> EvaluationResult:
        """Evaluate multiple choice answer"""
        
        correct_answer = question.get("correct_answer", "")
        options = question.get("options", [])
        
        # Normalize answers for comparison
        user_answer_norm = user_answer.strip()
        correct_answer_norm = correct_answer.strip()
        
        # Direct match check
        is_correct = False
        match_method = "no_match"
        
        if user_answer_norm == correct_answer_norm:
            is_correct = True
            match_method = "exact_match"
        else:
            # Check if user answer matches any option exactly
            for option in options:
                if user_answer_norm.lower() == option.strip().lower():
                    if option.strip().lower() == correct_answer_norm.lower():
                        is_correct = True
                        match_method = "option_match"
                    break
            
            # Check partial matches within correct answer
            if not is_correct:
                if user_answer_norm.lower() in correct_answer_norm.lower():
                    is_correct = True
                    match_method = "partial_match"
                elif correct_answer_norm.lower() in user_answer_norm.lower():
                    is_correct = True
                    match_method = "contains_match"
        
        # Generate feedback
        if is_correct:
            feedback = f"Correct! {question.get('explanation', '')}"
        else:
            feedback = f"Incorrect. The correct answer is: {correct_answer}. {question.get('explanation', '')}"
        
        detailed_feedback = {
            "match_method": match_method,
            "correct_answer": correct_answer,
            "user_answer": user_answer_norm,
            "available_options": options
        }
        
        return EvaluationResult(
            is_correct=is_correct,
            score=1.0 if is_correct else 0.0,
            max_score=1.0,
            feedback=feedback.strip(),
            detailed_feedback=detailed_feedback,
            evaluation_method="multiple_choice_exact",
            processing_time=0.0  # Will be set by caller
        )
    
    async def _evaluate_true_false(
        self,
        question: Dict[str, Any],
        user_answer: str
    ) -> EvaluationResult:
        """Evaluate true/false answer"""
        
        correct_answer = question.get("correct_answer", "").lower().strip()
        user_answer_norm = user_answer.lower().strip()
        
        # Determine user's intent
        user_intent = None
        
        # Check direct matches
        if user_answer_norm in ["true", "t", "1", "yes", "y"]:
            user_intent = "true"
        elif user_answer_norm in ["false", "f", "0", "no", "n"]:
            user_intent = "false"
        else:
            # Check pattern matches
            for pattern in self.true_patterns:
                if pattern in user_answer_norm:
                    user_intent = "true"
                    break
            
            if not user_intent:
                for pattern in self.false_patterns:
                    if pattern in user_answer_norm:
                        user_intent = "false"
                        break
        
        # Evaluate correctness
        is_correct = False
        evaluation_confidence = 1.0
        
        if user_intent == correct_answer:
            is_correct = True
        elif user_intent is None:
            # Ambiguous answer
            evaluation_confidence = 0.5
        
        # Generate feedback
        if is_correct:
            feedback = f"Correct! {question.get('explanation', '')}"
        elif user_intent is None:
            feedback = f"Your answer is unclear. The correct answer is '{correct_answer.capitalize()}'. {question.get('explanation', '')}"
        else:
            feedback = f"Incorrect. The correct answer is '{correct_answer.capitalize()}'. {question.get('explanation', '')}"
        
        detailed_feedback = {
            "user_intent": user_intent,
            "correct_answer": correct_answer,
            "evaluation_confidence": evaluation_confidence,
            "original_answer": user_answer
        }
        
        return EvaluationResult(
            is_correct=is_correct,
            score=1.0 if is_correct else 0.0,
            max_score=1.0,
            feedback=feedback.strip(),
            detailed_feedback=detailed_feedback,
            evaluation_method="true_false_pattern",
            processing_time=0.0
        )
    
    async def _evaluate_short_answer(
        self,
        question: Dict[str, Any],
        user_answer: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """Evaluate short answer with multiple scoring methods"""
        
        correct_answer = question.get("correct_answer", "")
        
        if not user_answer.strip():
            return EvaluationResult(
                is_correct=False,
                score=0.0,
                max_score=1.0,
                feedback="No answer provided.",
                detailed_feedback={"error": "empty_answer"},
                evaluation_method="short_answer_empty",
                processing_time=0.0
            )
        
        # Analyze both answers
        user_analysis = await self._analyze_answer(user_answer)
        correct_analysis = await self._analyze_answer(correct_answer)
        
        # Multiple evaluation methods
        evaluation_methods = []
        
        # Method 1: Keyword-based evaluation
        keyword_score = self._evaluate_keywords(user_analysis, correct_analysis)
        evaluation_methods.append(("keyword", keyword_score))
        
        # Method 2: String similarity
        similarity_score = self._evaluate_string_similarity(user_answer, correct_answer)
        evaluation_methods.append(("similarity", similarity_score))
        
        # Method 3: Semantic similarity (using embeddings)
        try:
            semantic_score = await self._evaluate_semantic_similarity(user_answer, correct_answer)
            evaluation_methods.append(("semantic", semantic_score))
        except Exception as e:
            logger.debug(f"Semantic evaluation failed: {e}")
            semantic_score = 0.0
        
        # Method 4: Contextual evaluation (if context provided)
        contextual_score = 0.0
        if context and context.get("source_content"):
            contextual_score = self._evaluate_contextual_accuracy(
                user_answer, context["source_content"]
            )
            evaluation_methods.append(("contextual", contextual_score))
        
        # Combine scores using weighted average
        final_score = self._combine_evaluation_scores(evaluation_methods)
        
        # Determine correctness and partial credit
        is_correct, partial_credit = self._determine_correctness(final_score)
        
        # Generate detailed feedback
        feedback = self._generate_short_answer_feedback(
            user_answer, correct_answer, final_score, evaluation_methods,
            question.get("explanation", "")
        )
        
        detailed_feedback = {
            "final_score": final_score,
            "evaluation_methods": dict(evaluation_methods),
            "keyword_matches": user_analysis.keyword_matches or [],
            "partial_credit_factors": user_analysis.partial_credit_factors or {},
            "semantic_similarity": semantic_score,
            "user_key_terms": user_analysis.key_terms,
            "expected_key_terms": correct_analysis.key_terms
        }
        
        return EvaluationResult(
            is_correct=is_correct,
            score=final_score,
            max_score=1.0,
            feedback=feedback,
            detailed_feedback=detailed_feedback,
            evaluation_method="short_answer_hybrid",
            processing_time=0.0
        )
    
    async def _analyze_answer(self, answer: str) -> AnswerAnalysis:
        """Analyze answer text for key components"""
        
        # Normalize text
        normalized = re.sub(r'[^\w\s]', '', answer.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Extract key terms (non-stop words)
        words = normalized.split()
        key_terms = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        return AnswerAnalysis(
            normalized_answer=normalized,
            key_terms=key_terms
        )
    
    def _evaluate_keywords(self, user_analysis: AnswerAnalysis, correct_analysis: AnswerAnalysis) -> float:
        """Evaluate answer based on keyword matching"""
        
        if not correct_analysis.key_terms:
            return 0.5  # No keywords to match against
        
        user_terms = set(user_analysis.key_terms)
        correct_terms = set(correct_analysis.key_terms)
        
        # Calculate overlap
        matches = user_terms & correct_terms
        match_ratio = len(matches) / len(correct_terms)
        
        # Store matches for feedback
        user_analysis.keyword_matches = list(matches)
        
        # Bonus for having additional relevant terms
        extra_terms = user_terms - correct_terms
        bonus = min(0.2, len(extra_terms) * 0.05)
        
        return min(1.0, match_ratio + bonus)
    
    def _evaluate_string_similarity(self, user_answer: str, correct_answer: str) -> float:
        """Evaluate using string similarity"""
        
        # Normalize both answers
        user_norm = re.sub(r'[^\w\s]', '', user_answer.lower()).strip()
        correct_norm = re.sub(r'[^\w\s]', '', correct_answer.lower()).strip()
        
        # Use sequence matcher for similarity
        similarity = SequenceMatcher(None, user_norm, correct_norm).ratio()
        
        return similarity
    
    async def _evaluate_semantic_similarity(self, user_answer: str, correct_answer: str) -> float:
        """Evaluate using semantic similarity via embeddings"""
        
        try:
            # Generate embeddings for both answers
            answers = [user_answer, correct_answer]
            embeddings = await generate_embeddings(answers)
            
            if len(embeddings) != 2:
                return 0.0
            
            user_embedding = embeddings[0]
            correct_embedding = embeddings[1]
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(user_embedding, correct_embedding)
            
            return max(0.0, similarity)  # Ensure non-negative
            
        except Exception as e:
            logger.debug(f"Semantic similarity calculation failed: {e}")
            return 0.0
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        
        import math
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _evaluate_contextual_accuracy(self, user_answer: str, source_content: str) -> float:
        """Evaluate answer accuracy against source context"""
        
        # Simple implementation - check if key terms from answer appear in source
        user_words = set(re.findall(r'\w+', user_answer.lower()))
        source_words = set(re.findall(r'\w+', source_content.lower()))
        
        # Remove stop words
        user_words -= self.stop_words
        source_words -= self.stop_words
        
        if not user_words:
            return 0.0
        
        # Calculate how many user terms are supported by source
        supported_terms = user_words & source_words
        support_ratio = len(supported_terms) / len(user_words)
        
        return support_ratio
    
    def _combine_evaluation_scores(self, evaluation_methods: List[Tuple[str, float]]) -> float:
        """Combine multiple evaluation scores using weighted average"""
        
        # Weights for different evaluation methods
        method_weights = {
            "keyword": 0.4,
            "semantic": 0.3,
            "similarity": 0.2,
            "contextual": 0.1
        }
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for method, score in evaluation_methods:
            weight = method_weights.get(method, 0.1)
            weighted_score += score * weight
            total_weight += weight
        
        # Normalize by actual total weight used
        if total_weight > 0:
            final_score = weighted_score / total_weight
        else:
            final_score = 0.0
        
        return min(1.0, final_score)
    
    def _determine_correctness(self, score: float) -> Tuple[bool, Dict[str, Any]]:
        """Determine if answer is correct and calculate partial credit"""
        
        # Correctness thresholds
        if score >= 0.8:
            is_correct = True
            credit_level = "full"
        elif score >= 0.6:
            is_correct = True  # Partial credit counts as correct
            credit_level = "high_partial"
        elif score >= 0.4:
            is_correct = self.partial_credit_enabled
            credit_level = "medium_partial"
        elif score >= 0.2:
            is_correct = False
            credit_level = "low_partial"
        else:
            is_correct = False
            credit_level = "none"
        
        partial_credit = {
            "level": credit_level,
            "threshold_met": score >= 0.4,
            "score": score
        }
        
        return is_correct, partial_credit
    
    def _generate_short_answer_feedback(
        self,
        user_answer: str,
        correct_answer: str,
        score: float,
        evaluation_methods: List[Tuple[str, float]],
        explanation: str
    ) -> str:
        """Generate detailed feedback for short answer questions"""
        
        feedback_parts = []
        
        # Overall assessment
        if score >= 0.8:
            feedback_parts.append("Excellent answer!")
        elif score >= 0.6:
            feedback_parts.append("Good answer with room for improvement.")
        elif score >= 0.4:
            feedback_parts.append("Partially correct answer.")
        else:
            feedback_parts.append("Answer needs significant improvement.")
        
        # Specific feedback based on evaluation methods
        method_scores = dict(evaluation_methods)
        
        if "keyword" in method_scores:
            keyword_score = method_scores["keyword"]
            if keyword_score < 0.5:
                feedback_parts.append("Your answer is missing some key terms from the expected answer.")
            elif keyword_score > 0.8:
                feedback_parts.append("You included the important key terms.")
        
        if "semantic" in method_scores:
            semantic_score = method_scores["semantic"]
            if semantic_score < 0.5:
                feedback_parts.append("The meaning of your answer differs from what was expected.")
        
        # Add explanation if provided
        if explanation:
            feedback_parts.append(f"Explanation: {explanation}")
        
        # Show expected answer for low scores
        if score < 0.6:
            feedback_parts.append(f"Expected answer: {correct_answer}")
        
        return " ".join(feedback_parts)
    
    async def evaluate_quiz_submission(
        self,
        questions: List[Dict[str, Any]],
        user_answers: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate complete quiz submission
        
        Args:
            questions: List of question data
            user_answers: List of user answer data
            context: Optional additional context
            
        Returns:
            Complete evaluation results
        """
        start_time = time.time()
        
        # Create answer lookup
        answer_lookup = {
            answer["question_id"]: answer["answer"]
            for answer in user_answers
        }
        
        # Evaluate each question
        question_results = []
        total_score = 0.0
        total_possible = 0.0
        
        for question in questions:
            question_id = question.get("id", "")
            user_answer = answer_lookup.get(question_id, "")
            
            result = await self.evaluate_answer(question, user_answer, context)
            
            question_results.append({
                "question_id": question_id,
                "result": result,
                "user_answer": user_answer
            })
            
            total_score += result.score
            total_possible += result.max_score
        
        # Calculate overall statistics
        percentage = (total_score / total_possible * 100) if total_possible > 0 else 0
        correct_count = sum(1 for qr in question_results if qr["result"].is_correct)
        
        # Determine pass/fail (70% threshold)
        passed = percentage >= 70.0
        
        processing_time = time.time() - start_time
        
        return {
            "total_score": total_score,
            "max_score": total_possible,
            "percentage": percentage,
            "correct_answers": correct_count,
            "total_questions": len(questions),
            "passed": passed,
            "question_results": question_results,
            "processing_time": processing_time,
            "evaluation_summary": self._generate_evaluation_summary(question_results)
        }
    
    def _generate_evaluation_summary(self, question_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of evaluation results"""
        
        # Analyze by question type
        type_performance = {}
        method_performance = {}
        
        for qr in question_results:
            result = qr["result"]
            question_id = qr["question_id"]
            
            # Track performance by evaluation method
            method = result.evaluation_method
            if method not in method_performance:
                method_performance[method] = {"scores": [], "correct": 0, "total": 0}
            
            method_performance[method]["scores"].append(result.score)
            method_performance[method]["total"] += 1
            if result.is_correct:
                method_performance[method]["correct"] += 1
        
        # Calculate averages
        for method, data in method_performance.items():
            data["average_score"] = sum(data["scores"]) / len(data["scores"])
            data["accuracy"] = data["correct"] / data["total"] if data["total"] > 0 else 0
        
        return {
            "method_performance": method_performance,
            "overall_accuracy": sum(qr["result"].score for qr in question_results) / len(question_results),
            "questions_evaluated": len(question_results)
        }


def test_question_evaluator():
    """Test question evaluation functionality"""
    
    async def run_tests():
        evaluator = QuestionEvaluator()
        
        # Test multiple choice evaluation
        mc_question = {
            "id": "q1",
            "type": "multiple_choice",
            "question": "What is machine learning?",
            "options": ["AI subset", "Programming language", "Hardware", "Software"],
            "correct_answer": "AI subset",
            "explanation": "Machine learning is a subset of AI"
        }
        
        result1 = await evaluator.evaluate_answer(mc_question, "AI subset")
        print(f"✓ Multiple choice (correct): {result1.is_correct}, score: {result1.score}")
        
        result2 = await evaluator.evaluate_answer(mc_question, "Programming language")
        print(f"✓ Multiple choice (incorrect): {result2.is_correct}, score: {result2.score}")
        
        # Test true/false evaluation
        tf_question = {
            "id": "q2",
            "type": "true_false",
            "question": "Machine learning uses data to learn patterns.",
            "correct_answer": "true",
            "explanation": "This is correct"
        }
        
        result3 = await evaluator.evaluate_answer(tf_question, "yes")
        print(f"✓ True/false (correct): {result3.is_correct}, score: {result3.score}")
        
        # Test short answer evaluation
        sa_question = {
            "id": "q3",
            "type": "short_answer",
            "question": "Explain cross-validation",
            "correct_answer": "Cross-validation is a technique to validate model performance by splitting data into training and testing sets",
            "explanation": "Used for robust validation"
        }
        
        result4 = await evaluator.evaluate_answer(
            sa_question, 
            "Cross validation splits data to test model performance"
        )
        print(f"✓ Short answer evaluation: {result4.is_correct}, score: {result4.score:.2f}")
        
        print("✓ Question evaluator tests completed")
        return evaluator
    
    import asyncio
    return asyncio.run(run_tests())


if __name__ == "__main__":
    test_question_evaluator()
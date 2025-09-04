"""Quiz generation and submission endpoints"""

import logging
import uuid
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from uuid import UUID

from app.models.quiz import (
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizSubmitRequest, 
    QuizSubmitResponse,
    QuizQuestion,
    QuizResult,
    QuizConfig
)
from app.api.deps import get_current_user_id, get_trace_id

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=QuizGenerateResponse)
async def generate_quiz(
    request: QuizGenerateRequest,
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    Generate quiz from document content
    
    Process:
    1. Sample relevant chunks from document (spread across sections)
    2. Use LLM to generate questions from selected chunks
    3. Create mix of question types (MC, True/False, Short Answer)
    4. Store quiz for later submission
    5. Return questions for user interaction
    
    Generated questions include source references for learning feedback.
    """
    logger.info(
        "Quiz generation started",
        extra={
            "trace_id": trace_id,
            "document_id": str(request.document_id),
            "user_id": str(user_id),
            "question_count": request.config.question_count,
            "difficulty": request.config.difficulty,
            "question_types": request.config.question_types
        }
    )
    
    # DUMMY: Generate sample quiz questions
    quiz_id = UUID(f"{uuid.uuid4()}")
    
    dummy_questions = [
        QuizQuestion(
            id="q1",
            type="multiple_choice",
            question="What is the primary methodology used in the research?",
            options=[
                "Cross-validation with statistical significance testing",
                "Simple randomized controlled trial",
                "Observational case study analysis", 
                "Theoretical mathematical modeling"
            ],
            correctAnswer="Cross-validation with statistical significance testing",
            explanation="The document explicitly states that cross-validation techniques and statistical significance testing were employed to validate results, as mentioned in the methodology section.",
            sourceChunkId=UUID("660e8400-e29b-41d4-a716-446655440000"),
            difficulty="medium"
        ),
        QuizQuestion(
            id="q2", 
            type="true_false",
            question="The research findings show statistical significance with p < 0.05.",
            options=None,
            correctAnswer="true",
            explanation="The document clearly states that statistical analysis reveals the observed improvements are statistically significant (p < 0.05).",
            sourceChunkId=UUID("660e8400-e29b-41d4-a716-446655440002"),
            difficulty="easy"
        ),
        QuizQuestion(
            id="q3",
            type="multiple_choice", 
            question="According to the document, what was the performance improvement compared to baseline approaches?",
            options=[
                "5% increase in accuracy",
                "10% increase in accuracy",
                "15% increase in accuracy",
                "20% increase in accuracy"
            ],
            correctAnswer="15% increase in accuracy",
            explanation="The experimental results section specifically mentions a 15% increase in accuracy compared to baseline approaches.",
            sourceChunkId=UUID("660e8400-e29b-41d4-a716-446655440000"),
            difficulty="easy"
        ),
        QuizQuestion(
            id="q4",
            type="short_answer",
            question="What are the main application domains mentioned for the research findings?",
            options=None,
            correctAnswer="industrial automation, data processing pipelines, real-time decision support systems",
            explanation="The conclusions section mentions three key application domains: industrial automation, data processing pipelines, and real-time decision support systems.",
            sourceChunkId=UUID("660e8400-e29b-41d4-a716-446655440002"),
            difficulty="medium"
        ),
        QuizQuestion(
            id="q5",
            type="true_false",
            question="The proposed approach addresses limitations identified in earlier studies.",
            options=None,
            correctAnswer="true", 
            explanation="The discussion section explicitly states that the approach addresses key limitations identified in earlier studies.",
            sourceChunkId=UUID("660e8400-e29b-41d4-a716-446655440001"),
            difficulty="easy"
        )
    ]
    
    # Filter questions based on requested count and types
    filtered_questions = []
    for q in dummy_questions:
        if len(filtered_questions) >= request.config.question_count:
            break
        if q.type in request.config.question_types:
            filtered_questions.append(q)
    
    # If not enough questions, pad with remaining questions regardless of type
    while len(filtered_questions) < request.config.question_count and len(filtered_questions) < len(dummy_questions):
        for q in dummy_questions:
            if q not in filtered_questions:
                filtered_questions.append(q)
                break
    
    return QuizGenerateResponse(
        quiz_id=quiz_id,
        document_id=request.document_id,
        questions=filtered_questions,
        config=request.config,
        expires_at=(datetime.utcnow() + timedelta(hours=24)).isoformat(),
        trace_id=trace_id
    )


@router.post("/submit", response_model=QuizSubmitResponse)
async def submit_quiz(
    request: QuizSubmitRequest,
    user_id: UUID = Depends(get_current_user_id),
    trace_id: Optional[str] = Depends(get_trace_id)
):
    """
    Submit quiz answers and get results
    
    Process:
    1. Load quiz questions and correct answers
    2. Evaluate each submitted answer
    3. Calculate score and generate feedback
    4. Store results for analytics and progress tracking
    5. Return detailed breakdown with explanations
    
    Provides explanations for incorrect answers to support learning.
    """
    logger.info(
        "Quiz submission started",
        extra={
            "trace_id": trace_id,
            "quiz_id": str(request.quiz_id),
            "user_id": str(user_id),
            "answers_count": len(request.answers),
            "total_time_seconds": request.total_time_seconds
        }
    )
    
    # DUMMY: Simulate grading with realistic results
    submission_id = UUID(f"{uuid.uuid4()}")
    
    # Sample correct answers (matching the generated quiz above)
    correct_answers = {
        "q1": "Cross-validation with statistical significance testing",
        "q2": "true", 
        "q3": "15% increase in accuracy",
        "q4": "industrial automation, data processing pipelines, real-time decision support systems",
        "q5": "true"
    }
    
    results = []
    total_score = 0.0
    max_score = len(request.answers) * 1.0  # 1 point per question
    
    for answer in request.answers:
        question_id = answer.question_id
        user_answer = answer.answer.lower().strip() if answer.answer else ""
        
        # Get correct answer
        correct_answer = correct_answers.get(question_id, "").lower().strip()
        
        # Simple evaluation logic
        is_correct = False
        if question_id in ["q2", "q5"]:  # True/False questions
            is_correct = user_answer == correct_answer
        elif question_id in ["q1", "q3"]:  # Multiple choice
            is_correct = user_answer in correct_answer
        elif question_id == "q4":  # Short answer - partial credit
            keywords = ["automation", "processing", "decision", "support"]
            matched_keywords = sum(1 for kw in keywords if kw in user_answer)
            is_correct = matched_keywords >= 2  # At least 2 keywords
        
        points_earned = 1.0 if is_correct else 0.0
        total_score += points_earned
        
        results.append(QuizResult(
            questionId=question_id,
            userAnswer=answer.answer,
            correctAnswer=correct_answers.get(question_id, "Unknown"),
            isCorrect=is_correct,
            explanation=f"Explanation for question {question_id} based on document content.",
            pointsEarned=points_earned,
            maxPoints=1.0
        ))
    
    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    passed = percentage >= 70.0  # 70% pass threshold
    correct_count = sum(1 for r in results if r.is_correct)
    
    return QuizSubmitResponse(
        quiz_id=request.quiz_id,
        submission_id=submission_id,
        score=total_score,
        max_score=max_score,
        percentage=percentage,
        passed=passed,
        results=results,
        total_questions=len(request.answers),
        correct_answers=correct_count,
        time_spent_seconds=request.total_time_seconds,
        trace_id=trace_id
    )
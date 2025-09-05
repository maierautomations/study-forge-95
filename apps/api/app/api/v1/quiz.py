"""Quiz generation and submission endpoints"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
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
from app.services.quiz import QuizOrchestrator
from app.services.quiz.question_generator import QuestionType, DifficultyLevel
from app.services.quiz.quiz_orchestrator import QuizConfig as ServiceQuizConfig

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
    
    try:
        # Convert API models to service models
        question_types = []
        for qtype in request.config.question_types:
            if qtype == "multiple_choice":
                question_types.append(QuestionType.MULTIPLE_CHOICE)
            elif qtype == "true_false":
                question_types.append(QuestionType.TRUE_FALSE)
            elif qtype == "short_answer":
                question_types.append(QuestionType.SHORT_ANSWER)
        
        # Convert difficulty if specified
        difficulty = None
        if request.config.difficulty:
            if request.config.difficulty == "easy":
                difficulty = DifficultyLevel.BEGINNER
            elif request.config.difficulty == "medium":
                difficulty = DifficultyLevel.INTERMEDIATE
            elif request.config.difficulty == "hard":
                difficulty = DifficultyLevel.ADVANCED
        
        # Create service configuration
        service_config = ServiceQuizConfig(
            question_count=request.config.question_count,
            question_types=question_types,
            difficulty=difficulty,
            time_limit_minutes=30  # Default time limit
        )
        
        # Generate quiz using orchestrator
        async with QuizOrchestrator() as orchestrator:
            quiz_result = await orchestrator.generate_quiz(
                document_id=str(request.document_id),
                user_id=str(user_id),
                config=service_config
            )
        
        # Convert service questions to API models
        api_questions = []
        for q in quiz_result["questions"]:
            # Convert question type
            question_type = q["type"]
            if question_type == "multiple_choice":
                api_type = "multiple_choice"
            elif question_type == "true_false":
                api_type = "true_false"
            elif question_type == "short_answer":
                api_type = "short_answer"
            else:
                api_type = "multiple_choice"  # fallback
            
            # Convert difficulty
            difficulty_str = q.get("difficulty", "beginner")
            if difficulty_str == "beginner":
                api_difficulty = "easy"
            elif difficulty_str == "intermediate":
                api_difficulty = "medium"
            elif difficulty_str == "advanced":
                api_difficulty = "hard"
            else:
                api_difficulty = "easy"  # fallback
            
            api_question = QuizQuestion(
                id=q["id"],
                type=api_type,
                question=q["question"],
                options=q.get("options"),
                correctAnswer=None,  # Don't send correct answer to client
                explanation=None,    # Don't send explanation to client yet
                sourceChunkId=UUID(q["source_reference"]["chunk_id"]) if q.get("source_reference") and q["source_reference"].get("chunk_id") else None,
                difficulty=api_difficulty
            )
            api_questions.append(api_question)
        
        return QuizGenerateResponse(
            quiz_id=UUID(quiz_result["attempt_id"]),
            document_id=request.document_id,
            questions=api_questions,
            config=request.config,
            expires_at=quiz_result["expires_at"],
            trace_id=trace_id
        )
        
    except Exception as e:
        logger.error(
            "Quiz generation failed",
            extra={
                "trace_id": trace_id,
                "document_id": str(request.document_id),
                "user_id": str(user_id),
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate quiz: {str(e)}"
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
    
    try:
        # Convert API answer models to service format
        service_answers = []
        for answer in request.answers:
            service_answers.append({
                "question_id": answer.question_id,
                "answer": answer.answer
            })
        
        # Submit quiz using orchestrator
        async with QuizOrchestrator() as orchestrator:
            submission_result = await orchestrator.submit_quiz_answers(
                attempt_id=str(request.quiz_id),
                answers=service_answers,
                user_id=str(user_id)
            )
        
        # Convert service results to API models
        api_results = []
        for result in submission_result["evaluation_results"]:
            api_result = QuizResult(
                questionId=result["question_id"],
                userAnswer=result["user_answer"],
                correctAnswer=None,  # Will be filled from explanation
                isCorrect=result["correct"],
                explanation=result["explanation"],
                pointsEarned=result["score"],
                maxPoints=result["max_score"]
            )
            api_results.append(api_result)
        
        # Calculate totals
        total_score = sum(r.pointsEarned for r in api_results)
        max_score = sum(r.maxPoints for r in api_results)
        percentage = submission_result["score"]  # Already calculated as percentage
        passed = percentage >= 70.0  # 70% pass threshold
        
        return QuizSubmitResponse(
            quiz_id=request.quiz_id,
            submission_id=UUID(submission_result["attempt_id"]),  # Use attempt_id as submission_id
            score=total_score,
            max_score=max_score,
            percentage=percentage,
            passed=passed,
            results=api_results,
            total_questions=submission_result["total_questions"],
            correct_answers=submission_result["correct_answers"],
            time_spent_seconds=request.total_time_seconds,
            trace_id=trace_id
        )
        
    except ValueError as e:
        logger.warning(
            "Quiz submission validation error",
            extra={
                "trace_id": trace_id,
                "quiz_id": str(request.quiz_id),
                "user_id": str(user_id),
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Quiz submission failed",
            extra={
                "trace_id": trace_id,
                "quiz_id": str(request.quiz_id),
                "user_id": str(user_id),
                "error": str(e)
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit quiz: {str(e)}"
        )
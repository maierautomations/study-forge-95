"""Quiz generation and submission models"""

from typing import List, Optional, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field

from .common import BaseResponse


class QuizConfig(BaseModel):
    """Quiz generation configuration"""
    question_count: int = Field(default=5, description="Number of questions to generate", alias="questionCount", ge=1, le=20)
    difficulty: Literal["easy", "medium", "hard"] = Field(default="medium", description="Quiz difficulty level")
    question_types: List[Literal["multiple_choice", "true_false", "short_answer"]] = Field(
        default=["multiple_choice"],
        description="Types of questions to generate",
        alias="questionTypes"
    )
    focus_sections: Optional[List[str]] = Field(
        default=None, 
        description="Specific sections to focus on (optional)",
        alias="focusSections"
    )
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "questionCount": 10,
                "difficulty": "medium",
                "questionTypes": ["multiple_choice", "true_false"],
                "focusSections": ["Introduction", "Methodology", "Results"]
            }
        }


class QuizGenerateRequest(BaseModel):
    """Quiz generation request"""
    document_id: UUID = Field(description="Document ID to generate quiz from", alias="documentId")
    config: QuizConfig = Field(description="Quiz generation configuration")
    
    class Config:
        populate_by_name = True


class QuizQuestion(BaseModel):
    """Individual quiz question"""
    id: str = Field(description="Question ID")
    type: Literal["multiple_choice", "true_false", "short_answer"] = Field(description="Question type")
    question: str = Field(description="Question text")
    options: Optional[List[str]] = Field(default=None, description="Answer options (for multiple choice)")
    correct_answer: str = Field(description="Correct answer", alias="correctAnswer")
    explanation: Optional[str] = Field(default=None, description="Explanation for the answer")
    source_chunk_id: Optional[UUID] = Field(default=None, description="Source chunk for the question", alias="sourceChunkId")
    difficulty: Literal["easy", "medium", "hard"] = Field(description="Question difficulty")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "q1",
                "type": "multiple_choice",
                "question": "What is the main hypothesis of the research?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correctAnswer": "Option B",
                "explanation": "The research clearly states that the main hypothesis focuses on...",
                "sourceChunkId": "660e8400-e29b-41d4-a716-446655440000",
                "difficulty": "medium"
            }
        }


class QuizGenerateResponse(BaseResponse):
    """Quiz generation response"""
    quiz_id: UUID = Field(description="Generated quiz ID", alias="quizId")
    document_id: UUID = Field(description="Source document ID", alias="documentId")
    questions: List[QuizQuestion] = Field(description="Generated questions")
    config: QuizConfig = Field(description="Configuration used")
    expires_at: Optional[str] = Field(default=None, description="Quiz expiration time", alias="expiresAt")
    
    class Config:
        populate_by_name = True


class QuizAnswer(BaseModel):
    """Individual quiz answer submission"""
    question_id: str = Field(description="Question ID", alias="questionId")
    answer: str = Field(description="User's answer")
    time_spent_seconds: Optional[float] = Field(default=None, description="Time spent on question", alias="timeSpentSeconds", ge=0)
    
    class Config:
        populate_by_name = True


class QuizSubmitRequest(BaseModel):
    """Quiz submission request"""
    quiz_id: UUID = Field(description="Quiz ID", alias="quizId")
    answers: List[QuizAnswer] = Field(description="User's answers")
    total_time_seconds: Optional[float] = Field(default=None, description="Total time spent", alias="totalTimeSeconds", ge=0)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "quizId": "770e8400-e29b-41d4-a716-446655440000",
                "answers": [
                    {
                        "questionId": "q1",
                        "answer": "Option B",
                        "timeSpentSeconds": 45.5
                    }
                ],
                "totalTimeSeconds": 300.0
            }
        }


class QuizResult(BaseModel):
    """Individual question result"""
    question_id: str = Field(description="Question ID", alias="questionId")
    user_answer: str = Field(description="User's answer", alias="userAnswer")
    correct_answer: str = Field(description="Correct answer", alias="correctAnswer")
    is_correct: bool = Field(description="Whether answer is correct", alias="isCorrect")
    explanation: Optional[str] = Field(default=None, description="Explanation for the answer")
    points_earned: float = Field(description="Points earned for this question", alias="pointsEarned", ge=0)
    max_points: float = Field(description="Maximum points for this question", alias="maxPoints", ge=0)
    
    class Config:
        populate_by_name = True


class QuizSubmitResponse(BaseResponse):
    """Quiz submission response with results"""
    quiz_id: UUID = Field(description="Quiz ID", alias="quizId")
    submission_id: UUID = Field(description="Submission ID", alias="submissionId")
    score: float = Field(description="Total score", ge=0)
    max_score: float = Field(description="Maximum possible score", alias="maxScore", ge=0)
    percentage: float = Field(description="Score percentage", ge=0, le=100)
    passed: bool = Field(description="Whether the quiz was passed")
    results: List[QuizResult] = Field(description="Detailed results for each question")
    total_questions: int = Field(description="Total number of questions", alias="totalQuestions", ge=0)
    correct_answers: int = Field(description="Number of correct answers", alias="correctAnswers", ge=0)
    time_spent_seconds: Optional[float] = Field(default=None, description="Total time spent", alias="timeSpentSeconds")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "quizId": "770e8400-e29b-41d4-a716-446655440000",
                "submissionId": "880e8400-e29b-41d4-a716-446655440000",
                "score": 8.0,
                "maxScore": 10.0,
                "percentage": 80.0,
                "passed": True,
                "totalQuestions": 10,
                "correctAnswers": 8,
                "timeSpentSeconds": 300.0,
                "results": [],
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
"""Question generation templates for different question types and difficulty levels"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QuestionType(Enum):
    """Question types supported by the quiz engine"""
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"

class DifficultyLevel(Enum):
    """Difficulty levels for questions"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate" 
    ADVANCED = "advanced"


@dataclass
class QuestionTemplate:
    """Template for generating questions"""
    question_type: QuestionType
    difficulty: DifficultyLevel
    system_prompt: str
    user_prompt: str
    example_response: Dict
    validation_criteria: List[str]


class QuestionTemplates:
    """Manages templates for generating different types of quiz questions"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def get_template(
        self, 
        question_type: QuestionType, 
        difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    ) -> QuestionTemplate:
        """
        Get template for specific question type and difficulty
        
        Args:
            question_type: Type of question to generate
            difficulty: Difficulty level
            
        Returns:
            Question template with prompts and examples
        """
        template_key = f"{question_type.value}_{difficulty.value}"
        
        if template_key not in self.templates:
            logger.warning(f"Template not found: {template_key}, using default")
            template_key = f"{question_type.value}_intermediate"
        
        return self.templates.get(template_key)
    
    def get_generation_prompt(
        self,
        question_type: QuestionType,
        difficulty: DifficultyLevel,
        chunk_content: str,
        question_count: int = 1,
        document_title: Optional[str] = None
    ) -> str:
        """
        Build complete prompt for question generation
        
        Args:
            question_type: Type of questions to generate
            difficulty: Difficulty level
            chunk_content: Source text content
            question_count: Number of questions to generate
            document_title: Optional document title
            
        Returns:
            Complete formatted prompt for LLM
        """
        template = self.get_template(question_type, difficulty)
        
        context = f"Document: {document_title}\\n\\n" if document_title else ""
        context += f"Source Text:\\n{chunk_content}"
        
        # Format the prompt with variables
        formatted_prompt = template.user_prompt.format(
            context=context,
            question_count=question_count,
            difficulty=difficulty.value,
            question_type=question_type.value
        )
        
        return f"{template.system_prompt}\\n\\n{formatted_prompt}"
    
    def _initialize_templates(self) -> Dict[str, QuestionTemplate]:
        """Initialize all question templates"""
        templates = {}
        
        # Multiple Choice Templates
        templates.update(self._create_multiple_choice_templates())
        
        # True/False Templates
        templates.update(self._create_true_false_templates())
        
        # Short Answer Templates
        templates.update(self._create_short_answer_templates())
        
        return templates
    
    def _create_multiple_choice_templates(self) -> Dict[str, QuestionTemplate]:
        """Create multiple choice question templates"""
        base_system = """You are an expert educational content creator specializing in generating high-quality multiple choice questions from academic texts. Your questions should test comprehension, application, and critical thinking skills."""
        
        return {
            "multiple_choice_beginner": QuestionTemplate(
                question_type=QuestionType.MULTIPLE_CHOICE,
                difficulty=DifficultyLevel.BEGINNER,
                system_prompt=base_system,
                user_prompt="""Generate {question_count} EASY multiple choice question(s) from the following content:

{context}

Requirements for EASY questions:
- Test direct facts, definitions, or explicit information
- Answer should be clearly stated in the text
- Create 4 plausible options with only 1 correct answer
- Distractors should be reasonable but clearly incorrect
- Avoid tricky wording or complex interpretations

Return as JSON array:
[{{
  "question": "Clear, direct question about factual content",
  "type": "multiple_choice", 
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_answer": "Option B",
  "explanation": "Brief explanation referencing the source text",
  "difficulty": "easy",
  "source_reference": "Quote or paraphrase from source text"
}}]""",
                example_response={
                    "question": "According to the text, what is machine learning?",
                    "type": "multiple_choice",
                    "options": [
                        "A computer virus that spreads automatically",
                        "A subset of AI that enables computers to learn from data",
                        "A type of hardware component",
                        "A programming language"
                    ],
                    "correct_answer": "A subset of AI that enables computers to learn from data",
                    "explanation": "The text explicitly states that machine learning is a subset of artificial intelligence that enables computers to learn from data.",
                    "difficulty": "easy",
                    "source_reference": "Machine learning is a subset of AI..."
                },
                validation_criteria=[
                    "Question tests factual recall",
                    "Answer is explicitly in text",
                    "4 distinct options provided",
                    "Only 1 clearly correct answer"
                ]
            ),
            
            "multiple_choice_medium": QuestionTemplate(
                question_type="multiple_choice",
                difficulty="medium",
                system_prompt=base_system,
                user_prompt="""Generate {question_count} MEDIUM multiple choice question(s) from the following content:

{context}

Requirements for MEDIUM questions:
- Test comprehension, relationships, or application of concepts
- Require understanding beyond direct recall
- May involve comparing, contrasting, or inferring
- Create 4 challenging but fair options
- Distractors should be plausible and require careful consideration

Return as JSON array:
[{{
  "question": "Question requiring comprehension or application",
  "type": "multiple_choice",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_answer": "Option C",
  "explanation": "Detailed explanation connecting answer to source content",
  "difficulty": "medium",
  "source_reference": "Relevant quote supporting the answer"
}}]""",
                example_response={
                    "question": "Based on the methodology described, what is the primary advantage of using cross-validation?",
                    "type": "multiple_choice",
                    "options": [
                        "It reduces computational time",
                        "It ensures statistical significance and robust validation",
                        "It eliminates the need for large datasets",
                        "It automatically selects the best model"
                    ],
                    "correct_answer": "It ensures statistical significance and robust validation",
                    "explanation": "The text indicates that cross-validation was used specifically to ensure robust validation and statistical significance of results.",
                    "difficulty": "medium",
                    "source_reference": "Cross-validation techniques and statistical significance testing were employed to validate results"
                },
                validation_criteria=[
                    "Question tests comprehension",
                    "Requires understanding of concepts",
                    "Plausible distractors included",
                    "Answer can be reasoned from text"
                ]
            ),
            
            "multiple_choice_hard": QuestionTemplate(
                question_type="multiple_choice",
                difficulty="hard",
                system_prompt=base_system,
                user_prompt="""Generate {question_count} HARD multiple choice question(s) from the following content:

{context}

Requirements for HARD questions:
- Test analysis, synthesis, evaluation, or complex reasoning
- Require deep understanding and critical thinking
- May involve implications, consequences, or complex relationships
- Create sophisticated distractors that require expert-level discrimination
- Question should challenge advanced understanding

Return as JSON array:
[{{
  "question": "Complex analytical or evaluative question",
  "type": "multiple_choice",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct_answer": "Option A",
  "explanation": "Comprehensive explanation of reasoning and analysis",
  "difficulty": "hard",
  "source_reference": "Multiple references supporting complex reasoning"
}}]""",
                example_response={
                    "question": "Considering the limitations mentioned and the proposed solutions, what is the most likely reason previous approaches failed to achieve similar performance improvements?",
                    "type": "multiple_choice",
                    "options": [
                        "Insufficient computational resources for optimization",
                        "Lack of domain-specific training data",
                        "Failure to address scalability and accuracy trade-offs simultaneously",
                        "Poor algorithm selection for the problem domain"
                    ],
                    "correct_answer": "Failure to address scalability and accuracy trade-offs simultaneously",
                    "explanation": "The text suggests previous approaches had limitations in both scalability and accuracy, and the current work specifically addresses both issues together, implying this was the key limitation of earlier methods.",
                    "difficulty": "hard",
                    "source_reference": "Previous research showed limitations in scalability and accuracy... Our approach addresses these issues through novel improvements"
                },
                validation_criteria=[
                    "Question requires analysis or evaluation",
                    "Tests complex understanding",
                    "Sophisticated reasoning required",
                    "Expert-level discrimination needed"
                ]
            )
        }
    
    def _create_true_false_templates(self) -> Dict[str, QuestionTemplate]:
        """Create true/false question templates"""
        base_system = """You are an expert at creating true/false questions that test specific factual knowledge and comprehension. Your statements should be clear, unambiguous, and directly testable against the source material."""
        
        return {
            "true_false_easy": QuestionTemplate(
                question_type="true_false",
                difficulty="easy",
                system_prompt=base_system,
                user_prompt="""Generate {question_count} EASY true/false statement(s) from the following content:

{context}

Requirements for EASY true/false:
- Create clear factual statements that are definitely true or false
- Based on explicit information in the text
- Avoid ambiguous or subjective statements
- No complex interpretations required

Return as JSON array:
[{{
  "question": "Clear factual statement about content",
  "type": "true_false",
  "options": null,
  "correct_answer": "true",
  "explanation": "Brief explanation with text reference",
  "difficulty": "easy",
  "source_reference": "Direct quote supporting the answer"
}}]""",
                example_response={
                    "question": "The research employed cross-validation techniques for result validation.",
                    "type": "true_false",
                    "options": None,
                    "correct_answer": "true",
                    "explanation": "The text explicitly mentions that cross-validation techniques were used to validate results.",
                    "difficulty": "easy",
                    "source_reference": "cross-validation techniques and statistical significance testing were employed to validate results"
                },
                validation_criteria=[
                    "Statement is factually clear",
                    "Answer is explicit in text",
                    "No ambiguous interpretations",
                    "Directly verifiable"
                ]
            ),
            
            "true_false_medium": QuestionTemplate(
                question_type="true_false",
                difficulty="medium",
                system_prompt=base_system,
                user_prompt="""Generate {question_count} MEDIUM true/false statement(s) from the following content:

{context}

Requirements for MEDIUM true/false:
- Test comprehension of concepts or relationships
- May require understanding implications or connections
- Still clearly answerable as true or false
- Avoid overly complex statements

Return as JSON array:
[{{
  "question": "Statement requiring comprehension of concepts",
  "type": "true_false", 
  "options": null,
  "correct_answer": "false",
  "explanation": "Explanation of why statement is true/false with reasoning",
  "difficulty": "medium",
  "source_reference": "Supporting evidence from text"
}}]""",
                example_response={
                    "question": "The performance improvements achieved were primarily due to increased computational power rather than algorithmic innovations.",
                    "type": "true_false",
                    "options": None,
                    "correct_answer": "false",
                    "explanation": "The text emphasizes algorithmic improvements and optimization strategies as the key factors, not just computational power.",
                    "difficulty": "medium",
                    "source_reference": "novel algorithmic improvements and optimization strategies that reduce computational complexity while maintaining performance"
                },
                validation_criteria=[
                    "Tests conceptual understanding",
                    "Requires reasoning about content",
                    "Clear true/false answer",
                    "Based on text evidence"
                ]
            ),
            
            "true_false_hard": QuestionTemplate(
                question_type="true_false",
                difficulty="hard",
                system_prompt=base_system,
                user_prompt="""Generate {question_count} HARD true/false statement(s) from the following content:

{context}

Requirements for HARD true/false:
- Test analysis of complex relationships or implications
- May involve subtle distinctions or nuanced understanding
- Require deep comprehension of the material
- Still definitively answerable as true or false

Return as JSON array:
[{{
  "question": "Complex statement requiring analytical thinking",
  "type": "true_false",
  "options": null,
  "correct_answer": "true",
  "explanation": "Sophisticated analysis of why statement is true/false",
  "difficulty": "hard",
  "source_reference": "Complex evidence supporting reasoning"
}}]""",
                example_response={
                    "question": "The research methodology's emphasis on both scalability and accuracy suggests that previous approaches typically optimized for one at the expense of the other.",
                    "type": "true_false",
                    "options": None,
                    "correct_answer": "true",
                    "explanation": "The text's discussion of addressing limitations in both scalability and accuracy, combined with the novel approach that maintains both, implies previous methods had to trade one for the other.",
                    "difficulty": "hard",
                    "source_reference": "Previous research showed limitations in scalability and accuracy... Our approach addresses these issues through optimization strategies that reduce complexity while maintaining performance"
                },
                validation_criteria=[
                    "Requires analytical thinking",
                    "Tests complex understanding",
                    "Involves nuanced reasoning",
                    "Expert-level interpretation"
                ]
            )
        }
    
    def _create_short_answer_templates(self) -> Dict[str, QuestionTemplate]:
        """Create short answer question templates"""
        base_system = """You are an expert at creating short answer questions that promote deeper understanding and application of knowledge. Your questions should encourage thoughtful responses while remaining clearly answerable from the source material."""
        
        return {
            "short_answer_easy": QuestionTemplate(
                question_type="short_answer",
                difficulty="easy",
                system_prompt=base_system,
                user_prompt="""Generate {question_count} EASY short answer question(s) from the following content:

{context}

Requirements for EASY short answer:
- Ask for specific facts, definitions, or lists
- Answer should be directly available in the text
- Require 1-3 sentences or a brief list
- Clear, straightforward questions

Return as JSON array:
[{{
  "question": "Direct question asking for specific information",
  "type": "short_answer",
  "options": null,
  "correct_answer": "Brief factual answer from text",
  "explanation": "Explanation referencing where answer is found",
  "difficulty": "easy",
  "source_reference": "Text location of answer"
}}]""",
                example_response={
                    "question": "What techniques were used to validate the research results?",
                    "type": "short_answer",
                    "options": None,
                    "correct_answer": "Cross-validation techniques and statistical significance testing",
                    "explanation": "The text explicitly states these two validation methods were employed to ensure robust results.",
                    "difficulty": "easy",
                    "source_reference": "cross-validation techniques and statistical significance testing were employed to validate results"
                },
                validation_criteria=[
                    "Answer directly in text",
                    "Requires brief factual response",
                    "Clear question structure",
                    "Specific information requested"
                ]
            ),
            
            "short_answer_medium": QuestionTemplate(
                question_type="short_answer",
                difficulty="medium",
                system_prompt=base_system,
                user_prompt="""Generate {question_count} MEDIUM short answer question(s) from the following content:

{context}

Requirements for MEDIUM short answer:
- Ask for explanations, comparisons, or applications
- Require understanding and synthesis of information
- Answer should be 2-4 sentences
- Test comprehension beyond simple recall

Return as JSON array:
[{{
  "question": "Question requiring explanation or analysis",
  "type": "short_answer",
  "options": null,
  "correct_answer": "Comprehensive answer showing understanding",
  "explanation": "Detailed explanation of expected answer elements",
  "difficulty": "medium",
  "source_reference": "Multiple text sources supporting answer"
}}]""",
                example_response={
                    "question": "Explain how the proposed approach addresses the limitations of previous research methods.",
                    "type": "short_answer",
                    "options": None,
                    "correct_answer": "The proposed approach uses novel algorithmic improvements and optimization strategies that address both scalability and accuracy limitations simultaneously, unlike previous methods that typically had weaknesses in one or both areas.",
                    "explanation": "A complete answer should mention the novel algorithmic approach, the dual focus on scalability and accuracy, and contrast with previous limitations.",
                    "difficulty": "medium",
                    "source_reference": "Previous research showed limitations in scalability and accuracy. Our approach addresses these issues through novel algorithmic improvements"
                },
                validation_criteria=[
                    "Requires explanation or synthesis",
                    "Tests deeper understanding",
                    "Multiple sentence response",
                    "Shows comprehension"
                ]
            ),
            
            "short_answer_hard": QuestionTemplate(
                question_type="short_answer", 
                difficulty="hard",
                system_prompt=base_system,
                user_prompt="""Generate {question_count} HARD short answer question(s) from the following content:

{context}

Requirements for HARD short answer:
- Ask for analysis, evaluation, or complex reasoning
- Require critical thinking and deep understanding
- Answer should be 3-5 sentences with sophisticated reasoning
- Test highest levels of comprehension

Return as JSON array:
[{{
  "question": "Complex analytical or evaluative question",
  "type": "short_answer",
  "options": null,
  "correct_answer": "Sophisticated answer demonstrating expert understanding",
  "explanation": "Comprehensive explanation of analytical reasoning required",
  "difficulty": "hard",
  "source_reference": "Complex textual evidence supporting analysis"
}}]""",
                example_response={
                    "question": "Analyze the potential implications of these research findings for real-world applications, considering both the benefits and potential limitations mentioned in the text.",
                    "type": "short_answer",
                    "options": None,
                    "correct_answer": "The findings suggest significant potential for industrial automation, data processing pipelines, and real-time decision support systems due to improved accuracy and maintained performance. However, the scalability improvements may be context-dependent, and the computational complexity reduction needs further validation in diverse real-world scenarios before widespread adoption.",
                    "explanation": "A strong answer should identify specific application domains, recognize both benefits (accuracy, performance) and limitations (scalability context, validation needs), and demonstrate understanding of implementation challenges.",
                    "difficulty": "hard",
                    "source_reference": "Applications include industrial automation, data processing pipelines, and real-time decision support systems... optimization strategies that reduce computational complexity while maintaining performance"
                },
                validation_criteria=[
                    "Requires complex analysis",
                    "Tests critical thinking",
                    "Multi-faceted reasoning needed",
                    "Expert-level response expected"
                ]
            )
        }


def test_question_templates():
    """Test question templates functionality"""
    templates = QuestionTemplates()
    
    # Test template retrieval
    mc_template = templates.get_template("multiple_choice", "medium")
    print(f"✓ Retrieved template: {mc_template.question_type}_{mc_template.difficulty}")
    
    # Test prompt generation
    sample_text = "Machine learning is a subset of artificial intelligence that enables computers to learn from data without explicit programming."
    prompt = templates.get_generation_prompt(
        question_type="multiple_choice",
        difficulty="easy",
        chunk_content=sample_text,
        question_count=2,
        document_title="AI Fundamentals"
    )
    
    print(f"✓ Generated prompt length: {len(prompt)} characters")
    print("✓ Question templates initialized successfully")
    
    return templates


if __name__ == "__main__":
    test_question_templates()
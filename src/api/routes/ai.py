"""AI reasoning and Q&A API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ...services.ai_service import ai_service


router = APIRouter(prefix="/api/ai", tags=["AI Reasoning"])


class QuestionRequest(BaseModel):
    """Request model for asking a question."""
    question: str
    use_case: str = "general"  # general, symptom_triage, vaccine_info
    max_tokens: int = 200


class SymptomTriageRequest(BaseModel):
    """Request model for symptom triage."""
    symptoms: str
    child_age_months: Optional[int] = None


@router.post("/ask")
async def ask_question(request: QuestionRequest):
    """
    Ask a parenting question and get AI-powered answer with RAG context.

    The AI will search the knowledge base and provide evidence-based answers.

    Use cases:
    - general: General parenting questions
    - symptom_triage: Medical symptom assessment
    - vaccine_info: Vaccine information and concerns
    """
    result = ai_service.answer_question(
        question=request.question,
        use_case=request.use_case,
        max_tokens=request.max_tokens
    )

    if "error" in result and result.get("error") == "no_api_key":
        raise HTTPException(status_code=503, detail=result["answer"])

    return result


@router.post("/triage")
async def triage_symptoms(request: SymptomTriageRequest):
    """
    Triage symptoms and get urgency assessment.

    Returns:
    - EMERGENCY: Call 911 immediately
    - URGENT: See doctor today
    - ROUTINE: Schedule appointment
    - HOME_CARE: Monitor at home

    **Important**: This is an AI assessment tool, not a substitute for
    professional medical advice. When in doubt, always consult a healthcare provider.
    """
    # Quick check for emergency keywords
    if ai_service.check_emergency_keywords(request.symptoms):
        return {
            "urgency": "EMERGENCY",
            "action": "CALL 911 IMMEDIATELY or go to emergency room",
            "reason": "Symptoms suggest potential medical emergency",
            "full_response": "Emergency keywords detected. Seek immediate medical attention.",
            "sources": 0,
            "emergency_detected": True
        }

    result = ai_service.triage_symptoms(
        symptom_description=request.symptoms,
        child_age_months=request.child_age_months
    )

    return result


@router.get("/test")
async def test_ai_service():
    """
    Test if AI service is configured and working.

    Returns the status of the Claude API connection.
    """
    if not ai_service.client:
        return {
            "status": "not_configured",
            "message": "AI service requires ANTHROPIC_API_KEY in .env file",
            "configured": False
        }

    # Test with a simple question
    try:
        result = ai_service.answer_question(
            question="What is a normal temperature for a baby?",
            max_tokens=50
        )

        return {
            "status": "operational",
            "message": "AI service is working correctly",
            "configured": True,
            "test_response_length": len(result.get("answer", "")),
            "model": result.get("model")
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "configured": True
        }

"""SMS routes for Twilio webhook and sending messages."""
from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from ...database import get_db
from ...schemas.schemas import SMSSendRequest, SMSSendToFamilyRequest
from ...services.sms_service import sms_service
from ...services.rag_service import rag_service
from ...services.ai_service import ai_service
from ...services.conversation_service import conversation_service
from ...services.intent_service import intent_service

router = APIRouter(prefix="/api/sms", tags=["SMS"])


@router.post("/webhook")
async def sms_webhook(
    From: Annotated[str, Form()],
    To: Annotated[str, Form()],
    Body: Annotated[str, Form()],
    MessageSid: Annotated[str, Form()],
    db: Session = Depends(get_db)
):
    """
    Twilio webhook endpoint for receiving incoming SMS.

    This endpoint is called by Twilio when an SMS is received.
    """
    result = sms_service.process_incoming_sms(
        from_phone=From,
        to_phone=To,
        message_body=Body,
        message_sid=MessageSid,
        db=db
    )

    if not result["success"]:
        # Unknown sender - send help message
        sms_service.send_sms(
            to_phone=From,
            message="Welcome to Coo! Please sign up at our website to get started.",
            db=db
        )
        return {"status": "unknown_sender", "message": "Help message sent"}

    # Extract user's question
    question = Body.strip()
    family_id = result["family_id"]

    # Check for cancel intent first
    if intent_service.detect_cancel_intent(question):
        current_state = conversation_service.get_conversation_state(family_id, From, db)
        if current_state:
            conversation_service.set_conversation_state(family_id, From, None, db)
            response = "Ok, cancelled. How else can I help you?"
            sms_service.send_sms(to_phone=From, message=response, db=db, family_id=family_id)
            return {
                "status": "cancelled",
                "family_id": family_id,
                "message_id": result["message_id"],
                "response_sent": True
            }

    # Add user message to conversation context
    conversation_service.add_message_to_context(
        family_id=family_id,
        phone=From,
        role="user",
        content=question,
        db=db
    )

    # Check if we're in a multi-turn conversation state
    current_state = conversation_service.get_conversation_state(family_id, From, db)

    # Handle multi-turn flows (child registration, etc.)
    if current_state and current_state.startswith("ADDING_CHILD"):
        # Continue child registration flow
        result_intent = intent_service.handle_add_child_intent(
            message=question,
            family_id=family_id,
            phone=From,
            db=db,
            current_state=current_state
        )

        response = result_intent["response"]

        # Add AI response to context
        conversation_service.add_message_to_context(
            family_id=family_id,
            phone=From,
            role="assistant",
            content=response,
            db=db
        )

        # Send response
        sms_service.send_sms(to_phone=From, message=response, db=db, family_id=family_id)

        return {
            "status": "intent_flow",
            "family_id": family_id,
            "message_id": result["message_id"],
            "response_sent": True,
            "intent_state": result_intent.get("next_state"),
            "child_created": result_intent.get("child_created", False)
        }

    # Classify question type
    question_type = ai_service.classify_question_type(question)

    # Check if user wants to add a child (start new intent flow)
    if question_type == "account_management" and any(keyword in question.lower() for keyword in ["add", "register", "new"]):
        # Start child registration flow
        result_intent = intent_service.handle_add_child_intent(
            message=question,
            family_id=family_id,
            phone=From,
            db=db,
            current_state=None  # Start new flow
        )

        response = result_intent["response"]

        # Add AI response to context
        conversation_service.add_message_to_context(
            family_id=family_id,
            phone=From,
            role="assistant",
            content=response,
            db=db
        )

        # Send response
        sms_service.send_sms(to_phone=From, message=response, db=db, family_id=family_id)

        return {
            "status": "intent_started",
            "family_id": family_id,
            "message_id": result["message_id"],
            "response_sent": True,
            "intent_state": result_intent.get("next_state"),
            "question_type": question_type
        }

    # Regular conversation flow (not in multi-turn intent)
    # Try to extract child context from message
    child_context = conversation_service.extract_child_from_message(
        message=question,
        family_id=family_id,
        db=db
    )

    # If child identified, set as active child in conversation
    if child_context:
        conversation_service.set_active_child(
            family_id=family_id,
            phone=From,
            child_id=child_context["child_id"],
            child_name=child_context["name"],
            child_age_months=child_context.get("age_months", 0),
            db=db
        )
    else:
        # Try to get previously active child from context
        child_context = conversation_service.get_active_child_context(
            family_id=family_id,
            phone=From,
            db=db
        )

    # Get conversation history
    conversation_history = conversation_service.format_context_for_ai(
        family_id=family_id,
        phone=From,
        db=db,
        last_n=3  # Last 3 exchanges
    )

    # Check for emergency keywords first
    if ai_service.check_emergency_keywords(question):
        response = "⚠️ EMERGENCY: If this is a medical emergency, CALL 911 immediately or go to the nearest emergency room. For urgent concerns, contact your pediatrician's emergency line."
        urgency = "EMERGENCY"
    else:
        # Generate AI-powered response using RAG context with conversation history
        response = ai_service.generate_sms_response(
            question=question,
            max_length=300,
            conversation_history=conversation_history,
            child_context=child_context,
            question_type=question_type
        )
        urgency = "answered"

    # Add AI response to conversation context
    conversation_service.add_message_to_context(
        family_id=family_id,
        phone=From,
        role="assistant",
        content=response,
        db=db,
        metadata={"question_type": question_type, "child_context": child_context}
    )

    # Send response back to the sender only (not all family members)
    sms_service.send_sms(
        to_phone=From,
        message=response,
        db=db,
        family_id=family_id
    )

    return {
        "status": urgency,
        "family_id": family_id,
        "message_id": result["message_id"],
        "response_sent": True,
        "ai_powered": True,
        "question_type": question_type,
        "child_identified": child_context is not None
    }


@router.post("/send")
async def send_sms(
    request: SMSSendRequest,
    db: Session = Depends(get_db)
):
    """
    Send a test SMS to a phone number.

    This is useful for testing SMS functionality.
    """
    result = sms_service.send_sms(
        to_phone=request.to_phone,
        message=request.message,
        db=db
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/send-to-family/{family_id}")
async def send_to_family(
    family_id: int,
    request: SMSSendToFamilyRequest,
    db: Session = Depends(get_db)
):
    """
    Send SMS to family members.

    - If send_to_all=True, sends to all members with receive_proactive=True
    - If send_to_all=False, sends only to primary member
    """
    result = sms_service.send_to_family(
        family_id=family_id,
        message=request.message,
        db=db,
        send_to_all=request.send_to_all
    )

    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])

    return result

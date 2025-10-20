"""Intent handlers for multi-turn conversational flows."""
from sqlalchemy.orm import Session
from typing import Dict, Optional
from datetime import datetime
from ..models.models import Child, Family
from .conversation_service import conversation_service
import re


class IntentService:
    """Handles multi-turn conversational intents like adding children."""

    def handle_add_child_intent(
        self,
        message: str,
        family_id: int,
        phone: str,
        db: Session,
        current_state: Optional[str] = None
    ) -> Dict:
        """
        Handle conversational child registration flow.

        States:
        - None → ADDING_CHILD_NAME (ask for name)
        - ADDING_CHILD_NAME → ADDING_CHILD_BIRTHDATE (ask for birthdate)
        - ADDING_CHILD_BIRTHDATE → Complete (create child)

        Args:
            message: User's message
            family_id: Family ID
            phone: Phone number
            db: Database session
            current_state: Current conversation state

        Returns:
            Dict with response and next_state
        """
        # Check child limit first
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            return {
                "response": "Sorry, I couldn't find your account. Please contact support.",
                "next_state": None,
                "success": False
            }

        child_count = db.query(Child).filter(Child.family_id == family_id).count()
        tier_limits = {"FREE": 1, "FAMILY": 3, "PREMIUM": 3}
        max_children = tier_limits.get(family.subscription_tier, 1)

        if child_count >= max_children:
            return {
                "response": f"You've reached the limit of {max_children} children for your {family.subscription_tier} tier. Upgrade to add more!",
                "next_state": None,
                "success": False
            }

        # State machine
        if current_state is None:
            # Initial state - ask for name
            conversation_service.set_conversation_state(
                family_id=family_id,
                phone=phone,
                state="ADDING_CHILD_NAME",
                db=db,
                state_data={}
            )
            return {
                "response": "I'd be happy to help you add a child! What's their name?",
                "next_state": "ADDING_CHILD_NAME",
                "success": True
            }

        elif current_state == "ADDING_CHILD_NAME":
            # Extract name from message
            name = message.strip().title()

            # Validate name (basic check)
            if len(name) < 2 or len(name) > 50:
                return {
                    "response": "Please provide a valid name (2-50 characters).",
                    "next_state": "ADDING_CHILD_NAME",
                    "success": False
                }

            # Store name and ask for birthdate
            conversation_service.set_conversation_state(
                family_id=family_id,
                phone=phone,
                state="ADDING_CHILD_BIRTHDATE",
                db=db,
                state_data={"child_name": name}
            )

            return {
                "response": f"Thanks! When was {name} born? Please use format MM/DD/YYYY (e.g., 03/15/2022)",
                "next_state": "ADDING_CHILD_BIRTHDATE",
                "success": True
            }

        elif current_state == "ADDING_CHILD_BIRTHDATE":
            # Get stored name
            state_data = conversation_service.get_state_data(family_id, phone, db)
            if not state_data or "child_name" not in state_data:
                # Something went wrong, restart
                conversation_service.set_conversation_state(family_id, phone, None, db)
                return {
                    "response": "Sorry, something went wrong. Let's start over. What's your child's name?",
                    "next_state": None,
                    "success": False
                }

            child_name = state_data["child_name"]

            # Parse birthdate
            birthdate = self._parse_birthdate(message)
            if not birthdate:
                return {
                    "response": "I couldn't understand that date. Please use MM/DD/YYYY format (e.g., 03/15/2022)",
                    "next_state": "ADDING_CHILD_BIRTHDATE",
                    "success": False
                }

            # Validate birthdate (not in future, not too old)
            today = datetime.now().date()
            if birthdate > today:
                return {
                    "response": "Birthdate can't be in the future! Please use MM/DD/YYYY format.",
                    "next_state": "ADDING_CHILD_BIRTHDATE",
                    "success": False
                }

            # Check if birthdate is reasonable (not more than 10 years ago for child)
            age_days = (today - birthdate).days
            if age_days > 365 * 10:
                return {
                    "response": "That seems too old. Coo is for children up to 5 years. Please check the birthdate.",
                    "next_state": "ADDING_CHILD_BIRTHDATE",
                    "success": False
                }

            # Create child
            try:
                new_child = Child(
                    family_id=family_id,
                    name=child_name,
                    birth_date=birthdate,
                    is_pregnancy=False
                )
                db.add(new_child)
                db.commit()
                db.refresh(new_child)

                # Calculate age for response
                age_months = age_days // 30
                age_years = age_days // 365

                if age_years >= 1:
                    age_str = f"{age_years} year{'s' if age_years != 1 else ''} old"
                else:
                    age_str = f"{age_months} month{'s' if age_months != 1 else ''} old"

                # Clear state
                conversation_service.set_conversation_state(family_id, phone, None, db)

                # Set as active child
                conversation_service.set_active_child(
                    family_id=family_id,
                    phone=phone,
                    child_id=new_child.id,
                    child_name=child_name,
                    child_age_months=age_months,
                    db=db
                )

                return {
                    "response": f"Perfect! I've added {child_name} ({age_str}) to your account. You can now ask me questions about {child_name}!",
                    "next_state": None,
                    "success": True,
                    "child_created": True,
                    "child_id": new_child.id
                }

            except Exception as e:
                conversation_service.set_conversation_state(family_id, phone, None, db)
                return {
                    "response": f"Sorry, I couldn't add {child_name}. Please try again or use the web portal.",
                    "next_state": None,
                    "success": False,
                    "error": str(e)
                }

        return {
            "response": "Sorry, I got confused. Let's start over. What's your child's name?",
            "next_state": None,
            "success": False
        }

    def _parse_birthdate(self, message: str):
        """
        Parse birthdate from various formats.

        Supports:
        - MM/DD/YYYY
        - M/D/YYYY
        - MM-DD-YYYY
        - YYYY-MM-DD

        Args:
            message: User's message

        Returns:
            datetime.date object or None
        """
        message = message.strip()

        # Try MM/DD/YYYY or MM-DD-YYYY
        patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',  # MM/DD/YYYY or MM-DD-YYYY
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # YYYY/MM/DD or YYYY-MM-DD
        ]

        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                groups = match.groups()
                try:
                    if len(groups[0]) == 4:  # YYYY-MM-DD format
                        year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                    else:  # MM/DD/YYYY format
                        month, day, year = int(groups[0]), int(groups[1]), int(groups[2])

                    return datetime(year, month, day).date()
                except ValueError:
                    continue

        return None

    def detect_cancel_intent(self, message: str) -> bool:
        """
        Check if user wants to cancel current flow.

        Args:
            message: User's message

        Returns:
            True if cancel intent detected
        """
        cancel_keywords = ["cancel", "stop", "nevermind", "never mind", "quit", "exit"]
        message_lower = message.lower().strip()
        return any(keyword in message_lower for keyword in cancel_keywords)


# Global intent service instance
intent_service = IntentService()

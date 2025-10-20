"""Conversation context service for maintaining multi-turn dialogue state."""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ..models.models import ConversationContext, Child
import json


class ConversationService:
    """Manages conversation context and history for multi-turn dialogues."""

    def __init__(self):
        """Initialize conversation service."""
        self.max_messages = 50  # Keep last 50 messages
        self.context_timeout_hours = 24  # Reset context after 24 hours of inactivity

    def get_or_create_context(self, family_id: int, phone: str, db: Session) -> ConversationContext:
        """
        Get existing conversation context or create new one.

        Args:
            family_id: Family ID
            phone: Phone number
            db: Database session

        Returns:
            ConversationContext object
        """
        context = db.query(ConversationContext).filter(
            ConversationContext.family_id == family_id,
            ConversationContext.phone == phone
        ).first()

        if not context:
            context = ConversationContext(
                family_id=family_id,
                phone=phone,
                message_count=0,
                context_data={"messages": [], "metadata": {}}
            )
            db.add(context)
            db.commit()
            db.refresh(context)

        # Check if context should be reset (24 hours of inactivity)
        elif context.updated_at:
            time_since_update = datetime.utcnow() - context.updated_at
            if time_since_update > timedelta(hours=self.context_timeout_hours):
                # Reset old context
                context.context_data = {"messages": [], "metadata": {}}
                context.message_count = 0
                context.last_context_reset = datetime.utcnow()
                db.commit()

        return context

    def add_message_to_context(
        self,
        family_id: int,
        phone: str,
        role: str,
        content: str,
        db: Session,
        metadata: Optional[Dict] = None
    ):
        """
        Add a message to the conversation context.

        Args:
            family_id: Family ID
            phone: Phone number
            role: "user" or "assistant"
            content: Message content
            db: Database session
            metadata: Optional metadata (child_id, question_type, etc.)
        """
        context = self.get_or_create_context(family_id, phone, db)

        # Get current context data
        context_data = context.context_data if context.context_data else {"messages": [], "metadata": {}}
        messages = context_data.get("messages", [])

        # Add new message
        message_entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata if metadata else {}
        }
        messages.append(message_entry)

        # Keep only last N messages
        if len(messages) > self.max_messages:
            messages = messages[-self.max_messages:]

        # Update context
        context_data["messages"] = messages
        context.context_data = context_data
        context.message_count = len(messages)
        context.updated_at = datetime.utcnow()

        db.commit()

    def get_conversation_history(
        self,
        family_id: int,
        phone: str,
        db: Session,
        last_n: int = 10
    ) -> List[Dict]:
        """
        Get recent conversation history.

        Args:
            family_id: Family ID
            phone: Phone number
            db: Database session
            last_n: Number of recent messages to retrieve

        Returns:
            List of messages in format: [{"role": "user", "content": "..."}, ...]
        """
        context = db.query(ConversationContext).filter(
            ConversationContext.family_id == family_id,
            ConversationContext.phone == phone
        ).first()

        if not context or not context.context_data:
            return []

        messages = context.context_data.get("messages", [])

        # Return last N messages
        return messages[-last_n:] if messages else []

    def get_active_child_context(
        self,
        family_id: int,
        phone: str,
        db: Session
    ) -> Optional[Dict]:
        """
        Get the active child context from conversation metadata.

        This helps determine which child the parent is asking about.

        Args:
            family_id: Family ID
            phone: Phone number
            db: Database session

        Returns:
            Dict with child info if found, None otherwise
        """
        context = db.query(ConversationContext).filter(
            ConversationContext.family_id == family_id,
            ConversationContext.phone == phone
        ).first()

        if not context or not context.context_data:
            return None

        metadata = context.context_data.get("metadata", {})
        return metadata.get("active_child")

    def set_active_child(
        self,
        family_id: int,
        phone: str,
        child_id: int,
        child_name: str,
        child_age_months: int,
        db: Session
    ):
        """
        Set the active child in conversation context.

        Args:
            family_id: Family ID
            phone: Phone number
            child_id: Child's database ID
            child_name: Child's name
            child_age_months: Child's age in months
            db: Database session
        """
        context = self.get_or_create_context(family_id, phone, db)

        context_data = context.context_data if context.context_data else {"messages": [], "metadata": {}}
        metadata = context_data.get("metadata", {})

        metadata["active_child"] = {
            "child_id": child_id,
            "name": child_name,
            "age_months": child_age_months,
            "set_at": datetime.utcnow().isoformat()
        }

        context_data["metadata"] = metadata
        context.context_data = context_data
        db.commit()

    def extract_child_from_message(
        self,
        message: str,
        family_id: int,
        db: Session
    ) -> Optional[Dict]:
        """
        Extract child reference from user message.

        Looks for patterns like:
        - "my 2 year old"
        - "my baby"
        - "Emma"
        - "my daughter"

        Args:
            message: User's message
            family_id: Family ID
            db: Database session

        Returns:
            Dict with child info if identified, None otherwise
        """
        # Get all children for this family
        children = db.query(Child).filter(Child.family_id == family_id).all()

        if not children:
            return None

        message_lower = message.lower()

        # Check if child name is mentioned
        for child in children:
            if child.name.lower() in message_lower:
                age_months = self._calculate_age_months(child)
                return {
                    "child_id": child.id,
                    "name": child.name,
                    "age_months": age_months,
                    "match_type": "name"
                }

        # Check age patterns
        age_keywords = [
            ("2 year old", 24),
            ("3 year old", 36),
            ("4 year old", 48),
            ("newborn", 0),
            ("infant", 6),
            ("baby", 12),
            ("toddler", 18)
        ]

        for keyword, approx_months in age_keywords:
            if keyword in message_lower:
                # Find child closest to this age
                best_match = None
                min_diff = float('inf')

                for child in children:
                    child_age = self._calculate_age_months(child)
                    if child_age is not None:
                        diff = abs(child_age - approx_months)
                        if diff < min_diff:
                            min_diff = diff
                            best_match = child

                if best_match and min_diff < 12:  # Within 12 months tolerance
                    return {
                        "child_id": best_match.id,
                        "name": best_match.name,
                        "age_months": self._calculate_age_months(best_match),
                        "match_type": "age_pattern",
                        "pattern": keyword
                    }

        # If only one child, assume they're talking about that child
        if len(children) == 1:
            child = children[0]
            return {
                "child_id": child.id,
                "name": child.name,
                "age_months": self._calculate_age_months(child),
                "match_type": "only_child"
            }

        return None

    def _calculate_age_months(self, child: Child) -> Optional[int]:
        """Calculate child's age in months."""
        if child.is_pregnancy or not child.birth_date:
            return None

        today = datetime.utcnow().date()
        age_days = (today - child.birth_date).days
        age_months = age_days // 30  # Approximate

        return age_months

    def format_context_for_ai(
        self,
        family_id: int,
        phone: str,
        db: Session,
        last_n: int = 5
    ) -> str:
        """
        Format conversation history for AI context.

        Args:
            family_id: Family ID
            phone: Phone number
            db: Database session
            last_n: Number of recent exchanges to include

        Returns:
            Formatted string with conversation history
        """
        history = self.get_conversation_history(family_id, phone, db, last_n * 2)

        if not history:
            return ""

        formatted = "Previous conversation:\n"
        for msg in history:
            role = "Parent" if msg["role"] == "user" else "Coo"
            content = msg["content"]
            formatted += f"{role}: {content}\n"

        return formatted

    def clear_context(self, family_id: int, phone: str, db: Session):
        """
        Clear conversation context for a user.

        Args:
            family_id: Family ID
            phone: Phone number
            db: Database session
        """
        context = db.query(ConversationContext).filter(
            ConversationContext.family_id == family_id,
            ConversationContext.phone == phone
        ).first()

        if context:
            context.context_data = {"messages": [], "metadata": {}}
            context.message_count = 0
            context.last_context_reset = datetime.utcnow()
            db.commit()

    def get_conversation_state(self, family_id: int, phone: str, db: Session) -> Optional[str]:
        """
        Get current conversation state (for multi-turn flows).

        Args:
            family_id: Family ID
            phone: Phone number
            db: Database session

        Returns:
            State string (e.g., "adding_child_name") or None
        """
        context = db.query(ConversationContext).filter(
            ConversationContext.family_id == family_id,
            ConversationContext.phone == phone
        ).first()

        if not context or not context.context_data:
            return None

        metadata = context.context_data.get("metadata", {})
        return metadata.get("conversation_state")

    def set_conversation_state(
        self,
        family_id: int,
        phone: str,
        state: Optional[str],
        db: Session,
        state_data: Optional[Dict] = None
    ):
        """
        Set conversation state for multi-turn flows.

        Args:
            family_id: Family ID
            phone: Phone number
            state: State name (e.g., "adding_child_name") or None to clear
            db: Database session
            state_data: Optional data to store with state
        """
        context = self.get_or_create_context(family_id, phone, db)

        context_data = context.context_data if context.context_data else {"messages": [], "metadata": {}}
        metadata = context_data.get("metadata", {})

        if state:
            metadata["conversation_state"] = state
            if state_data:
                metadata["state_data"] = state_data
        else:
            # Clear state
            metadata.pop("conversation_state", None)
            metadata.pop("state_data", None)

        context_data["metadata"] = metadata
        context.context_data = context_data
        db.commit()

    def get_state_data(self, family_id: int, phone: str, db: Session) -> Optional[Dict]:
        """
        Get data stored with current conversation state.

        Args:
            family_id: Family ID
            phone: Phone number
            db: Database session

        Returns:
            State data dict or None
        """
        context = db.query(ConversationContext).filter(
            ConversationContext.family_id == family_id,
            ConversationContext.phone == phone
        ).first()

        if not context or not context.context_data:
            return None

        metadata = context.context_data.get("metadata", {})
        return metadata.get("state_data")


# Global conversation service instance
conversation_service = ConversationService()

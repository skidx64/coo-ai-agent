"""Twilio SMS service for sending and receiving messages."""
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from typing import List, Optional
from sqlalchemy.orm import Session
from ..config import settings
from ..models.models import Family, FamilyMember, Message, PhoneLookup, MessageDirection, MessageStatus
from datetime import datetime


class SMSService:
    """Service for handling SMS operations with Twilio."""

    def __init__(self):
        """Initialize Twilio client."""
        self.client = None
        if settings.twilio_account_sid and settings.twilio_auth_token:
            self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        self.from_number = settings.twilio_phone_number

    def send_sms(self, to_phone: str, message: str, db: Session = None, family_id: Optional[int] = None) -> dict:
        """
        Send SMS to a phone number.

        Args:
            to_phone: Recipient phone number
            message: Message content
            db: Database session (optional for test mode)
            family_id: Optional family ID for message logging

        Returns:
            dict with success status and message info

        Twilio Test Credentials:
        - Use phone number: +15005550006 for valid test number (always succeeds)
        - Use phone number: +15005550001 for invalid test number (always fails)
        - Test credentials will print code to console instead of sending SMS
        """
        if not self.client:
            # In test mode, just print the message
            print(f"\n{'='*60}")
            print(f"[SMS] TEST MODE - No Twilio configured")
            print(f"To: {to_phone}")
            print(f"Message: {message}")
            print(f"{'='*60}\n")
            return {
                "success": True,
                "error": "Test mode - no SMS sent",
                "sid": "TEST_SID_" + str(datetime.now().timestamp())
            }

        try:
            # Check for Twilio test numbers
            # +15005550006 = valid test number (always succeeds)
            # +15005550001 = invalid test number (always fails)
            if to_phone in ['+15005550006', '+15005550001']:
                print(f"\n{'='*60}")
                print(f"[SMS] TWILIO TEST NUMBER DETECTED: {to_phone}")
                print(f"Verification Code: {message}")
                print(f"{'='*60}\n")

            # Send via Twilio
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_phone
            )

            # Log message if family_id provided
            if family_id:
                db_message = Message(
                    family_id=family_id,
                    from_phone=self.from_number,
                    to_phone=to_phone,
                    direction=MessageDirection.OUTBOUND,
                    content=message,
                    twilio_sid=twilio_message.sid,
                    status=MessageStatus.SENT
                )
                db.add(db_message)
                db.commit()

            return {
                "success": True,
                "sid": twilio_message.sid,
                "status": twilio_message.status,
                "to": to_phone
            }

        except TwilioRestException as e:
            return {
                "success": False,
                "error": str(e),
                "sid": None
            }

    def send_to_family(self, family_id: int, message: str, db: Session, send_to_all: bool = True) -> dict:
        """
        Send SMS to family members.

        Args:
            family_id: Family ID
            message: Message content
            db: Database session
            send_to_all: If True, send to all members with receive_proactive=True.
                        If False, send only to primary member.

        Returns:
            dict with results for each member
        """
        family = db.query(Family).filter(Family.id == family_id).first()
        if not family:
            return {"success": False, "error": "Family not found"}

        results = []

        if send_to_all:
            # Send to all members who opted in for proactive messages
            members = db.query(FamilyMember).filter(
                FamilyMember.family_id == family_id,
                FamilyMember.receive_proactive == True
            ).all()

            for member in members:
                result = self.send_sms(member.phone, message, db, family_id)
                results.append({
                    "member_id": member.id,
                    "name": member.name,
                    "phone": member.phone,
                    **result
                })
        else:
            # Send only to primary member
            primary = db.query(FamilyMember).filter(
                FamilyMember.family_id == family_id,
                FamilyMember.is_primary == True
            ).first()

            if not primary:
                # Fallback to family's primary phone
                result = self.send_sms(family.primary_phone, message, db, family_id)
                results.append({
                    "phone": family.primary_phone,
                    **result
                })
            else:
                result = self.send_sms(primary.phone, message, db, family_id)
                results.append({
                    "member_id": primary.id,
                    "name": primary.name,
                    "phone": primary.phone,
                    **result
                })

        return {
            "success": True,
            "family_id": family_id,
            "sent_count": len(results),
            "results": results
        }

    def process_incoming_sms(self, from_phone: str, to_phone: str, message_body: str,
                            message_sid: str, db: Session) -> dict:
        """
        Process incoming SMS from Twilio webhook.

        Args:
            from_phone: Sender phone number
            to_phone: Recipient phone number (our Twilio number)
            message_body: Message content
            message_sid: Twilio message SID
            db: Database session

        Returns:
            dict with processing result and family info
        """
        # Lookup family by phone
        lookup = db.query(PhoneLookup).filter(PhoneLookup.phone == from_phone).first()

        if not lookup:
            # Unknown sender
            return {
                "success": False,
                "error": "Phone number not registered",
                "from_phone": from_phone
            }

        family = db.query(Family).filter(Family.id == lookup.family_id).first()

        # Log incoming message
        db_message = Message(
            family_id=lookup.family_id,
            from_phone=from_phone,
            to_phone=to_phone,
            direction=MessageDirection.INBOUND,
            content=message_body,
            twilio_sid=message_sid,
            status=MessageStatus.DELIVERED
        )
        db.add(db_message)
        db.commit()

        return {
            "success": True,
            "family_id": lookup.family_id,
            "family_member_id": lookup.family_member_id,
            "message_id": db_message.id,
            "content": message_body,
            "family": family
        }

    def update_phone_lookup(self, phone: str, family_id: int, family_member_id: Optional[int], db: Session):
        """
        Update phone lookup table for fast lookups.

        Args:
            phone: Phone number
            family_id: Family ID
            family_member_id: Family member ID (optional)
            db: Database session
        """
        # Check if exists
        lookup = db.query(PhoneLookup).filter(PhoneLookup.phone == phone).first()

        if lookup:
            # Update existing
            lookup.family_id = family_id
            lookup.family_member_id = family_member_id
        else:
            # Create new
            lookup = PhoneLookup(
                phone=phone,
                family_id=family_id,
                family_member_id=family_member_id
            )
            db.add(lookup)

        db.commit()


# Global instance
sms_service = SMSService()

"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


# Enums
class SubscriptionTier(str, Enum):
    FREE = "FREE"
    FAMILY = "FAMILY"
    PREMIUM = "PREMIUM"


class RelationshipType(str, Enum):
    MOM = "mom"
    DAD = "dad"
    GRANDPARENT = "grandparent"
    NANNY = "nanny"
    CAREGIVER = "caregiver"
    AUNT = "aunt"
    UNCLE = "uncle"
    SIBLING = "sibling"
    OTHER = "other"


class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class TaskStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    CANCELLED = "cancelled"


# Family schemas
class FamilyCreate(BaseModel):
    primary_name: str
    primary_phone: str
    primary_email: str  # Required for signup
    password: Optional[str] = None  # Will be hashed
    zip_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE


class FamilyLogin(BaseModel):
    email: str
    password: str


class PhoneVerificationRequest(BaseModel):
    phone: str


class PhoneVerificationConfirm(BaseModel):
    phone: str
    code: str


class FamilyResponse(BaseModel):
    id: int
    primary_name: str
    primary_phone: str
    primary_email: str
    is_email_verified: bool
    is_phone_verified: bool
    zip_code: Optional[str]
    city: Optional[str]
    state: Optional[str]
    subscription_tier: SubscriptionTier
    trial_start_date: Optional[datetime]
    trial_end_date: Optional[datetime]
    is_trial_active: bool
    messages_this_month: int
    onboarding_complete: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Family Member schemas
class FamilyMemberCreate(BaseModel):
    family_id: int
    name: str
    phone: str
    relationship_type: RelationshipType
    receive_proactive: bool = True
    can_ask_questions: bool = True
    is_primary: bool = False


class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    receive_proactive: Optional[bool] = None
    can_ask_questions: Optional[bool] = None


class FamilyMemberResponse(BaseModel):
    id: int
    family_id: int
    name: str
    phone: str
    relationship_type: RelationshipType
    receive_proactive: bool
    can_ask_questions: bool
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Child schemas
class ChildCreate(BaseModel):
    family_id: int
    name: str
    birth_date: Optional[date] = None
    due_date: Optional[date] = None
    is_pregnancy: bool = False
    gender: Optional[str] = None


class ChildUpdate(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[date] = None
    due_date: Optional[date] = None
    is_pregnancy: Optional[bool] = None
    gender: Optional[str] = None


class ChildResponse(BaseModel):
    id: int
    family_id: int
    name: str
    birth_date: Optional[date]
    due_date: Optional[date]
    is_pregnancy: bool
    gender: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChildAgeResponse(BaseModel):
    child_id: int
    name: str
    is_pregnancy: bool
    age_days: Optional[int] = None
    age_months: Optional[int] = None
    age_years: Optional[int] = None
    pregnancy_weeks: Optional[int] = None
    description: str


# Message schemas
class MessageCreate(BaseModel):
    family_id: int
    from_phone: str
    to_phone: str
    direction: MessageDirection
    content: str
    twilio_sid: Optional[str] = None
    status: MessageStatus = MessageStatus.PENDING


class MessageResponse(BaseModel):
    id: int
    family_id: int
    from_phone: str
    to_phone: str
    direction: MessageDirection
    content: str
    twilio_sid: Optional[str]
    status: MessageStatus
    created_at: datetime

    class Config:
        from_attributes = True


class MessageStatsResponse(BaseModel):
    total_messages: int
    last_7_days: int
    last_30_days: int
    inbound_count: int
    outbound_count: int


# Task schemas
class ScheduledTaskCreate(BaseModel):
    family_id: int
    child_id: Optional[int] = None
    task_type: str
    scheduled_for: datetime
    task_data: Optional[dict] = None


class ScheduledTaskUpdate(BaseModel):
    scheduled_for: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    task_data: Optional[dict] = None


class ScheduledTaskResponse(BaseModel):
    id: int
    family_id: int
    child_id: Optional[int]
    task_type: str
    scheduled_for: datetime
    status: TaskStatus
    task_data: Optional[dict]
    result: Optional[str]
    executed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# SMS schemas
class SMSWebhookRequest(BaseModel):
    From: str = Field(alias="From")
    To: str = Field(alias="To")
    Body: str = Field(alias="Body")
    MessageSid: str = Field(alias="MessageSid")

    class Config:
        populate_by_name = True


class SMSSendRequest(BaseModel):
    to_phone: str
    message: str


class SMSSendToFamilyRequest(BaseModel):
    message: str
    send_to_all: bool = True  # Send to all members with receive_proactive=True


# Combined responses
class FamilyWithMembersAndChildren(BaseModel):
    family: FamilyResponse
    members: List[FamilyMemberResponse]
    children: List[ChildResponse]

    class Config:
        from_attributes = True

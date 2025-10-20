"""Authentication routes for signup, login, and verification."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from ...database import get_db
from ...models.models import Family, FamilyMember, PhoneLookup
from ...schemas.schemas import (
    FamilyCreate, FamilyLogin, FamilyResponse,
    PhoneVerificationRequest, PhoneVerificationConfirm
)
from ...services.auth_service import (
    hash_password, verify_password, create_access_token,
    generate_verification_code, generate_email_verification_token,
    is_verification_code_expired
)
from ...services.sms_service import SMSService
from ...config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])
sms_service = SMSService()


@router.post("/signup", response_model=FamilyResponse, status_code=status.HTTP_201_CREATED)
async def signup(family_data: FamilyCreate, db: Session = Depends(get_db)):
    """
    Create new family account with email and password.

    - Validates email uniqueness
    - Validates phone uniqueness
    - Hashes password
    - Activates 30-day FAMILY trial
    - Creates primary family member
    - Sends phone verification code
    """
    # Check if email already exists
    existing_email = db.query(Family).filter(Family.primary_email == family_data.primary_email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if phone already exists
    existing_phone = db.query(Family).filter(Family.primary_phone == family_data.primary_phone).first()
    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )

    # Create new family
    new_family = Family(
        primary_name=family_data.primary_name,
        primary_phone=family_data.primary_phone,
        primary_email=family_data.primary_email,
        zip_code=family_data.zip_code,
        city=family_data.city,
        state=family_data.state,
        subscription_tier=family_data.subscription_tier,

        # Hash password if provided
        password_hash=hash_password(family_data.password) if family_data.password else None,

        # Activate 30-day FAMILY trial
        trial_start_date=datetime.utcnow(),
        trial_end_date=datetime.utcnow() + timedelta(days=30),
        is_trial_active=True,

        # Initialize message tracking
        messages_this_month=0,
        last_message_reset=datetime.utcnow(),

        # Auto-verify phone numbers for all users
        is_email_verified=False,
        is_phone_verified=True,  # Auto-verified for all users

        # Generate email verification token
        email_verification_token=generate_email_verification_token(),

        # Onboarding not complete
        onboarding_complete=False
    )

    db.add(new_family)
    db.flush()  # Get the family ID

    # Create primary family member
    primary_member = FamilyMember(
        family_id=new_family.id,
        name=family_data.primary_name,
        phone=family_data.primary_phone,
        relationship_type="mom",  # Default, can be updated later
        receive_proactive=True,
        can_ask_questions=True,
        is_primary=True
    )
    db.add(primary_member)

    # Add to phone lookup
    phone_lookup = PhoneLookup(
        phone=family_data.primary_phone,
        family_id=new_family.id,
        family_member_id=None  # Will be set after member is created
    )
    db.add(phone_lookup)

    db.commit()
    db.refresh(new_family)

    # Update phone lookup with member ID
    phone_lookup.family_member_id = primary_member.id
    db.commit()

    # Send phone verification code
    try:
        verification_code = generate_verification_code()
        new_family.phone_verification_code = verification_code
        new_family.verification_code_expires = datetime.utcnow() + timedelta(minutes=10)
        db.commit()

        # Send SMS with verification code
        sms_service.send_sms(
            to_phone=family_data.primary_phone,
            message=f"Welcome to Coo! Your verification code is: {verification_code}\n\nThis code expires in 10 minutes.",
            db=db,
            family_id=new_family.id
        )
    except Exception as e:
        print(f"Failed to send verification SMS: {e}")
        # Don't fail signup if SMS fails

    return new_family


@router.post("/login")
async def login(credentials: FamilyLogin, db: Session = Depends(get_db)):
    """
    Login with email/phone and password.

    Returns JWT access token on success.
    Accepts either email or phone number in the email field.
    """
    # Try to find family by email first, then by phone
    family = db.query(Family).filter(Family.primary_email == credentials.email).first()

    if not family:
        # Try finding by phone number
        family = db.query(Family).filter(Family.primary_phone == credentials.email).first()

    if not family:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/phone or password"
        )

    # Verify password
    if not family.password_hash or not verify_password(credentials.password, family.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/phone or password"
        )

    # Check if account is deleted
    if family.deletion_status in ["archived", "deleted"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deleted or archived. Reply RESTORE via SMS to restore."
        )

    # Create JWT token
    access_token = create_access_token(
        data={"sub": str(family.id), "email": family.primary_email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "family_id": family.id,
        "email": family.primary_email,
        "is_phone_verified": family.is_phone_verified,
        "is_email_verified": family.is_email_verified,
        "trial_active": family.is_trial_active,
        "trial_end_date": family.trial_end_date
    }


@router.post("/request-phone-verification")
async def request_phone_verification(
    request: PhoneVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Request phone verification code via SMS.

    Generates and sends 6-digit code.
    """
    # Find family by phone
    family = db.query(Family).filter(Family.primary_phone == request.phone).first()

    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not found"
        )

    # Generate and save verification code
    verification_code = generate_verification_code()
    family.phone_verification_code = verification_code
    family.verification_code_expires = datetime.utcnow() + timedelta(minutes=10)
    db.commit()

    # Send SMS
    try:
        sms_service.send_sms(
            to_phone=request.phone,
            message=f"Your Coo verification code is: {verification_code}\n\nExpires in 10 minutes.",
            db=db,
            family_id=family.id
        )

        return {
            "success": True,
            "message": "Verification code sent",
            "expires_in_minutes": 10
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send SMS: {str(e)}"
        )


@router.post("/verify-phone")
async def verify_phone(
    verification: PhoneVerificationConfirm,
    db: Session = Depends(get_db)
):
    """
    Verify phone number with 6-digit code.

    Marks phone as verified on success.
    """
    # Find family by phone
    family = db.query(Family).filter(Family.primary_phone == verification.phone).first()

    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not found"
        )

    # Check if already verified
    if family.is_phone_verified:
        return {
            "success": True,
            "message": "Phone already verified",
            "is_phone_verified": True
        }

    # Check if code exists
    if not family.phone_verification_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No verification code found. Request a new code."
        )

    # Check if code is expired
    if is_verification_code_expired(family.verification_code_expires):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired. Request a new code."
        )

    # Verify code
    if family.phone_verification_code != verification.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )

    # Mark as verified
    family.is_phone_verified = True
    family.phone_verification_code = None  # Clear code
    family.verification_code_expires = None
    db.commit()

    return {
        "success": True,
        "message": "Phone verified successfully! 🎉",
        "is_phone_verified": True
    }


@router.get("/me", response_model=FamilyResponse)
async def get_current_user(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Get current user info from JWT token.

    Used for authenticated requests.
    """
    from ...services.auth_service import verify_token

    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    family_id = int(payload.get("sub"))
    family = db.query(Family).filter(Family.id == family_id).first()

    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return family


@router.post("/delete-account")
async def delete_account(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Initiate account deletion (30/90-day process).

    - Day 0: Messages stopped
    - Day 30: Data archived (can restore)
    - Day 90: Permanent deletion
    """
    from ...services.auth_service import verify_token

    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    family_id = int(payload.get("sub"))
    family = db.query(Family).filter(Family.id == family_id).first()

    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Mark for deletion
    family.deletion_requested_at = datetime.utcnow()
    family.deletion_archived_at = datetime.utcnow() + timedelta(days=30)
    family.deletion_final_at = datetime.utcnow() + timedelta(days=90)
    family.deletion_status = "pending"
    db.commit()

    # Send confirmation SMS
    try:
        sms_service.send_sms(
            to_phone=family.primary_phone,
            message="Account deletion initiated. ❌\n\n• Day 0: Messages stopped\n• Day 30: Data archived\n• Day 90: Permanent deletion\n\nReply RESTORE to cancel anytime."
        )
    except Exception as e:
        print(f"Failed to send deletion SMS: {e}")

    return {
        "success": True,
        "message": "Deletion initiated",
        "deletion_archived_at": family.deletion_archived_at,
        "deletion_final_at": family.deletion_final_at
    }


@router.post("/restore-account")
async def restore_account(
    phone: str,
    db: Session = Depends(get_db)
):
    """
    Restore account that was marked for deletion.

    Can be done anytime before Day 91.
    """
    family = db.query(Family).filter(Family.primary_phone == phone).first()

    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not found"
        )

    if family.deletion_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not marked for deletion"
        )

    # Restore account
    family.deletion_requested_at = None
    family.deletion_archived_at = None
    family.deletion_final_at = None
    family.deletion_status = "restored"
    db.commit()

    # Send confirmation SMS
    try:
        sms_service.send_sms(
            to_phone=family.primary_phone,
            message="Welcome back! 🎉 Your account has been restored.\n\nAll your data is safe and messages are active again."
        )
    except Exception as e:
        print(f"Failed to send restore SMS: {e}")

    return {
        "success": True,
        "message": "Account restored successfully! 🎉"
    }


@router.get("/deletion-status")
async def check_deletion_status(
    phone: str,
    db: Session = Depends(get_db)
):
    """
    Check account deletion status.
    """
    family = db.query(Family).filter(Family.primary_phone == phone).first()

    if not family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not found"
        )

    return {
        "deletion_status": family.deletion_status,
        "deletion_requested_at": family.deletion_requested_at,
        "deletion_archived_at": family.deletion_archived_at,
        "deletion_final_at": family.deletion_final_at,
        "days_until_archive": (family.deletion_archived_at - datetime.utcnow()).days if family.deletion_archived_at else None,
        "days_until_final": (family.deletion_final_at - datetime.utcnow()).days if family.deletion_final_at else None
    }

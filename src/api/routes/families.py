"""Family and family member CRUD routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ...database import get_db
from ...models.models import Family, FamilyMember, PhoneLookup
from ...schemas.schemas import (
    FamilyCreate, FamilyResponse, FamilyMemberCreate,
    FamilyMemberResponse, FamilyMemberUpdate, FamilyWithMembersAndChildren
)
from ...services.sms_service import sms_service
from ...config import settings

router = APIRouter(prefix="/api/families", tags=["Families"])


@router.post("/", response_model=FamilyResponse)
async def create_family(family: FamilyCreate, db: Session = Depends(get_db)):
    """
    Create a new family.

    Automatically creates a primary family member with the primary contact info.
    """
    # Check if phone already exists
    existing = db.query(Family).filter(Family.primary_phone == family.primary_phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    # Create family
    db_family = Family(**family.dict())
    db.add(db_family)
    db.commit()
    db.refresh(db_family)

    # Create primary family member
    primary_member = FamilyMember(
        family_id=db_family.id,
        name=family.primary_name,
        phone=family.primary_phone,
        relationship_type="mom",  # Default, can be updated
        receive_proactive=True,
        can_ask_questions=True,
        is_primary=True
    )
    db.add(primary_member)
    db.commit()
    db.refresh(primary_member)

    # Update phone lookup
    sms_service.update_phone_lookup(
        phone=family.primary_phone,
        family_id=db_family.id,
        family_member_id=primary_member.id,
        db=db
    )

    return db_family


@router.get("/{family_id}", response_model=FamilyWithMembersAndChildren)
async def get_family(family_id: int, db: Session = Depends(get_db)):
    """Get family with all members and children."""
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    return {
        "family": family,
        "members": family.members,
        "children": family.children
    }


@router.get("/{family_id}/children", response_model=List)
async def get_family_children(family_id: int, db: Session = Depends(get_db)):
    """Get all children for a family."""
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    return family.children


@router.get("/phone/{phone}")
async def lookup_family_by_phone(phone: str, db: Session = Depends(get_db)):
    """Lookup family by phone number."""
    lookup = db.query(PhoneLookup).filter(PhoneLookup.phone == phone).first()
    if not lookup:
        raise HTTPException(status_code=404, detail="Phone number not found")

    family = db.query(Family).filter(Family.id == lookup.family_id).first()

    return {
        "family_id": lookup.family_id,
        "family_member_id": lookup.family_member_id,
        "family": family
    }


@router.delete("/{family_id}")
async def delete_family(family_id: int, db: Session = Depends(get_db)):
    """Delete a family and all associated data."""
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    # Delete phone lookups
    db.query(PhoneLookup).filter(PhoneLookup.family_id == family_id).delete()

    # Delete family (cascade will delete members, children, messages, tasks)
    db.delete(family)
    db.commit()

    return {"message": "Family deleted successfully"}


# Family Members endpoints

@router.post("/members", response_model=FamilyMemberResponse)
async def add_family_member(member: FamilyMemberCreate, db: Session = Depends(get_db)):
    """
    Add a family member (max 10 per family).
    """
    # Check family exists
    family = db.query(Family).filter(Family.id == member.family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    # Check member limit based on subscription tier
    member_count = db.query(FamilyMember).filter(FamilyMember.family_id == member.family_id).count()

    # Tier-specific limits
    tier_limits = {
        "FREE": 1,
        "FAMILY": 2,
        "PREMIUM": 10
    }
    max_members = tier_limits.get(family.subscription_tier, 1)

    if member_count >= max_members:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {max_members} family members allowed for {family.subscription_tier} tier"
        )

    # Check if phone already used
    existing = db.query(FamilyMember).filter(FamilyMember.phone == member.phone).first()
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered to another member")

    # Create member
    db_member = FamilyMember(**member.dict())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)

    # Update phone lookup
    sms_service.update_phone_lookup(
        phone=member.phone,
        family_id=member.family_id,
        family_member_id=db_member.id,
        db=db
    )

    return db_member


@router.get("/{family_id}/members", response_model=List[FamilyMemberResponse])
async def get_family_members(family_id: int, db: Session = Depends(get_db)):
    """Get all members for a family."""
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    return family.members


@router.put("/members/{member_id}", response_model=FamilyMemberResponse)
async def update_family_member(
    member_id: int,
    member_update: FamilyMemberUpdate,
    db: Session = Depends(get_db)
):
    """Update family member preferences."""
    member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    # Update fields
    update_data = member_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)

    db.commit()
    db.refresh(member)

    return member


@router.delete("/members/{member_id}")
async def remove_family_member(member_id: int, db: Session = Depends(get_db)):
    """Remove a family member."""
    member = db.query(FamilyMember).filter(FamilyMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    # Don't allow deleting primary member
    if member.is_primary:
        raise HTTPException(status_code=400, detail="Cannot delete primary family member")

    # Delete phone lookup
    db.query(PhoneLookup).filter(PhoneLookup.phone == member.phone).delete()

    # Delete member
    db.delete(member)
    db.commit()

    return {"message": "Family member removed successfully"}

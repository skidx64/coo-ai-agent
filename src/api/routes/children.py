"""Children CRUD routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime
from ...database import get_db
from ...models.models import Family, Child
from ...schemas.schemas import ChildCreate, ChildResponse, ChildUpdate, ChildAgeResponse
from ...config import settings

router = APIRouter(prefix="/api/children", tags=["Children"])


@router.post("/", response_model=ChildResponse)
async def create_child(child: ChildCreate, db: Session = Depends(get_db)):
    """
    Create a new child (max 3 per family).

    Can be either a pregnancy (with due_date) or born child (with birth_date).
    """
    # Check family exists
    family = db.query(Family).filter(Family.id == child.family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    # Check child limit based on subscription tier
    child_count = db.query(Child).filter(Child.family_id == child.family_id).count()

    # Tier-specific limits
    tier_limits = {
        "FREE": 1,
        "FAMILY": 3,
        "PREMIUM": 3
    }
    max_children = tier_limits.get(family.subscription_tier, 1)

    if child_count >= max_children:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {max_children} children allowed for {family.subscription_tier} tier"
        )

    # Validate pregnancy vs born child
    if child.is_pregnancy and not child.due_date:
        raise HTTPException(status_code=400, detail="Pregnancy must have due_date")
    if not child.is_pregnancy and not child.birth_date:
        raise HTTPException(status_code=400, detail="Born child must have birth_date")

    # Create child
    db_child = Child(**child.dict())
    db.add(db_child)
    db.commit()
    db.refresh(db_child)

    return db_child


@router.get("/{child_id}", response_model=ChildResponse)
async def get_child(child_id: int, db: Session = Depends(get_db)):
    """Get child by ID."""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    return child


@router.put("/{child_id}", response_model=ChildResponse)
async def update_child(child_id: int, child_update: ChildUpdate, db: Session = Depends(get_db)):
    """
    Update child information.

    Common use case: Mark pregnancy as born by setting birth_date and is_pregnancy=False.
    """
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Update fields
    update_data = child_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(child, field, value)

    db.commit()
    db.refresh(child)

    return child


@router.delete("/{child_id}")
async def delete_child(child_id: int, db: Session = Depends(get_db)):
    """Delete a child."""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    db.delete(child)
    db.commit()

    return {"message": "Child deleted successfully"}


@router.get("/{child_id}/age", response_model=ChildAgeResponse)
async def get_child_age(child_id: int, db: Session = Depends(get_db)):
    """
    Calculate child's age or pregnancy weeks.

    Returns:
    - For born children: age in days, months, and years
    - For pregnancies: weeks pregnant
    """
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    today = date.today()

    if child.is_pregnancy:
        # Calculate pregnancy weeks
        if not child.due_date:
            raise HTTPException(status_code=400, detail="Pregnancy missing due_date")

        # Pregnancy is 40 weeks, so calculate from due date
        days_until_due = (child.due_date - today).days
        weeks_pregnant = 40 - (days_until_due // 7)

        return {
            "child_id": child.id,
            "name": child.name,
            "is_pregnancy": True,
            "pregnancy_weeks": weeks_pregnant,
            "description": f"{weeks_pregnant} weeks pregnant, due {child.due_date}"
        }
    else:
        # Calculate age for born child
        if not child.birth_date:
            raise HTTPException(status_code=400, detail="Born child missing birth_date")

        delta = today - child.birth_date
        age_days = delta.days
        age_months = age_days // 30
        age_years = age_days // 365

        # Create description
        if age_years >= 2:
            description = f"{age_years} years old"
        elif age_months >= 2:
            description = f"{age_months} months old"
        else:
            description = f"{age_days} days old"

        return {
            "child_id": child.id,
            "name": child.name,
            "is_pregnancy": False,
            "age_days": age_days,
            "age_months": age_months,
            "age_years": age_years,
            "description": description
        }

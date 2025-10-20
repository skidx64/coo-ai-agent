"""Message history routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta
from ...database import get_db
from ...models.models import Message, Family, MessageDirection
from ...schemas.schemas import MessageResponse, MessageStatsResponse

router = APIRouter(prefix="/api/messages", tags=["Messages"])


@router.get("/family/{family_id}", response_model=List[MessageResponse])
async def get_family_messages(
    family_id: int,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    direction: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get message history for a family (paginated).

    Args:
        family_id: Family ID
        limit: Max messages to return (default 50, max 200)
        offset: Offset for pagination
        direction: Filter by direction ("inbound" or "outbound")
    """
    # Check family exists
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    # Build query
    query = db.query(Message).filter(Message.family_id == family_id)

    if direction:
        if direction.lower() == "inbound":
            query = query.filter(Message.direction == MessageDirection.INBOUND)
        elif direction.lower() == "outbound":
            query = query.filter(Message.direction == MessageDirection.OUTBOUND)

    # Order by newest first
    query = query.order_by(Message.created_at.desc())

    # Apply pagination
    messages = query.offset(offset).limit(limit).all()

    return messages


@router.get("/conversation/{phone}", response_model=List[MessageResponse])
async def get_conversation(
    phone: str,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    """
    Get conversation for a specific phone number.

    Returns all messages where phone is either sender or recipient.
    """
    messages = db.query(Message).filter(
        (Message.from_phone == phone) | (Message.to_phone == phone)
    ).order_by(Message.created_at.desc()).limit(limit).all()

    return messages


@router.get("/family/{family_id}/stats", response_model=MessageStatsResponse)
async def get_message_stats(family_id: int, db: Session = Depends(get_db)):
    """
    Get message statistics for a family.

    Returns:
        - Total messages
        - Messages in last 7 days
        - Messages in last 30 days
        - Inbound vs outbound counts
    """
    # Check family exists
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    # Total messages
    total = db.query(Message).filter(Message.family_id == family_id).count()

    # Last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    last_7_days = db.query(Message).filter(
        and_(
            Message.family_id == family_id,
            Message.created_at >= seven_days_ago
        )
    ).count()

    # Last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    last_30_days = db.query(Message).filter(
        and_(
            Message.family_id == family_id,
            Message.created_at >= thirty_days_ago
        )
    ).count()

    # Inbound count
    inbound_count = db.query(Message).filter(
        and_(
            Message.family_id == family_id,
            Message.direction == MessageDirection.INBOUND
        )
    ).count()

    # Outbound count
    outbound_count = db.query(Message).filter(
        and_(
            Message.family_id == family_id,
            Message.direction == MessageDirection.OUTBOUND
        )
    ).count()

    return {
        "total_messages": total,
        "last_7_days": last_7_days,
        "last_30_days": last_30_days,
        "inbound_count": inbound_count,
        "outbound_count": outbound_count
    }


@router.delete("/family/{family_id}")
async def delete_old_messages(
    family_id: int,
    days_old: int = Query(default=90, ge=1),
    db: Session = Depends(get_db)
):
    """
    Delete messages older than X days for a family.

    Useful for message retention policies.

    Args:
        family_id: Family ID
        days_old: Delete messages older than this many days (default 90)
    """
    # Check family exists
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    cutoff_date = datetime.utcnow() - timedelta(days=days_old)

    # Delete old messages
    deleted_count = db.query(Message).filter(
        and_(
            Message.family_id == family_id,
            Message.created_at < cutoff_date
        )
    ).delete()

    db.commit()

    return {
        "message": f"Deleted {deleted_count} messages older than {days_old} days",
        "deleted_count": deleted_count
    }

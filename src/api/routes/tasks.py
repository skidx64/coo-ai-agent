"""Task scheduling routes."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from ...database import get_db
from ...models.models import Family, Child, ScheduledTask, TaskStatus
from ...schemas.schemas import (
    ScheduledTaskCreate, ScheduledTaskResponse,
    ScheduledTaskUpdate
)
from ...services.sms_service import sms_service

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post("/", response_model=ScheduledTaskResponse)
async def create_task(task: ScheduledTaskCreate, db: Session = Depends(get_db)):
    """
    Schedule a new task.

    Task types can include:
    - vaccine_reminder
    - milestone
    - preschool_deadline
    - doctor_appointment
    - etc.
    """
    # Check family exists
    family = db.query(Family).filter(Family.id == task.family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    # Check child exists if provided
    if task.child_id:
        child = db.query(Child).filter(Child.id == task.child_id).first()
        if not child:
            raise HTTPException(status_code=404, detail="Child not found")
        if child.family_id != task.family_id:
            raise HTTPException(status_code=400, detail="Child does not belong to this family")

    # Create task
    db_task = ScheduledTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    return db_task


@router.get("/family/{family_id}", response_model=List[ScheduledTaskResponse])
async def get_family_tasks(
    family_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all tasks for a family.

    Can filter by status: pending, sent, cancelled
    """
    # Check family exists
    family = db.query(Family).filter(Family.id == family_id).first()
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")

    query = db.query(ScheduledTask).filter(ScheduledTask.family_id == family_id)

    if status:
        if status.lower() == "pending":
            query = query.filter(ScheduledTask.status == TaskStatus.PENDING)
        elif status.lower() == "sent":
            query = query.filter(ScheduledTask.status == TaskStatus.SENT)
        elif status.lower() == "cancelled":
            query = query.filter(ScheduledTask.status == TaskStatus.CANCELLED)

    tasks = query.order_by(ScheduledTask.scheduled_for).all()
    return tasks


@router.get("/child/{child_id}", response_model=List[ScheduledTaskResponse])
async def get_child_tasks(child_id: int, db: Session = Depends(get_db)):
    """Get all tasks for a specific child."""
    # Check child exists
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    tasks = db.query(ScheduledTask).filter(
        ScheduledTask.child_id == child_id
    ).order_by(ScheduledTask.scheduled_for).all()

    return tasks


@router.get("/pending", response_model=List[ScheduledTaskResponse])
async def get_pending_tasks(
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db)
):
    """
    Get pending tasks that are due now or in the past.

    This endpoint is used by the scheduler/cron job to execute tasks.
    """
    now = datetime.utcnow()

    tasks = db.query(ScheduledTask).filter(
        ScheduledTask.status == TaskStatus.PENDING,
        ScheduledTask.scheduled_for <= now
    ).order_by(ScheduledTask.scheduled_for).limit(limit).all()

    return tasks


@router.post("/{task_id}/execute")
async def execute_task(task_id: int, db: Session = Depends(get_db)):
    """
    Execute a scheduled task.

    Sends SMS to the family and marks task as sent.
    """
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Task already {task.status}")

    # Get family
    family = db.query(Family).filter(Family.id == task.family_id).first()

    # Build message based on task type and data
    message = _build_task_message(task, family, db)

    # Send SMS to family
    result = sms_service.send_to_family(
        family_id=task.family_id,
        message=message,
        db=db,
        send_to_all=True
    )

    # Update task
    task.status = TaskStatus.SENT
    task.executed_at = datetime.utcnow()
    task.result = f"Sent to {result.get('sent_count', 0)} family members"
    db.commit()

    return {
        "message": "Task executed successfully",
        "task_id": task_id,
        "sms_result": result
    }


@router.put("/{task_id}/cancel", response_model=ScheduledTaskResponse)
async def cancel_task(task_id: int, db: Session = Depends(get_db)):
    """Cancel a scheduled task."""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status == TaskStatus.SENT:
        raise HTTPException(status_code=400, detail="Cannot cancel already sent task")

    task.status = TaskStatus.CANCELLED
    db.commit()
    db.refresh(task)

    return task


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a scheduled task."""
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully"}


@router.post("/schedule-child-tasks/{child_id}")
async def schedule_all_child_tasks(child_id: int, db: Session = Depends(get_db)):
    """
    Auto-schedule all relevant tasks for a child based on their age.

    For born children:
    - Vaccine reminders at 2, 4, 6, 12, 15, 18 months
    - Milestone celebrations
    - Annual checkups

    For pregnancies:
    - Prenatal visit reminders
    - Pregnancy milestones (week 20, 30, etc.)
    """
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    tasks_created = []

    if child.is_pregnancy:
        # Schedule pregnancy tasks
        tasks_created = _schedule_pregnancy_tasks(child, db)
    else:
        # Schedule baby/child tasks
        tasks_created = _schedule_child_development_tasks(child, db)

    return {
        "message": f"Scheduled {len(tasks_created)} tasks for {child.name}",
        "tasks_created": len(tasks_created),
        "child_id": child_id
    }


# Helper functions

def _build_task_message(task: ScheduledTask, family: Family, db: Session) -> str:
    """Build SMS message based on task type."""
    task_data = task.task_data or {}

    if task.task_type == "vaccine_reminder":
        child = db.query(Child).filter(Child.id == task.child_id).first()
        vaccine_name = task_data.get("vaccine_name", "vaccination")
        return f"Hi {family.primary_name}! Reminder: {child.name} is due for {vaccine_name}. Please schedule an appointment with your pediatrician."

    elif task.task_type == "milestone":
        child = db.query(Child).filter(Child.id == task.child_id).first()
        milestone = task_data.get("milestone", "a milestone")
        return f"Congratulations! {child.name} is reaching {milestone}! This is an exciting time in your child's development."

    elif task.task_type == "preschool_deadline":
        child = db.query(Child).filter(Child.id == task.child_id).first()
        deadline = task_data.get("deadline", "soon")
        return f"Reminder: Preschool registration for {child.name} is due {deadline}. Don't miss the deadline!"

    else:
        # Generic message
        message_text = task_data.get("message", "You have a reminder from Coo.")
        return message_text


def _schedule_pregnancy_tasks(child: Child, db: Session) -> List[ScheduledTask]:
    """Schedule tasks for pregnancy."""
    if not child.due_date:
        return []

    tasks = []
    now = datetime.utcnow()

    # Week 20 ultrasound
    week_20 = child.due_date - timedelta(days=140)
    if week_20 > now.date():
        task = ScheduledTask(
            family_id=child.family_id,
            child_id=child.id,
            task_type="milestone",
            scheduled_for=datetime.combine(week_20, datetime.min.time()),
            task_data={"milestone": "20-week anatomy scan"}
        )
        tasks.append(task)
        db.add(task)

    # Tdap vaccine (week 27-36)
    week_30 = child.due_date - timedelta(days=70)
    if week_30 > now.date():
        task = ScheduledTask(
            family_id=child.family_id,
            child_id=child.id,
            task_type="vaccine_reminder",
            scheduled_for=datetime.combine(week_30, datetime.min.time()),
            task_data={"vaccine_name": "Tdap vaccine (whooping cough)"}
        )
        tasks.append(task)
        db.add(task)

    db.commit()
    return tasks


def _schedule_child_development_tasks(child: Child, db: Session) -> List[ScheduledTask]:
    """Schedule tasks for born child."""
    if not child.birth_date:
        return []

    tasks = []
    now = datetime.utcnow()

    # Vaccine schedule (simplified)
    vaccine_schedule = [
        (60, "2-month vaccines"),
        (120, "4-month vaccines"),
        (180, "6-month vaccines"),
        (365, "12-month vaccines"),
        (450, "15-month vaccines"),
        (540, "18-month vaccines")
    ]

    for days_after_birth, vaccine_name in vaccine_schedule:
        vaccine_date = child.birth_date + timedelta(days=days_after_birth)
        if vaccine_date > now.date():
            task = ScheduledTask(
                family_id=child.family_id,
                child_id=child.id,
                task_type="vaccine_reminder",
                scheduled_for=datetime.combine(vaccine_date, datetime.min.time()),
                task_data={"vaccine_name": vaccine_name}
            )
            tasks.append(task)
            db.add(task)

    # Milestone reminders
    milestones = [
        (180, "6-month milestone (sitting up, babbling)"),
        (365, "1st birthday"),
        (730, "2nd birthday"),
        (1095, "3rd birthday")
    ]

    for days_after_birth, milestone in milestones:
        milestone_date = child.birth_date + timedelta(days=days_after_birth)
        if milestone_date > now.date():
            task = ScheduledTask(
                family_id=child.family_id,
                child_id=child.id,
                task_type="milestone",
                scheduled_for=datetime.combine(milestone_date, datetime.min.time()),
                task_data={"milestone": milestone}
            )
            tasks.append(task)
            db.add(task)

    db.commit()
    return tasks

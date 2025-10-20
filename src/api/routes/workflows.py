"""Agentic AI workflow API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from ...services.workflow_service import workflow_service


router = APIRouter(prefix="/api/workflows", tags=["AI Workflows"])


class PregnancyWorkflowRequest(BaseModel):
    """Request model for pregnancy guidance workflow."""
    family_id: Optional[int] = None  # Optional for demo/testing
    weeks_pregnant: int
    concerns: Optional[str] = None


class VaccineWorkflowRequest(BaseModel):
    """Request model for vaccine planning workflow."""
    family_id: Optional[int] = None  # Optional for demo/testing
    child_id: Optional[int] = None  # Optional child ID for specific child
    child_age_months: int
    concerns: Optional[str] = None
    completed_vaccines: Optional[List[str]] = []


class MilestoneWorkflowRequest(BaseModel):
    """Request model for milestone assessment workflow."""
    family_id: Optional[int] = None  # Optional for demo/testing
    child_id: Optional[int] = None
    child_age_months: int
    current_abilities: Optional[str] = None
    concerns: Optional[str] = None


class ActivityWorkflowRequest(BaseModel):
    """Request model for activity recommendation workflow."""
    family_id: Optional[int] = None  # Optional for demo/testing
    child_id: Optional[int] = None
    child_age_months: int
    interests: Optional[str] = None
    goals: Optional[str] = "general development"


class PreschoolWorkflowRequest(BaseModel):
    """Request model for preschool readiness workflow."""
    family_id: Optional[int] = None  # Optional for demo/testing
    child_id: Optional[int] = None
    child_age_months: int
    current_skills: Optional[str] = None
    target_start_date: Optional[str] = None


@router.get("/")
async def list_workflows():
    """
    List all available workflows.

    Returns information about each workflow including purpose and required context.
    """
    return {
        "available_workflows": [
            {
                "name": "pregnancy",
                "description": "Multi-step pregnancy guidance with trimester info and milestones",
                "endpoint": "/api/workflows/pregnancy",
                "required_fields": ["weeks_pregnant"],
                "optional_fields": ["concerns"]
            },
            {
                "name": "vaccines",
                "description": "Vaccine planning with schedule, education, and concern addressing",
                "endpoint": "/api/workflows/vaccines",
                "required_fields": ["child_age_months"],
                "optional_fields": ["concerns", "completed_vaccines"]
            },
            {
                "name": "milestones",
                "description": "Developmental milestone assessment with activities and red flags",
                "endpoint": "/api/workflows/milestones",
                "required_fields": ["child_age_months"],
                "optional_fields": ["current_abilities", "concerns"]
            },
            {
                "name": "activities",
                "description": "Personalized activity recommendations with weekly plan",
                "endpoint": "/api/workflows/activities",
                "required_fields": ["child_age_months"],
                "optional_fields": ["interests", "goals"]
            },
            {
                "name": "preschool",
                "description": "Preschool readiness assessment with preparation plan",
                "endpoint": "/api/workflows/preschool",
                "required_fields": ["child_age_months"],
                "optional_fields": ["current_skills", "target_start_date"]
            }
        ],
        "workflow_features": [
            "Multi-step AI reasoning",
            "RAG-powered knowledge retrieval",
            "Personalized recommendations",
            "Actionable plans and timelines"
        ]
    }


@router.post("/pregnancy")
async def pregnancy_workflow(request: PregnancyWorkflowRequest):
    """
    Execute pregnancy guidance workflow.

    This workflow provides:
    1. Current trimester information
    2. Personalized guidance for current week
    3. Upcoming pregnancy milestones
    4. Action items (appointments, tests)

    Example:
    ```json
    {
      "weeks_pregnant": 20,
      "concerns": "Is it normal to feel more tired?"
    }
    ```
    """
    context = request.dict()
    result = workflow_service.execute_workflow("pregnancy", context)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/vaccines")
async def vaccine_workflow(request: VaccineWorkflowRequest):
    """
    Execute vaccine planning workflow.

    This workflow provides:
    1. Vaccines due now based on age
    2. Detailed vaccine plan and importance
    3. Addresses parent concerns with evidence
    4. Timeline of upcoming vaccines
    5. What to expect (side effects, comfort tips)

    Example:
    ```json
    {
      "child_age_months": 6,
      "concerns": "Are vaccines safe?",
      "completed_vaccines": ["DTaP", "Hib"]
    }
    ```
    """
    context = request.dict()
    result = workflow_service.execute_workflow("vaccines", context)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/milestones")
async def milestone_workflow(request: MilestoneWorkflowRequest):
    """
    Execute developmental milestone assessment workflow.

    This workflow provides:
    1. Expected milestones for child's age
    2. Assessment of current development
    3. Recommended activities to support development
    4. Red flags requiring pediatrician follow-up

    Example:
    ```json
    {
      "child_age_months": 18,
      "current_abilities": "walking, says a few words, points to objects",
      "concerns": "Not talking much yet"
    }
    ```
    """
    context = request.dict()
    result = workflow_service.execute_workflow("milestones", context)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/activities")
async def activity_workflow(request: ActivityWorkflowRequest):
    """
    Execute activity recommendation workflow.

    This workflow provides:
    1. Age-appropriate activity categories
    2. 5 detailed activity recommendations
    3. Weekly activity plan
    4. Safety tips for activities
    5. Materials needed (household items preferred)

    Example:
    ```json
    {
      "child_age_months": 12,
      "interests": "music, water play",
      "goals": "motor skills and language"
    }
    ```
    """
    context = request.dict()
    result = workflow_service.execute_workflow("activities", context)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/preschool")
async def preschool_workflow(request: PreschoolWorkflowRequest):
    """
    Execute preschool readiness workflow.

    This workflow provides:
    1. Age appropriateness assessment
    2. Readiness evaluation across 4 domains
    3. 3-month preparation plan
    4. School selection guidance
    5. Timeline recommendations

    Example:
    ```json
    {
      "child_age_months": 36,
      "current_skills": "potty trained, plays with others, speaks in sentences",
      "target_start_date": "2025-09"
    }
    ```
    """
    context = request.dict()
    result = workflow_service.execute_workflow("preschool", context)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result


@router.post("/execute")
async def execute_generic_workflow(workflow_name: str, context: Dict[str, Any]):
    """
    Execute any workflow by name with generic context.

    This is a flexible endpoint for advanced use cases.

    Args:
        workflow_name: Name of workflow (pregnancy, vaccines, milestones, activities, preschool)
        context: Dict with workflow-specific context

    Returns:
        Workflow execution results
    """
    result = workflow_service.execute_workflow(workflow_name, context)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))

    return result

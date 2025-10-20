"""Agentic AI workflows for complex multi-step parenting guidance."""
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from .ai_service import ai_service
from .rag_service import rag_service


class WorkflowService:
    """Service for orchestrating multi-step AI workflows."""

    def __init__(self):
        """Initialize workflow service."""
        self.workflows = {
            "pregnancy": self.pregnancy_guidance_workflow,
            "vaccines": self.vaccine_planning_workflow,
            "milestones": self.milestone_assessment_workflow,
            "activities": self.activity_recommendation_workflow,
            "preschool": self.preschool_readiness_workflow
        }

    def execute_workflow(
        self,
        workflow_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a specific workflow.

        Args:
            workflow_name: Name of workflow to execute
            context: Context data for the workflow

        Returns:
            Dict with workflow results
        """
        if workflow_name not in self.workflows:
            return {
                "success": False,
                "error": f"Unknown workflow: {workflow_name}",
                "available_workflows": list(self.workflows.keys())
            }

        workflow_func = self.workflows[workflow_name]
        try:
            result = workflow_func(context)
            result["success"] = True
            result["workflow"] = workflow_name
            result["executed_at"] = datetime.now().isoformat()
            return result
        except Exception as e:
            return {
                "success": False,
                "workflow": workflow_name,
                "error": str(e)
            }

    def pregnancy_guidance_workflow(self, context: Dict) -> Dict:
        """
        Multi-step workflow for pregnancy guidance.

        Steps:
        1. Determine current trimester/week
        2. Get relevant pregnancy info from knowledge base
        3. Generate personalized guidance
        4. Identify upcoming milestones
        5. Provide actionable next steps

        Context:
            - weeks_pregnant: int (required)
            - concerns: str (optional)
        """
        weeks = context.get("weeks_pregnant")
        concerns = context.get("concerns", "")

        if not weeks:
            return {"error": "weeks_pregnant is required"}

        # Step 1: Determine trimester
        if weeks <= 13:
            trimester = 1
            trimester_name = "first"
        elif weeks <= 26:
            trimester = 2
            trimester_name = "second"
        else:
            trimester = 3
            trimester_name = "third"

        # Step 2: Get pregnancy knowledge from RAG
        rag_context = rag_service.get_context_for_question(
            f"pregnancy {trimester_name} trimester week {weeks}",
            n_results=5
        )

        # Step 3: Generate personalized guidance
        guidance_prompt = f"""Based on the pregnancy information provided, give guidance for a parent at week {weeks} of pregnancy ({trimester_name} trimester).

Pregnancy Resources:
{rag_context if rag_context else "Use general pregnancy knowledge."}

{"Additional concerns: " + concerns if concerns else ""}

Provide:
1. What to expect this week
2. Important dos and don'ts
3. Warning signs to watch for
4. Next appointment/milestone coming up"""

        guidance = ai_service.answer_question(
            question=guidance_prompt,
            context=rag_context,
            use_case="general",
            max_tokens=400
        )

        # Step 4: Identify upcoming milestones
        milestones = []
        if weeks < 20:
            milestones.append({"week": 20, "milestone": "Anatomy ultrasound (gender reveal possible)"})
        if weeks < 28:
            milestones.append({"week": 28, "milestone": "Glucose screening test, start third trimester"})
        if weeks < 36:
            milestones.append({"week": 36, "milestone": "Group B strep test, weekly checkups begin"})

        # Step 5: Generate action items
        action_items = []
        if 18 <= weeks <= 22:
            action_items.append("Schedule anatomy ultrasound (weeks 18-22)")
        if 24 <= weeks <= 28:
            action_items.append("Schedule glucose screening test")
        if 27 <= weeks <= 30:
            action_items.append("Get Tdap vaccine (protects baby from whooping cough)")
        if weeks >= 35:
            action_items.append("Pack hospital bag, finalize birth plan")

        return {
            "trimester": trimester,
            "weeks_pregnant": weeks,
            "guidance": guidance.get("answer", ""),
            "upcoming_milestones": milestones[:2],  # Next 2 milestones
            "action_items": action_items,
            "sources_used": guidance.get("sources", 0),
            "workflow_steps": 5
        }

    def vaccine_planning_workflow(self, context: Dict) -> Dict:
        """
        Multi-step workflow for vaccine planning and education.

        Steps:
        1. Calculate child's age and determine vaccine schedule
        2. Get vaccine info from knowledge base
        3. Generate personalized vaccine plan
        4. Address common concerns with AI
        5. Create timeline of upcoming vaccines

        Context:
            - child_age_months: int (required)
            - concerns: str (optional)
            - completed_vaccines: List[str] (optional)
        """
        age_months = context.get("child_age_months")
        concerns = context.get("concerns", "")
        completed = context.get("completed_vaccines", [])

        if age_months is None:
            return {"error": "child_age_months is required"}

        # Step 1: Determine vaccine schedule based on age
        vaccine_schedule = {
            0: ["Hepatitis B (dose 1)"],
            2: ["DTaP", "Hib", "PCV", "Polio", "Rotavirus", "Hepatitis B (dose 2)"],
            4: ["DTaP", "Hib", "PCV", "Polio", "Rotavirus"],
            6: ["DTaP", "Hib", "PCV", "Polio", "Rotavirus", "Hepatitis B (dose 3)", "Flu vaccine"],
            12: ["MMR", "Varicella (Chickenpox)", "Hepatitis A (dose 1)", "PCV"],
            15: ["DTaP", "Hib"],
            18: ["Hepatitis A (dose 2)", "Flu vaccine"],
            24: ["Flu vaccine (annual)"],
            48: ["DTaP", "Polio", "MMR", "Varicella"],
        }

        # Find vaccines due now or overdue
        due_now = []
        upcoming = []
        for schedule_age, vaccines in vaccine_schedule.items():
            if schedule_age <= age_months and schedule_age >= age_months - 2:
                # Due now (within 2-month window)
                due_now.extend([v for v in vaccines if v not in completed])
            elif schedule_age > age_months:
                # Upcoming
                upcoming.append({"age_months": schedule_age, "vaccines": vaccines})
                if len(upcoming) >= 2:  # Only next 2 upcoming
                    break

        # Step 2: Get vaccine knowledge from RAG
        rag_context = rag_service.get_context_for_question(
            f"vaccines for {age_months} month old baby",
            n_results=5
        )

        # Step 3: Generate vaccine plan
        plan_prompt = f"""Create a vaccine plan for a {age_months}-month-old child.

Vaccines due now: {', '.join(due_now) if due_now else 'None (up to date)'}

Vaccine Resources:
{rag_context if rag_context else "Use general vaccine knowledge."}

{"Parent concerns: " + concerns if concerns else ""}

Provide:
1. Which vaccines are due now
2. Why each vaccine is important
3. What to expect (side effects)
4. Tips for comfort after vaccination"""

        plan = ai_service.answer_question(
            question=plan_prompt,
            context=rag_context,
            use_case="vaccine_info",
            max_tokens=400
        )

        # Step 4: Address concerns with AI if provided
        concern_response = None
        if concerns:
            concern_response = ai_service.answer_question(
                question=f"Parent vaccine concern: {concerns}",
                context=rag_context,
                use_case="vaccine_info",
                max_tokens=200
            )

        # Step 5: Create timeline
        timeline = []
        for item in upcoming[:3]:  # Next 3 vaccine visits
            timeline.append({
                "age_months": item["age_months"],
                "age_display": f"{item['age_months']} months",
                "vaccines": item["vaccines"][:3]  # Top 3 vaccines at that age
            })

        return {
            "child_age_months": age_months,
            "vaccines_due_now": due_now,
            "vaccine_plan": plan.get("answer", ""),
            "concern_addressed": concern_response.get("answer") if concern_response else None,
            "upcoming_timeline": timeline,
            "sources_used": plan.get("sources", 0),
            "workflow_steps": 5
        }

    def milestone_assessment_workflow(self, context: Dict) -> Dict:
        """
        Multi-step workflow for developmental milestone assessment.

        Steps:
        1. Determine age and expected milestones
        2. Get developmental info from knowledge base
        3. Assess current development
        4. Generate personalized activities
        5. Flag any concerns

        Context:
            - child_age_months: int (required)
            - current_abilities: str (optional)
            - concerns: str (optional)
        """
        age_months = context.get("child_age_months")
        abilities = context.get("current_abilities", "")
        concerns = context.get("concerns", "")

        if age_months is None:
            return {"error": "child_age_months is required"}

        # Step 1: Define expected milestones by age
        milestone_ranges = {
            (0, 3): ["Lifts head", "Tracks objects", "Smiles socially"],
            (4, 6): ["Rolls over", "Reaches for toys", "Babbles", "Sits with support"],
            (7, 9): ["Sits without support", "Crawls", "Says mama/dada", "Picks up objects"],
            (10, 12): ["Stands with support", "First steps", "Waves bye-bye", "Says 1-2 words"],
            (13, 18): ["Walks independently", "Says 5-10 words", "Drinks from cup", "Points to objects"],
            (19, 24): ["Runs", "Kicks ball", "2-word phrases", "Follows simple directions"],
            (25, 36): ["Jumps", "Uses sentences", "Plays pretend", "Knows colors"],
        }

        # Find appropriate milestone range
        expected_milestones = []
        for (start, end), milestones in milestone_ranges.items():
            if start <= age_months <= end:
                expected_milestones = milestones
                break

        # Step 2: Get developmental knowledge from RAG
        rag_context = rag_service.get_context_for_question(
            f"development milestones {age_months} months",
            n_results=5
        )

        # Step 3: Assess development
        assessment_prompt = f"""Assess development for a {age_months}-month-old child.

Expected milestones at this age: {', '.join(expected_milestones)}
{"Current abilities: " + abilities if abilities else ""}
{"Parent concerns: " + concerns if concerns else ""}

Developmental Resources:
{rag_context if rag_context else "Use general developmental knowledge."}

Provide:
1. Overall development status
2. Which milestones are on track
3. Which to focus on next
4. When to consult pediatrician (red flags)"""

        assessment = ai_service.answer_question(
            question=assessment_prompt,
            context=rag_context,
            use_case="general",
            max_tokens=400
        )

        # Step 4: Generate activities to support development
        activities_prompt = f"""Suggest 3-5 age-appropriate activities to support development for a {age_months}-month-old.

Focus on: {', '.join(expected_milestones[:3])}

Activities Resources:
{rag_service.get_context_for_question(f"activities {age_months} months", n_results=3)}

List specific, practical activities parents can do at home."""

        activities = ai_service.answer_question(
            question=activities_prompt,
            max_tokens=250
        )

        # Step 5: Flag concerns
        red_flags = []
        if age_months >= 6 and abilities and "sit" not in abilities.lower():
            red_flags.append("Not sitting by 6 months")
        if age_months >= 12 and abilities and "walk" not in abilities.lower():
            red_flags.append("Not walking by 12 months")
        if age_months >= 18 and abilities and "word" not in abilities.lower():
            red_flags.append("Limited words by 18 months")

        return {
            "child_age_months": age_months,
            "expected_milestones": expected_milestones,
            "assessment": assessment.get("answer", ""),
            "recommended_activities": activities.get("answer", ""),
            "red_flags": red_flags if red_flags else None,
            "follow_up_needed": len(red_flags) > 0,
            "sources_used": assessment.get("sources", 0),
            "workflow_steps": 5
        }

    def activity_recommendation_workflow(self, context: Dict) -> Dict:
        """
        Multi-step workflow for personalized activity recommendations.

        Steps:
        1. Determine age-appropriate activities
        2. Get activity ideas from knowledge base
        3. Generate personalized recommendations
        4. Create weekly activity plan
        5. Provide safety tips

        Context:
            - child_age_months: int (required)
            - interests: str (optional)
            - goals: str (optional, e.g., "motor skills", "language")
        """
        age_months = context.get("child_age_months")
        interests = context.get("interests", "")
        goals = context.get("goals", "general development")

        if age_months is None:
            return {"error": "child_age_months is required"}

        # Step 1: Determine age-appropriate activity categories
        if age_months <= 6:
            categories = ["Sensory play", "Tummy time", "Visual stimulation"]
        elif age_months <= 12:
            categories = ["Motor skills", "Object exploration", "Cause and effect"]
        elif age_months <= 24:
            categories = ["Physical play", "Pretend play", "Art activities"]
        else:
            categories = ["Learning activities", "Social play", "Creative arts", "Outdoor play"]

        # Step 2: Get activity knowledge from RAG
        rag_context = rag_service.get_context_for_question(
            f"activities for {age_months} month old {interests} {goals}",
            n_results=5
        )

        # Step 3: Generate recommendations
        rec_prompt = f"""Recommend age-appropriate activities for a {age_months}-month-old child.

Focus areas: {goals}
{"Child interests: " + interests if interests else ""}
Activity categories: {', '.join(categories)}

Activity Resources:
{rag_context if rag_context else "Use general activity knowledge."}

Provide:
1. 5 specific activities with clear instructions
2. Materials needed (household items preferred)
3. Developmental benefits of each
4. How to adapt for different skill levels"""

        recommendations = ai_service.answer_question(
            question=rec_prompt,
            context=rag_context,
            max_tokens=500
        )

        # Step 4: Create weekly activity plan
        weekly_plan = {
            "Monday": f"Sensory play - {categories[0] if categories else 'Exploration'}",
            "Tuesday": f"Physical activity - {categories[1] if len(categories) > 1 else 'Movement'}",
            "Wednesday": "Reading & songs",
            "Thursday": f"Creative play - {categories[2] if len(categories) > 2 else 'Art'}",
            "Friday": "Outdoor time",
            "Weekend": "Family activities & free play"
        }

        # Step 5: Safety tips
        safety_tips = []
        if age_months <= 12:
            safety_tips.append("Supervise all activities closely")
            safety_tips.append("Avoid small objects (choking hazard)")
            safety_tips.append("Ensure safe play surface")
        else:
            safety_tips.append("Supervise with age-appropriate distance")
            safety_tips.append("Check toys for small parts")
            safety_tips.append("Set clear boundaries for active play")

        return {
            "child_age_months": age_months,
            "activity_categories": categories,
            "detailed_recommendations": recommendations.get("answer", ""),
            "weekly_plan": weekly_plan,
            "safety_tips": safety_tips,
            "sources_used": recommendations.get("sources", 0),
            "workflow_steps": 5
        }

    def preschool_readiness_workflow(self, context: Dict) -> Dict:
        """
        Multi-step workflow for preschool readiness assessment.

        Steps:
        1. Assess age and readiness factors
        2. Get preschool info from knowledge base
        3. Evaluate readiness across domains
        4. Generate preparation plan
        5. Provide school selection guidance

        Context:
            - child_age_months: int (required)
            - current_skills: str (optional)
            - target_start_date: str (optional, YYYY-MM format)
        """
        age_months = context.get("child_age_months")
        skills = context.get("current_skills", "")
        target_date = context.get("target_start_date", "")

        if age_months is None:
            return {"error": "child_age_months is required"}

        age_years = age_months / 12

        # Step 1: Define readiness domains
        readiness_domains = {
            "Social-Emotional": [
                "Separates from parent",
                "Plays with other children",
                "Follows simple rules"
            ],
            "Physical": [
                "Toilet trained or working on it",
                "Can feed self",
                "Uses stairs"
            ],
            "Cognitive": [
                "Knows colors and shapes",
                "Follows 2-3 step directions",
                "Recognizes some letters"
            ],
            "Language": [
                "Speaks in sentences",
                "Understood by others",
                "Can express needs"
            ]
        }

        # Step 2: Get preschool knowledge from RAG
        rag_context = rag_service.get_context_for_question(
            f"preschool readiness {age_months} months",
            n_results=5
        )

        # Step 3: Evaluate readiness
        eval_prompt = f"""Assess preschool readiness for a {age_months}-month-old ({age_years:.1f} years).

{"Current skills: " + skills if skills else ""}
{"Target start: " + target_date if target_date else ""}

Readiness domains: {', '.join(readiness_domains.keys())}

Preschool Resources:
{rag_context if rag_context else "Use general preschool knowledge."}

Provide:
1. Overall readiness assessment
2. Strengths
3. Areas to develop before starting
4. Realistic timeline recommendation"""

        evaluation = ai_service.answer_question(
            question=eval_prompt,
            context=rag_context,
            use_case="general",
            max_tokens=400
        )

        # Step 4: Generate preparation plan
        prep_plan = {
            "3_months_before": [
                "Visit preschools",
                "Practice separation (playdates, babysitter)",
                "Establish bedtime routine"
            ],
            "1_month_before": [
                "Talk positively about school",
                "Read books about starting school",
                "Practice self-help skills (putting on shoes, washing hands)"
            ],
            "1_week_before": [
                "Visit the classroom if possible",
                "Meet the teacher",
                "Practice the morning routine"
            ]
        }

        # Step 5: School selection guidance
        selection_prompt = f"""Provide preschool selection guidance for a {age_years:.1f}-year-old.

What should parents look for when choosing a preschool?
Provide 5 key factors to consider."""

        selection_guidance = ai_service.answer_question(
            question=selection_prompt,
            max_tokens=250
        )

        # Determine if age-appropriate for preschool
        typical_preschool_age = 36  # 3 years
        age_appropriate = age_months >= typical_preschool_age - 6  # Within 6 months

        return {
            "child_age_months": age_months,
            "child_age_years": round(age_years, 1),
            "age_appropriate": age_appropriate,
            "readiness_domains": readiness_domains,
            "readiness_evaluation": evaluation.get("answer", ""),
            "preparation_plan": prep_plan,
            "school_selection_guidance": selection_guidance.get("answer", ""),
            "sources_used": evaluation.get("sources", 0),
            "workflow_steps": 5
        }


# Global workflow service instance
workflow_service = WorkflowService()

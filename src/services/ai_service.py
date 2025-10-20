"""AI service for intelligent question answering and symptom triage using Claude API."""
from anthropic import Anthropic
from typing import Dict, Optional, List
from ..config import settings
from .rag_service import rag_service
import os
import json


class AIService:
    """Service for AI-powered reasoning and responses."""

    def __init__(self):
        """Initialize AI service with Claude API or AWS Bedrock."""
        self.client = None
        self.bedrock_runtime = None
        self.provider = settings.ai_provider

        if self.provider == "anthropic":
            if settings.anthropic_api_key:
                self.client = Anthropic(api_key=settings.anthropic_api_key)
        elif self.provider == "bedrock":
            try:
                import boto3
                self.bedrock_runtime = boto3.client(
                    'bedrock-runtime',
                    region_name=settings.aws_region
                )
            except Exception as e:
                print(f"[AI] Error initializing Bedrock: {e}")

        # System prompts for different use cases
        self.system_prompts = {
            "general": """You are Coo, a helpful and empathetic AI parenting assistant.
You provide evidence-based parenting advice using the knowledge base provided.
Keep responses warm, supportive, and concise (under 300 characters for SMS).
Always remind parents to consult their pediatrician for medical concerns.""",

            "symptom_triage": """You are Coo, a medical symptom triage assistant for parents.
Analyze symptoms carefully and categorize urgency:
- EMERGENCY: Call 911 immediately (e.g., difficulty breathing, unconsciousness, severe bleeding)
- URGENT: See doctor today (e.g., high fever in infant, persistent vomiting)
- ROUTINE: Schedule appointment (e.g., mild rash, cold symptoms)
- HOME_CARE: Monitor at home (e.g., teething discomfort, minor bruise)

Be conservative - when in doubt, escalate urgency level. Provide specific action steps.""",

            "vaccine_info": """You are Coo, a vaccine information specialist for parents.
Provide clear, evidence-based information about childhood vaccines.
Address common concerns with empathy. Cite CDC/AAP guidelines when relevant.
Keep responses concise and reassuring.""",

            "account_management": """You are Coo, a helpful assistant for account management.
Help users with questions about managing their account, adding children, subscription tiers, etc.
Be clear and concise. Direct them to the web portal for account changes.
Keep responses under 300 characters for SMS."""
        }

    def _call_model(self, messages: List[Dict], system_prompt: str, max_tokens: int = 200) -> Dict:
        """
        Abstract model call - works with both Anthropic and Bedrock.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: System prompt for the model
            max_tokens: Maximum tokens to generate

        Returns:
            Dict with response text and metadata
        """
        if self.provider == "anthropic":
            if not self.client:
                return {
                    "text": "AI service not configured. Please add ANTHROPIC_API_KEY.",
                    "error": "no_api_key"
                }

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                system=system_prompt,
                messages=messages
            )

            return {
                "text": response.content[0].text,
                "model": "claude-3-5-sonnet-20241022",
                "tokens": response.usage.output_tokens if hasattr(response, 'usage') else None,
                "provider": "anthropic"
            }

        elif self.provider == "bedrock":
            if not self.bedrock_runtime:
                return {
                    "text": "Bedrock service not configured.",
                    "error": "no_bedrock"
                }

            try:
                body = json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "system": system_prompt,
                    "messages": messages
                })

                response = self.bedrock_runtime.invoke_model(
                    modelId=settings.bedrock_model_id,
                    body=body
                )

                response_body = json.loads(response['body'].read())

                return {
                    "text": response_body['content'][0]['text'],
                    "model": settings.bedrock_model_id,
                    "tokens": response_body.get('usage', {}).get('output_tokens'),
                    "provider": "bedrock"
                }

            except Exception as e:
                return {
                    "text": f"Error calling Bedrock: {str(e)}",
                    "error": str(e)
                }

    def answer_question(
        self,
        question: str,
        context: Optional[str] = None,
        use_case: str = "general",
        max_tokens: int = 200
    ) -> Dict:
        """
        Answer a parenting question using RAG + AI.

        Args:
            question: User's question
            context: Optional pre-retrieved context (if None, will use RAG)
            use_case: Type of response (general, symptom_triage, vaccine_info)
            max_tokens: Maximum response length

        Returns:
            Dict with answer, sources used, and metadata
        """
        if not self.client and not self.bedrock_runtime:
            return {
                "answer": "AI service not configured. Please add ANTHROPIC_API_KEY to your .env file or configure Bedrock.",
                "sources": 0,
                "error": "no_api_key"
            }

        # Get context from RAG if not provided
        if not context:
            context = rag_service.get_context_for_question(question, n_results=5)

        # Build the prompt
        if context:
            user_message = f"""Based on the following trusted parenting resources, please answer this question:

Question: {question}

Resources:
{context}

Please provide a helpful, accurate answer based on these resources."""
        else:
            user_message = f"""Question: {question}

Note: No specific resources found, but please provide general evidence-based parenting guidance."""

        try:
            # Call model (works with both Anthropic and Bedrock)
            result = self._call_model(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=self.system_prompts.get(use_case, self.system_prompts["general"]),
                max_tokens=max_tokens
            )

            if "error" in result:
                return {
                    "answer": result.get("text", "AI service unavailable"),
                    "error": result.get("error"),
                    "sources": 0
                }

            return {
                "answer": result["text"],
                "sources": len(context.split("[Source")) - 1 if context else 0,
                "model": result.get("model"),
                "use_case": use_case,
                "tokens": result.get("tokens"),
                "provider": result.get("provider")
            }

        except Exception as e:
            return {
                "answer": f"I'm having trouble processing your question right now. Please try again or consult your pediatrician.",
                "error": str(e),
                "sources": 0
            }

    def triage_symptoms(self, symptom_description: str, child_age_months: Optional[int] = None) -> Dict:
        """
        Triage symptoms and provide urgency assessment.

        Args:
            symptom_description: Description of symptoms
            child_age_months: Age of child in months (important for context)

        Returns:
            Dict with urgency level, recommended action, and explanation
        """
        # Get relevant symptom information from knowledge base
        context = rag_service.get_context_for_question(
            f"symptoms: {symptom_description}",
            n_results=3
        )

        age_context = f"\nChild's age: {child_age_months} months old" if child_age_months else ""

        user_message = f"""Triage these symptoms and provide urgency assessment:

Symptoms: {symptom_description}{age_context}

Relevant medical information:
{context if context else "No specific information found in knowledge base."}

Please provide:
1. Urgency level (EMERGENCY, URGENT, ROUTINE, or HOME_CARE)
2. Recommended immediate action
3. Brief explanation (under 200 characters)

Format response as:
URGENCY: [level]
ACTION: [what to do]
REASON: [why]"""

        try:
            result = self._call_model(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=self.system_prompts["symptom_triage"],
                max_tokens=300
            )

            if "error" in result:
                return {
                    "urgency": "URGENT",
                    "action": "Consult your pediatrician",
                    "reason": "Unable to assess - AI service unavailable",
                    "error": result.get("error"),
                    "sources": 0
                }

            result_text = result["text"]

            # Parse the response
            lines = result_text.strip().split('\n')
            urgency = "ROUTINE"
            action = "Consult your pediatrician"
            reason = "Assessment needed"

            for line in lines:
                if line.startswith("URGENCY:"):
                    urgency = line.split(":", 1)[1].strip()
                elif line.startswith("ACTION:"):
                    action = line.split(":", 1)[1].strip()
                elif line.startswith("REASON:"):
                    reason = line.split(":", 1)[1].strip()

            return {
                "urgency": urgency,
                "action": action,
                "reason": reason,
                "full_response": result_text,
                "sources": len(context.split("[Source")) - 1 if context else 0
            }

        except Exception as e:
            return {
                "urgency": "URGENT",  # Default to urgent on error
                "action": "Consult your pediatrician or call nurse hotline",
                "reason": "Unable to assess - please seek professional medical advice",
                "error": str(e),
                "sources": 0
            }

    def generate_sms_response(
        self,
        question: str,
        max_length: int = 300,
        conversation_history: str = "",
        child_context: dict = None,
        question_type: str = "general"
    ) -> str:
        """
        Generate SMS-friendly response (concise, under character limit).

        Args:
            question: User's question
            max_length: Max characters for SMS
            conversation_history: Previous conversation context
            child_context: Dict with child info (name, age_months, etc.)
            question_type: Type of question (vaccine, symptom, general, etc.)

        Returns:
            Concise answer suitable for SMS
        """
        # Determine use case based on question type
        use_case_map = {
            "vaccine": "vaccine_info",
            "symptom": "symptom_triage",
            "account_management": "account_management",
            "general": "general"
        }
        use_case = use_case_map.get(question_type, "general")

        # Get RAG context - enhance query with child age if available
        enhanced_query = question
        if child_context:
            age_months = child_context.get("age_months")
            name = child_context.get("name")
            if age_months is not None:
                enhanced_query = f"child age {age_months} months: {question}"

        context = rag_service.get_context_for_question(enhanced_query, n_results=5)

        # Build enhanced prompt with conversation history and child context
        context_parts = []

        if conversation_history:
            context_parts.append(f"Previous conversation:\n{conversation_history}")

        if child_context:
            name = child_context.get("name", "child")
            age_months = child_context.get("age_months")
            if age_months is not None:
                age_years = age_months // 12
                age_remainder = age_months % 12
                if age_years > 0:
                    age_str = f"{age_years} year{'s' if age_years != 1 else ''}"
                    if age_remainder > 0:
                        age_str += f" {age_remainder} month{'s' if age_remainder != 1 else ''}"
                else:
                    age_str = f"{age_months} month{'s' if age_months != 1 else ''}"
                context_parts.append(f"Child context: {name}, {age_str} old")

        context_prefix = "\n".join(context_parts)

        # Build user message
        if context:
            user_message = f"""Based on the following trusted parenting resources, please answer this question:

{context_prefix}

Current question: {question}

Resources:
{context}

Please provide a helpful, accurate answer based on these resources. Keep it under {max_length} characters for SMS."""
        else:
            user_message = f"""{context_prefix}

Current question: {question}

Note: No specific resources found, but please provide general evidence-based parenting guidance. Keep it under {max_length} characters for SMS."""

        try:
            result = self._call_model(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=self.system_prompts.get(use_case, self.system_prompts["general"]),
                max_tokens=150
            )

            if "error" in result:
                return "I'm having trouble right now. Please try again or consult your pediatrician."

            answer = result.get("text", "I couldn't find an answer. Please consult your pediatrician.")

            # Truncate if too long for SMS
            if len(answer) > max_length:
                answer = answer[:max_length-3] + "..."

            return answer

        except Exception as e:
            return "I'm having trouble processing your question. Please try again or consult your pediatrician."

    def classify_question_type(self, question: str, child_context: dict = None) -> str:
        """
        Hybrid classification: Keywords first, then Nova Lite fallback.

        Args:
            question: User's question
            child_context: Optional child context for LLM classification

        Returns:
            Question type: "vaccine", "symptom", "development", "general", etc.
        """
        # First try keyword-based classification (fast, free)
        category = self._classify_with_keywords(question)

        # If no keywords matched and LLM classification is enabled, use Nova Lite
        if category == "general" and settings.use_llm_classification and len(question) > 10:
            category = self._classify_with_nova_lite(question, child_context)

        return category

    def _classify_with_keywords(self, question: str) -> str:
        """
        Keyword-based classification (Tier 1).

        Args:
            question: User's question

        Returns:
            Question type based on keyword matching
        """
        text_lower = question.lower()

        # Vaccine-related
        vaccine_keywords = [
            "vaccine", "vaccination", "shot", "immunization",
            "dtap", "mmr", "pcv", "hep", "hepatitis", "varicella",
            "rotavirus", "hib", "polio", "flu shot"
        ]
        if any(keyword in text_lower for keyword in vaccine_keywords):
            return "vaccine"

        # Symptom/health-related
        symptom_keywords = [
            "fever", "sick", "cough", "cold", "vomit", "diarrhea",
            "rash", "pain", "hurt", "crying", "fussy", "won't eat",
            "sleep", "temperature", "congested", "runny nose"
        ]
        if any(keyword in text_lower for keyword in symptom_keywords):
            return "symptom"

        # Development/milestones
        development_keywords = [
            "milestone", "development", "walking", "talking", "crawling",
            "sit up", "stand", "words", "babbling", "delayed"
        ]
        if any(keyword in text_lower for keyword in development_keywords):
            return "development"

        # Activities/classes
        activity_keywords = [
            "class", "swimming", "music", "dance", "sport", "activity",
            "lesson", "gym", "playgroup"
        ]
        if any(keyword in text_lower for keyword in activity_keywords):
            return "activity"

        # Education (preschool, kindergarten)
        education_keywords = [
            "preschool", "kindergarten", "school", "daycare", "pre-k"
        ]
        if any(keyword in text_lower for keyword in education_keywords):
            return "education"

        # Pregnancy
        pregnancy_keywords = [
            "pregnant", "pregnancy", "trimester", "due date", "ultrasound",
            "prenatal", "expecting"
        ]
        if any(keyword in text_lower for keyword in pregnancy_keywords):
            return "pregnancy"

        # Account management
        account_keywords = [
            "add child", "add a child", "add another child", "register child",
            "can i add", "how to add", "how do i add",
            "new child", "new baby", "subscription", "upgrade", "account",
            "profile", "add member", "family member", "change password",
            "delete account", "cancel", "sign up", "register"
        ]
        if any(keyword in text_lower for keyword in account_keywords):
            return "account_management"

        return "general"

    def _classify_with_nova_lite(self, question: str, child_context: dict = None) -> str:
        """
        AI-powered classification using Nova Lite (Tier 2 - fallback only).

        Args:
            question: User's question
            child_context: Optional child context (age, name)

        Returns:
            Question type from AI classification
        """
        if self.provider != "bedrock" or not self.bedrock_runtime:
            return "general"  # Fallback if Bedrock not available

        # Build context string
        context_str = ""
        if child_context:
            child_age = child_context.get("age_months")
            child_name = child_context.get("name")
            if child_age is not None:
                context_str = f"\nChild: {child_name or 'Unknown'}, Age: {child_age} months"

        # Minimal classification prompt
        prompt = f"""Classify this parenting question into ONE category only.

Categories: vaccine, symptom, development, activity, pregnancy, education, account_management, general

Question: {question}{context_str}

Respond with ONLY the category name (one word, lowercase)."""

        try:
            # Use Nova Lite for fast, cheap classification
            body = json.dumps({
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 10,  # Very short response needed
                "temperature": 0.1,  # Low temperature for consistency
                "top_p": 0.9
            })

            response = self.bedrock_runtime.invoke_model(
                modelId=settings.bedrock_classifier_model,  # amazon.nova-lite-v1:0
                body=body
            )

            result = json.loads(response['body'].read())

            # Parse Nova Lite response format
            if 'output' in result and 'message' in result['output']:
                category = result['output']['message']['content'][0]['text'].strip().lower()
            elif 'content' in result:
                category = result['content'][0]['text'].strip().lower()
            else:
                category = "general"

            # Validate category
            valid_categories = [
                "vaccine", "symptom", "development", "activity",
                "pregnancy", "education", "account_management", "general"
            ]

            if category in valid_categories:
                print(f"[AI] Nova Lite classified '{question[:30]}...' as: {category}")
                return category
            else:
                print(f"[AI] Nova Lite returned invalid category '{category}', defaulting to 'general'")
                return "general"

        except Exception as e:
            print(f"[AI] Nova Lite classification error: {e}")
            return "general"  # Fallback to general on error

    def check_emergency_keywords(self, text: str) -> bool:
        """
        Quick check for emergency keywords that should trigger immediate escalation.

        Args:
            text: Message text to check

        Returns:
            True if emergency keywords detected
        """
        emergency_keywords = [
            "can't breathe", "not breathing", "unconscious", "unresponsive",
            "severe bleeding", "seizure", "convulsion", "turning blue",
            "severe pain", "chest pain", "head injury", "poisoning",
            "allergic reaction", "swelling throat", "choking"
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in emergency_keywords)


# Global AI service instance
ai_service = AIService()

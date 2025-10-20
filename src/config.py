"""Configuration settings for Coo application."""
import os
from typing import ClassVar, Dict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""

    # Environment Mode: "local" or "aws"
    environment: str = os.getenv("ENVIRONMENT", "local")

    # AI Provider: "anthropic" (local) or "bedrock" (aws)
    ai_provider: str = os.getenv("AI_PROVIDER", "anthropic")

    # RAG Provider: "chromadb" (local) or "bedrock_kb" (aws)
    rag_provider: str = os.getenv("RAG_PROVIDER", "chromadb")

    # Anthropic API (for local development)
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")

    # AWS Settings (for production)
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    bedrock_nova_model_id: str = os.getenv("BEDROCK_NOVA_MODEL_ID", "amazon.nova-pro-v1:0")
    bedrock_kb_id: str = os.getenv("BEDROCK_KB_ID", "")

    # Nova Lite for classification (cheap, fast)
    bedrock_classifier_model: str = os.getenv("BEDROCK_CLASSIFIER_MODEL", "amazon.nova-lite-v1:0")
    use_llm_classification: bool = os.getenv("USE_LLM_CLASSIFICATION", "true").lower() == "true"

    # Twilio
    twilio_account_sid: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    twilio_auth_token: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    twilio_phone_number: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./coo.db")

    # App settings
    app_name: str = "Coo - AI Parenting Companion"
    debug: bool = True

    # Message limits by tier - per month (ClassVar so it's not a field)
    message_limits: ClassVar[Dict[str, int]] = {
        "FREE": 50,  # 50 per year total
        "FAMILY": 100,  # 100 per month (1,200/year max)
        "PREMIUM": 1000  # 1,000 per month (12,000/year max)
    }

    # Member/child limits (used as fallback/max)
    max_family_members: int = 10  # PREMIUM tier limit
    max_children: int = 3  # FAMILY/PREMIUM tier limit

    # Tier-specific limits enforced in routes
    # FREE: 1 member, 1 child
    # FAMILY: 2 members, 3 children
    # PREMIUM: 10 members, 3 children

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()

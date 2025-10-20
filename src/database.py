"""Database connection and session management."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from .config import settings

# Create engine with appropriate settings
# For AWS Lambda, use NullPool to avoid connection pooling issues
if settings.environment == "aws":
    engine = create_engine(
        settings.database_url,
        poolclass=NullPool,
        echo=False
    )
else:
    # For local development
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
        echo=True
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for FastAPI routes to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from .models import models  # Import models to register them
    Base.metadata.create_all(bind=engine)

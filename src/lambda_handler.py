"""Lambda handler for AWS deployment using Mangum."""
from mangum import Mangum
from src.main import app
from src.database import init_db

# Initialize database tables on Lambda cold start
init_db()

# Lambda entry point - Mangum wraps FastAPI for AWS Lambda
handler = Mangum(app, lifespan="off")

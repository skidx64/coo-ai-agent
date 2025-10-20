"""Main FastAPI application for Coo - AI Parenting Companion."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import init_db
from .config import settings
from .api.routes import sms, families, children, messages, tasks, rag, ai, workflows, auth, demo
import os

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI-powered parenting assistant with SMS support",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)  # Auth routes first
app.include_router(sms.router)
app.include_router(families.router)
app.include_router(children.router)
app.include_router(messages.router)
app.include_router(tasks.router)
app.include_router(rag.router)
app.include_router(ai.router)
app.include_router(workflows.router)
app.include_router(demo.router)  # Demo endpoint with token protection


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    print(f"[OK] {settings.app_name} started successfully")
    print(f"[DB] Database: {settings.database_url}")
    print(f"[SMS] Twilio configured: {bool(settings.twilio_account_sid)}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Mount static files for frontend
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


@app.get("/demo")
async def serve_demo():
    """Serve the API demo/testing frontend."""
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    return FileResponse(os.path.join(frontend_path, "index.html"))


@app.get("/app")
async def serve_app():
    """Serve the user-facing application."""
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
    return FileResponse(os.path.join(frontend_path, "app.html"))

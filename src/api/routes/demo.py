"""Demo API routes - DELETED per Phase 0 cleanup.

The /demo frontend page now calls real API endpoints directly.
This file is kept empty to avoid import errors.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/demo", tags=["Demo"])

# All demo endpoints have been removed.
# The /demo frontend page uses real API endpoints instead.

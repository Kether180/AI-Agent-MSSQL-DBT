"""
FastAPI dependencies

Shared dependencies for authentication and database access.
"""

from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from datetime import datetime

from app.database import SessionLocal
from app.models import APIKey
from app.services import AuthService, UsageTracker


# Dependency: Get database session
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency: API Key authentication
async def verify_api_key(
    authorization: Optional[str] = Header(None),
    db = Depends(get_db)
) -> APIKey:
    """
    Verify API key from Authorization header.

    Expected format: Authorization: Bearer <api_key>
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Use: Bearer <api_key>"
        )

    api_key_str = parts[1]

    # Authenticate API key
    auth_service = AuthService(db)
    api_key = auth_service.authenticate_api_key(api_key_str)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key"
        )

    # Check rate limit
    tracker = UsageTracker(db)
    if not tracker.check_rate_limit(api_key.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {api_key.rate_limit} requests/hour"
        )

    # Update last used timestamp
    api_key.last_used = datetime.utcnow()
    db.commit()

    return api_key

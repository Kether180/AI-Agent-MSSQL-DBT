"""
FastAPI Public API

REST API for MSSQL to dbt migrations with API key authentication.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import time

from app.database import SessionLocal
from app.services import AuthService

# Import dependencies
from .dependencies import verify_api_key

# Import routes
from .routes import migrations

# Create FastAPI app
app = FastAPI(
    title="MSSQL to dbt Migration API",
    description="Automated MSSQL to dbt migration using AI agents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware to log usage
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all API requests for usage tracking"""
    start_time = time.time()

    response = await call_next(request)

    # Calculate response time
    response_time = (time.time() - start_time) * 1000  # ms

    # Get API key from request if present
    authorization = request.headers.get("authorization")
    if authorization:
        parts = authorization.split()
        if len(parts) == 2:
            api_key_str = parts[1]
            db = SessionLocal()
            try:
                auth_service = AuthService(db)
                api_key = auth_service.authenticate_api_key(api_key_str)

                if api_key:
                    tracker = UsageTracker(db)
                    tracker.log_request(
                        api_key_id=api_key.id,
                        endpoint=str(request.url.path),
                        method=request.method,
                        status_code=response.status_code,
                        response_time=response_time
                    )
            finally:
                db.close()

    return response


# Include routers
app.include_router(
    migrations.router,
    prefix="/api/v1",
    tags=["migrations"],
    dependencies=[Depends(verify_api_key)]
)


# Health check endpoint (no auth required)
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """API root endpoint"""
    return {
        "name": "MSSQL to dbt Migration API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

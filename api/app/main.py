"""
BACOWR FastAPI Application

Production-ready REST API for BACOWR content generation system.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from .database import engine, get_db, init_db, Base
from .auth import create_default_user
from .routes import jobs, backlinks, analytics, websocket, users, batches, audit, export, auth, user_management
from .middleware.prometheus import setup_metrics
from .middleware.rate_limit import setup_rate_limiting
from .middleware.audit import AuditMiddleware

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="BACOWR API",
    description="BacklinkContent Engine - AI-powered content generation for SEO",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration - OPEN FOR DEVELOPMENT
# TODO: Restrict this in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Setup Prometheus metrics
setup_metrics(app)

# Setup rate limiting
setup_rate_limiting(app)

# Setup audit logging middleware
# TODO: Fix AuditMiddleware body reading issue
# app.add_middleware(AuditMiddleware)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and create default user on startup."""
    print("=" * 70)
    print("BACOWR API Starting...")
    print("=" * 70)

    # Initialize database
    init_db()
    print("✓ Database initialized")

    # Create default user
    db = next(get_db())
    try:
        user = create_default_user(db)
        if user:
            print("✓ Default admin user ready")
    finally:
        db.close()

    print("=" * 70)
    print("✓ BACOWR API Ready!")
    print(f"  Docs: http://localhost:8000/docs")
    print("=" * 70)


# Health check
@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "bacowr-api",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "service": "BACOWR API",
        "version": "1.0.0",
        "description": "BacklinkContent Engine - AI-powered content generation for SEO",
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(backlinks.router, prefix="/api/v1")
app.include_router(batches.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")  # Google Sheets/Docs export

# Wave 5: Enterprise features
app.include_router(auth.router, prefix="/api/v1")  # JWT authentication
app.include_router(user_management.router, prefix="/api/v1")  # User management


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if os.getenv("DEBUG") else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

"""
BACOWR FastAPI Application

Production-ready REST API for BACOWR content generation system.
"""

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
import socketio
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .database import engine, get_db, init_db, Base
from .auth import create_default_user, get_current_user_optional
from .routes import jobs, backlinks, analytics, auth, notifications, campaigns, templates, scheduling, publisher_research, serp_research, intent_analysis, qc_validation
from .websocket import sio
from .rate_limit import limiter
from .scheduler_service import start_scheduler, stop_scheduler

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

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware to set user in request state for rate limiting
@app.middleware("http")
async def add_user_to_request(request: Request, call_next):
    """
    Middleware to add authenticated user to request.state.

    This allows the rate limiter to use user ID for per-user rate limiting.
    Falls back to IP address for unauthenticated requests.
    """
    db = next(get_db())
    try:
        # Try to get current user (won't raise exception if not authenticated)
        user = await get_current_user_optional(request, db)
        request.state.user = user
    except:
        request.state.user = None
    finally:
        db.close()

    response = await call_next(request)
    return response


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

    # Start scheduler
    start_scheduler()

    print("=" * 70)
    print("✓ BACOWR API Ready!")
    print(f"  Docs: http://localhost:8000/docs")
    print(f"  WebSocket: ws://localhost:8000/socket.io")
    print("=" * 70)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("Shutting down BACOWR API...")
    stop_scheduler()
    print("✓ Scheduler stopped")


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
app.include_router(auth.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(backlinks.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(campaigns.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")
app.include_router(scheduling.router, prefix="/api/v1")
app.include_router(publisher_research.router, prefix="/api/v1")
app.include_router(serp_research.router, prefix="/api/v1")
app.include_router(intent_analysis.router, prefix="/api/v1")
app.include_router(qc_validation.router, prefix="/api/v1")


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


# Wrap FastAPI app with Socket.IO ASGI application
socket_app = socketio.ASGIApp(
    sio,
    app,
    socketio_path='socket.io'
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:socket_app",  # Run Socket.IO wrapped app
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

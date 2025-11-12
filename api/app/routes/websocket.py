"""
WebSocket route for real-time job progress updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Set
import json
import logging
from datetime import datetime

from ..database import get_db
from ..models.database import Job
from ..auth import api_key_header

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections for job progress updates."""

    def __init__(self):
        # Map of job_id -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map of websocket -> user_id for auth
        self.websocket_users: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, job_id: str, user_id: str):
        """Accept and register a new WebSocket connection for a job."""
        await websocket.accept()

        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()

        self.active_connections[job_id].add(websocket)
        self.websocket_users[websocket] = user_id

        logger.info(f"WebSocket connected for job {job_id} (user: {user_id})")

    def disconnect(self, websocket: WebSocket, job_id: str):
        """Remove a WebSocket connection."""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)

            # Clean up empty sets
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

        if websocket in self.websocket_users:
            del self.websocket_users[websocket]

        logger.info(f"WebSocket disconnected for job {job_id}")

    async def send_progress_update(
        self,
        job_id: str,
        status: str,
        progress: float,
        message: str
    ):
        """
        Send progress update to all connected clients for a job.

        Args:
            job_id: Job ID
            status: Current job status
            progress: Progress percentage (0-100)
            message: Human-readable message
        """
        if job_id not in self.active_connections:
            return

        update_data = {
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Send to all connected clients for this job
        disconnected = set()
        for websocket in self.active_connections[job_id]:
            try:
                await websocket.send_json(update_data)
            except Exception as e:
                logger.error(f"Error sending to websocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected websockets
        for ws in disconnected:
            self.disconnect(ws, job_id)

    async def broadcast_to_user(self, user_id: str, message: dict):
        """Broadcast message to all connections for a specific user."""
        for websocket, ws_user_id in self.websocket_users.items():
            if ws_user_id == user_id:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {e}")


# Global connection manager
manager = ConnectionManager()


@router.websocket("/jobs/{job_id}")
async def websocket_job_progress(
    websocket: WebSocket,
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time job progress updates.

    Usage:
        const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/jobs/${jobId}?api_key=${apiKey}`);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log(`Progress: ${data.progress}% - ${data.message}`);
        };

    Messages sent to client:
        {
            "job_id": "job_123",
            "status": "processing",
            "progress": 45.5,
            "message": "Generating article content...",
            "timestamp": "2025-11-12T10:30:00Z"
        }
    """
    # Extract API key from query params
    api_key = websocket.query_params.get("api_key")

    if not api_key:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="API key required")
        return

    # Verify API key and get user
    from ..models.database import User
    user = db.query(User).filter(User.api_key == api_key).first()

    if not user or not user.is_active:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid API key")
        return

    # Verify job belongs to user
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == user.id
    ).first()

    if not job:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Job not found")
        return

    # Connect websocket
    await manager.connect(websocket, job_id, user.id)

    try:
        # Send initial status
        await websocket.send_json({
            "job_id": job_id,
            "status": job.status,
            "progress": 0 if job.status == "pending" else (100 if job.status in ["delivered", "blocked", "aborted"] else 50),
            "message": f"Connected. Current status: {job.status}",
            "timestamp": datetime.utcnow().isoformat()
        })

        # Keep connection alive and listen for client messages
        while True:
            try:
                # Wait for client messages (ping/pong)
                data = await websocket.receive_text()

                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")

                # Optionally handle other client messages
                # (For now, we just keep the connection alive)

            except WebSocketDisconnect:
                logger.info(f"Client disconnected from job {job_id}")
                break
            except Exception as e:
                logger.error(f"Error in websocket loop: {e}")
                break

    finally:
        manager.disconnect(websocket, job_id)


# Helper function to send progress updates from job processing
async def send_job_progress(
    job_id: str,
    status: str,
    progress: float,
    message: str
):
    """
    Helper function to send progress updates from anywhere in the application.

    This can be called from the job processing background task.

    Args:
        job_id: Job ID
        status: Current status
        progress: Progress percentage (0-100)
        message: Progress message
    """
    await manager.send_progress_update(job_id, status, progress, message)

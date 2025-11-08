"""
WebSocket Manager for Real-time Job Updates

Provides real-time bidirectional communication between backend and frontend
using Socket.IO for job status updates, progress tracking, and batch updates.
"""

import socketio
from typing import Dict, Set, Optional, Any
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create Socket.IO server instance
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # Configure per environment
    logger=True,
    engineio_logger=True
)

# Track active subscriptions
# job_id -> set of session IDs
job_subscriptions: Dict[str, Set[str]] = {}
# batch_id -> set of session IDs
batch_subscriptions: Dict[str, Set[str]] = {}
# session_id -> set of subscribed job_ids
session_jobs: Dict[str, Set[str]] = {}
# session_id -> set of subscribed batch_ids
session_batches: Dict[str, Set[str]] = {}


class WebSocketManager:
    """
    Manages WebSocket connections and event broadcasting.
    """

    @staticmethod
    async def broadcast_job_update(
        job_id: str,
        status: str,
        progress: float,
        message: str
    ) -> None:
        """
        Broadcast job update to all subscribed clients.

        Args:
            job_id: Job identifier
            status: Current job status
            progress: Progress percentage (0-100)
            message: Status message
        """
        data = {
            'job_id': job_id,
            'status': status,
            'progress': progress,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Emit to all subscribers of this specific job
        if job_id in job_subscriptions:
            for session_id in job_subscriptions[job_id]:
                await sio.emit('job:update', data, room=session_id)
                logger.debug(f"Sent job:update to {session_id} for job {job_id}")

    @staticmethod
    async def broadcast_job_completed(
        job_id: str,
        message: str = "Job completed successfully"
    ) -> None:
        """
        Broadcast job completion to all subscribed clients.

        Args:
            job_id: Job identifier
            message: Completion message
        """
        data = {
            'job_id': job_id,
            'status': 'DELIVERED',
            'progress': 100,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }

        if job_id in job_subscriptions:
            for session_id in job_subscriptions[job_id]:
                await sio.emit('job:completed', data, room=session_id)
                await sio.emit('job:update', data, room=session_id)
                logger.info(f"Sent job:completed to {session_id} for job {job_id}")

    @staticmethod
    async def broadcast_job_error(
        job_id: str,
        error_message: str
    ) -> None:
        """
        Broadcast job error to all subscribed clients.

        Args:
            job_id: Job identifier
            error_message: Error description
        """
        data = {
            'job_id': job_id,
            'status': 'ABORTED',
            'progress': 0,
            'message': f"Error: {error_message}",
            'timestamp': datetime.utcnow().isoformat()
        }

        if job_id in job_subscriptions:
            for session_id in job_subscriptions[job_id]:
                await sio.emit('job:error', data, room=session_id)
                await sio.emit('job:update', data, room=session_id)
                logger.error(f"Sent job:error to {session_id} for job {job_id}")

    @staticmethod
    async def broadcast_batch_update(
        batch_id: str,
        total: int,
        completed: int,
        status: str,
        message: str
    ) -> None:
        """
        Broadcast batch processing update to all subscribed clients.

        Args:
            batch_id: Batch identifier
            total: Total jobs in batch
            completed: Number of completed jobs
            status: Batch status
            message: Status message
        """
        data = {
            'batch_id': batch_id,
            'total': total,
            'completed': completed,
            'progress': (completed / total * 100) if total > 0 else 0,
            'status': status,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }

        if batch_id in batch_subscriptions:
            for session_id in batch_subscriptions[batch_id]:
                await sio.emit('batch:update', data, room=session_id)
                logger.debug(f"Sent batch:update to {session_id} for batch {batch_id}")


# Socket.IO Event Handlers

@sio.event
async def connect(sid: str, environ: dict):
    """
    Handle client connection.

    Args:
        sid: Session ID
        environ: Connection environment
    """
    logger.info(f"Client connected: {sid}")
    session_jobs[sid] = set()
    session_batches[sid] = set()

    # Send connection confirmation
    await sio.emit('connection', {'connected': True, 'session_id': sid}, room=sid)


@sio.event
async def disconnect(sid: str):
    """
    Handle client disconnection. Clean up subscriptions.

    Args:
        sid: Session ID
    """
    logger.info(f"Client disconnected: {sid}")

    # Clean up job subscriptions
    if sid in session_jobs:
        for job_id in session_jobs[sid]:
            if job_id in job_subscriptions:
                job_subscriptions[job_id].discard(sid)
                if not job_subscriptions[job_id]:
                    del job_subscriptions[job_id]
        del session_jobs[sid]

    # Clean up batch subscriptions
    if sid in session_batches:
        for batch_id in session_batches[sid]:
            if batch_id in batch_subscriptions:
                batch_subscriptions[batch_id].discard(sid)
                if not batch_subscriptions[batch_id]:
                    del batch_subscriptions[batch_id]
        del session_batches[sid]


@sio.on('subscribe:job')
async def handle_subscribe_job(sid: str, data: dict):
    """
    Subscribe client to job updates.

    Args:
        sid: Session ID
        data: {'job_id': str}
    """
    job_id = data.get('job_id')
    if not job_id:
        logger.warning(f"subscribe:job called without job_id by {sid}")
        return

    # Add to subscriptions
    if job_id not in job_subscriptions:
        job_subscriptions[job_id] = set()
    job_subscriptions[job_id].add(sid)

    if sid not in session_jobs:
        session_jobs[sid] = set()
    session_jobs[sid].add(job_id)

    logger.info(f"Client {sid} subscribed to job {job_id}")

    # Acknowledge subscription
    await sio.emit('subscribed', {'job_id': job_id}, room=sid)


@sio.on('unsubscribe:job')
async def handle_unsubscribe_job(sid: str, data: dict):
    """
    Unsubscribe client from job updates.

    Args:
        sid: Session ID
        data: {'job_id': str}
    """
    job_id = data.get('job_id')
    if not job_id:
        return

    # Remove from subscriptions
    if job_id in job_subscriptions:
        job_subscriptions[job_id].discard(sid)
        if not job_subscriptions[job_id]:
            del job_subscriptions[job_id]

    if sid in session_jobs:
        session_jobs[sid].discard(job_id)

    logger.info(f"Client {sid} unsubscribed from job {job_id}")


@sio.on('subscribe:batch')
async def handle_subscribe_batch(sid: str, data: dict):
    """
    Subscribe client to batch updates.

    Args:
        sid: Session ID
        data: {'batch_id': str}
    """
    batch_id = data.get('batch_id')
    if not batch_id:
        logger.warning(f"subscribe:batch called without batch_id by {sid}")
        return

    # Add to subscriptions
    if batch_id not in batch_subscriptions:
        batch_subscriptions[batch_id] = set()
    batch_subscriptions[batch_id].add(sid)

    if sid not in session_batches:
        session_batches[sid] = set()
    session_batches[sid].add(batch_id)

    logger.info(f"Client {sid} subscribed to batch {batch_id}")

    # Acknowledge subscription
    await sio.emit('subscribed', {'batch_id': batch_id}, room=sid)


@sio.on('unsubscribe:batch')
async def handle_unsubscribe_batch(sid: str, data: dict):
    """
    Unsubscribe client from batch updates.

    Args:
        sid: Session ID
        data: {'batch_id': str}
    """
    batch_id = data.get('batch_id')
    if not batch_id:
        return

    # Remove from subscriptions
    if batch_id in batch_subscriptions:
        batch_subscriptions[batch_id].discard(sid)
        if not batch_subscriptions[batch_id]:
            del batch_subscriptions[batch_id]

    if sid in session_batches:
        session_batches[sid].discard(batch_id)

    logger.info(f"Client {sid} unsubscribed from batch {batch_id}")


# Export singleton instance
ws_manager = WebSocketManager()

# WebSocket Real-Time Updates Guide

## Overview

BACOWR API provides real-time bidirectional communication using WebSocket (Socket.IO) for job status updates, progress tracking, and batch processing notifications.

## Features

- **Real-time job updates**: Get instant notifications when job status changes
- **Progress tracking**: Monitor job progress from 0-100%
- **Error notifications**: Immediate error alerts
- **Batch updates**: Track batch processing in real-time
- **Automatic reconnection**: Client handles connection drops gracefully
- **Room-based subscriptions**: Subscribe only to jobs you care about

---

## Connection

### Backend WebSocket Server

**URL**: `ws://localhost:8000/socket.io` (development)
**Protocol**: Socket.IO with ASGI backend
**Transports**: WebSocket, Polling (fallback)

### Frontend Client

The frontend already has a WebSocket client configured in `frontend/src/lib/api/websocket.ts`.

**Example Usage**:

```typescript
import { wsClient } from '@/lib/api/websocket'

// Connect to WebSocket server
wsClient.connect()

// Subscribe to specific job updates
wsClient.subscribeToJob('job-123-456')

// Listen for updates
wsClient.on('job:update', (data) => {
  console.log('Job update:', data)
  // { job_id, status, progress, message, timestamp }
})

// Listen for completion
wsClient.on('job:completed', (data) => {
  console.log('Job completed:', data)
})

// Listen for errors
wsClient.on('job:error', (data) => {
  console.error('Job error:', data)
})

// Unsubscribe when done
wsClient.unsubscribeFromJob('job-123-456')
```

---

## Events

### Server → Client Events

#### `connection`
Sent when client successfully connects.

```json
{
  "connected": true,
  "session_id": "abc123"
}
```

#### `job:update`
General job status update.

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PROCESSING",
  "progress": 45,
  "message": "Content generated - Running quality checks",
  "timestamp": "2025-11-08T23:50:00.000Z"
}
```

**Status values**: `PENDING`, `PROCESSING`, `DELIVERED`, `BLOCKED`, `ABORTED`

#### `job:completed`
Job successfully completed.

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "DELIVERED",
  "progress": 100,
  "message": "Article successfully generated and delivered",
  "timestamp": "2025-11-08T23:55:00.000Z"
}
```

#### `job:error`
Job encountered an error.

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "ABORTED",
  "progress": 0,
  "message": "Error: API key invalid",
  "timestamp": "2025-11-08T23:52:00.000Z"
}
```

#### `batch:update`
Batch processing progress update.

```json
{
  "batch_id": "batch-001",
  "total": 50,
  "completed": 23,
  "progress": 46,
  "status": "running",
  "message": "Processing batch...",
  "timestamp": "2025-11-08T23:50:00.000Z"
}
```

#### `subscribed`
Acknowledgment of subscription.

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Client → Server Events

#### `subscribe:job`
Subscribe to updates for a specific job.

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### `unsubscribe:job`
Unsubscribe from job updates.

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### `subscribe:batch`
Subscribe to batch processing updates.

```json
{
  "batch_id": "batch-001"
}
```

#### `unsubscribe:batch`
Unsubscribe from batch updates.

```json
{
  "batch_id": "batch-001"
}
```

---

## Job Lifecycle Events

A typical job goes through these WebSocket events:

1. **Job Created** (progress: 0%)
   ```
   status: PENDING
   message: "Job created and queued for processing"
   ```

2. **Job Started** (progress: 10%)
   ```
   status: PROCESSING
   message: "Job started - Profiling publisher and target"
   ```

3. **Content Generated** (progress: 80%)
   ```
   status: PROCESSING
   message: "Content generated - Running quality checks"
   ```

4. **Job Completed** (progress: 100%)
   ```
   status: DELIVERED
   message: "Article successfully generated and delivered"
   ```

**Alternative endings**:
- `BLOCKED` - QC issues block delivery
- `ABORTED` - Error occurred

---

## Implementation Details

### Backend Components

**File**: `api/app/websocket.py`
- WebSocket connection manager
- Event handlers for subscriptions
- Broadcast functions for updates
- Automatic cleanup on disconnect

**File**: `api/app/main.py`
- Socket.IO ASGI wrapper integration
- CORS configuration for WebSocket

**File**: `api/app/routes/jobs.py`
- WebSocket event emissions during job processing
- Progress tracking integration

### Frontend Components

**File**: `frontend/src/lib/api/websocket.ts`
- WebSocket client singleton
- Connection management
- Event subscription system
- Automatic reconnection with exponential backoff

**File**: `frontend/src/types/index.ts`
- Type definitions for WebSocket events
- `WSJobUpdate` interface

---

## Configuration

### Backend

**Environment Variables**:
```env
FRONTEND_URL=http://localhost:3000  # For CORS
```

**CORS Configuration** (main.py):
```python
allow_origins=[
    FRONTEND_URL,
    "http://localhost:3000",
    "https://*.vercel.app"
]
```

### Frontend

**Environment Variables**:
```env
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

**Connection Settings** (websocket.ts):
```typescript
const socket = io(WS_URL, {
  transports: ['websocket', 'polling'],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5,
})
```

---

## Testing WebSocket

### Manual Testing with Browser Console

```javascript
// Connect to WebSocket
const socket = io('ws://localhost:8000')

// Listen for connection
socket.on('connect', () => {
  console.log('Connected!', socket.id)
})

// Subscribe to a job
socket.emit('subscribe:job', { job_id: 'your-job-id-here' })

// Listen for updates
socket.on('job:update', (data) => {
  console.log('Update:', data)
})

socket.on('job:completed', (data) => {
  console.log('Completed:', data)
})

socket.on('job:error', (data) => {
  console.error('Error:', data)
})
```

### Testing with Python

```python
import socketio

# Create client
sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('Connected!')
    # Subscribe to job
    sio.emit('subscribe:job', {'job_id': 'your-job-id'})

@sio.on('job:update')
def on_job_update(data):
    print(f"Job update: {data}")

@sio.on('job:completed')
def on_job_completed(data):
    print(f"Job completed: {data}")

# Connect
sio.connect('http://localhost:8000')
sio.wait()
```

---

## Production Deployment

### Considerations

1. **SSL/TLS**: Use `wss://` instead of `ws://` in production
2. **Load Balancing**: Socket.IO requires sticky sessions
3. **Scaling**: Use Redis adapter for multiple server instances
4. **Rate Limiting**: Implement connection limits per user
5. **Authentication**: Add token-based auth for WebSocket connections

### Example Production Config

```python
# api/app/websocket.py
import socketio
import redis

# Redis adapter for scaling
mgr = socketio.AsyncRedisManager('redis://localhost:6379')

sio = socketio.AsyncServer(
    async_mode='asgi',
    client_manager=mgr,
    cors_allowed_origins=[
        'https://yourdomain.com',
        'https://app.yourdomain.com'
    ],
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25
)
```

---

## Troubleshooting

### Connection Issues

**Problem**: "WebSocket connection failed"
**Solution**:
- Check backend is running on correct port
- Verify CORS settings allow frontend origin
- Ensure firewall allows WebSocket connections

**Problem**: "Frequent disconnections"
**Solution**:
- Increase `ping_timeout` and `ping_interval`
- Check network stability
- Verify load balancer has sticky sessions enabled

### Not Receiving Updates

**Problem**: "Subscribed but not getting updates"
**Solution**:
- Verify job_id is correct
- Check backend logs for subscription confirmation
- Ensure job is actually running/updating
- Test with browser console to isolate client vs server issue

### Performance Issues

**Problem**: "High latency or delayed updates"
**Solution**:
- Use WebSocket transport only (disable polling)
- Reduce number of simultaneous subscriptions
- Implement Redis adapter for distributed systems
- Monitor server resource usage

---

## Best Practices

1. **Subscribe selectively**: Only subscribe to jobs you're actively monitoring
2. **Unsubscribe when done**: Clean up subscriptions to reduce server load
3. **Handle reconnection**: Always implement reconnection logic
4. **Graceful degradation**: Fall back to polling if WebSocket unavailable
5. **Error handling**: Always listen for error events
6. **Connection pooling**: Use singleton WebSocket client
7. **State synchronization**: Sync UI state on reconnection

---

## Future Enhancements

### Planned Features

- **Authentication**: Token-based WebSocket auth
- **Rate limiting**: Per-user connection limits
- **Compression**: Enable WebSocket compression
- **Binary data**: Support for binary message formats
- **Rooms**: User-specific rooms for multi-tenant support
- **Presence**: Online/offline user status
- **Typing indicators**: Real-time collaboration features

### Scaling Improvements

- Redis adapter for horizontal scaling
- Message queue integration (Celery + Redis)
- WebSocket connection pooling
- Load balancer sticky session config
- CDN-based WebSocket routing

---

## Related Documentation

- [API Backend Guide](./API_BACKEND_COMPLETE.md)
- [Frontend Overview](./FRONTEND_OVERVIEW.md)
- [Production Guide](./PRODUCTION_GUIDE.md)
- [Socket.IO Documentation](https://socket.io/docs/)

---

**Version**: 1.0.0
**Last Updated**: 2025-11-08
**Status**: Production-ready
**Author**: BACOWR Team

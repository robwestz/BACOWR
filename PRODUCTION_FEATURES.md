# Production Features Guide

Comprehensive guide to BACOWR's production-ready features including rate limiting, email notifications, and webhook integrations.

---

## Table of Contents

1. [Rate Limiting](#rate-limiting)
2. [Email Notifications](#email-notifications)
3. [Webhook Integrations](#webhook-integrations)
4. [Configuration](#configuration)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Rate Limiting

Rate limiting prevents API abuse and ensures fair usage across all users.

### Features

- **Per-User Rate Limiting**: Authenticated users get their own rate limits
- **IP-Based Fallback**: Unauthenticated requests are limited by IP address
- **Redis Backend**: Distributed rate limiting for multi-instance deployments
- **In-Memory Mode**: Development mode without Redis dependency
- **Automatic 429 Responses**: Clean error responses when limits exceeded

### Rate Limits

| Endpoint Type | Limit | Description |
|--------------|-------|-------------|
| Login | 5/minute | Prevents brute force attacks |
| Register | 3/hour | Prevents account spam |
| Refresh Token | 10/minute | Token refresh operations |
| Change Password | 3/hour | Password change attempts |
| Create Job | 30/minute | Job creation limit per user |
| List Jobs | 100/minute | Job listing requests |
| Analytics | 60/minute | Analytics queries |
| Export | 10/minute | Data export operations |
| Admin | 100/minute | Admin operations |
| Default | 100/minute | All other endpoints |

### Configuration

**Development (In-Memory):**
```env
REDIS_URL=memory://
```

**Production (Redis):**
```env
REDIS_URL=redis://localhost:6379
```

**With Redis Auth:**
```env
REDIS_URL=redis://:password@localhost:6379/0
```

### Rate Limit Headers

Responses include rate limit information:

```http
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 29
X-RateLimit-Reset: 1699564800
```

### 429 Response

When rate limit is exceeded:

```json
{
  "error": "Rate limit exceeded",
  "detail": "30 per 1 minute"
}
```

### Architecture

```
Request → Middleware (Identify User) → Rate Limiter → Endpoint
                ↓
        request.state.user = User or None
                ↓
        Limiter uses user ID or IP
```

### Code Example

```python
from ..rate_limit import limiter, RATE_LIMITS

@router.post("/expensive-operation")
@limiter.limit(RATE_LIMITS["create_job"])
def expensive_operation(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    # Endpoint logic
    pass
```

---

## Email Notifications

Automated email notifications for job completion and errors.

### Features

- **Job Completion Emails**: Notified when jobs finish (delivered/blocked/aborted)
- **Job Error Emails**: Alerted when jobs fail with error details
- **HTML Templates**: Beautiful, responsive email templates
- **Async Sending**: Non-blocking email delivery
- **Per-User Configuration**: Each user configures their own email preferences

### Setup

#### 1. Configure SMTP

Add to `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=notifications@bacowr.local
SMTP_FROM_NAME=BACOWR
```

#### 2. Gmail App Password (Recommended)

For Gmail, use App Passwords instead of your account password:

1. Go to Google Account Settings
2. Security → 2-Step Verification
3. App passwords → Generate password
4. Use generated password in `SMTP_PASSWORD`

#### 3. Enable Notifications

```bash
curl -X PUT http://localhost:8000/api/v1/notifications \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_email": "alerts@example.com",
    "enable_email_notifications": true
  }'
```

#### 4. Test Email

```bash
curl -X POST http://localhost:8000/api/v1/notifications/test-email \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Email Templates

Templates are located in `api/app/notifications/templates/`:

- `job_completed.html`: Job completion notification
- `job_error.html`: Job error notification

### Notification Events

**Job Completed:**
- Status: DELIVERED, BLOCKED, or ABORTED
- Includes: Job ID, publisher, target URL, cost
- Action: Link to view job in dashboard

**Job Error:**
- Triggered on exceptions during job processing
- Includes: Error message, job details
- Action: Link to error details in dashboard

### API Endpoints

**Get Notification Preferences:**
```http
GET /api/v1/notifications
Authorization: Bearer <token>
```

**Update Preferences:**
```http
PUT /api/v1/notifications
Authorization: Bearer <token>
Content-Type: application/json

{
  "notification_email": "alerts@example.com",
  "enable_email_notifications": true
}
```

**Test Email:**
```http
POST /api/v1/notifications/test-email
Authorization: Bearer <token>
```

### SMTP Providers

**Gmail:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
```

**SendGrid:**
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_USE_TLS=true
```

**Mailgun:**
```env
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USERNAME=postmaster@yourdomain.com
SMTP_PASSWORD=your-mailgun-password
SMTP_USE_TLS=true
```

**AWS SES:**
```env
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-ses-username
SMTP_PASSWORD=your-ses-password
SMTP_USE_TLS=true
```

---

## Webhook Integrations

HTTP POST callbacks for external systems integration.

### Features

- **Real-time Events**: Instant notifications when jobs complete or error
- **Automatic Retries**: Failed webhooks retried up to 3 times
- **HMAC Signatures**: Verify webhook authenticity
- **Timeout Protection**: 10-second timeout prevents hanging
- **Per-User Configuration**: Each user configures their own webhook URL

### Setup

#### 1. Configure Webhook

```bash
curl -X PUT http://localhost:8000/api/v1/notifications \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://example.com/webhooks/bacowr",
    "enable_webhook_notifications": true
  }'
```

#### 2. Test Webhook

```bash
curl -X POST http://localhost:8000/api/v1/notifications/test-webhook \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Webhook Payload

**Job Completed:**
```json
{
  "event": "job.completed",
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "delivered",
    "publisher_domain": "aftonbladet.se",
    "target_url": "https://example.com",
    "completed_at": "2025-11-09T12:34:56Z",
    "actual_cost": 0.0123,
    "timestamp": "2025-11-09T12:34:56Z"
  },
  "timestamp": "2025-11-09T12:34:56Z"
}
```

**Job Error:**
```json
{
  "event": "job.error",
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "publisher_domain": "aftonbladet.se",
    "error_message": "API rate limit exceeded",
    "timestamp": "2025-11-09T12:34:56Z"
  },
  "timestamp": "2025-11-09T12:34:56Z"
}
```

### Webhook Headers

```http
POST /webhooks/bacowr HTTP/1.1
Host: example.com
Content-Type: application/json
User-Agent: BACOWR-Webhook/1.0
X-BACOWR-Signature: a1b2c3d4e5f6...
```

### Signature Verification

Webhooks include HMAC-SHA256 signature for verification:

**Configure Secret:**
```env
WEBHOOK_SECRET_KEY=your-webhook-secret-key
```

**Verify Signature (Python):**
```python
import hmac
import hashlib

def verify_webhook(payload: str, signature: str, secret: str) -> bool:
    """Verify webhook signature."""
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)

# In your webhook handler:
signature = request.headers.get('X-BACOWR-Signature')
payload = request.body.decode()
secret = os.getenv('WEBHOOK_SECRET_KEY')

if not verify_webhook(payload, signature, secret):
    return {"error": "Invalid signature"}, 401
```

**Verify Signature (Node.js):**
```javascript
const crypto = require('crypto');

function verifyWebhook(payload, signature, secret) {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(signature)
  );
}

// In your webhook handler:
const signature = req.headers['x-bacowr-signature'];
const payload = JSON.stringify(req.body);
const secret = process.env.WEBHOOK_SECRET_KEY;

if (!verifyWebhook(payload, signature, secret)) {
  return res.status(401).json({ error: 'Invalid signature' });
}
```

### Retry Logic

- **Max Retries**: 3 attempts
- **Retry Conditions**: 5xx errors, timeouts
- **No Retry**: 2xx, 3xx, 4xx responses
- **Timeout**: 10 seconds per attempt

### Configuration

```env
WEBHOOK_TIMEOUT=10          # Seconds
WEBHOOK_MAX_RETRIES=3       # Max retry attempts
WEBHOOK_SECRET_KEY=secret   # HMAC signature key
```

### Integration Examples

**Slack Webhook:**
```bash
curl -X PUT http://localhost:8000/api/v1/notifications \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    "enable_webhook_notifications": true
  }'
```

**Discord Webhook:**
```bash
curl -X PUT http://localhost:8000/api/v1/notifications \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://discord.com/api/webhooks/YOUR/WEBHOOK",
    "enable_webhook_notifications": true
  }'
```

**Custom Server:**
```python
# Flask webhook receiver
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhooks/bacowr', methods=['POST'])
def bacowr_webhook():
    payload = request.json
    event = payload.get('event')
    data = payload.get('data')

    if event == 'job.completed':
        print(f"Job {data['job_id']} completed with status {data['status']}")
    elif event == 'job.error':
        print(f"Job {data['job_id']} failed: {data['error_message']}")

    return jsonify({"status": "received"}), 200
```

---

## Configuration

### Environment Variables

Complete `.env` configuration:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bacowr

# Frontend URL (for CORS and email links)
FRONTEND_URL=http://localhost:3000

# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...
GOOGLE_API_KEY=...

# Ahrefs API (optional)
AHREFS_API_KEY=...

# JWT Secret Key
JWT_SECRET_KEY=your-secret-key-here-change-in-production

# Rate Limiting
REDIS_URL=memory://  # or redis://localhost:6379

# Email Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=notifications@bacowr.local
SMTP_FROM_NAME=BACOWR

# Webhook Notifications
WEBHOOK_TIMEOUT=10
WEBHOOK_MAX_RETRIES=3
WEBHOOK_SECRET_KEY=your-webhook-secret-key

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### Redis Setup (Production)

**Install Redis:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Start Redis
redis-server
```

**Configure:**
```env
REDIS_URL=redis://localhost:6379
```

**With Authentication:**
```bash
# redis.conf
requirepass your-password
```

```env
REDIS_URL=redis://:your-password@localhost:6379/0
```

---

## Best Practices

### Rate Limiting

1. **Use Redis in Production**: In-memory storage is lost on restart
2. **Monitor Rate Limit Headers**: Track usage patterns
3. **Customize Limits**: Adjust based on your user base
4. **Plan for Scaling**: Redis supports multiple app instances

### Email Notifications

1. **Use App Passwords**: Don't use your main email password
2. **Dedicated Email Service**: Use SendGrid, Mailgun, or AWS SES for production
3. **Test Email Delivery**: Use test endpoint before going live
4. **Monitor Failures**: Check logs for SMTP errors
5. **Separate Notification Email**: Allow users to use different email than login

### Webhooks

1. **Verify Signatures**: Always validate webhook signatures
2. **Handle Retries**: Implement idempotency in webhook receivers
3. **Quick Response**: Return 200 quickly, process async
4. **Monitor Failures**: Track webhook delivery success rate
5. **Test Webhooks**: Use test endpoint to verify configuration

### Security

1. **HTTPS Only**: Use HTTPS in production
2. **Strong Secrets**: Generate strong JWT and webhook secrets
3. **Environment Variables**: Never commit secrets to version control
4. **Rate Limiting**: Protect against brute force attacks
5. **Input Validation**: Validate all webhook URLs and emails

---

## Troubleshooting

### Rate Limiting

**Problem:** Rate limits not working
```bash
# Check Redis connection
redis-cli ping
# Should return: PONG
```

**Problem:** Rate limits reset on server restart
```
Solution: Use Redis instead of memory:// storage
```

**Problem:** Different limits for same user
```
Solution: Ensure JWT_SECRET_KEY is consistent across instances
```

### Email Notifications

**Problem:** Emails not sending
```bash
# Check SMTP configuration
python -c "
import aiosmtplib
import asyncio

async def test():
    await aiosmtplib.send(
        message,
        hostname='smtp.gmail.com',
        port=587,
        username='your@email.com',
        password='your-password',
        use_tls=True
    )

asyncio.run(test())
"
```

**Problem:** Gmail authentication fails
```
Solution: Use App Password, not account password
1. Enable 2-Step Verification
2. Generate App Password
3. Use App Password in SMTP_PASSWORD
```

**Problem:** Emails go to spam
```
Solution:
1. Use verified email service (SendGrid, Mailgun)
2. Configure SPF and DKIM records
3. Use professional from_email domain
```

### Webhooks

**Problem:** Webhooks timing out
```
Solution: Increase WEBHOOK_TIMEOUT or optimize webhook receiver
```

**Problem:** Webhooks failing signature verification
```
Solution: Ensure WEBHOOK_SECRET_KEY matches on both sides
```

**Problem:** Duplicate webhook deliveries
```
Solution: Implement idempotency using job_id + timestamp
```

**Test Webhook Receiver:**
```bash
# Use ngrok for local testing
ngrok http 3000

# Update webhook URL
curl -X PUT http://localhost:8000/api/v1/notifications \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://YOUR_NGROK_URL/webhooks/bacowr",
    "enable_webhook_notifications": true
  }'
```

---

## Related Documentation

- [API Backend Guide](./API_BACKEND_COMPLETE.md)
- [Authentication Guide](./AUTH_GUIDE.md)
- [Analytics Guide](./ANALYTICS_GUIDE.md)
- [WebSocket Guide](./WEBSOCKET_GUIDE.md)

---

**Version:** 1.0.0
**Last Updated:** 2025-11-09
**Status:** Production-ready

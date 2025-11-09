# Authentication Guide

## Overview

BACOWR API supports **dual authentication** for maximum flexibility:

1. **API Key Authentication** - Simple, long-lived tokens for programmatic access
2. **JWT Bearer Token Authentication** - Secure, short-lived tokens with refresh mechanism

Both methods can be used interchangeably throughout the API.

---

## Quick Start

### Option 1: Register a New Account

```bash
# Register new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "full_name": "John Doe"
  }'

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

###Option 2: Login with Existing Account

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

### Option 3: Use API Key

```bash
# Get your API key
curl -X GET http://localhost:8000/api/v1/auth/api-key \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response
{
  "api_key": "bacowr_abc123...",
  "usage": "Include in requests as 'X-API-Key' header"
}
```

---

## Authentication Methods

### Method 1: JWT Bearer Token

**Best for:** Web applications, mobile apps, temporary access

**Advantages:**
- Automatic expiration (30 minutes)
- Refresh token mechanism
- Secure and stateless
- Industry standard

**Usage:**
```bash
# Use access token in Authorization header
curl -X GET http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Token Lifecycle:**
1. **Access Token**: 30 minutes lifetime
2. **Refresh Token**: 30 days lifetime
3. When access token expires, use refresh token to get new tokens
4. When refresh token expires, user must login again

### Method 2: API Key

**Best for:** Server-to-server integrations, scripts, long-running jobs

**Advantages:**
- Never expires (until manually regenerated)
- Simple to use
- Perfect for automation

**Usage:**
```bash
# Use API key in X-API-Key header
curl -X GET http://localhost:8000/api/v1/jobs \
  -H "X-API-Key: bacowr_abc123..."
```

---

## Authentication Endpoints

### POST /api/v1/auth/register

Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe"  // optional
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

**Response:** (201 Created)
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `400` - Email already registered
- `422` - Validation error (password requirements)

---

### POST /api/v1/auth/login

Login with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:** (200 OK)
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `401` - Incorrect email or password
- `403` - Account is inactive

---

### POST /api/v1/auth/refresh

Refresh access token using refresh token.

**Request Headers:**
```
Authorization: Bearer YOUR_REFRESH_TOKEN
```

**Response:** (200 OK)
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Errors:**
- `401` - Invalid or expired refresh token

---

### GET /api/v1/auth/me

Get current user profile.

**Authentication:** Bearer token or API key

**Response:** (200 OK)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_admin": false,
  "created_at": "2025-11-08T12:00:00Z"
}
```

---

### PUT /api/v1/auth/me

Update user profile.

**Authentication:** Bearer token or API key

**Request:**
```json
{
  "full_name": "Jane Doe",
  "email": "newemail@example.com"  // optional
}
```

**Response:** (200 OK)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newemail@example.com",
  "full_name": "Jane Doe",
  "is_active": true,
  "is_admin": false,
  "created_at": "2025-11-08T12:00:00Z"
}
```

**Errors:**
- `400` - Email already in use

---

### POST /api/v1/auth/change-password

Change user password.

**Authentication:** Bearer token or API key

**Request:**
```json
{
  "current_password": "OldPass123",
  "new_password": "NewSecurePass456"
}
```

**Response:** (200 OK)
```json
{
  "message": "Password updated successfully"
}
```

**Errors:**
- `401` - Current password is incorrect
- `422` - New password doesn't meet requirements

---

### GET /api/v1/auth/api-key

Get your API key.

**Authentication:** Bearer token or API key

**Response:** (200 OK)
```json
{
  "api_key": "bacowr_abc123def456...",
  "usage": "Include in requests as 'X-API-Key' header"
}
```

---

### POST /api/v1/auth/regenerate-api-key

Generate a new API key and invalidate the old one.

**Authentication:** Bearer token or API key

**Response:** (200 OK)
```json
{
  "api_key": "bacowr_new789xyz...",
  "message": "API key regenerated successfully. Old key is now invalid."
}
```

**Warning:** All existing integrations using the old API key will stop working!

---

## Admin Endpoints

These endpoints require admin privileges.

### GET /api/v1/auth/users

List all users.

**Authentication:** Bearer token or API key (admin only)

**Query Parameters:**
- `skip`: Offset for pagination (default: 0)
- `limit`: Number of users to return (default: 100)

**Response:** (200 OK)
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "api_key": "bacowr_abc...",
    "is_active": true,
    "is_admin": false,
    "created_at": "2025-11-08T12:00:00Z"
  },
  ...
]
```

---

### GET /api/v1/auth/users/{user_id}

Get user by ID.

**Authentication:** Bearer token or API key (admin only)

**Response:** (200 OK)
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "John Doe",
  "api_key": "bacowr_abc...",
  "is_active": true,
  "is_admin": false,
  "created_at": "2025-11-08T12:00:00Z"
}
```

**Errors:**
- `404` - User not found

---

### PATCH /api/v1/auth/users/{user_id}/activate

Activate a user account.

**Authentication:** Bearer token or API key (admin only)

**Response:** (200 OK)
```json
{
  "message": "User user@example.com activated successfully"
}
```

---

### PATCH /api/v1/auth/users/{user_id}/deactivate

Deactivate a user account.

**Authentication:** Bearer token or API key (admin only)

**Response:** (200 OK)
```json
{
  "message": "User user@example.com deactivated successfully"
}
```

**Errors:**
- `400` - Cannot deactivate your own account

---

### DELETE /api/v1/auth/users/{user_id}

Delete a user account.

**Authentication:** Bearer token or API key (admin only)

**Response:** (204 No Content)

**Warning:** This will delete all jobs and backlinks associated with the user!

**Errors:**
- `400` - Cannot delete your own account
- `404` - User not found

---

## Usage Examples

### JavaScript/TypeScript

```typescript
// Register
const registerResponse = await fetch('http://localhost:8000/api/v1/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePass123',
    full_name: 'John Doe'
  })
});

const { access_token, refresh_token } = await registerResponse.json();

// Use access token
const jobsResponse = await fetch('http://localhost:8000/api/v1/jobs', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});

// Refresh token when expired
const refreshResponse = await fetch('http://localhost:8000/api/v1/auth/refresh', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${refresh_token}`
  }
});

const { access_token: newAccessToken } = await refreshResponse.json();
```

### Python

```python
import requests

# Register
response = requests.post(
    'http://localhost:8000/api/v1/auth/register',
    json={
        'email': 'user@example.com',
        'password': 'SecurePass123',
        'full_name': 'John Doe'
    }
)

tokens = response.json()
access_token = tokens['access_token']

# Use access token
jobs_response = requests.get(
    'http://localhost:8000/api/v1/jobs',
    headers={'Authorization': f'Bearer {access_token}'}
)

# Or use API key
api_key_response = requests.get(
    'http://localhost:8000/api/v1/auth/api-key',
    headers={'Authorization': f'Bearer {access_token}'}
)

api_key = api_key_response.json()['api_key']

# Use API key for subsequent requests
jobs_response = requests.get(
    'http://localhost:8000/api/v1/jobs',
    headers={'X-API-Key': api_key}
)
```

### cURL

```bash
# Register
ACCESS_TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123"}' \
  | jq -r '.access_token')

# Create job with token
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "aftonbladet.se",
    "target_url": "https://example.com",
    "anchor_text": "example link"
  }'

# Get API key
API_KEY=$(curl -X GET http://localhost:8000/api/v1/auth/api-key \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  | jq -r '.api_key')

# Create job with API key
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "svd.se",
    "target_url": "https://example.com/page2",
    "anchor_text": "another link"
  }'
```

---

## Security Best Practices

### 1. JWT Secret Key

**Generate a strong secret key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add to `.env`:
```env
JWT_SECRET_KEY=your-generated-secret-key-here
```

**Never commit secrets to version control!**

### 2. HTTPS in Production

Always use HTTPS in production. JWT tokens should never be transmitted over HTTP.

### 3. Token Storage

**Frontend Applications:**
- Store access token in memory or sessionStorage
- Store refresh token in httpOnly cookie (if backend supports)
- Never store tokens in localStorage (XSS risk)

**Backend/CLI Applications:**
- Use API keys instead of JWT tokens
- Store API keys in environment variables or secure key management systems

### 4. Password Requirements

Enforced automatically:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit

### 5. Rate Limiting

Consider implementing rate limiting for authentication endpoints:
- Login: 5 requests per minute
- Register: 3 requests per hour
- Refresh: 10 requests per minute

---

## Token Expiration

| Token Type | Lifetime | Renewal |
|------------|----------|---------|
| Access Token | 30 minutes | Use refresh token |
| Refresh Token | 30 days | Login again |
| API Key | Indefinite | Manual regeneration |

---

## Migration from API Key Only

If you're currently using API keys and want to add JWT authentication:

1. **Keep existing API key authentication** - Still works!
2. **Add JWT support** - Users can choose their preferred method
3. **Frontend uses JWT** - Better user experience with automatic refresh
4. **Scripts use API keys** - Simpler for automation

Both methods work simultaneously - no breaking changes!

---

## Troubleshooting

### "Authentication required" Error

**Problem:** Getting 401 Unauthorized

**Solutions:**
1. Check if token/API key is included in request
2. Verify header format: `Authorization: Bearer <token>` or `X-API-Key: <key>`
3. Check if access token expired (use refresh token)
4. Verify API key hasn't been regenerated

### "Invalid token" Error

**Problem:** Token is rejected

**Solutions:**
1. Check if using correct token (access vs refresh)
2. Verify JWT_SECRET_KEY matches between environments
3. Check token expiration time
4. Try logging in again to get new tokens

### "User account is inactive" Error

**Problem:** Getting 403 Forbidden

**Solutions:**
1. Contact admin to activate account
2. Admin can activate via: `PATCH /api/v1/auth/users/{user_id}/activate`

---

## Configuration

### Environment Variables

```env
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here  # Required for production
```

### Token Lifetimes

Edit `api/app/auth.py` to customize:

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 30    # Access token lifetime
REFRESH_TOKEN_EXPIRE_DAYS = 30      # Refresh token lifetime
```

---

## Related Documentation

- [API Backend Guide](./API_BACKEND_COMPLETE.md)
- [WebSocket Guide](./WEBSOCKET_GUIDE.md)
- [Frontend Overview](./FRONTEND_OVERVIEW.md)
- [Production Guide](./PRODUCTION_GUIDE.md)

---

**Version:** 1.0.0
**Last Updated:** 2025-11-09
**Status:** Production-ready

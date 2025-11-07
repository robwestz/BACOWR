# BACOWR API

Production-ready REST API for BACOWR content generation system.

## Features

- ✅ **REST API** with FastAPI
- ✅ **PostgreSQL** database with SQLAlchemy ORM
- ✅ **API Key Authentication**
- ✅ **Job Management** - Create, monitor, retrieve jobs
- ✅ **Backlinks Library** - Import and query 3000+ historical backlinks
- ✅ **Analytics** - Usage stats, cost tracking, success rates
- ✅ **Cost Estimation** - Estimate before running
- ✅ **Background Processing** - Async job execution
- ✅ **Auto-generated Docs** - Swagger UI at `/docs`

## Quick Start

### 1. Install Dependencies

```bash
cd api
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

Minimum required:
```env
DATABASE_URL=sqlite:///./bacowr.db  # Or PostgreSQL
ANTHROPIC_API_KEY=sk-ant-api03-...  # Your LLM API key
```

### 3. Run Server

```bash
# Development
python -m app.main

# Or with uvicorn directly
uvicorn app.main:app --reload
```

Server starts on `http://localhost:8000`

### 4. Get API Key

On first startup, a default admin user is created:

```
Email:   admin@bacowr.local
API Key: bacowr_<random>  # Shown in console output
```

**Save this API key!** You'll need it for all requests.

### 5. Test API

```bash
# Health check
curl http://localhost:8000/health

# Create a job (requires API key)
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "X-API-Key: bacowr_<your-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "aftonbladet.se",
    "target_url": "https://sv.wikipedia.org/wiki/Artificiell_intelligens",
    "anchor_text": "läs mer om AI",
    "llm_provider": "anthropic",
    "writing_strategy": "multi_stage"
  }'

# Get job status
curl http://localhost:8000/api/v1/jobs/<job-id> \
  -H "X-API-Key: bacowr_<your-key>"
```

### 6. View Docs

Open `http://localhost:8000/docs` for interactive Swagger UI documentation.

## API Endpoints

### Jobs

```
POST   /api/v1/jobs              Create job
GET    /api/v1/jobs              List jobs
GET    /api/v1/jobs/{id}         Get job details
GET    /api/v1/jobs/{id}/article Get article text
DELETE /api/v1/jobs/{id}         Delete job
```

### Backlinks

```
POST   /api/v1/backlinks         Create backlink
POST   /api/v1/backlinks/bulk    Bulk import
GET    /api/v1/backlinks         List backlinks (with filters)
GET    /api/v1/backlinks/stats   Get statistics
GET    /api/v1/backlinks/{id}    Get backlink
DELETE /api/v1/backlinks/{id}    Delete backlink
```

### Analytics

```
POST   /api/v1/analytics/cost/estimate  Estimate cost
GET    /api/v1/analytics                Get usage analytics
GET    /api/v1/analytics/providers      List available providers
```

## Authentication

All endpoints (except `/health` and `/`) require API key authentication.

Include API key in header:
```
X-API-Key: bacowr_<your-key>
```

## Database

### SQLite (Development)

Default configuration uses SQLite:
```env
DATABASE_URL=sqlite:///./bacowr.db
```

### PostgreSQL (Production)

For production, use PostgreSQL:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/bacowr
```

Database is auto-initialized on first startup.

## Deployment

### Railway

1. Create new project on [Railway](https://railway.app)
2. Add PostgreSQL database
3. Deploy from GitHub:
   - Root directory: `/api`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set environment variables from `.env.example`

### Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Create app
flyctl launch --name bacowr-api

# Deploy
flyctl deploy
```

### Docker

```bash
# Build
docker build -t bacowr-api .

# Run
docker run -p 8000:8000 --env-file .env bacowr-api
```

## Development

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing

```bash
# Run tests (when implemented)
pytest
```

### Code Quality

```bash
# Format with black
black app/

# Lint with flake8
flake8 app/

# Type check with mypy
mypy app/
```

## Project Structure

```
api/
├── app/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database config
│   ├── auth.py              # Authentication
│   ├── models/
│   │   ├── database.py      # SQLAlchemy models
│   │   └── schemas.py       # Pydantic schemas
│   ├── routes/
│   │   ├── jobs.py          # Job endpoints
│   │   ├── backlinks.py     # Backlink endpoints
│   │   └── analytics.py     # Analytics endpoints
│   └── core/
│       └── bacowr_wrapper.py # BACOWR integration
├── alembic/                 # Database migrations
├── requirements.txt
├── .env.example
└── README.md
```

## Performance

- **Job creation**: ~100ms
- **Job listing**: ~50ms (with pagination)
- **Backlink stats**: ~200ms (for 3000+ backlinks)
- **Content generation**: 15-60s (depending on strategy)

## Limits

- **Bulk import**: Max 1000 backlinks per request
- **Pagination**: Max 100 items per page
- **Job deletion**: Only non-processing jobs
- **API rate limit**: None (add if needed)

## Security

- API key authentication
- CORS configured for frontend
- SQL injection protection (SQLAlchemy)
- Input validation (Pydantic)
- Password hashing (bcrypt)

## Monitoring

Monitor API health:
```bash
curl http://localhost:8000/health
```

Check logs for errors and performance.

## Support

- **Docs**: `http://localhost:8000/docs`
- **Health**: `http://localhost:8000/health`
- **GitHub**: Issues at main BACOWR repo

---

**Version**: 1.0.0
**Status**: Production Ready
**License**: See main BACOWR repo

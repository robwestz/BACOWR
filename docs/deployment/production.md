# BACOWR Production Deployment Guide

## Overview

This guide covers deploying BACOWR to production environments. The system consists of:

- **Backend API**: FastAPI application (Python 3.11+)
- **Frontend**: Next.js 14 application (Node.js 20+)
- **Database**: PostgreSQL 15+ (SQLite for local only)
- **Cache**: Redis 7+ (optional, for rate limiting)

## Pre-Deployment Checklist

### 1. Environment Variables

Create a `.env` file with the following variables:

**Backend (`api/.env`):**
```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/bacowr
# For Railway/Heroku: postgresql://... (automatically converted)

# Authentication
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM Providers (at least one required)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# CORS
FRONTEND_URL=https://your-frontend.vercel.app

# Redis (optional, for distributed rate limiting)
REDIS_URL=redis://default:password@host:6379

# Monitoring (optional)
SENTRY_DSN=https://...@sentry.io/...

# Debug (set to false in production)
DEBUG=false
```

**Frontend (`frontend/.env.local`):**
```bash
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
NEXT_PUBLIC_WS_URL=wss://your-backend.railway.app/api/v1/ws
```

### 2. Generate Secrets

```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate initial admin password
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

### 3. Prepare Database

**For PostgreSQL on Railway/Heroku:**
```bash
# Database is provisioned automatically
# Connection string provided as DATABASE_URL
```

**For managed PostgreSQL (AWS RDS, Google Cloud SQL):**
```bash
# Create database
createdb bacowr

# Update DATABASE_URL with connection string
DATABASE_URL=postgresql://user:password@rds-host:5432/bacowr
```

## Deployment Options

### Option 1: Railway (Recommended)

Railway provides easy deployment with automatic provisioning.

#### Backend Deployment

1. **Create Railway Project**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli

   # Login
   railway login

   # Create new project
   railway init
   ```

2. **Add PostgreSQL Database**
   ```bash
   # In Railway dashboard or CLI
   railway add postgresql

   # Railway automatically sets DATABASE_URL
   ```

3. **Configure Backend Service**

   Create `railway.json` in project root:
   ```json
   {
     "build": {
       "builder": "NIXPACKS",
       "buildCommand": "cd api && pip install -r requirements.txt"
     },
     "deploy": {
       "startCommand": "cd api && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT",
       "restartPolicyType": "ON_FAILURE",
       "restartPolicyMaxRetries": 10
     }
   }
   ```

4. **Set Environment Variables**
   ```bash
   railway variables set SECRET_KEY=<your-secret>
   railway variables set ANTHROPIC_API_KEY=<your-key>
   railway variables set OPENAI_API_KEY=<your-key>
   railway variables set FRONTEND_URL=<your-frontend-url>
   ```

5. **Deploy**
   ```bash
   railway up
   ```

6. **Run Migrations**
   ```bash
   # Migrations run automatically via startCommand
   # Or manually:
   railway run alembic upgrade head
   ```

7. **Get Backend URL**
   ```bash
   railway domain
   # Returns: https://your-app.railway.app
   ```

#### Frontend Deployment (Vercel)

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Deploy Frontend**
   ```bash
   cd frontend
   vercel

   # Follow prompts:
   # - Link to existing project or create new
   # - Set environment variables when prompted
   ```

3. **Set Environment Variables in Vercel Dashboard**
   - `NEXT_PUBLIC_API_URL`: https://your-backend.railway.app/api/v1
   - `NEXT_PUBLIC_WS_URL`: wss://your-backend.railway.app/api/v1/ws

4. **Deploy to Production**
   ```bash
   vercel --prod
   ```

### Option 2: Docker Compose

For self-hosted deployments or local production testing.

#### Docker Setup

**Create `docker-compose.yml` in project root:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: bacowr
      POSTGRES_USER: bacowr
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bacowr"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./api
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://bacowr:${DB_PASSWORD}@postgres:5432/bacowr
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      FRONTEND_URL: ${FRONTEND_URL}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1
      NEXT_PUBLIC_WS_URL: ws://localhost:8000/api/v1/ws
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

**Create `api/Dockerfile`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 bacowr && chown -R bacowr:bacowr /app
USER bacowr

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Create `frontend/Dockerfile`:**
```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy application
COPY . .

# Build application
RUN npm run build

# Production image
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs

EXPOSE 3000

CMD ["node", "server.js"]
```

#### Deploy with Docker Compose

```bash
# Create .env file with all variables
cp .env.example .env
# Edit .env with production values

# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Check health
curl http://localhost:8000/health
```

### Option 3: AWS Deployment

For enterprise deployments requiring full control.

#### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AWS Cloud                             │
│                                                          │
│  ┌──────────────┐      ┌──────────────┐                │
│  │ CloudFront   │──────│ S3 (Static)  │                │
│  │ (Frontend)   │      │ (Next.js)    │                │
│  └──────────────┘      └──────────────┘                │
│         │                                                │
│         │              ┌──────────────┐                │
│         └──────────────│ API Gateway  │                │
│                        └──────┬───────┘                │
│                               │                         │
│                    ┌──────────┴────────┐               │
│                    │ ECS Fargate       │               │
│                    │ (Backend API)     │               │
│                    └──────────┬────────┘               │
│                               │                         │
│              ┌────────────────┼────────────┐           │
│              │                │            │           │
│     ┌────────▼─────┐  ┌──────▼─────┐  ┌──▼──────┐    │
│     │ RDS Postgres │  │ ElastiCache│  │ Secrets │    │
│     │              │  │ (Redis)    │  │ Manager │    │
│     └──────────────┘  └────────────┘  └─────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### Backend (ECS Fargate)

1. **Create ECR Repository**
   ```bash
   aws ecr create-repository --repository-name bacowr-backend
   ```

2. **Build and Push Docker Image**
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | \
     docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

   # Build
   docker build -t bacowr-backend ./api

   # Tag
   docker tag bacowr-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/bacowr-backend:latest

   # Push
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/bacowr-backend:latest
   ```

3. **Create ECS Task Definition**
   ```json
   {
     "family": "bacowr-backend",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024",
     "containerDefinitions": [
       {
         "name": "bacowr-api",
         "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/bacowr-backend:latest",
         "portMappings": [{"containerPort": 8000}],
         "secrets": [
           {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:..."},
           {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:..."}
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/bacowr-backend",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

4. **Create ECS Service**
   ```bash
   aws ecs create-service \
     --cluster bacowr-cluster \
     --service-name bacowr-backend \
     --task-definition bacowr-backend \
     --desired-count 2 \
     --launch-type FARGATE \
     --load-balancers targetGroupArn=<target-group-arn>,containerName=bacowr-api,containerPort=8000
   ```

#### Frontend (S3 + CloudFront)

1. **Build Frontend**
   ```bash
   cd frontend
   npm run build
   npm run export  # If using static export
   ```

2. **Create S3 Bucket**
   ```bash
   aws s3 mb s3://bacowr-frontend
   aws s3 website s3://bacowr-frontend --index-document index.html
   ```

3. **Upload to S3**
   ```bash
   aws s3 sync out/ s3://bacowr-frontend
   ```

4. **Create CloudFront Distribution**
   ```bash
   aws cloudfront create-distribution \
     --origin-domain-name bacowr-frontend.s3.amazonaws.com \
     --default-root-object index.html
   ```

## Database Migrations

Always run migrations before deploying new code:

### Railway/Heroku
Migrations run automatically via `startCommand`:
```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Docker Compose
```bash
docker-compose exec backend alembic upgrade head
```

### AWS ECS
Run as one-off task before deploying new service:
```bash
aws ecs run-task \
  --cluster bacowr-cluster \
  --task-definition bacowr-migration \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
```

### Manual Migration
```bash
cd api
alembic upgrade head
```

## Health Checks

Configure health checks for load balancers and orchestrators:

**Endpoint**: `GET /health`

**Expected Response**:
```json
{
  "status": "healthy",
  "service": "bacowr-api",
  "version": "1.0.0"
}
```

**Health Check Configuration**:
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Healthy Threshold**: 2
- **Unhealthy Threshold**: 3

## Monitoring

### Application Logs

**Railway**:
```bash
railway logs
```

**Docker Compose**:
```bash
docker-compose logs -f backend
```

**AWS CloudWatch**:
- Log Group: `/ecs/bacowr-backend`
- Retention: 30 days minimum

### Metrics (if Prometheus enabled)

Key metrics to monitor:
- `api_requests_total` - Request count by endpoint
- `api_request_duration_seconds` - Response time distribution
- `llm_generation_duration_seconds` - LLM API latency
- `llm_generation_cost_dollars` - Cost tracking
- `active_jobs` - Current job queue size

### Alerts

Configure alerts for:
- Error rate > 5% (5xx responses)
- Response time p95 > 2 seconds
- Database connection failures
- LLM provider failures
- Disk usage > 80%
- Memory usage > 90%

## Backup and Recovery

### Database Backups

**Railway**: Automatic daily backups (configurable)

**PostgreSQL on RDS**: Enable automated backups
```bash
aws rds modify-db-instance \
  --db-instance-identifier bacowr-db \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00"
```

**Manual Backup**:
```bash
pg_dump -h host -U user bacowr > bacowr_backup_$(date +%Y%m%d).sql
```

### Restore from Backup

```bash
# Drop existing database (WARNING: data loss)
dropdb bacowr

# Create new database
createdb bacowr

# Restore from backup
psql -h host -U user bacowr < bacowr_backup_20251119.sql

# Run migrations to ensure schema is current
cd api && alembic upgrade head
```

## Security Hardening

### 1. HTTPS Only

**Railway/Vercel**: Automatic HTTPS

**Custom Domain**: Configure SSL certificate via Let's Encrypt or AWS Certificate Manager

### 2. Environment Variables

Never commit `.env` files. Use secret management:
- Railway: Built-in environment variables
- AWS: Secrets Manager
- Docker: Docker secrets or .env file (mounted, not in image)

### 3. Database Security

- Use strong passwords (32+ characters)
- Enable SSL connections only
- Restrict network access (VPC, security groups)
- Regular security updates

### 4. Rate Limiting

Configure rate limits based on usage patterns:
```python
# api/app/middleware/rate_limit.py
DEFAULT_LIMITS = ["1000/day", "100/hour"]
EXPENSIVE_LIMITS = ["10/minute", "100/hour"]
```

### 5. CORS Configuration

Restrict origins in production:
```python
# api/app/main.py
allow_origins = [
    os.getenv("FRONTEND_URL"),  # Production frontend only
]
```

## Scaling

### Horizontal Scaling

**Railway**: Increase replica count in dashboard

**ECS**: Update desired count
```bash
aws ecs update-service \
  --cluster bacowr-cluster \
  --service bacowr-backend \
  --desired-count 4
```

**Docker Compose**: Use Docker Swarm
```bash
docker service scale bacowr_backend=4
```

### Vertical Scaling

**Railway**: Change instance size in dashboard

**ECS**: Update task definition with more CPU/memory

**PostgreSQL**: Increase instance size via provider dashboard

### Database Connection Pooling

Configure in `api/app/database.py`:
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,        # Max persistent connections
    max_overflow=40,     # Additional connections under load
    pool_pre_ping=True   # Verify connections before use
)
```

## Troubleshooting

### Issue: Migration Fails on Deployment

**Symptom**: Service fails to start, migration error in logs

**Solution**:
```bash
# Check current migration version
alembic current

# Check pending migrations
alembic history

# Try manual migration
alembic upgrade head

# If corrupted, stamp to current code version
alembic stamp head
```

### Issue: Database Connection Refused

**Symptom**: `sqlalchemy.exc.OperationalError: could not connect to server`

**Solutions**:
1. Verify DATABASE_URL is correct
2. Check database is running: `pg_isready -h host`
3. Verify network access (security groups, firewall)
4. Check SSL requirements: `sslmode=require` in connection string

### Issue: High Memory Usage

**Symptom**: Container OOMKilled or slow performance

**Solutions**:
1. Check connection pool size (reduce if too high)
2. Add memory limits to prevent unbounded growth
3. Profile application: `py-spy record --pid <pid>`
4. Check for memory leaks in LLM service

### Issue: Rate Limit Errors

**Symptom**: Users getting 429 Too Many Requests

**Solutions**:
1. Check Redis connection (fallback to in-memory if down)
2. Adjust rate limits in `api/app/middleware/rate_limit.py`
3. Implement per-plan rate limits for different user tiers

### Issue: Slow LLM Response

**Symptom**: Jobs taking too long to complete

**Solutions**:
1. Check LLM provider status page
2. Implement timeout and retry logic
3. Add fallback to alternative providers
4. Consider caching common responses

## Post-Deployment Validation

After deployment, validate all critical workflows:

```bash
# 1. Health check
curl https://your-backend.railway.app/health

# 2. Create test user (if not exists)
curl -X POST https://your-backend.railway.app/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# 3. Run smoke test
cd tools
python smoke_test_wave1.py --api-url https://your-backend.railway.app

# 4. Run E2E tests
cd tests/e2e
pytest test_critical_workflows.py -v
```

## Rollback Procedure

If deployment fails:

### Railway
```bash
# Redeploy previous version
railway redeploy <deployment-id>
```

### Docker
```bash
# Stop new version
docker-compose down

# Checkout previous version
git checkout <previous-commit>

# Start previous version
docker-compose up -d
```

### Database Rollback
```bash
# Rollback one migration
cd api && alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision-id>
```

## Maintenance Windows

For major updates, schedule maintenance:

1. **Notify users** 24-48 hours in advance
2. **Enable maintenance mode**: Show maintenance page
3. **Backup database** before changes
4. **Run migrations** during low-traffic period
5. **Validate deployment** with smoke tests
6. **Monitor logs** for 1 hour post-deployment
7. **Disable maintenance mode** after validation

## Cost Optimization

### Railway Pricing

- **Hobby Plan**: $5/month + usage
- **Pro Plan**: $20/month + usage
- **Database**: ~$5-10/month for small database

**Optimization**:
- Use SQLite for development
- Scale down instances during low traffic
- Monitor database size, archive old data

### AWS Pricing Estimate

- **ECS Fargate**: $30-50/month (2 tasks, 0.5 vCPU, 1GB RAM)
- **RDS Postgres**: $50-100/month (db.t3.micro with backups)
- **ElastiCache**: $15-30/month (cache.t3.micro)
- **CloudFront**: $5-20/month (depends on traffic)
- **Total**: ~$100-200/month

**Optimization**:
- Use Reserved Instances for predictable workloads
- Enable auto-scaling to scale down during low traffic
- Use S3 lifecycle policies for old data

## Support and Documentation

- **API Docs**: https://your-backend.railway.app/docs
- **Architecture**: [Architecture Overview](../architecture/overview.md)
- **Development**: [Development Setup](../development/setup.md)
- **Migrations**: [Database Migrations](../../api/DATABASE_MIGRATIONS.md)
- **Status Page**: https://status.your-domain.com (optional)

## Next Steps

After successful deployment:

1. Configure custom domain
2. Set up monitoring and alerts
3. Enable automated backups
4. Create runbook for common issues
5. Train support team on troubleshooting procedures

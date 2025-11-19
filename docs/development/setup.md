# BACOWR Development Setup Guide

## Quick Start

Get BACOWR running locally in 5 minutes:

```bash
# Clone repository
git clone https://github.com/your-org/BACOWR.git
cd BACOWR

# Backend setup
cd api
cp .env.example .env
# Edit .env with your API keys
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# In a new terminal: Frontend setup
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with backend URL
npm run dev
```

Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Prerequisites

### Required Software

| Software | Minimum Version | Recommended | Installation |
|----------|----------------|-------------|--------------|
| Python | 3.11 | 3.11+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18.0 | 20.0+ | [nodejs.org](https://nodejs.org/) |
| Git | 2.0 | Latest | [git-scm.com](https://git-scm.com/) |

### Optional Software

| Software | Purpose | Installation |
|----------|---------|--------------|
| PostgreSQL | Production-like database | [postgresql.org](https://www.postgresql.org/download/) |
| Redis | Rate limiting (testing) | [redis.io](https://redis.io/download/) |
| Docker | Containerized development | [docker.com](https://www.docker.com/get-started/) |

### LLM API Keys

You need at least one LLM provider API key:

- **Anthropic (Claude)**: [console.anthropic.com](https://console.anthropic.com/)
- **OpenAI (GPT)**: [platform.openai.com](https://platform.openai.com/)
- **Google (Gemini)**: [ai.google.dev](https://ai.google.dev/)

## Detailed Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/BACOWR.git
cd BACOWR
```

**Project Structure:**
```
BACOWR/
├── api/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py        # Application entry point
│   │   ├── models/        # Database models
│   │   ├── routes/        # API endpoints
│   │   ├── services/      # Business logic
│   │   └── middleware/    # Auth, rate limiting, audit
│   ├── alembic/           # Database migrations
│   ├── tests/             # Backend tests
│   └── requirements.txt   # Python dependencies
├── frontend/              # Next.js frontend
│   ├── src/app/          # App router pages
│   ├── components/       # React components
│   └── package.json      # Node dependencies
├── docs/                 # Documentation
├── tools/                # Utility scripts
└── README.md
```

### 2. Backend Setup (FastAPI)

#### Install Python Dependencies

```bash
cd api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Common Issues:**

- **Problem**: `pip install` fails with compiler errors
  - **Solution**: Install build tools:
    - macOS: `xcode-select --install`
    - Ubuntu: `sudo apt-get install python3-dev build-essential`
    - Windows: Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/)

- **Problem**: `psycopg2` installation fails
  - **Solution**: Use binary version: `pip install psycopg2-binary`

#### Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit with your preferred editor
nano .env  # or vim, code, etc.
```

**Minimal `.env` for Development:**
```bash
# Database (SQLite for development)
DATABASE_URL=sqlite:///./bacowr.db

# Authentication (generate with: openssl rand -hex 32)
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM Provider (at least one required)
ANTHROPIC_API_KEY=sk-ant-your-key-here
# OPENAI_API_KEY=sk-your-key-here
# GOOGLE_API_KEY=your-key-here

# CORS (for frontend)
FRONTEND_URL=http://localhost:3000

# Debug mode
DEBUG=true
```

**Full `.env` for Production-like Development:**
```bash
# PostgreSQL database
DATABASE_URL=postgresql://bacowr:password@localhost:5432/bacowr_dev

# Redis for rate limiting
REDIS_URL=redis://localhost:6379

# All other variables same as minimal setup
```

#### Initialize Database

```bash
# Run migrations to create tables
alembic upgrade head

# Verify database was created
# For SQLite:
ls -lh bacowr.db

# For PostgreSQL:
psql -h localhost -U bacowr -d bacowr_dev -c "\dt"
```

#### Start Backend Server

```bash
# Start with auto-reload for development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the convenience script
python -m app.main
```

**Expected Output:**
```
======================================================================
BACOWR API Starting...
======================================================================
✓ Database initialized
✓ Default admin user ready
======================================================================
✓ BACOWR API Ready!
  Docs: http://localhost:8000/docs
======================================================================
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

#### Verify Backend

```bash
# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"bacowr-api","version":"1.0.0"}

# View API documentation
open http://localhost:8000/docs  # macOS
# Or navigate to http://localhost:8000/docs in browser
```

### 3. Frontend Setup (Next.js)

Open a **new terminal window** (keep backend running).

#### Install Node Dependencies

```bash
cd frontend

# Install dependencies
npm install

# Or use yarn/pnpm
yarn install
pnpm install
```

**Common Issues:**

- **Problem**: `npm install` hangs or is very slow
  - **Solution**: Clear npm cache: `npm cache clean --force`
  - **Solution**: Try yarn instead: `npm install -g yarn && yarn install`

- **Problem**: `MODULE_NOT_FOUND` errors
  - **Solution**: Delete `node_modules` and reinstall:
    ```bash
    rm -rf node_modules package-lock.json
    npm install
    ```

#### Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env.local

# Edit with your preferred editor
nano .env.local
```

**`.env.local` Configuration:**
```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# WebSocket URL for real-time updates
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1/ws
```

**Note**: `NEXT_PUBLIC_` prefix is required for environment variables accessible in browser.

#### Start Frontend Server

```bash
# Start development server
npm run dev

# Or with specific port
npm run dev -- -p 3001
```

**Expected Output:**
```
▲ Next.js 14.0.0
- Local:        http://localhost:3000
- Network:      http://192.168.1.100:3000

✓ Ready in 2.3s
```

#### Verify Frontend

Navigate to http://localhost:3000 in your browser. You should see the BACOWR interface.

### 4. Verify Full Stack

#### Test Complete Workflow

1. **Create a Job**
   - Navigate to http://localhost:3000/jobs/new
   - Fill in:
     - Link URL: `https://example.com`
     - Context: `Test article about development`
     - Model: Claude 3.5 Sonnet
   - Click "Create Job"

2. **Execute Job**
   - Click "Execute Job" on the created job
   - Watch progress in real-time via WebSocket
   - Wait for completion (15-30 seconds)

3. **Review Output**
   - View generated backlink article
   - Check quality metrics

4. **Create Batch** (optional)
   - Create 2-3 more jobs
   - Navigate to Batches
   - Create batch from completed jobs
   - Test batch review workflow

#### Run Automated Tests

```bash
# Backend tests
cd api
pytest tests/ -v

# Frontend tests (if implemented)
cd frontend
npm test

# E2E tests
cd tests/e2e
pytest test_critical_workflows.py -v

# Smoke test
cd tools
python smoke_test_wave1.py
```

## Development Workflow

### Working on Backend

#### 1. Making Database Changes

When modifying models in `api/app/models/`:

```bash
cd api

# Edit models
vim app/models/database.py

# Generate migration
alembic revision --autogenerate -m "Add new field to User model"

# Review generated migration
vim alembic/versions/<timestamp>_add_new_field_to_user_model.py

# Apply migration
alembic upgrade head

# Test rollback
alembic downgrade -1
alembic upgrade head
```

**Best Practices:**
- Always review auto-generated migrations
- Test both upgrade and downgrade
- Use descriptive migration messages
- One logical change per migration

#### 2. Adding API Endpoints

**File Structure:**
```
api/app/
├── routes/
│   └── new_feature.py      # New route file
├── services/
│   └── new_feature.py      # Business logic
└── models/
    └── schemas.py          # Pydantic schemas
```

**Example: Adding a new endpoint**

1. **Create Pydantic Schema** (`api/app/models/schemas.py`):
```python
class NewFeatureCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
```

2. **Create Service** (`api/app/services/new_feature.py`):
```python
class NewFeatureService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: NewFeatureCreate) -> NewFeature:
        feature = NewFeature(**data.dict())
        self.db.add(feature)
        self.db.commit()
        return feature
```

3. **Create Route** (`api/app/routes/new_feature.py`):
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.new_feature import NewFeatureService
from ..models.schemas import NewFeatureCreate

router = APIRouter(tags=["new-feature"])

@router.post("/new-feature")
def create_feature(
    data: NewFeatureCreate,
    db: Session = Depends(get_db)
):
    service = NewFeatureService(db)
    return service.create(data)
```

4. **Register Router** (`api/app/main.py`):
```python
from .routes import new_feature

app.include_router(new_feature.router, prefix="/api/v1")
```

5. **Test Endpoint**:
```bash
# Start server (auto-reloads)
uvicorn app.main:app --reload

# Test with curl
curl -X POST http://localhost:8000/api/v1/new-feature \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","description":"Testing"}'

# Or use Swagger UI
open http://localhost:8000/docs
```

#### 3. Writing Tests

**Create test file** (`api/tests/test_new_feature.py`):
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_feature():
    response = client.post(
        "/api/v1/new-feature",
        json={"name": "Test Feature", "description": "Testing"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Feature"

def test_create_feature_validation():
    response = client.post(
        "/api/v1/new-feature",
        json={"name": ""}  # Invalid: empty name
    )
    assert response.status_code == 422  # Validation error
```

**Run tests:**
```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_new_feature.py::test_create_feature -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Working on Frontend

#### 1. Creating New Pages

**App Router Structure:**
```
frontend/src/app/
├── layout.tsx              # Root layout
├── page.tsx                # Home page (/)
├── jobs/
│   ├── page.tsx            # Jobs list (/jobs)
│   ├── new/page.tsx        # Create job (/jobs/new)
│   └── [id]/page.tsx       # Job detail (/jobs/:id)
└── new-feature/
    └── page.tsx            # New feature page (/new-feature)
```

**Example: Create a new page**

1. **Create Page File** (`frontend/src/app/new-feature/page.tsx`):
```typescript
'use client';

import { useState, useEffect } from 'react';

export default function NewFeaturePage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/new-feature`)
      .then(res => res.json())
      .then(setData);
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">New Feature</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
```

2. **Test Page**:
Navigate to http://localhost:3000/new-feature

#### 2. Creating Reusable Components

**Component Structure:**
```
frontend/src/components/
├── ui/                     # Base UI components
│   ├── Button.tsx
│   ├── Input.tsx
│   └── Card.tsx
└── features/               # Feature-specific components
    └── NewFeatureForm.tsx
```

**Example: Create a component** (`frontend/src/components/features/NewFeatureForm.tsx`):
```typescript
'use client';

import { useState } from 'react';

interface NewFeatureFormProps {
  onSubmit: (data: { name: string; description: string }) => void;
}

export default function NewFeatureForm({ onSubmit }: NewFeatureFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ name, description });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium">Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full px-3 py-2 border rounded"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full px-3 py-2 border rounded"
        />
      </div>

      <button type="submit" className="px-4 py-2 bg-blue-500 text-white rounded">
        Submit
      </button>
    </form>
  );
}
```

#### 3. API Integration

**Using fetch:**
```typescript
const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/jobs`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ name: 'Test Job' })
});

const data = await response.json();
```

**Using React Query (recommended):**
```typescript
import { useQuery, useMutation } from '@tanstack/react-query';

// Fetch data
const { data, isLoading, error } = useQuery({
  queryKey: ['jobs'],
  queryFn: () => fetch(`${process.env.NEXT_PUBLIC_API_URL}/jobs`).then(r => r.json())
});

// Mutate data
const mutation = useMutation({
  mutationFn: (newJob) => {
    return fetch(`${process.env.NEXT_PUBLIC_API_URL}/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newJob)
    });
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['jobs'] });
  }
});
```

## IDE Setup

### Visual Studio Code

**Recommended Extensions:**
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-typescript-next"
  ]
}
```

**Workspace Settings** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/api/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  }
}
```

**Launch Configuration** (`.vscode/launch.json`):
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "cwd": "${workspaceFolder}/api",
      "env": {
        "DATABASE_URL": "sqlite:///./bacowr.db"
      }
    },
    {
      "name": "Next.js: debug server-side",
      "type": "node",
      "request": "launch",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "cwd": "${workspaceFolder}/frontend",
      "port": 9229,
      "serverReadyAction": {
        "pattern": "started server on .+, url: (https?://.+)",
        "uriFormat": "%s",
        "action": "debugWithChrome"
      }
    }
  ]
}
```

### PyCharm / IntelliJ IDEA

1. **Set Python Interpreter**: `Settings → Project → Python Interpreter`
   - Add interpreter from `api/venv`

2. **Configure Run Configuration**:
   - Script path: `uvicorn`
   - Parameters: `app.main:app --reload`
   - Working directory: `<project>/api`

3. **Enable Django Support** (for better SQLAlchemy support):
   - `Settings → Languages & Frameworks → Django`

## Debugging

### Backend Debugging

#### Using Debugger

**VS Code**: Set breakpoint, press F5

**PyCharm**: Set breakpoint, Run → Debug

**Manual**:
```python
# Add to code
import pdb; pdb.set_trace()

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()
```

#### Logging

```python
import logging

logger = logging.getLogger(__name__)

# In your code
logger.info(f"Processing job {job_id}")
logger.error(f"Failed to generate content: {error}")
logger.debug(f"Request data: {request_data}")
```

**View logs:**
```bash
# Backend logs are written to console
# Set log level in .env
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

### Frontend Debugging

#### Browser DevTools

1. **Console**: View logs and errors
2. **Network**: Inspect API requests
3. **React DevTools**: Inspect component tree and state

#### Debugging in VS Code

1. Set breakpoint in TypeScript file
2. Launch "Next.js: debug server-side"
3. Debugger will attach when breakpoint is hit

## Database Management

### SQLite (Development)

**View Database:**
```bash
# Install SQLite browser
brew install --cask db-browser-for-sqlite  # macOS
# Or download from https://sqlitebrowser.org/

# Open database
open bacowr.db  # macOS
# Or use sqlite3 command line
sqlite3 bacowr.db

# View schema
.schema

# Query data
SELECT * FROM users;
SELECT * FROM jobs LIMIT 10;

# Exit
.quit
```

### PostgreSQL (Production-like)

**Install PostgreSQL:**
```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu
sudo apt-get install postgresql-15
sudo systemctl start postgresql

# Windows: Download from postgresql.org
```

**Create Development Database:**
```bash
# Create user
createuser bacowr -P  # Enter password when prompted

# Create database
createdb bacowr_dev -O bacowr

# Update .env
DATABASE_URL=postgresql://bacowr:password@localhost:5432/bacowr_dev

# Run migrations
cd api && alembic upgrade head
```

**View Database:**
```bash
# Command line
psql -h localhost -U bacowr -d bacowr_dev

# List tables
\dt

# Query data
SELECT * FROM users;

# Exit
\q

# GUI: Use pgAdmin or DBeaver
```

## Troubleshooting

### Backend Issues

#### Issue: `ModuleNotFoundError: No module named 'app'`

**Solution**: Ensure you're in the `api` directory and virtual environment is activated:
```bash
cd api
source venv/bin/activate  # or venv\Scripts\activate on Windows
python -m uvicorn app.main:app --reload
```

#### Issue: Database connection errors

**Solution**: Check DATABASE_URL and database is running:
```bash
# For PostgreSQL
pg_isready -h localhost

# For SQLite, ensure file path is correct
ls -l bacowr.db
```

#### Issue: Migration conflicts

**Solution**: Reset database (development only):
```bash
# SQLite
rm bacowr.db
alembic upgrade head

# PostgreSQL
dropdb bacowr_dev && createdb bacowr_dev -O bacowr
alembic upgrade head
```

### Frontend Issues

#### Issue: API calls fail with CORS errors

**Solution**: Ensure `FRONTEND_URL` in backend `.env` matches frontend URL:
```bash
# Backend .env
FRONTEND_URL=http://localhost:3000

# Restart backend after changing
```

#### Issue: Environment variables not working

**Solution**: Ensure variables are prefixed with `NEXT_PUBLIC_` and restart dev server:
```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Restart
npm run dev
```

#### Issue: Hot reload not working

**Solution**:
```bash
# Clear Next.js cache
rm -rf .next

# Restart
npm run dev
```

## Performance Optimization (Development)

### Backend

**Enable SQL logging** (see what queries are running):
```python
# In app/database.py
engine = create_engine(
    DATABASE_URL,
    echo=True  # Prints all SQL queries
)
```

**Profile slow endpoints:**
```bash
# Install py-spy
pip install py-spy

# Profile running server
py-spy top --pid <uvicorn-pid>

# Record flamegraph
py-spy record -o profile.svg --pid <uvicorn-pid>
```

### Frontend

**Analyze bundle size:**
```bash
# Install analyzer
npm install --save-dev @next/bundle-analyzer

# Analyze
ANALYZE=true npm run build
```

**Check for unnecessary re-renders:**
```bash
# Install React DevTools Profiler
# Then record interactions and analyze
```

## Contributing

### Code Style

**Backend (Python):**
- Follow PEP 8
- Use Black for formatting: `black api/`
- Use Pylint for linting: `pylint api/app/`
- Maximum line length: 100 characters

**Frontend (TypeScript):**
- Follow Airbnb style guide
- Use Prettier for formatting: `npm run format`
- Use ESLint for linting: `npm run lint`
- Maximum line length: 100 characters

### Commit Messages

Follow Conventional Commits:

```
feat(jobs): Add batch export functionality
fix(auth): Resolve token expiration bug
docs(api): Update endpoint documentation
test(jobs): Add E2E test for job creation
refactor(database): Optimize query performance
```

### Pull Request Process

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit
3. Push to remote: `git push origin feature/my-feature`
4. Create pull request on GitHub
5. Wait for CI tests to pass
6. Request review from team
7. Address feedback and merge

## Next Steps

- **Read**: [Architecture Overview](../architecture/overview.md)
- **Deploy**: [Production Deployment](../deployment/production.md)
- **Contribute**: Check open issues on GitHub
- **Learn**: Explore the codebase and documentation

## Getting Help

- **Documentation**: Check `/docs` directory
- **API Docs**: http://localhost:8000/docs
- **Issues**: Report bugs on GitHub
- **Discussions**: Ask questions in GitHub Discussions

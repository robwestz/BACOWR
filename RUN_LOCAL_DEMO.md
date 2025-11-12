# BACOWR - Lokal Demo Setup

## Snabbstart (5 minuter)

### 1. Klona Repo
```bash
git clone https://github.com/robwestz/BACOWR.git
cd BACOWR
git checkout claude/separate-test-environment-011CV3e57XWWzEgYJ47Vxxm8
```

### 2. Installera Dependencies

**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

### 3. Sätt API Keys

Skapa `.env` fil:
```bash
cat > .env << EOF
# LLM Providers (minst en krävs)
ANTHROPIC_API_KEY=sk-ant-your-key-here
# OPENAI_API_KEY=sk-proj-your-key-here  # Optional
# GOOGLE_API_KEY=your-key-here           # Optional

# SERP Research (optional, mock data används annars)
# SERPAPI_KEY=your-serpapi-key

# Database
DATABASE_URL=sqlite:///./bacowr.db

# API Settings
SECRET_KEY=your-secret-key-here
FRONTEND_URL=http://localhost:3000
EOF
```

### 4. Starta Backend

Terminal 1:
```bash
cd api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Öppnas på: http://localhost:8000/docs (Swagger UI)

### 5. Starta Frontend

Terminal 2:
```bash
cd frontend
npm run dev
```

Öppnas på: http://localhost:3000

### 6. Öppna i Webbläsare

Gå till: **http://localhost:3000**

Default login:
- Email: `admin@bacowr.local`
- Password: `admin123`

---

## Snabb Test (Endast Demo Script)

Om du bara vill se demon utan att starta web-applikationen:

```bash
# Sätt API key
export ANTHROPIC_API_KEY="demo_key"

# Kör demo
python demo_for_management.py
```

---

## Troubleshooting

**Port redan i bruk:**
```bash
# Backend på annan port
uvicorn app.main:app --reload --port 8001

# Frontend på annan port
npm run dev -- -p 3001
```

**Dependencies saknas:**
```bash
# Backend
pip install fastapi uvicorn sqlalchemy anthropic openai google-generativeai

# Frontend
cd frontend && npm install
```

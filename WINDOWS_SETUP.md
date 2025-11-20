# 🚀 BACOWR - Windows Setup Guide

Quick start guide for Windows users.

## ⚡ Quick Start (One Command)

Open **PowerShell** (or Windows Terminal) and run:

```powershell
cd C:\Users\robin\PycharmProjects\BACOWR
.\start_bacowr.ps1
```

**That's it!** The script will:
- ✅ Set up everything automatically
- ✅ Start backend and frontend
- ✅ Open your browser

**Login with:**
- Email: `admin@bacowr.local`
- Password: `admin123`

---

## ⚠️ PowerShell Execution Policy

If you get an error about execution policy, run this first:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try again:
```powershell
.\start_bacowr.ps1
```

---

## 🐛 Troubleshooting

### Error: "Cannot be loaded because running scripts is disabled"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\start_bacowr.ps1
```

### Error: "Missing closing '}' in statement block"

This is an issue with your PowerShell profile. To temporarily bypass it:

```powershell
# Start PowerShell without profile
powershell -NoProfile

# Then navigate and run
cd C:\Users\robin\PycharmProjects\BACOWR
.\start_bacowr.ps1
```

**To fix permanently**, edit your profile:
```powershell
notepad $PROFILE
```
Find the `Show-PSHelp` function around line 143 and make sure it has a closing `}`.

### Backend won't start

```powershell
cd api
python -m pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
```

### Frontend won't start

```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
npm install
npm run dev
```

### Port already in use

```powershell
# Kill processes on port 8000
Get-NetTCPConnection -LocalPort 8000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Kill processes on port 3000
Get-NetTCPConnection -LocalPort 3000 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

---

## 🎯 Manual Setup (Alternative)

### Backend

**Terminal 1 (PowerShell):**
```powershell
cd C:\Users\robin\PycharmProjects\BACOWR\api

# Create .env file
@"
DATABASE_URL=sqlite:///./bacowr.db
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
FRONTEND_URL=http://localhost:3000
DEBUG=true
"@ | Out-File -FilePath .env -Encoding UTF8

# Install dependencies
python -m pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start backend
python -m uvicorn app.main:app --reload
```

### Frontend

**Terminal 2 (PowerShell):**
```powershell
cd C:\Users\robin\PycharmProjects\BACOWR\frontend

# Create .env.local
"NEXT_PUBLIC_API_URL=http://localhost:8000" | Out-File -FilePath .env.local -Encoding UTF8

# Install dependencies (first time only)
npm install

# Start frontend
npm run dev
```

**Open:** http://localhost:3000

---

## 🛑 Stop Services

**If using start_bacowr.ps1:**
- Press `Ctrl+C` in the PowerShell window

**If running manually:**
- Press `Ctrl+C` in both terminal windows

**Force kill:**
```powershell
# Find and kill processes
Get-Process | Where-Object {$_.ProcessName -like "*uvicorn*"} | Stop-Process -Force
Get-Process | Where-Object {$_.ProcessName -like "*node*"} | Stop-Process -Force
```

---

## 📝 What You Get

After running `start_bacowr.ps1`, you'll have:

- ✅ Backend API running on http://localhost:8000
- ✅ Frontend UI running on http://localhost:3000
- ✅ Database initialized with demo user
- ✅ All dependencies installed
- ✅ Browser opened automatically

**Login:**
- Email: `admin@bacowr.local`
- Password: `admin123`

---

## 🎮 Next Steps

1. **Login** at http://localhost:3000
2. **Create a job** - Test single article generation
3. **Create a batch** - Test batch workflow
4. **Review batch** - Use the QA interface
5. **Check your quota** - Click your avatar in the header

---

## 💡 Tips

### Use Windows Terminal
For better experience, use [Windows Terminal](https://aka.ms/terminal) instead of old PowerShell.

### Keep terminals open
Don't close the PowerShell windows while services are running.

### Check logs
If something goes wrong, check:
- Backend logs in the first terminal
- Frontend logs in the second terminal

### Python virtual environment
If you have a virtual environment, activate it first:
```powershell
.\.venv\Scripts\Activate.ps1
.\start_bacowr.ps1
```

---

## 🔗 More Information

- **Full Documentation:** `COMPLETE_AUTH_SETUP.md`
- **API Docs:** http://localhost:8000/docs (when running)
- **Production Deployment:** `docs/deployment/production.md`

---

## ❓ Need Help?

1. Check backend is running: `curl http://localhost:8000/health`
2. Check frontend is running: `curl http://localhost:3000`
3. Review the error messages in the terminal
4. Try manual setup if automated script fails

**Common Issues:**
- Port 8000 or 3000 already in use → Kill the process
- Missing dependencies → Run pip/npm install manually
- Database errors → Delete `api/bacowr.db` and run migrations again

---

**🎉 You're all set! Enjoy using BACOWR!**

#!/usr/bin/env python3
"""
BACOWR Demo Setup

Förbereder allt som behövs för att köra demo.
Kör denna fil FÖRST, sen kör start_demo.py
"""

import subprocess
import os
from pathlib import Path

def run_cmd(cmd, cwd=None):
    """Kör kommando och visa output."""
    print(f"➤ {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=False)
    if result.returncode != 0:
        print(f"⚠ Varning: Kommando misslyckades (kan vara OK)")
    return result.returncode == 0

def main():
    root = Path(__file__).parent
    api_dir = root / "api"
    frontend_dir = root / "frontend"

    print("=" * 70)
    print("BACOWR DEMO SETUP")
    print("=" * 70)
    print()

    # 1. Installera Python dependencies för API
    print("\n[1/5] Installerar Python dependencies för API...")
    run_cmd("pip install -q -r requirements.txt", cwd=api_dir)

    # 2. Skapa .env för API
    print("\n[2/5] Skapar .env för API...")
    env_file = api_dir / ".env"
    env_example = api_dir / ".env.example"

    if not env_file.exists():
        # Kopiera från .env.example
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("✓ .env skapad från .env.example")
            print()
            print("⚠️  VIKTIGT: Lägg till din ANTHROPIC_API_KEY i api/.env")
            print("   Öppna filen och ersätt 'sk-ant-api03-...' med din riktiga nyckel")
        else:
            # Fallback: skapa minimal .env
            with open(env_file, "w") as f:
                f.write(f"""# BACOWR API Configuration
DATABASE_URL=sqlite:///{api_dir}/bacowr.db
FRONTEND_URL=http://localhost:3000
ANTHROPIC_API_KEY=din-api-nyckel-här
DEBUG=true
HOST=0.0.0.0
PORT=8000
""")
            print("✓ .env skapad")
            print()
            print("⚠️  VIKTIGT: Lägg till din ANTHROPIC_API_KEY i api/.env")
    else:
        print("✓ .env finns redan")

    # 3. Installera npm dependencies för frontend
    print("\n[3/5] Installerar npm dependencies för frontend...")
    print("(Detta kan ta någon minut första gången...)")
    run_cmd("npm install", cwd=frontend_dir)

    # 4. Skapa .env.local för frontend
    print("\n[4/5] Skapar .env.local för frontend...")
    env_local = frontend_dir / ".env.local"
    if not env_local.exists():
        with open(env_local, "w") as f:
            f.write("""# BACOWR Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
""")
        print("✓ .env.local skapad")
    else:
        print("✓ .env.local finns redan")

    # 5. Bygg frontend (optional - kan ta tid)
    # print("\n[5/5] Bygger frontend...")
    # run_cmd("npm run build", cwd=frontend_dir)

    print("\n" + "=" * 70)
    print("✅ SETUP KLAR!")
    print("=" * 70)
    print()
    print("Nästa steg:")
    print("  1. Kör: python start_demo.py")
    print("  2. Öppna: http://localhost:3000")
    print()
    print("=" * 70)

if __name__ == "__main__":
    main()

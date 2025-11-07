#!/usr/bin/env python3
"""
BACOWR Demo Starter

Startar både API backend och Next.js frontend samtidigt.

Användning:
  python start_demo.py

Tryck Ctrl+C för att stoppa båda.
"""

import subprocess
import sys
import time
import signal
from pathlib import Path
from threading import Thread

# Global för att hålla koll på processer
processes = []

def signal_handler(sig, frame):
    """Hantera Ctrl+C och stoppa alla processer."""
    print("\n\n⏹ Stoppar alla tjänster...")
    for p in processes:
        if p.poll() is None:  # Om processen fortfarande kör
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
    print("✓ Alla tjänster stoppade")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def run_api():
    """Starta API backend."""
    root = Path(__file__).parent
    api_dir = root / "api"

    print("🔧 Startar API backend...")

    # Sätt environment variables
    env = {
        **subprocess.os.environ,
        "PYTHONPATH": str(root)
    }

    p = subprocess.Popen(
        [sys.executable, "-m", "app.main"],
        cwd=api_dir,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    processes.append(p)

    # Visa output
    for line in p.stdout:
        print(f"[API] {line}", end='')

        # Leta efter API-nyckel i output
        if "API Key:" in line:
            print("\n" + "=" * 70)
            print("⚠️  SPARA DENNA API-NYCKEL!")
            print("=" * 70)

def run_frontend():
    """Starta Next.js frontend."""
    root = Path(__file__).parent
    frontend_dir = root / "frontend"

    # Vänta lite så API hinner starta först
    time.sleep(3)

    print("\n🎨 Startar Next.js frontend...")

    p = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    processes.append(p)

    # Visa output
    for line in p.stdout:
        print(f"[Frontend] {line}", end='')

def main():
    root = Path(__file__).parent

    print("=" * 70)
    print("BACOWR DEMO")
    print("=" * 70)
    print()

    # Kolla att setup är gjord
    if not (root / "api" / ".env").exists():
        print("❌ Fel: API .env saknas!")
        print()
        print("Kör först:")
        print("  python setup_demo.py")
        print()
        sys.exit(1)

    if not (root / "frontend" / "node_modules").exists():
        print("❌ Fel: Frontend dependencies saknas!")
        print()
        print("Kör först:")
        print("  python setup_demo.py")
        print()
        sys.exit(1)

    print("✓ Setup verifierad")
    print()
    print("Startar tjänster...")
    print("(Tryck Ctrl+C för att stoppa)")
    print()
    print("-" * 70)
    print()

    # Starta API i egen tråd
    api_thread = Thread(target=run_api, daemon=True)
    api_thread.start()

    # Vänta lite
    time.sleep(2)

    # Starta frontend i huvudtråden (så vi kan visa output)
    try:
        run_frontend()
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()

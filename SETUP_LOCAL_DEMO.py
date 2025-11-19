#!/usr/bin/env python3
"""
BACOWR Demo Setup - Automatisk Fork & Installation
Kör detta script för att sätta upp en lokal demo-miljö (rör ej original-repo!)
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Print setup banner."""
    print("\n" + "=" * 70)
    print("  BACOWR DEMO SETUP - Automatisk Installation")
    print("=" * 70 + "\n")

def run_command(cmd, cwd=None, check=True):
    """Run shell command and return result."""
    print(f"  → {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )

    if check and result.returncode != 0:
        print(f"    ❌ ERROR: {result.stderr}")
        return False

    return True

def check_requirements():
    """Check if required tools are installed."""
    print("🔍 Checking requirements...")

    required = {
        'git': 'git --version',
        'python': 'python --version',
    }

    for tool, cmd in required.items():
        result = subprocess.run(cmd, shell=True, capture_output=True)
        if result.returncode != 0:
            print(f"  ❌ {tool} is not installed!")
            print(f"     Install it first: https://git-scm.com/ or https://python.org/")
            return False
        print(f"  ✓ {tool} found")

    return True

def setup_demo():
    """Main setup function."""
    print_banner()

    # 1. Check requirements
    if not check_requirements():
        sys.exit(1)

    # 2. Choose demo directory
    print("\n📁 Setup directory:")

    home_dir = Path.home()
    default_location = home_dir / "BACOWR-demo"

    print(f"\n  Default location: {default_location}")
    custom = input("  Use this location? (y/n): ").strip().lower()

    if custom == 'n':
        custom_path = input("  Enter custom path: ").strip()
        demo_dir = Path(custom_path)
    else:
        demo_dir = default_location

    # Check if already exists
    if demo_dir.exists():
        print(f"\n  ⚠️  Directory already exists: {demo_dir}")
        overwrite = input("  Delete and re-setup? (y/n): ").strip().lower()
        if overwrite == 'y':
            print("  🗑️  Removing old installation...")
            shutil.rmtree(demo_dir)
        else:
            print("  ℹ️  Using existing directory")

    # 3. Clone repository
    if not demo_dir.exists():
        print(f"\n📦 Cloning BACOWR to: {demo_dir}")
        print("  (This creates a LOCAL COPY - won't affect original repo)")

        clone_cmd = f'git clone https://github.com/robwestz/BACOWR.git "{demo_dir}"'
        if not run_command(clone_cmd):
            print("\n❌ Failed to clone repository!")
            sys.exit(1)

    # 4. Checkout demo branch
    print("\n🔀 Checking out demo branch...")
    branch_cmd = 'git checkout claude/separate-test-environment-011CV3e57XWWzEgYJ47Vxxm8'
    if not run_command(branch_cmd, cwd=demo_dir):
        print("  ⚠️  Branch checkout failed, using current branch")

    # 5. Create virtual environment
    venv_path = demo_dir / "venv"
    if not venv_path.exists():
        print("\n🐍 Creating Python virtual environment...")
        venv_cmd = f'python -m venv "{venv_path}"'
        if not run_command(venv_cmd, cwd=demo_dir):
            print("\n❌ Failed to create virtual environment!")
            sys.exit(1)

    # 6. Install dependencies
    print("\n📚 Installing Python dependencies...")
    print("  (This may take 2-3 minutes...)")

    # Determine pip path
    if sys.platform == "win32":
        pip_path = venv_path / "Scripts" / "pip.exe"
    else:
        pip_path = venv_path / "bin" / "pip"

    install_cmd = f'"{pip_path}" install -q -r requirements.txt'
    if not run_command(install_cmd, cwd=demo_dir, check=False):
        print("  ⚠️  Some packages failed, trying essential ones...")
        essential = [
            'fastapi', 'uvicorn', 'sqlalchemy', 'pydantic',
            'python-dotenv', 'requests', 'beautifulsoup4', 'lxml'
        ]
        for pkg in essential:
            run_command(f'"{pip_path}" install -q {pkg}', cwd=demo_dir, check=False)

    # 7. Create .env file
    env_file = demo_dir / ".env"
    if not env_file.exists():
        print("\n⚙️  Creating .env configuration...")
        env_content = """# BACOWR Demo Configuration

# LLM Providers (minst en krävs för RIKTIGA tester)
# För DEMO: Lämna som "demo_key" - scriptet kommer använda mock data
ANTHROPIC_API_KEY=demo_key
# OPENAI_API_KEY=demo_key
# GOOGLE_API_KEY=demo_key

# SERP API (optional)
SERPAPI_KEY=demo_key

# Database
DATABASE_URL=sqlite:///./bacowr.db

# API Settings
SECRET_KEY=demo-secret-key-change-in-production
FRONTEND_URL=http://localhost:3000
API_HOST=0.0.0.0
API_PORT=8000

# INSTRUKTIONER:
# För att testa med RIKTIGA API:er, ersätt "demo_key" ovan med:
# - Anthropic key från: https://console.anthropic.com/settings/keys
# - OpenAI key från: https://platform.openai.com/api-keys
# - Google key från: https://aistudio.google.com/app/apikey
# - SerpAPI key från: https://serpapi.com/manage-api-key
"""
        env_file.write_text(env_content)
        print("  ✓ .env file created (using demo keys)")

    # 8. Create demo runner script
    print("\n📝 Creating demo runner script...")

    demo_runner = demo_dir / "RUN_DEMO_FOR_BOSSES.py"
    demo_runner_content = '''#!/usr/bin/env python3
"""
BACOWR Demo - För Chefspresentation
Kör detta script för att visa demon!
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run the demo."""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "BACOWR BACKLINK CONTENT WRITER" + " " * 22 + "║")
    print("║" + " " * 18 + "Demo för Cheferna" + " " * 30 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    print("Välj demo-typ:")
    print()
    print("  1. Snabb Overview (5 min)")
    print("     → Visa arkitektur, QC-kriterier, costs")
    print()
    print("  2. Interaktiv Demo (15 min)")
    print("     → Skapa jobb, utforska system")
    print()
    print("  3. Kör alla tester (2 min)")
    print("     → Visa att allt fungerar")
    print()

    choice = input("Välj (1-3): ").strip()
    print()

    if choice == '1':
        print("🚀 Startar Management Overview...")
        print()
        subprocess.run([sys.executable, "demo_for_management.py"])

    elif choice == '2':
        print("🎮 Startar Interaktiv Demo...")
        print()
        subprocess.run([sys.executable, "interactive_demo.py"])

    elif choice == '3':
        print("🧪 Kör Test Suite...")
        print()
        subprocess.run([sys.executable, "tests/test_core_services.py"])

    else:
        print("❌ Ogiltigt val")
        return

    print()
    print("✅ Demo klar!")
    print()
    input("Tryck Enter för att avsluta...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\\n\\n👋 Demo avbruten.\\n")
        sys.exit(0)
'''
    demo_runner.write_text(demo_runner_content)

    # Make executable on Unix
    if sys.platform != "win32":
        os.chmod(demo_runner, 0o755)

    # 9. Test installation
    print("\n🧪 Testing installation...")

    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"

    test_cmd = f'"{python_path}" -c "import fastapi; import sqlalchemy; print(\'✓ Core packages work\')"'
    if run_command(test_cmd, cwd=demo_dir, check=False):
        print("  ✓ Installation verified!")
    else:
        print("  ⚠️  Some packages may not be installed correctly")

    # 10. Success!
    print("\n" + "=" * 70)
    print("  ✅ SETUP KLAR!")
    print("=" * 70)

    print(f"""
📁 Demo installerat i: {demo_dir}

🚀 FÖR ATT VISA CHEFERNA:

   1. Öppna PyCharm
   2. File → Open → Välj: {demo_dir}
   3. PyCharm kommer hitta venv automatiskt
   4. Högerklicka på: RUN_DEMO_FOR_BOSSES.py
   5. Välj: "Run 'RUN_DEMO_FOR_BOSSES'"

   ELLER i terminal:

   cd "{demo_dir}"
   {"venv\\\\Scripts\\\\activate" if sys.platform == "win32" else "source venv/bin/activate"}
   python RUN_DEMO_FOR_BOSSES.py

💡 TIPS:

   - För snabb overview: Välj option 1
   - För interaktiv demo: Välj option 2
   - Allt körs lokalt, ingen risk att röra original-repo!

📝 För att använda RIKTIGA API keys:

   Redigera: {demo_dir}/.env
   Ersätt "demo_key" med dina riktiga keys från:
   - Anthropic: https://console.anthropic.com/settings/keys
   - OpenAI: https://platform.openai.com/api-keys

🎬 LYCKA TILL MED PRESENTATIONEN!
""")

    # Offer to open in PyCharm (if on Mac/Linux)
    if sys.platform != "win32":
        open_pycharm = input("\nÖppna i PyCharm nu? (y/n): ").strip().lower()
        if open_pycharm == 'y':
            subprocess.run(f'open -a PyCharm "{demo_dir}"', shell=True)

if __name__ == "__main__":
    try:
        setup_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Setup avbruten.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

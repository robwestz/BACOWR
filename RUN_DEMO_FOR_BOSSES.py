#!/usr/bin/env python3
"""
LEGACY SCRIPT - DEPRECATED

This script is kept for backward compatibility but is no longer the recommended way to run BACOWR.

Please use the new unified entry point instead:
  python run_bacowr.py --mode demo

---

BACOWR Demo - För Chefspresentation
Kör detta script för att visa demon!

ANVÄNDNING:
  python RUN_DEMO_FOR_BOSSES.py

FÖRUTSÄTTNINGAR:
  - Har du kört SETUP_LOCAL_DEMO.py? Om nej, gör det först!
  - Eller bara installerat requirements.txt manuellt
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run the demo."""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "BACOWR BACKLINK CONTENT WRITER" + " " * 22 + "║")
    print("║" + " " * 18 + "Demo för Cheferna" + " " * 30 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # Check if we're in the right directory
    if not Path("demo_for_management.py").exists():
        print("❌ ERROR: Kan inte hitta demo-filer!")
        print()
        print("Du måste köra detta script från BACOWR projekt-mappen.")
        print()
        input("Tryck Enter för att avsluta...")
        sys.exit(1)

    print("Välj demo-typ:")
    print()
    print("  1. 📊 Snabb Overview (5 min)")
    print("     → Visa arkitektur, QC-kriterier, costs")
    print("     → Perfekt för snabb presentation")
    print()
    print("  2. 🎮 Interaktiv Demo (15 min)")
    print("     → Skapa jobb, utforska system")
    print("     → Bra för att visa funktionalitet i detalj")
    print()
    print("  3. 🧪 Kör alla tester (2 min)")
    print("     → Visa att allt fungerar")
    print("     → Teknisk trovärdighet")
    print()
    print("  4. ❌ Avsluta")
    print()

    choice = input("Välj (1-4): ").strip()
    print()

    if choice == '1':
        print("🚀 Startar Management Overview...")
        print("-" * 70)
        print()
        result = subprocess.run([sys.executable, "demo_for_management.py"])
        success = result.returncode == 0

    elif choice == '2':
        print("🎮 Startar Interaktiv Demo...")
        print("-" * 70)
        print()
        result = subprocess.run([sys.executable, "interactive_demo.py"])
        success = result.returncode == 0

    elif choice == '3':
        print("🧪 Kör Test Suite...")
        print("-" * 70)
        print()
        # Set mock env vars
        env = os.environ.copy()
        env['ANTHROPIC_API_KEY'] = 'demo_key'
        env['SERPAPI_KEY'] = 'demo_key'

        result = subprocess.run(
            [sys.executable, "tests/test_core_services.py"],
            env=env
        )
        success = result.returncode == 0

    elif choice == '4':
        print("👋 Avslutar...")
        return

    else:
        print("❌ Ogiltigt val")
        input("\nTryck Enter för att avsluta...")
        return

    # Show results
    print()
    print("=" * 70)
    if success:
        print("  ✅ Demo kördes utan problem!")
    else:
        print("  ⚠️  Demo avslutades (kan vara normalt)")
    print("=" * 70)
    print()

    # Ask if they want to run another
    again = input("Vill du köra en till demo? (y/n): ").strip().lower()
    if again == 'y':
        print()
        main()  # Recursive call to run again
    else:
        print()
        print("👋 Tack för att du använde BACOWR!")
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo avbruten.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        input("\nTryck Enter för att avsluta...")
        sys.exit(1)

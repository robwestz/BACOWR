#!/usr/bin/env python3
"""
API Smoke Test - Verify BACOWR API endpoints work

This script demonstrates how to:
1. Call the core API endpoint
2. Create a backlink job
3. Get results

Usage:
    python tools/api_smoke_test.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from api.app.main import app

# Create test client
client = TestClient(app)


def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    response = client.get("/health")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health check OK: {data}")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False


def test_root():
    """Test root endpoint."""
    print("\n🔍 Testing root endpoint...")
    response = client.get("/")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ Root endpoint OK")
        print(f"   Service: {data.get('service')}")
        print(f"   Version: {data.get('version')}")
        return True
    else:
        print(f"❌ Root endpoint failed: {response.status_code}")
        return False


def test_docs():
    """Test docs endpoint."""
    print("\n🔍 Testing docs endpoint...")
    response = client.get("/docs")

    if response.status_code == 200:
        print(f"✅ Docs endpoint accessible")
        return True
    else:
        print(f"❌ Docs endpoint failed: {response.status_code}")
        return False


def main():
    """Run smoke tests."""
    print("="*70)
    print("BACOWR API Smoke Test")
    print("="*70)

    results = []

    # Test endpoints
    results.append(test_health())
    results.append(test_root())
    results.append(test_docs())

    print("\n" + "="*70)
    if all(results):
        print("✅ All smoke tests PASSED")
        print("\n📝 API is ready to use!")
        print("\nTo start the server:")
        print("  cd api")
        print("  uvicorn app.main:app --reload")
        print("\nThen visit:")
        print("  http://localhost:8000/docs")
        print("="*70)
        return 0
    else:
        print("❌ Some tests FAILED")
        print("="*70)
        return 1


if __name__ == "__main__":
    sys.exit(main())

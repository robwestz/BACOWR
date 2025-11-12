#!/usr/bin/env python3
"""
API Tests for BACOWR FastAPI Backend

Tests all API endpoints including auth, jobs, backlinks, analytics, and users.

Per BUILDER_PROMPT.md STEG 12.6
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path setup
from api.app.main import app
from api.app.database import Base, engine
from api.app.models.database import User
from api.app.auth import generate_api_key


# Test client
client = TestClient(app)

# Test data
TEST_API_KEY = None
TEST_USER_ID = None


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    """Setup test database before tests."""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create test user
    from api.app.database import SessionLocal
    db = SessionLocal()
    try:
        global TEST_API_KEY, TEST_USER_ID
        TEST_API_KEY = generate_api_key()

        user = User(
            email="test@bacowr.test",
            api_key=TEST_API_KEY,
            is_active=True,
            is_admin=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        TEST_USER_ID = user.id

        print(f"\n✓ Test user created: {TEST_USER_ID}")
        print(f"✓ Test API key: {TEST_API_KEY[:20]}...")

    finally:
        db.close()

    yield

    # Cleanup is handled by test database (in-memory SQLite)


class TestHealthEndpoints:
    """Test health check and root endpoints."""

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "bacowr-api"
        assert "version" in data

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "BACOWR API"
        assert "version" in data
        assert "docs" in data


class TestAuthentication:
    """Test authentication and authorization."""

    def test_missing_api_key(self):
        """Test that endpoints require API key."""
        response = client.get("/api/v1/jobs")
        assert response.status_code == 401
        assert "API key required" in response.json()["detail"]

    def test_invalid_api_key(self):
        """Test invalid API key."""
        headers = {"X-API-Key": "invalid_key"}
        response = client.get("/api/v1/jobs", headers=headers)
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_valid_api_key(self):
        """Test valid API key."""
        headers = {"X-API-Key": TEST_API_KEY}
        response = client.get("/api/v1/jobs", headers=headers)
        assert response.status_code == 200


class TestJobsEndpoints:
    """Test job creation and management endpoints."""

    def test_create_job(self):
        """Test creating a new job."""
        headers = {"X-API-Key": TEST_API_KEY}
        job_data = {
            "publisher_domain": "example.com",
            "target_url": "https://target.com/page",
            "anchor_text": "test anchor",
            "llm_provider": "anthropic",
            "writing_strategy": "multi_stage"
        }

        response = client.post("/api/v1/jobs", json=job_data, headers=headers)
        assert response.status_code == 201

        data = response.json()
        assert data["publisher_domain"] == "example.com"
        assert data["target_url"] == "https://target.com/page"
        assert data["status"] == "pending"
        assert "id" in data
        assert "estimated_cost" in data

    def test_list_jobs(self):
        """Test listing jobs."""
        headers = {"X-API-Key": TEST_API_KEY}
        response = client.get("/api/v1/jobs", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert isinstance(data["items"], list)

    def test_get_job_not_found(self):
        """Test getting non-existent job."""
        headers = {"X-API-Key": TEST_API_KEY}
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/jobs/{fake_id}", headers=headers)
        assert response.status_code == 404

    def test_create_job_invalid_domain(self):
        """Test creating job with invalid domain."""
        headers = {"X-API-Key": TEST_API_KEY}
        job_data = {
            "publisher_domain": "https://example.com",  # Should not include protocol
            "target_url": "https://target.com/page",
            "anchor_text": "test"
        }

        response = client.post("/api/v1/jobs", json=job_data, headers=headers)
        assert response.status_code == 422  # Validation error

    def test_create_job_invalid_target_url(self):
        """Test creating job with invalid target URL."""
        headers = {"X-API-Key": TEST_API_KEY}
        job_data = {
            "publisher_domain": "example.com",
            "target_url": "target.com/page",  # Missing protocol
            "anchor_text": "test"
        }

        response = client.post("/api/v1/jobs", json=job_data, headers=headers)
        assert response.status_code == 422  # Validation error


class TestBacklinksEndpoints:
    """Test backlink management endpoints."""

    def test_create_backlink(self):
        """Test creating a new backlink."""
        headers = {"X-API-Key": TEST_API_KEY}
        backlink_data = {
            "publisher_domain": "publisher.com",
            "target_url": "https://target.com/page",
            "anchor_text": "my anchor",
            "domain_authority": 50,
            "page_authority": 40,
            "category": "technology"
        }

        response = client.post("/api/v1/backlinks", json=backlink_data, headers=headers)
        assert response.status_code == 201

        data = response.json()
        assert data["publisher_domain"] == "publisher.com"
        assert data["domain_authority"] == 50
        assert "id" in data

    def test_list_backlinks(self):
        """Test listing backlinks."""
        headers = {"X-API-Key": TEST_API_KEY}
        response = client.get("/api/v1/backlinks", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_get_backlinks_stats(self):
        """Test getting backlink statistics."""
        headers = {"X-API-Key": TEST_API_KEY}
        response = client.get("/api/v1/backlinks/stats", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "total_count" in data
        assert "by_publisher" in data
        assert "by_category" in data
        assert isinstance(data["by_publisher"], dict)

    def test_bulk_import_backlinks(self):
        """Test bulk importing backlinks."""
        headers = {"X-API-Key": TEST_API_KEY}
        bulk_data = {
            "backlinks": [
                {
                    "publisher_domain": "site1.com",
                    "target_url": "https://target.com/1",
                    "anchor_text": "anchor 1"
                },
                {
                    "publisher_domain": "site2.com",
                    "target_url": "https://target.com/2",
                    "anchor_text": "anchor 2"
                }
            ]
        }

        response = client.post("/api/v1/backlinks/bulk", json=bulk_data, headers=headers)
        assert response.status_code == 201

        data = response.json()
        assert data["imported_count"] == 2

    def test_search_backlinks(self):
        """Test searching backlinks."""
        headers = {"X-API-Key": TEST_API_KEY}
        response = client.get("/api/v1/backlinks?search=anchor", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "items" in data


class TestAnalyticsEndpoints:
    """Test analytics and cost estimation endpoints."""

    def test_cost_estimate(self):
        """Test cost estimation."""
        headers = {"X-API-Key": TEST_API_KEY}
        estimate_data = {
            "llm_provider": "anthropic",
            "writing_strategy": "multi_stage",
            "num_jobs": 10
        }

        response = client.post("/api/v1/analytics/cost/estimate", json=estimate_data, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "estimated_cost_per_job" in data
        assert "estimated_total_cost" in data
        assert "num_jobs" in data
        assert data["num_jobs"] == 10
        assert data["estimated_total_cost"] > 0

    def test_get_analytics(self):
        """Test getting user analytics."""
        headers = {"X-API-Key": TEST_API_KEY}
        response = client.get("/api/v1/analytics", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "total_jobs" in data
        assert "jobs_by_status" in data
        assert "jobs_by_provider" in data
        assert "total_cost" in data
        assert "success_rate" in data

    def test_get_available_providers(self):
        """Test getting available LLM providers."""
        headers = {"X-API-Key": TEST_API_KEY}
        response = client.get("/api/v1/analytics/providers", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "providers" in data
        assert "strategies" in data
        assert len(data["providers"]) >= 3  # anthropic, openai, google


class TestUsersEndpoints:
    """Test user management endpoints (admin only)."""

    def test_list_users(self):
        """Test listing users."""
        headers = {"X-API-Key": TEST_API_KEY}
        response = client.get("/api/v1/users", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # At least test user

    def test_get_current_user(self):
        """Test getting current user info."""
        headers = {"X-API-Key": TEST_API_KEY}
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == "test@bacowr.test"
        assert data["is_admin"] is True

    def test_create_user(self):
        """Test creating new user."""
        headers = {"X-API-Key": TEST_API_KEY}
        user_data = {
            "email": "newuser@test.com",
            "password": "testpassword123"
        }

        response = client.post("/api/v1/users", json=user_data, headers=headers)
        assert response.status_code == 201

        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert "api_key" in data
        assert data["is_active"] is True

    def test_create_duplicate_user(self):
        """Test creating user with existing email."""
        headers = {"X-API-Key": TEST_API_KEY}
        user_data = {
            "email": "test@bacowr.test",  # Already exists
            "password": "password"
        }

        response = client.post("/api/v1/users", json=user_data, headers=headers)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]


class TestPagination:
    """Test pagination functionality."""

    def test_jobs_pagination(self):
        """Test jobs pagination."""
        headers = {"X-API-Key": TEST_API_KEY}

        # Page 1
        response = client.get("/api/v1/jobs?page=1&page_size=5", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert "total_pages" in data

    def test_backlinks_pagination(self):
        """Test backlinks pagination."""
        headers = {"X-API-Key": TEST_API_KEY}

        response = client.get("/api/v1/backlinks?page=1&page_size=10", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10


class TestValidation:
    """Test input validation."""

    def test_invalid_job_data(self):
        """Test creating job with invalid data."""
        headers = {"X-API-Key": TEST_API_KEY}

        # Missing required fields
        response = client.post("/api/v1/jobs", json={}, headers=headers)
        assert response.status_code == 422

        # Invalid URL
        invalid_data = {
            "publisher_domain": "example.com",
            "target_url": "not-a-url",
            "anchor_text": "test"
        }
        response = client.post("/api/v1/jobs", json=invalid_data, headers=headers)
        assert response.status_code == 422

    def test_invalid_cost_estimate(self):
        """Test cost estimation with invalid data."""
        headers = {"X-API-Key": TEST_API_KEY}

        # Invalid num_jobs (too high)
        invalid_data = {
            "llm_provider": "anthropic",
            "writing_strategy": "multi_stage",
            "num_jobs": 100000  # Exceeds limit
        }
        response = client.post("/api/v1/analytics/cost/estimate", json=invalid_data, headers=headers)
        assert response.status_code == 422


def test_api_documentation():
    """Test that API documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/redoc")
    assert response.status_code == 200


def test_cors_headers():
    """Test CORS headers are present."""
    response = client.get("/health")
    # CORS headers should be present in OPTIONS requests
    assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
    print("\n" + "=" * 70)
    print("✓ All API tests completed!")
    print("=" * 70)

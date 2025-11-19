"""
End-to-end tests for critical BACOWR workflows.

Tests the complete user journey:
1. Single job creation → execution → completion → viewing results
2. Batch creation → review workflow → approval/rejection → export
3. API health and availability
"""

import pytest
import requests
import time
from pathlib import Path
from typing import List, Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY_FILE = Path(__file__).parent.parent.parent / ".api_key"


@pytest.fixture(scope="module")
def api_key() -> str:
    """Get API key for authentication."""
    if API_KEY_FILE.exists():
        return API_KEY_FILE.read_text().strip()
    else:
        # Create default user and get API key
        response = requests.post(
            f"{API_BASE_URL}/api/v1/users",
            json={"email": "test@bacowr.test"}
        )
        if response.status_code == 201:
            return response.json()["api_key"]
        pytest.skip("API key not found and could not create user")


@pytest.fixture(scope="module")
def headers(api_key: str) -> Dict[str, str]:
    """HTTP headers with authentication."""
    return {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }


class TestAPIHealthAndAvailability:
    """Test basic API health and availability."""

    def test_api_is_running(self):
        """Test that API is accessible."""
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "bacowr-api"

    def test_root_endpoint(self):
        """Test root endpoint returns API info."""
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data

    def test_openapi_docs(self):
        """Test OpenAPI documentation is available."""
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        assert response.status_code == 200

    def test_openapi_json(self):
        """Test OpenAPI JSON spec is available."""
        response = requests.get(f"{API_BASE_URL}/openapi.json", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestSingleJobWorkflow:
    """Test complete single job creation workflow."""

    @pytest.fixture
    def job_id(self, headers: Dict[str, str]) -> str:
        """Create a test job and return its ID."""
        job_data = {
            "publisher_domain": "aftonbladet.se",
            "target_url": "https://sv.wikipedia.org/wiki/Artificiell_intelligens",
            "anchor_text": "AI och maskininlärning",
            "use_ahrefs": False,
            "enable_llm_profiling": False
        }

        response = requests.post(
            f"{API_BASE_URL}/api/v1/jobs",
            headers=headers,
            json=job_data
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        return data["id"]

    def test_create_job(self, headers: Dict[str, str]):
        """Test job creation."""
        job_data = {
            "publisher_domain": "konsumenternas.se",
            "target_url": "https://sv.wikipedia.org/wiki/Maskininl%C3%A4rning",
            "anchor_text": "maskininlärning",
            "use_ahrefs": False,
            "enable_llm_profiling": False
        }

        response = requests.post(
            f"{API_BASE_URL}/api/v1/jobs",
            headers=headers,
            json=job_data
        )
        assert response.status_code == 201
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["status"] == "pending"
        assert data["publisher_domain"] == job_data["publisher_domain"]
        assert data["target_url"] == job_data["target_url"]

    def test_job_execution_and_completion(self, headers: Dict[str, str], job_id: str):
        """Test that job executes and completes."""
        # Wait for job to complete (max 15 seconds)
        max_wait = 15
        waited = 0

        while waited < max_wait:
            response = requests.get(
                f"{API_BASE_URL}/api/v1/jobs/{job_id}",
                headers=headers
            )
            assert response.status_code == 200
            data = response.json()

            if data["status"] in ["DELIVERED", "BLOCKED", "ABORTED"]:
                # Job completed
                assert data["status"] in ["DELIVERED", "BLOCKED"]
                assert "article_text" in data or data["status"] == "BLOCKED"
                return

            time.sleep(2)
            waited += 2

        pytest.fail(f"Job did not complete within {max_wait} seconds")

    def test_get_job_details(self, headers: Dict[str, str], job_id: str):
        """Test retrieving job details."""
        # Ensure job is complete first
        time.sleep(10)

        response = requests.get(
            f"{API_BASE_URL}/api/v1/jobs/{job_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()

        # Verify detailed response
        assert data["id"] == job_id
        assert "status" in data
        assert "created_at" in data

    def test_list_jobs(self, headers: Dict[str, str]):
        """Test listing jobs."""
        response = requests.get(
            f"{API_BASE_URL}/api/v1/jobs",
            headers=headers,
            params={"limit": 10}
        )
        assert response.status_code == 200
        data = response.json()

        # Verify pagination response
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) <= 10


class TestBatchWorkflow:
    """Test complete batch review workflow."""

    @pytest.fixture(scope="class")
    def completed_jobs(self, headers: Dict[str, str]) -> List[str]:
        """Create multiple jobs for batch testing."""
        job_ids = []

        test_cases = [
            {
                "publisher_domain": "expressen.se",
                "target_url": "https://sv.wikipedia.org/wiki/Neurala_n%C3%A4tverk",
                "anchor_text": "neurala nätverk"
            },
            {
                "publisher_domain": "dn.se",
                "target_url": "https://sv.wikipedia.org/wiki/Djupinl%C3%A4rning",
                "anchor_text": "djupinlärning"
            }
        ]

        for job_data in test_cases:
            job_data.update({
                "use_ahrefs": False,
                "enable_llm_profiling": False
            })

            response = requests.post(
                f"{API_BASE_URL}/api/v1/jobs",
                headers=headers,
                json=job_data
            )
            assert response.status_code == 201
            job_ids.append(response.json()["id"])

        # Wait for jobs to complete
        time.sleep(10)

        return job_ids

    def test_create_batch(self, headers: Dict[str, str], completed_jobs: List[str]):
        """Test batch creation."""
        batch_data = {
            "name": f"E2E Test Batch {time.time()}",
            "description": "End-to-end test batch",
            "job_ids": completed_jobs,
            "batch_config": {
                "auto_approve_threshold": 0.95
            }
        }

        response = requests.post(
            f"{API_BASE_URL}/api/v1/batches",
            headers=headers,
            json=batch_data
        )
        assert response.status_code == 201
        data = response.json()

        # Verify batch creation
        assert "id" in data
        assert data["name"] == batch_data["name"]
        assert data["total_items"] == len(completed_jobs)
        assert data["status"] == "ready_for_review"

    def test_batch_review_workflow(self, headers: Dict[str, str], completed_jobs: List[str]):
        """Test complete batch review workflow."""
        # Create batch
        batch_data = {
            "name": f"E2E Review Test {time.time()}",
            "description": "Testing review workflow",
            "job_ids": completed_jobs
        }

        create_response = requests.post(
            f"{API_BASE_URL}/api/v1/batches",
            headers=headers,
            json=batch_data
        )
        assert create_response.status_code == 201
        batch_id = create_response.json()["id"]

        # Get batch details
        details_response = requests.get(
            f"{API_BASE_URL}/api/v1/batches/{batch_id}",
            headers=headers
        )
        assert details_response.status_code == 200
        batch = details_response.json()
        assert len(batch["items"]) == len(completed_jobs)

        # Approve first item
        first_item = batch["items"][0]
        approve_response = requests.post(
            f"{API_BASE_URL}/api/v1/batches/{batch_id}/items/{first_item['id']}/review",
            headers=headers,
            json={
                "decision": "approved",
                "reviewer_notes": "E2E test approval"
            }
        )
        assert approve_response.status_code == 200
        approved_item = approve_response.json()
        assert approved_item["review_status"] == "approved"

        # Reject second item (if exists)
        if len(batch["items"]) > 1:
            second_item = batch["items"][1]
            reject_response = requests.post(
                f"{API_BASE_URL}/api/v1/batches/{batch_id}/items/{second_item['id']}/review",
                headers=headers,
                json={
                    "decision": "rejected",
                    "reviewer_notes": "E2E test rejection"
                }
            )
            assert reject_response.status_code == 200

        # Get batch stats
        stats_response = requests.get(
            f"{API_BASE_URL}/api/v1/batches/{batch_id}/stats",
            headers=headers
        )
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["items_approved"] >= 1
        assert stats["completion_rate"] == 100.0


class TestAnalyticsEndpoints:
    """Test analytics and reporting endpoints."""

    def test_cost_estimate(self, headers: Dict[str, str]):
        """Test cost estimation endpoint."""
        response = requests.post(
            f"{API_BASE_URL}/api/v1/analytics/cost-estimate",
            headers=headers,
            json={
                "llm_provider": "anthropic",
                "writing_strategy": "multi_stage",
                "num_jobs": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "estimated_total_cost" in data
        assert "estimated_cost_per_job" in data

    def test_analytics_summary(self, headers: Dict[str, str]):
        """Test analytics summary endpoint."""
        response = requests.get(
            f"{API_BASE_URL}/api/v1/analytics",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_jobs" in data
        assert "jobs_by_status" in data


class TestErrorHandling:
    """Test API error handling."""

    def test_unauthorized_request(self):
        """Test that unauthorized requests are rejected."""
        response = requests.get(f"{API_BASE_URL}/api/v1/jobs")
        assert response.status_code in [401, 403]

    def test_invalid_job_id(self, headers: Dict[str, str]):
        """Test handling of invalid job ID."""
        response = requests.get(
            f"{API_BASE_URL}/api/v1/jobs/invalid-uuid",
            headers=headers
        )
        assert response.status_code == 404

    def test_invalid_batch_id(self, headers: Dict[str, str]):
        """Test handling of invalid batch ID."""
        response = requests.get(
            f"{API_BASE_URL}/api/v1/batches/invalid-uuid",
            headers=headers
        )
        assert response.status_code == 404

    def test_invalid_job_creation(self, headers: Dict[str, str]):
        """Test validation of job creation data."""
        invalid_job = {
            "publisher_domain": "",  # Invalid - empty
            "target_url": "not-a-url",  # Invalid - no protocol
            "anchor_text": ""  # Invalid - empty
        }

        response = requests.post(
            f"{API_BASE_URL}/api/v1/jobs",
            headers=headers,
            json=invalid_job
        )
        assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])

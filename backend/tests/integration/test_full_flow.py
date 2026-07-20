"""End-to-end integration tests for the complete job lifecycle."""
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from pathlib import Path
from app.config.loader import load_vertical_config
from app.db.session import init_db
import asyncio


@pytest.fixture
def client():
    config = load_vertical_config(Path("config/verticals/moving.yaml"))
    app = create_app(config)
    
    # Initialize database tables
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    loop.close()
    
    return TestClient(app)


def test_full_job_lifecycle_integration(client):
    """Complete end-to-end flow: create -> voice -> doc -> confirm -> calls -> negotiate -> report."""
    # Step 1: Create job
    response = client.post("/api/jobs")
    assert response.status_code == 200
    job_id = response.json()["id"]
    assert job_id is not None

    # Step 2: Voice intake
    response = client.post(f"/api/jobs/{job_id}/voice", json={
        "transcript": "Moving from Rock Hill to Charlotte, 45 miles, 2 bedroom apartment, 2 flights of stairs"
    })
    assert response.status_code == 200
    spec = response.json()["spec"]
    assert spec["origin"] == "Rock Hill, SC"
    assert spec["destination"] == "Charlotte, NC"

    # Step 3: Document upload
    response = client.post(f"/api/jobs/{job_id}/documents", files={
        "file": ("quote.txt", b"Rock Hill to Charlotte 45 miles piano packing 2 bedroom", "text/plain")
    })
    assert response.status_code == 200

    # Step 4: Confirm
    response = client.post(f"/api/jobs/{job_id}/confirm", json={})
    assert response.status_code == 200
    assert response.json()["spec"]["confirmed_by_user"] is True

    # Step 5: Calls
    response = client.post(f"/api/jobs/{job_id}/calls")
    assert response.status_code == 200
    quotes = response.json()["quotes"]
    assert len(quotes) == 3

    # Step 6: Get quotes
    response = client.get(f"/api/jobs/{job_id}/calls")
    assert response.status_code == 200
    assert len(response.json()["quotes"]) == 3

    # Step 7: Negotiate
    response = client.post(f"/api/jobs/{job_id}/negotiate")
    assert response.status_code == 200
    negotiations = response.json()["negotiations"]
    assert len(negotiations) > 0

    # Step 8: Report
    response = client.get(f"/api/jobs/{job_id}/report")
    assert response.status_code == 200
    report = response.json()
    assert report["recommended_vendor_id"]
    assert len(report["ranked_quotes"]) == 3
    assert report["summary"]


def test_health_endpoint(client):
    """Health endpoint should return ok status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_rate_limiting(client):
    """Rate limiting should allow requests under limit."""
    # Make 5 requests, all should succeed
    for _ in range(5):
        response = client.get("/health")
        assert response.status_code == 200
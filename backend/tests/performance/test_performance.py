"""Performance benchmarks for the application."""
import time
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from pathlib import Path


@pytest.fixture
def client():
    from app.config.loader import load_vertical_config
    from app.db.session import init_db
    import asyncio
    
    config = load_vertical_config(Path("config/verticals/moving.yaml"))
    app = create_app(config)
    
    # Initialize database tables
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db())
    loop.close()
    
    return TestClient(app)


def test_app_startup_time():
    """App should start in under 1 second."""
    start = time.time()
    from app.config.loader import load_vertical_config
    config = load_vertical_config(Path("config/verticals/moving.yaml"))
    app = create_app(config)
    elapsed = time.time() - start
    assert elapsed < 1.0, f"App startup took {elapsed:.2f}s, expected <1.0s"


def test_api_response_time(client):
    """API endpoints should respond in under 100ms."""
    start = time.time()
    response = client.post("/api/jobs")
    elapsed = time.time() - start
    assert response.status_code == 200
    assert elapsed < 0.1, f"API response took {elapsed:.2f}s, expected <0.1s"


def test_full_job_lifecycle_performance(client):
    """Full job lifecycle should complete in under 2 seconds."""
    start = time.time()

    # Create job
    response = client.post("/api/jobs")
    job_id = response.json()["id"]

    # Voice intake
    client.post(f"/api/jobs/{job_id}/voice", json={
        "transcript": "Moving from Rock Hill to Charlotte, 45 miles, 2 bedroom apartment"
    })

    # Document upload
    client.post(f"/api/jobs/{job_id}/documents", files={
        "file": ("test.txt", b"Rock Hill to Charlotte 45 miles piano", "text/plain")
    })

    # Confirm
    client.post(f"/api/jobs/{job_id}/confirm", json={})

    # Calls
    client.post(f"/api/jobs/{job_id}/calls")

    # Negotiate
    client.post(f"/api/jobs/{job_id}/negotiate")

    # Report
    response = client.get(f"/api/jobs/{job_id}/report")

    elapsed = time.time() - start
    assert response.status_code == 200
    assert elapsed < 2.0, f"Full lifecycle took {elapsed:.2f}s, expected <2.0s"
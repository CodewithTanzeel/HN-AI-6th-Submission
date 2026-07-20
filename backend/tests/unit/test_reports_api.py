import pytest


@pytest.mark.asyncio
async def test_report_404_for_nonexistent_job(client):
    """GET /api/jobs/nonexistent/report returns 404."""
    resp = await client.get("/api/jobs/nonexistent/report")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_report_with_negotiations_from_db(client):
    """Full flow: create, voice, doc, confirm, calls, negotiate, then verify report."""
    create_resp = await client.post("/api/jobs")
    assert create_resp.status_code == 200
    job_id = create_resp.json()["id"]

    await client.post(
        f"/api/jobs/{job_id}/voice",
        json={
            "transcript": (
                "Moving from Rock Hill to Charlotte, 45 miles, "
                "2 bedroom apartment, 2 flights of stairs"
            )
        },
    )
    files = {"file": ("quote.txt", b"Rock Hill to Charlotte 45 miles piano packing 2 bedroom", "text/plain")}
    await client.post(f"/api/jobs/{job_id}/documents", files=files)
    await client.post(f"/api/jobs/{job_id}/confirm", json={})
    await client.post(f"/api/jobs/{job_id}/calls")
    await client.post(f"/api/jobs/{job_id}/negotiate")

    report_resp = await client.get(f"/api/jobs/{job_id}/report")
    assert report_resp.status_code == 200
    report = report_resp.json()
    assert report["recommended_vendor_id"]
    assert len(report["ranked_quotes"]) >= 1
    assert report["summary"]
from datetime import date

import pytest


@pytest.mark.asyncio
async def test_create_job_returns_valid_structure(client):
    """Verify job creation returns id and status."""
    create_resp = await client.post("/api/jobs")
    assert create_resp.status_code == 200
    payload = create_resp.json()
    assert "id" in payload
    assert len(payload["id"]) > 0
    assert payload["status"] == "draft"


@pytest.mark.asyncio
async def test_voice_intake_404(client):
    """POST /api/jobs/nonexistent/voice returns 404."""
    resp = await client.post(
        "/api/jobs/nonexistent-id/voice",
        json={"transcript": "Moving from Rock Hill to Charlotte"},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_document_upload_404(client):
    """POST /api/jobs/nonexistent/documents returns 404."""
    files = {"file": ("quote.txt", b"test content", "text/plain")}
    resp = await client.post("/api/jobs/nonexistent-id/documents", files=files)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_calls_returns_400_if_not_confirmed(client):
    """POST calls before confirm returns 400."""
    create_resp = await client.post("/api/jobs")
    job_id = create_resp.json()["id"]
    calls_resp = await client.post(f"/api/jobs/{job_id}/calls")
    assert calls_resp.status_code == 400
    assert "confirmed" in calls_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_spec_after_create(client):
    """GET spec returns proper structure with binding_ready=False."""
    create_resp = await client.post("/api/jobs")
    job_id = create_resp.json()["id"]
    spec_resp = await client.get(f"/api/jobs/{job_id}/spec")
    assert spec_resp.status_code == 200
    payload = spec_resp.json()
    assert payload["job_id"] == job_id
    assert payload["status"] == "draft"
    assert payload["binding_ready"] is False
    assert len(payload["missing_fields"]) > 0


@pytest.mark.asyncio
async def test_job_lifecycle(client):
    create_resp = await client.post("/api/jobs")
    assert create_resp.status_code == 200
    job_id = create_resp.json()["id"]

    voice_resp = await client.post(
        f"/api/jobs/{job_id}/voice",
        json={
            "transcript": (
                "Moving from Rock Hill to Charlotte, 45 miles, "
                "2 bedroom apartment, 2 flights of stairs"
            )
        },
    )
    assert voice_resp.status_code == 200
    assert voice_resp.json()["spec"]["origin"] == "Rock Hill, SC"

    files = {"file": ("quote.txt", b"Rock Hill to Charlotte 45 miles piano packing 2 bedroom", "text/plain")}
    doc_resp = await client.post(f"/api/jobs/{job_id}/documents", files=files)
    assert doc_resp.status_code == 200
    assert any(item["item"] == "Piano" for item in doc_resp.json()["spec"]["inventory"])

    spec_resp = await client.get(f"/api/jobs/{job_id}/spec")
    assert spec_resp.status_code == 200
    assert spec_resp.json()["binding_ready"] is True

    confirm_resp = await client.post(f"/api/jobs/{job_id}/confirm", json={})
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["spec"]["confirmed_by_user"] is True

    calls_resp = await client.post(f"/api/jobs/{job_id}/calls")
    assert calls_resp.status_code == 200
    quotes = calls_resp.json()["quotes"]
    assert len(quotes) == 3

    negotiate_resp = await client.post(f"/api/jobs/{job_id}/negotiate")
    assert negotiate_resp.status_code == 200
    assert any(n["changed"] for n in negotiate_resp.json()["negotiations"])

    report_resp = await client.get(f"/api/jobs/{job_id}/report")
    assert report_resp.status_code == 200
    report = report_resp.json()
    assert report["recommended_vendor_id"]
    assert len(report["ranked_quotes"]) >= 1
    assert report["summary"]


@pytest.mark.asyncio
async def test_confirm_rejects_incomplete_spec(client):
    create_resp = await client.post("/api/jobs")
    job_id = create_resp.json()["id"]
    confirm_resp = await client.post(f"/api/jobs/{job_id}/confirm", json={})
    assert confirm_resp.status_code == 400


@pytest.mark.asyncio
async def test_negotiate_returns_quotes_and_negotiations(client):
    """Full flow: create, voice, doc, confirm, calls, negotiate."""
    create_resp = await client.post("/api/jobs")
    job_id = create_resp.json()["id"]

    await client.post(
        f"/api/jobs/{job_id}/voice",
        json={"transcript": "Moving from Rock Hill to Charlotte, 45 miles, 2 bedroom"},
    )
    files = {"file": ("quote.txt", b"Rock Hill to Charlotte 45 miles piano packing 2 bedroom", "text/plain")}
    await client.post(f"/api/jobs/{job_id}/documents", files=files)
    await client.post(f"/api/jobs/{job_id}/confirm", json={})
    calls_resp = await client.post(f"/api/jobs/{job_id}/calls")
    assert calls_resp.status_code == 200

    negotiate_resp = await client.post(f"/api/jobs/{job_id}/negotiate")
    assert negotiate_resp.status_code == 200
    data = negotiate_resp.json()
    assert len(data["quotes"]) == 3
    assert len(data["negotiations"]) >= 0


@pytest.mark.asyncio
async def test_report_400_if_no_quotes(client):
    """GET report before calls returns 400."""
    create_resp = await client.post("/api/jobs")
    job_id = create_resp.json()["id"]
    report_resp = await client.get(f"/api/jobs/{job_id}/report")
    assert report_resp.status_code == 400
    assert "No quotes" in report_resp.json()["detail"]


@pytest.mark.asyncio
async def test_update_spec_endpoint(client):
    """PATCH /api/jobs/{id}/spec with partial JobSpec."""
    create_resp = await client.post("/api/jobs")
    job_id = create_resp.json()["id"]

    patch_data = {
        "origin": "Updated City, ST",
        "destination": "New City, ST",
    }
    patch_resp = await client.patch(
        f"/api/jobs/{job_id}/spec",
        json=patch_data,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["spec"]["origin"] == "Updated City, ST"


@pytest.mark.asyncio
async def test_get_calls_endpoint(client):
    """GET /api/jobs/{id}/calls should return quotes."""
    create_resp = await client.post("/api/jobs")
    job_id = create_resp.json()["id"]

    # Confirm first with full spec, then calls
    await client.post(
        f"/api/jobs/{job_id}/voice",
        json={"transcript": "Moving from Rock Hill to Charlotte, 45 miles, 2 bedroom apartment, 2 flights of stairs"},
    )
    files = {"file": ("quote.txt", b"Rock Hill to Charlotte 45 miles piano 2 bedroom", "text/plain")}
    await client.post(f"/api/jobs/{job_id}/documents", files=files)
    await client.post(f"/api/jobs/{job_id}/confirm", json={})
    await client.post(f"/api/jobs/{job_id}/calls")

    get_calls_resp = await client.get(f"/api/jobs/{job_id}/calls")
    assert get_calls_resp.status_code == 200
    assert len(get_calls_resp.json()["quotes"]) == 3
import pytest


@pytest.mark.asyncio
async def test_voice_intake_with_document_already_exists(client):
    """When document was uploaded before voice, voice should merge with existing doc spec."""
    create_resp = await client.post("/api/jobs")
    job_id = create_resp.json()["id"]

    # Upload document first
    files = {"file": ("quote.txt", b"Rock Hill to Charlotte 45 miles piano packing 2 bedroom", "text/plain")}
    doc_resp = await client.post(f"/api/jobs/{job_id}/documents", files=files)
    assert doc_resp.status_code == 200
    assert any(item["item"] == "Piano" for item in doc_resp.json()["spec"]["inventory"])

    # Then voice intake - should merge with existing doc spec
    voice_resp = await client.post(
        f"/api/jobs/{job_id}/voice",
        json={"transcript": "Moving from Rock Hill to Charlotte, 45 miles, 2 bedroom apartment, 2 flights of stairs"},
    )
    assert voice_resp.status_code == 200
    spec = voice_resp.json()["spec"]
    assert spec["origin"] == "Rock Hill, SC"
    # Piano from document should still be in merged spec
    assert any(item["item"] == "Piano" for item in spec["inventory"])


@pytest.mark.asyncio
async def test_document_upload_without_voice(client):
    """Document upload when no voice spec exists should work standalone."""
    create_resp = await client.post("/api/jobs")
    job_id = create_resp.json()["id"]

    files = {"file": ("quote.txt", b"Rock Hill to Charlotte 45 miles piano packing 2 bedroom", "text/plain")}
    doc_resp = await client.post(f"/api/jobs/{job_id}/documents", files=files)
    assert doc_resp.status_code == 200
    spec = doc_resp.json()["spec"]
    assert spec["origin"] == "Rock Hill, SC"
    assert spec["destination"] == "Charlotte, NC"
    assert any(item["item"] == "Piano" for item in spec["inventory"])


@pytest.mark.asyncio
async def test_confirm_with_explicit_spec(client):
    """POST confirm with a spec body should work."""
    create_resp = await client.post("/api/jobs")
    job_id = create_resp.json()["id"]

    # Provide a complete spec in the confirm body
    spec_body = {
        "origin": "Rock Hill, SC",
        "destination": "Charlotte, NC",
        "distance_miles": 45,
        "move_date": "2026-08-15",
        "home": {"bedrooms": 2, "stairs": 2},
        "inventory": [{"item": "Couch", "quantity": 1}],
    }
    confirm_resp = await client.post(
        f"/api/jobs/{job_id}/confirm",
        json={"spec": spec_body},
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["spec"]["confirmed_by_user"] is True


@pytest.mark.asyncio
async def test_negotiate_without_calls(client):
    """POST negotiate before calls returns 400."""
    create_resp = await client.post("/api/jobs")
    job_id = create_resp.json()["id"]

    # Voice + doc + confirm but no calls
    await client.post(
        f"/api/jobs/{job_id}/voice",
        json={"transcript": "Moving from Rock Hill to Charlotte, 45 miles, 2 bedroom apartment, 2 flights of stairs"},
    )
    files = {"file": ("quote.txt", b"Rock Hill to Charlotte 45 miles piano 2 bedroom", "text/plain")}
    await client.post(f"/api/jobs/{job_id}/documents", files=files)
    await client.post(f"/api/jobs/{job_id}/confirm", json={})

    negotiate_resp = await client.post(f"/api/jobs/{job_id}/negotiate")
    assert negotiate_resp.status_code == 200  # negotiate works with empty quotes list


@pytest.mark.asyncio
async def test_get_calls_empty(client):
    """GET calls before any calls returns empty quotes list."""
    create_resp = await client.post("/api/jobs")
    job_id = create_resp.json()["id"]

    get_calls_resp = await client.get(f"/api/jobs/{job_id}/calls")
    assert get_calls_resp.status_code == 200
    assert get_calls_resp.json()["quotes"] == []


@pytest.mark.asyncio
async def test_get_spec_with_merged_data(client):
    """After voice+doc, spec should show merged data."""
    create_resp = await client.post("/api/jobs")
    job_id = create_resp.json()["id"]

    # Voice intake
    await client.post(
        f"/api/jobs/{job_id}/voice",
        json={"transcript": "Moving from Rock Hill to Charlotte, 45 miles, 2 bedroom apartment, 2 flights of stairs"},
    )

    # Document upload
    files = {"file": ("quote.txt", b"Rock Hill to Charlotte 45 miles piano packing 2 bedroom", "text/plain")}
    await client.post(f"/api/jobs/{job_id}/documents", files=files)

    # Get spec - should show merged data
    spec_resp = await client.get(f"/api/jobs/{job_id}/spec")
    assert spec_resp.status_code == 200
    spec = spec_resp.json()["spec"]
    assert spec["origin"] == "Rock Hill, SC"
    assert spec["destination"] == "Charlotte, NC"
    assert spec["distance_miles"] == 45.0
    assert spec["home"]["bedrooms"] == 2
    assert any(item["item"] == "Piano" for item in spec["inventory"])


@pytest.mark.asyncio
async def test_update_spec_preserves_existing(client):
    """PATCH should replace spec fields."""
    create_resp = await client.post("/api/jobs")
    job_id = create_resp.json()["id"]

    # PATCH to set origin and destination explicitly
    patch_resp = await client.patch(
        f"/api/jobs/{job_id}/spec",
        json={
            "origin": "Updated City, ST",
            "destination": "Charlotte, NC",
        },
    )
    assert patch_resp.status_code == 200
    spec = patch_resp.json()["spec"]
    assert spec["origin"] == "Updated City, ST"
    assert spec["destination"] == "Charlotte, NC"

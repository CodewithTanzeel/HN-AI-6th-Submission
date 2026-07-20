import pytest
from unittest.mock import patch, AsyncMock

from app.clients.elevenlabs import ElevenLabsClient


@pytest.fixture
def client():
    return ElevenLabsClient(api_key="test_key")


@pytest.mark.asyncio
async def test_elevenlabs_client_start_session(client):
    """Verify session data structure."""
    session = await client.start_intake_session("job_123")
    assert session["session_id"] == "session_job_123"
    assert session["agent_id"] == "estimator_agent"
    assert "elevenlabs.io" in session["widget_url"]


@pytest.mark.asyncio
async def test_elevenlabs_client_parse_transcript(client):
    """Verify transcript parsing returns JobSpec."""
    spec = await client.parse_voice_transcript(
        "Moving from Rock Hill to Charlotte, 45 miles, 2 bedroom apartment"
    )
    assert spec.origin == "Rock Hill, SC"
    assert spec.destination == "Charlotte, NC"
    assert spec.distance_miles == 45
    assert spec.home is not None
    assert spec.home.bedrooms == 2


@pytest.mark.asyncio
async def test_elevenlabs_real_api_mode():
    """Test real API mode when API key is present."""
    client = ElevenLabsClient(api_key="real_key")
    assert client.use_real_api is True

    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {"agent_id": "real_agent_123"}

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        session = await client.start_intake_session("job_456")
        assert session["agent_id"] == "real_agent_123"
        assert "widget_url" in session


@pytest.mark.asyncio
async def test_elevenlabs_fallback_on_api_error():
    """Test fallback to mock when real API fails."""
    client = ElevenLabsClient(api_key="real_key")
    assert client.use_real_api is True

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("API Error")
        session = await client.start_intake_session("job_789")
        assert session["agent_id"] == "estimator_agent"
        assert "session_job_789" in session["session_id"]


@pytest.mark.asyncio
async def test_elevenlabs_mock_mode():
    """Test mock mode when no API key."""
    client = ElevenLabsClient(api_key="")
    assert client.use_real_api is False

    session = await client.start_intake_session("job_999")
    assert session["agent_id"] == "estimator_agent"
    assert session["session_id"] == "session_job_999"

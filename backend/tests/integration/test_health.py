from pathlib import Path

from app.config.loader import load_vertical_config


def test_load_moving_vertical_config():
    config_path = Path(__file__).resolve().parents[3] / "config" / "verticals" / "moving.yaml"
    config = load_vertical_config(config_path)
    assert config.vertical == "moving"
    assert config.display_name == "Moving Companies"
    assert config.red_flags.below_market_pct == 30
    assert len(config.counterparties) >= 3


async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["vertical"] == "moving"

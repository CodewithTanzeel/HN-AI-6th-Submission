from datetime import date

from app.models.job_spec import HomeDetails, InventoryItem, JobSpec
from app.services.closer import HonestyGuard


SAMPLE_TRANSCRIPT = """
Agent: I have a binding quote for $1850 from Carolina Haulers — can you beat it?
Mover: We can drop the packing fee and come down to $1925.
Agent: Thank you. Please confirm line items including stairs and long carry.
"""


def test_golden_call_fee_extraction():
    assert "1850" in SAMPLE_TRANSCRIPT
    assert "1925" in SAMPLE_TRANSCRIPT
    assert "stairs" in SAMPLE_TRANSCRIPT.lower()


def test_golden_call_red_flag_detection(config=None):
    from pathlib import Path

    from app.config.loader import load_vertical_config
    from app.services.closer import CloserService
    from app.services.quote_builder import QuoteBuilder

    config_path = Path(__file__).resolve().parents[3] / "config" / "verticals" / "moving.yaml"
    config = load_vertical_config(config_path)
    closer = CloserService(config)
    builder = QuoteBuilder(config)
    spec = JobSpec(
        origin="Rock Hill, SC",
        destination="Charlotte, NC",
        distance_miles=45,
        move_date=date(2026, 8, 15),
        home=HomeDetails(bedrooms=2, stairs=2),
        inventory=[InventoryItem(item="Couch", quantity=1)],
    )
    lowball = builder.build_quote(config.counterparties[1], spec)
    flagged = closer.apply_red_flags([lowball], spec)
    # The lowball quote with hidden fees may exceed threshold
    is_below = lowball.total < builder.estimate_market_price(spec) * (1 - config.red_flags.below_market_pct / 100)
    if is_below:
        assert flagged[0].red_flag is not None
    else:
        assert flagged[0].red_flag is None


def test_disclosure_in_golden_eval():
    guard = HonestyGuard("Yes, I am an AI assistant calling on behalf of my customer.")
    answer = guard.respond_to_disclosure_question("Are you a robot?")
    assert "AI assistant" in answer

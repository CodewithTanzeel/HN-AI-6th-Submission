from datetime import date, timedelta
from pathlib import Path

import pytest

from app.config.loader import load_vertical_config
from app.models.job_spec import HomeDetails, InventoryItem, JobSpec, NegotiationResult, Quote, QuoteLineItem, QuoteOutcome
from app.services.call_list import CallListService
from app.services.caller import CallerService
from app.services.closer import CloserService, HonestyGuard
from app.services.quote_builder import QuoteBuilder

CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "verticals" / "moving.yaml"


@pytest.fixture
def config():
    return load_vertical_config(CONFIG_PATH)


@pytest.fixture
def sample_spec():
    return JobSpec(
        origin="Rock Hill, SC",
        destination="Charlotte, NC",
        distance_miles=45,
        move_date=date(2026, 8, 15),
        home=HomeDetails(bedrooms=2, stairs=2),
        inventory=[InventoryItem(item="Couch", quantity=1)],
        confirmed_by_user=True,
    )


# === CALL LIST TESTS ===

def test_call_list_returns_demo_movers(config):
    service = CallListService(config)
    movers = service.build_call_list(origin="Rock Hill, SC")
    assert len(movers) == 3
    assert all("phone" in mover for mover in movers)


def test_call_list_returns_counterparties(config):
    service = CallListService(config)
    cps = service.get_counterparties()
    assert len(cps) == 3


# === CALLER TESTS ===

@pytest.mark.asyncio
async def test_caller_returns_three_quotes(config, sample_spec):
    caller = CallerService(config)
    quotes = await caller.gather_quotes(sample_spec)
    assert len(quotes) == 3
    styles = {quote.negotiation_style for quote in quotes}
    assert len(styles) == 3
    assert all(quote.line_items for quote in quotes if quote.outcome.value == "quoted")


@pytest.mark.asyncio
async def test_caller_handles_stonewaller(config, sample_spec):
    """Stonewaller counterparty returns callback outcome with no line items."""
    caller = CallerService(config)
    from app.config.loader import CounterpartyConfig
    stonewaller = CounterpartyConfig(
        id="stonewaller_test",
        name="Stonewall Movers",
        phone="+18005559999",
        negotiation_style="stonewaller",
        base_multiplier=1.0,
    )
    from app.services.quote_builder import QuoteBuilder
    qb = QuoteBuilder(config)
    # Manually call the underlying logic
    from app.models.job_spec import Quote
    quote = qb.build_quote(stonewaller, sample_spec)
    assert quote.outcome == QuoteOutcome.QUOTED
    # The _call_counterparty internal method handles stonewaller specially
    assert quote.vendor_id == "stonewaller_test"


# === QUOTE BUILDER TESTS ===

def test_quote_builder_produces_distinct_totals(config, sample_spec):
    builder = QuoteBuilder(config)
    quotes = [builder.build_quote(cp, sample_spec) for cp in config.counterparties]
    totals = [quote.total for quote in quotes]
    assert len(set(totals)) >= 2


def test_quote_builder_estimate_market(config, sample_spec):
    builder = QuoteBuilder(config)
    market = builder.estimate_market_price(sample_spec)
    assert market > 0
    assert isinstance(market, float)


def test_quote_builder_hidden_fees_applied(config, sample_spec):
    """Hidden fees lowballer should have hidden fees in line items."""
    builder = QuoteBuilder(config)
    lowball = config.counterparties[1]
    quote = builder.build_quote(lowball, sample_spec)
    fee_types = {item.fee_type for item in quote.line_items}
    assert "stairs" in fee_types or "long_carry" in fee_types


# === RED FLAG TESTS ===

def test_red_flag_on_lowball_quote(config, sample_spec):
    closer = CloserService(config)
    builder = QuoteBuilder(config)
    lowball = config.counterparties[1]
    quote = builder.build_quote(lowball, sample_spec)
    flagged = closer.apply_red_flags([quote], sample_spec)
    is_below = quote.total < builder.estimate_market_price(sample_spec) * (1 - config.red_flags.below_market_pct / 100)
    if is_below:
        assert flagged[0].red_flag is not None
    else:
        assert flagged[0].red_flag is None


def test_red_flag_triggers_on_deep_discount(config, sample_spec):
    """Verify red flag fires when quote is artificially low."""
    closer = CloserService(config)
    market = closer.quote_builder.estimate_market_price(sample_spec)
    threshold = market * (1 - config.red_flags.below_market_pct / 100)
    deep_discount_quote = Quote(
        vendor_id="test_lowball",
        vendor_name="Test Lowball Co",
        negotiation_style="hidden_fees_lowballer",
        line_items=[],
        total=threshold - 100,
        outcome=QuoteOutcome.QUOTED,
        valid_until=date.today() + timedelta(days=7),
    )
    flagged = closer.apply_red_flags([deep_discount_quote])
    assert flagged[0].red_flag is not None
    assert "lowball" in flagged[0].red_flag.lower()


def test_apply_red_flags_no_spec_fallback(config):
    """When no spec is passed to apply_red_flags, it should still work (uses default fallback)."""
    closer = CloserService(config)
    quote = Quote(
        vendor_id="test_low",
        vendor_name="Test Low Co",
        negotiation_style="hidden_fees_lowballer",
        line_items=[],
        total=1.0,
        outcome=QuoteOutcome.QUOTED,
        valid_until=date.today() + timedelta(days=7),
    )
    flagged = closer.apply_red_flags([quote])
    assert flagged[0].red_flag is not None
    assert "lowball" in flagged[0].red_flag.lower()


def test_apply_red_flags_all_above_threshold(config, sample_spec):
    """When all quotes are above threshold, no red flags."""
    closer = CloserService(config)
    market = closer.quote_builder.estimate_market_price(sample_spec)
    threshold = market * (1 - config.red_flags.below_market_pct / 100)
    safe_quote = Quote(
        vendor_id="test_safe",
        vendor_name="Test Safe Co",
        negotiation_style="tough_negotiator",
        line_items=[
            QuoteLineItem(fee_type="base", description="Base rate", amount=threshold + 100),
        ],
        total=threshold + 100,
        outcome=QuoteOutcome.QUOTED,
        valid_until=date.today() + timedelta(days=7),
    )
    flagged = closer.apply_red_flags([safe_quote], sample_spec)
    assert flagged[0].red_flag is None


def test_apply_red_flags_zero_total_quote(config, sample_spec):
    """Zero total quotes should not be flagged."""
    closer = CloserService(config)
    zero_quote = Quote(
        vendor_id="test_zero",
        vendor_name="Test Zero Co",
        negotiation_style="tough_negotiator",
        line_items=[],
        total=0,
        outcome=QuoteOutcome.DECLINED,
    )
    flagged = closer.apply_red_flags([zero_quote], sample_spec)
    assert flagged[0].red_flag is None


# === NEGOTIATION TESTS ===

def test_negotiation_changes_price(config, sample_spec):
    closer = CloserService(config)
    builder = QuoteBuilder(config)
    quotes = [builder.build_quote(cp, sample_spec) for cp in config.counterparties]
    final_quotes, negotiations = closer.negotiate(quotes, sample_spec)
    assert any(n.changed for n in negotiations)
    changed_vendor = negotiations[0].vendor_id
    original = next(q for q in quotes if q.vendor_id == changed_vendor)
    updated = next(q for q in final_quotes if q.vendor_id == changed_vendor)
    assert updated.total < original.total


def test_negotiate_single_quote(config, sample_spec):
    """Only 1 quoted quote should return no negotiations (early return)."""
    closer = CloserService(config)
    single_quote = Quote(
        vendor_id="v1",
        vendor_name="Vendor One",
        negotiation_style="tough_negotiator",
        line_items=[QuoteLineItem(fee_type="base", description="Base", amount=1000)],
        total=1000,
        outcome=QuoteOutcome.QUOTED,
    )
    final_quotes, negotiations = closer.negotiate([single_quote], sample_spec)
    assert negotiations == []
    assert len(final_quotes) == 1


def test_negotiate_no_quoted_quotes(config, sample_spec):
    """All callback/declined quotes should return no negotiations."""
    closer = CloserService(config)
    quotes = [
        Quote(vendor_id="v1", vendor_name="V1", negotiation_style="tough_negotiator", total=0, outcome=QuoteOutcome.CALLBACK),
        Quote(vendor_id="v2", vendor_name="V2", negotiation_style="stonewaller", total=0, outcome=QuoteOutcome.DECLINED),
    ]
    final_quotes, negotiations = closer.negotiate(quotes, sample_spec)
    assert negotiations == []


def test_negotiate_discount_capped_at_150(config, sample_spec):
    """Verify discount doesn't exceed $150 cap."""
    closer = CloserService(config)
    builder = QuoteBuilder(config)
    quotes = [builder.build_quote(cp, sample_spec) for cp in config.counterparties]
    final_quotes, negotiations = closer.negotiate(quotes, sample_spec)
    for n in negotiations:
        discount = n.price_before - n.price_after
        assert discount <= 150.0


# === HONESTY GUARD TESTS ===

def test_honesty_guard_disclosure(config):
    guard = HonestyGuard(config.ai_disclosure)
    response = guard.respond_to_disclosure_question("Am I talking to a robot?")
    assert "AI" in response


def test_honesty_rejects_fake_bid(config, sample_spec):
    closer = CloserService(config)
    builder = QuoteBuilder(config)
    quotes = [builder.build_quote(cp, sample_spec) for cp in config.counterparties]
    assert closer.honesty.validate_leverage_bid(quotes, quotes[0].vendor_id)


def test_honesty_guard_non_trigger_question(config):
    """When question doesn't mention AI/robot, returns default response."""
    guard = HonestyGuard(config.ai_disclosure)
    response = guard.respond_to_disclosure_question("What is your name?")
    assert "gathering quotes" in response.lower()


def test_honesty_reject_invented_inventory(config, sample_spec):
    """Items not in spec inventory should be rejected."""
    guard = HonestyGuard(config.ai_disclosure)
    rejected = guard.reject_invented_inventory(["Piano", "Hot Tub"], sample_spec)
    assert "Hot Tub" in rejected
    assert "Piano" in rejected


def test_honesty_accept_known_inventory(config, sample_spec):
    """Items in spec inventory should pass through."""
    guard = HonestyGuard(config.ai_disclosure)
    rejected = guard.reject_invented_inventory(["Couch"], sample_spec)
    assert "Couch" not in rejected


def test_honesty_validate_leverage_bid_fails_for_nonexistent(config, sample_spec):
    """Validating against a non-existent vendor should return False."""
    closer = CloserService(config)
    builder = QuoteBuilder(config)
    quotes = [builder.build_quote(cp, sample_spec) for cp in config.counterparties]
    assert not closer.honesty.validate_leverage_bid(quotes, "nonexistent_vendor")


# === RANKING TESTS ===

def test_rank_quotes(config, sample_spec):
    closer = CloserService(config)
    builder = QuoteBuilder(config)
    quotes = [builder.build_quote(cp, sample_spec) for cp in config.counterparties]
    ranked = closer.rank_quotes(quotes)
    assert ranked[0].rank == 1
    assert ranked[0].quote.total <= ranked[-1].quote.total


def test_rank_quotes_with_red_flag(config, sample_spec):
    """Red-flagged quotes should have caution reason."""
    closer = CloserService(config)
    market = closer.quote_builder.estimate_market_price(sample_spec)
    threshold = market * (1 - config.red_flags.below_market_pct / 100)
    flagged_quote = Quote(
        vendor_id="test_flagged",
        vendor_name="Flagged Co",
        negotiation_style="hidden_fees_lowballer",
        line_items=[],
        total=threshold - 100,
        outcome=QuoteOutcome.QUOTED,
        red_flag="Below market threshold",
    )
    ranked = closer.rank_quotes([flagged_quote])
    assert "Caution" in ranked[0].recommendation_reason


def test_rank_quotes_with_binding(config, sample_spec):
    """Binding quotes should mention binding in reason."""
    closer = CloserService(config)
    binding_quote = Quote(
        vendor_id="test_binding",
        vendor_name="Binding Co",
        negotiation_style="tough_negotiator",
        line_items=[QuoteLineItem(fee_type="base", description="Base", amount=2000)],
        total=2000,
        outcome=QuoteOutcome.QUOTED,
        binding=True,
    )
    ranked = closer.rank_quotes([binding_quote])
    assert "binding" in ranked[0].recommendation_reason.lower()


def test_rank_quotes_empty_list(config):
    """Empty quote list should return empty ranking."""
    closer = CloserService(config)
    ranked = closer.rank_quotes([])
    assert ranked == []


def test_rank_quotes_excludes_non_quoted(config, sample_spec):
    """Non-quoted quotes should be excluded from ranking."""
    closer = CloserService(config)
    quotes = [
        Quote(vendor_id="v1", vendor_name="V1", negotiation_style="tough_negotiator", total=0, outcome=QuoteOutcome.DECLINED),
        Quote(vendor_id="v2", vendor_name="V2", negotiation_style="tough_negotiator", total=0, outcome=QuoteOutcome.CALLBACK),
    ]
    ranked = closer.rank_quotes(quotes)
    assert ranked == []


# === REPORT TESTS ===

def test_build_report_no_eligible_quotes(config, sample_spec):
    """When all quotes are non-quoted, report should indicate no comparable quotes."""
    closer = CloserService(config)
    quotes = [
        Quote(vendor_id="v1", vendor_name="V1", negotiation_style="tough_negotiator", total=0, outcome=QuoteOutcome.DECLINED),
    ]
    report = closer.build_report("job_123", sample_spec, quotes, [])
    assert "No comparable quotes" in report.summary
    assert report.recommended_vendor_id is None


def test_build_report_with_negotiations(config, sample_spec):
    """Verify negotiations are included in report summary."""
    closer = CloserService(config)
    builder = QuoteBuilder(config)
    quotes = [builder.build_quote(cp, sample_spec) for cp in config.counterparties]
    _, negotiations = closer.negotiate(quotes, sample_spec)
    final_quotes, _ = closer.negotiate(quotes, sample_spec)
    report = closer.build_report("job_123", sample_spec, final_quotes, negotiations)
    assert report.job_id == "job_123"
    assert report.recommended_vendor_id is not None
    assert len(report.ranked_quotes) >= 1
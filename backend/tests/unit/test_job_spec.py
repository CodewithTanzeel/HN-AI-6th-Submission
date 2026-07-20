from datetime import date

import pytest
from pydantic import ValidationError

from app.models.job_spec import (
    HomeDetails,
    InventoryItem,
    JobSpec,
    NegotiationResult,
    Quote,
    QuoteLineItem,
    QuoteOutcome,
    ServiceOptions,
)


def test_valid_job_spec():
    spec = JobSpec(
        origin="Rock Hill, SC",
        destination="Charlotte, NC",
        distance_miles=45,
        move_date=date(2026, 8, 1),
        home=HomeDetails(bedrooms=2, stairs=2),
        inventory=[InventoryItem(item="Couch", quantity=1)],
    )
    required = [
        "origin",
        "destination",
        "distance_miles",
        "move_date",
        "home.bedrooms",
        "inventory",
    ]
    assert spec.is_binding_ready(required)
    assert spec.missing_binding_fields(required) == []


def test_invalid_job_spec_missing_binding_fields():
    spec = JobSpec(origin="Rock Hill, SC")
    required = ["origin", "destination", "inventory"]
    assert not spec.is_binding_ready(required)
    assert "destination" in spec.missing_binding_fields(required)
    assert "inventory" in spec.missing_binding_fields(required)


def test_merge_voice_and_document_specs():
    voice = JobSpec(
        origin="Rock Hill, SC",
        destination="Charlotte, NC",
        home=HomeDetails(bedrooms=2, stairs=2),
    )
    document = JobSpec(
        distance_miles=45,
        move_date=date(2026, 8, 15),
        inventory=[InventoryItem(item="Piano", quantity=1)],
        services=ServiceOptions(packing=True),
    )
    merged = JobSpec.merge(voice, document)
    assert merged.origin == "Rock Hill, SC"
    assert merged.distance_miles == 45
    assert merged.home.bedrooms == 2
    assert merged.inventory[0].item == "Piano"
    assert merged.services.packing is True


def test_negative_bedrooms_rejected():
    with pytest.raises(ValidationError):
        HomeDetails(bedrooms=-1)


def test_quote_sync_total_from_line_items():
    """When Quote has line_items but total=0, total should sync from line items."""
    quote = Quote(
        vendor_id="sync_test",
        vendor_name="Test Co",
        negotiation_style="tough_negotiator",
        line_items=[
            QuoteLineItem(fee_type="base", description="Base rate", amount=500.0),
            QuoteLineItem(fee_type="stairs", description="Stairs", amount=100.0),
        ],
        total=0,
        outcome=QuoteOutcome.QUOTED,
    )
    assert quote.total == 600.0


def test_quote_line_item_negative_non_price_match_rejected():
    """Negative amount for non-price_match fee_type should raise ValueError."""
    with pytest.raises(ValueError, match="must be >= 0"):
        QuoteLineItem(fee_type="base", description="Base rate", amount=-50.0)


def test_quote_line_item_negative_price_match_allowed():
    """Negative amount for price_match fee_type should be allowed."""
    item = QuoteLineItem(fee_type="price_match", description="Discount", amount=-50.0)
    assert item.amount == -50.0


def test_negotiation_result_changed_true():
    """price_after < price_before should set changed=True."""
    result = NegotiationResult(
        vendor_id="v1",
        vendor_name="Test",
        price_before=1000.0,
        price_after=900.0,
        lever_used="price_match",
        evidence_snippet="Competing bid",
    )
    assert result.changed is True


def test_negotiation_result_changed_false():
    """price_after >= price_before should set changed=False."""
    result = NegotiationResult(
        vendor_id="v1",
        vendor_name="Test",
        price_before=1000.0,
        price_after=1000.0,
        lever_used="price_match",
        evidence_snippet="Competing bid",
    )
    assert result.changed is False


def test_job_spec_merge_services_union():
    """Services should be OR-merged (packing from either source)."""
    voice = JobSpec(services=ServiceOptions(packing=True, disassembly=False))
    document = JobSpec(services=ServiceOptions(packing=False, storage=True))
    merged = JobSpec.merge(voice, document)
    assert merged.services.packing is True
    assert merged.services.storage is True
    assert merged.services.disassembly is False


def test_job_spec_merge_inventory_union():
    """Inventory items should be deduplicated by lowercase name."""
    voice = JobSpec(inventory=[InventoryItem(item="Piano", quantity=1)])
    document = JobSpec(inventory=[InventoryItem(item="Piano", quantity=1), InventoryItem(item="Couch", quantity=2)])
    merged = JobSpec.merge(voice, document)
    assert len(merged.inventory) == 2
    items = {i.item.lower() for i in merged.inventory}
    assert "piano" in items
    assert "couch" in items


def test_job_spec_missing_binding_partial():
    """Mix of missing and present fields."""
    spec = JobSpec(
        origin="Rock Hill, SC",
        destination="Charlotte, NC",
        distance_miles=45.0,
    )
    required = ["origin", "destination", "distance_miles", "move_date", "inventory"]
    missing = spec.missing_binding_fields(required)
    assert "move_date" in missing
    assert "inventory" in missing
    assert "origin" not in missing


def test_home_details_defaults():
    """HomeDetails should have sensible defaults."""
    home = HomeDetails(bedrooms=3)
    assert home.stairs == 0
    assert home.elevator is False
    assert home.sqft is None


def test_empty_origin_not_binding_ready():
    """Empty string origin should not be considered binding ready."""
    spec = JobSpec(origin="")
    required = ["origin"]
    assert not spec.is_binding_ready(required)
    assert "origin" in spec.missing_binding_fields(required)
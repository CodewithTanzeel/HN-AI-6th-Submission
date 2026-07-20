import pytest

from app.services.document_intake import DocumentIntakeService


@pytest.fixture
def parser():
    return DocumentIntakeService()


def test_parse_quote_text(parser):
    content = """
    Moving quote for 2 bedroom apartment
    From Rock Hill to Charlotte, 45 miles
    Includes packing service and piano handling
    """
    spec = parser.parse_text_content(content)
    assert spec.origin == "Rock Hill, SC"
    assert spec.destination == "Charlotte, NC"
    assert spec.distance_miles == 45
    assert spec.home.bedrooms == 2
    assert any(item.item == "Piano" for item in spec.inventory)
    assert spec.services.packing is True


@pytest.mark.asyncio
async def test_parse_upload_bytes(parser):
    content = b"Quote PDF: Rock Hill to Charlotte, 2 bedroom, 45 miles, piano"
    spec = await parser.parse_upload("existing_quote.pdf", content)
    assert spec.origin == "Rock Hill, SC"
    assert spec.destination == "Charlotte, NC"
    assert spec.move_date is not None


def test_parse_text_3_bedroom(parser):
    """3 bedroom text should set bedrooms=3, stairs=1."""
    content = "3 bedroom apartment from Rock Hill to Charlotte"
    spec = parser.parse_text_content(content)
    assert spec.home is not None
    assert spec.home.bedrooms == 3
    assert spec.home.stairs == 1


def test_parse_text_no_match(parser):
    """Text with no matching keywords should return empty spec."""
    content = "This is completely unrelated text about nothing important"
    spec = parser.parse_text_content(content)
    assert spec.origin is None
    assert spec.destination is None
    assert spec.distance_miles is None


def test_parse_filename_hint(parser):
    """Filename like 'rock_hill_to_charlotte.txt' should parse."""
    spec = parser.parse_filename_hint("rock_hill_to_charlotte.txt")
    assert spec.origin == "Rock Hill, SC"
    assert spec.destination == "Charlotte, NC"


def test_parse_upload_empty_content(parser):
    """Empty content should fall back to filename parsing."""
    spec = parser.parse_text_content("")
    assert spec.origin is None
    spec2 = parser.parse_text_content("rock_hill_to_charlotte.txt")
    assert spec2.origin == "Rock Hill, SC" or spec2.destination == "Charlotte, NC"
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class HomeDetails(BaseModel):
    bedrooms: int = Field(ge=0)
    sqft: Optional[int] = Field(default=None, ge=0)
    floor: Optional[int] = None
    stairs: int = Field(default=0, ge=0)
    elevator: bool = False


class InventoryItem(BaseModel):
    item: str
    quantity: int = Field(default=1, ge=1)
    special_handling: Optional[str] = None


class ServiceOptions(BaseModel):
    packing: bool = False
    disassembly: bool = False
    storage: bool = False
    insurance: bool = False


class JobSpec(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    distance_miles: Optional[float] = Field(default=None, ge=0)
    move_date: Optional[date] = None
    home: Optional[HomeDetails] = None
    inventory: list[InventoryItem] = Field(default_factory=list)
    services: ServiceOptions = Field(default_factory=ServiceOptions)
    confirmed_by_user: bool = False
    confirmed_at: Optional[datetime] = None

    def missing_binding_fields(self, required_fields: list[str]) -> list[str]:
        missing: list[str] = []
        for field_path in required_fields:
            if not self._has_field(field_path):
                missing.append(field_path)
        return missing

    def is_binding_ready(self, required_fields: list[str]) -> bool:
        return len(self.missing_binding_fields(required_fields)) == 0

    def _has_field(self, field_path: str) -> bool:
        parts = field_path.split(".")
        value: object = self
        for part in parts:
            if value is None:
                return False
            if isinstance(value, BaseModel):
                value = getattr(value, part, None)
            else:
                return False
        if value is None:
            return False
        if isinstance(value, list):
            return len(value) > 0
        if isinstance(value, str):
            return bool(value.strip())
        return True

    @classmethod
    def merge(cls, primary: "JobSpec", secondary: "JobSpec") -> "JobSpec":
        data = primary.model_dump()
        secondary_data = secondary.model_dump(exclude_none=True)
        for key, value in secondary_data.items():
            if key in {"inventory", "services"}:
                continue
            if value is None:
                continue
            current = data.get(key)
            if current in (None, "", [], {}):
                data[key] = value
        merged_inventory = {item["item"].lower(): item for item in data.get("inventory", [])}
        for item in secondary.inventory:
            merged_inventory[item.item.lower()] = item.model_dump()
        data["inventory"] = list(merged_inventory.values())
        services = ServiceOptions(**data.get("services", {}))
        secondary_services = secondary.services
        data["services"] = ServiceOptions(
            packing=services.packing or secondary_services.packing,
            disassembly=services.disassembly or secondary_services.disassembly,
            storage=services.storage or secondary_services.storage,
            insurance=services.insurance or secondary_services.insurance,
        ).model_dump()
        return cls.model_validate(data)


class QuoteOutcome(str, Enum):
    QUOTED = "quoted"
    CALLBACK = "callback"
    DECLINED = "declined"


class QuoteLineItem(BaseModel):
    fee_type: str
    description: str
    amount: float

    @model_validator(mode="after")
    def validate_amount(self) -> "QuoteLineItem":
        # Allow negative amounts for price_match adjustments (discounts)
        if self.fee_type == "price_match" and self.amount < 0:
            return self
        if self.amount < 0:
            raise ValueError(f"Amount must be >= 0 for fee_type '{self.fee_type}', got {self.amount}")
        return self


class Quote(BaseModel):
    vendor_id: str
    vendor_name: str
    negotiation_style: str
    line_items: list[QuoteLineItem] = Field(default_factory=list)
    total: float = Field(ge=0)
    binding: bool = False
    valid_until: Optional[date] = None
    outcome: QuoteOutcome = QuoteOutcome.QUOTED
    transcript_url: Optional[str] = None
    recording_url: Optional[str] = None
    red_flag: Optional[str] = None

    @model_validator(mode="after")
    def sync_total(self) -> "Quote":
        if self.line_items and self.total == 0:
            self.total = round(sum(item.amount for item in self.line_items), 2)
        return self


class NegotiationResult(BaseModel):
    vendor_id: str
    vendor_name: str
    price_before: float
    price_after: float
    lever_used: str
    evidence_snippet: str
    changed: bool = False

    @model_validator(mode="after")
    def compute_changed(self) -> "NegotiationResult":
        self.changed = self.price_after < self.price_before
        return self


class CallOutcome(str, Enum):
    QUOTED = "quoted"
    CALLBACK = "callback"
    DECLINED = "declined"


class RankedQuote(BaseModel):
    rank: int
    quote: Quote
    recommendation_reason: str


class JobReport(BaseModel):
    job_id: str
    recommended_vendor_id: Optional[str]
    ranked_quotes: list[RankedQuote]
    negotiations: list[NegotiationResult]
    red_flags: list[str]
    summary: str

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class BenchmarksConfig(BaseModel):
    price_per_mile: float
    price_per_bedroom: float
    base_fee: float
    market_example: dict = Field(default_factory=dict)


class RedFlagsConfig(BaseModel):
    below_market_pct: float


class CounterpartyConfig(BaseModel):
    id: str
    name: str
    phone: str
    negotiation_style: str
    base_multiplier: float = 1.0
    hidden_fees: list[dict] = Field(default_factory=list)
    upsell_fees: list[dict] = Field(default_factory=list)


class DemoMoverConfig(BaseModel):
    id: str
    name: str
    phone: str
    rating: float


class VerticalConfig(BaseModel):
    vertical: str
    display_name: str
    job_spec: dict = Field(default_factory=dict)
    benchmarks: BenchmarksConfig
    red_flags: RedFlagsConfig
    negotiation_levers: list[str] = Field(default_factory=list)
    ai_disclosure: str
    counterparties: list[CounterpartyConfig] = Field(default_factory=list)
    demo_movers: list[DemoMoverConfig] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)


def load_vertical_config(path: str | Path) -> VerticalConfig:
    config_path = Path(path)
    if not config_path.is_absolute():
        repo_root = Path(__file__).resolve().parents[3]
        config_path = repo_root / config_path
    with config_path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return VerticalConfig.model_validate(data)

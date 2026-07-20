from datetime import date, timedelta

from app.config.loader import CounterpartyConfig, VerticalConfig
from app.models.job_spec import JobSpec, Quote, QuoteLineItem, QuoteOutcome


class QuoteBuilder:
    def __init__(self, config: VerticalConfig):
        self.config = config

    def estimate_market_price(self, spec: JobSpec) -> float:
        benchmarks = self.config.benchmarks
        bedrooms = spec.home.bedrooms if spec.home else 2
        miles = spec.distance_miles or 45
        return round(
            benchmarks.base_fee
            + (benchmarks.price_per_mile * miles)
            + (benchmarks.price_per_bedroom * bedrooms),
            2,
        )

    def build_quote(self, counterparty: CounterpartyConfig, spec: JobSpec) -> Quote:
        market = self.estimate_market_price(spec)
        base = round(market * counterparty.base_multiplier, 2)
        line_items = [
            QuoteLineItem(
                fee_type="base",
                description="Base moving rate",
                amount=base,
            )
        ]
        if spec.home and spec.home.stairs > 0 and counterparty.negotiation_style != "hidden_fees_lowballer":
            line_items.append(
                QuoteLineItem(
                    fee_type="stairs",
                    description=f"Stair carry ({spec.home.stairs} flights)",
                    amount=round(35 * spec.home.stairs, 2),
                )
            )
        for fee in counterparty.hidden_fees:
            line_items.append(
                QuoteLineItem(
                    fee_type=fee["fee_type"],
                    description=fee["description"],
                    amount=fee["amount"],
                )
            )
        for fee in counterparty.upsell_fees:
            line_items.append(
                QuoteLineItem(
                    fee_type=fee["fee_type"],
                    description=fee["description"],
                    amount=fee["amount"],
                )
            )
        total = round(sum(item.amount for item in line_items), 2)
        return Quote(
            vendor_id=counterparty.id,
            vendor_name=counterparty.name,
            negotiation_style=counterparty.negotiation_style,
            line_items=line_items,
            total=total,
            binding=counterparty.negotiation_style == "tough_negotiator",
            valid_until=date.today() + timedelta(days=7),
            outcome=QuoteOutcome.QUOTED,
            transcript_url=f"/static/transcripts/{counterparty.id}.txt",
            recording_url=f"/static/recordings/{counterparty.id}.mp3",
        )

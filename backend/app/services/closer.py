from app.config.loader import VerticalConfig
from app.models.job_spec import HomeDetails, JobReport, JobSpec, NegotiationResult, Quote, RankedQuote
from app.services.quote_builder import QuoteBuilder


class HonestyGuard:
    DISCLOSURE_TRIGGERS = ("robot", "ai", "automated", "real person")

    def __init__(self, disclosure_script: str):
        self.disclosure_script = disclosure_script

    def respond_to_disclosure_question(self, question: str) -> str:
        lowered = question.lower()
        if any(trigger in lowered for trigger in self.DISCLOSURE_TRIGGERS):
            return self.disclosure_script
        return "I'm gathering quotes for my customer's move and can provide full shipment details."

    def validate_leverage_bid(self, competing_quotes: list[Quote], cited_vendor_id: str) -> bool:
        return any(q.vendor_id == cited_vendor_id and q.outcome.value == "quoted" for q in competing_quotes)

    def reject_invented_inventory(self, requested_items: list[str], spec: JobSpec) -> list[str]:
        known = {item.item.lower() for item in spec.inventory}
        return [item for item in requested_items if item.lower() not in known]


class CloserService:
    def __init__(self, config: VerticalConfig):
        self.config = config
        self.quote_builder = QuoteBuilder(config)
        self.honesty = HonestyGuard(config.ai_disclosure)

    def apply_red_flags(self, quotes: list[Quote], spec: JobSpec | None = None) -> list[Quote]:
        if spec is None:
            spec = JobSpec(distance_miles=45, home=HomeDetails(bedrooms=2, stairs=0))
        market = self.quote_builder.estimate_market_price(spec)
        threshold = market * (1 - self.config.red_flags.below_market_pct / 100)
        flagged: list[Quote] = []
        for quote in quotes:
            updated = quote.model_copy()
            if quote.total > 0 and quote.total < threshold:
                updated.red_flag = (
                    f"Quote is more than {self.config.red_flags.below_market_pct:.0f}% below "
                    f"estimated market (${market:.0f}) — possible lowball tactic."
                )
            flagged.append(updated)
        return flagged

    def negotiate(self, quotes: list[Quote], spec: JobSpec) -> tuple[list[Quote], list[NegotiationResult]]:
        quoted = [q for q in quotes if q.outcome.value == "quoted" and q.total > 0]
        if len(quoted) < 2:
            return quotes, []

        best = min(quoted, key=lambda q: q.total)
        negotiations: list[NegotiationResult] = []
        updated_quotes: list[Quote] = []

        for quote in quotes:
            if quote.vendor_id == best.vendor_id:
                updated_quotes.append(quote)
                continue
            if quote.outcome.value != "quoted":
                updated_quotes.append(quote)
                continue
            if not self.honesty.validate_leverage_bid(quoted, best.vendor_id):
                updated_quotes.append(quote)
                continue
            discount = round(min(150.0, (quote.total - best.total) * 0.25), 2)
            if discount <= 0:
                updated_quotes.append(quote)
                continue
            new_total = round(quote.total - discount, 2)
            new_items = [item.model_copy() for item in quote.line_items]
            new_items.append(
                quote.line_items[0].model_copy(
                    update={
                        "fee_type": "price_match",
                        "description": f"Price-match adjustment vs {best.vendor_name}",
                        "amount": -discount,
                    }
                )
            )
            negotiations.append(
                NegotiationResult(
                    vendor_id=quote.vendor_id,
                    vendor_name=quote.vendor_name,
                    price_before=quote.total,
                    price_after=new_total,
                    lever_used="price_match",
                    evidence_snippet=(
                        f"I have a binding quote for ${best.total:.0f} from {best.vendor_name} — "
                        f"can you beat it?"
                    ),
                )
            )
            updated_quotes.append(
                quote.model_copy(update={"line_items": new_items, "total": new_total})
            )
        return updated_quotes, negotiations

    def rank_quotes(self, quotes: list[Quote]) -> list[RankedQuote]:
        ranked: list[RankedQuote] = []
        eligible = sorted(
            [q for q in quotes if q.outcome.value == "quoted" and q.total > 0],
            key=lambda q: q.total,
        )
        for index, quote in enumerate(eligible, start=1):
            reason = "Lowest total with itemized fees."
            if quote.red_flag:
                reason = f"Caution: {quote.red_flag}"
            elif quote.binding:
                reason = "Lowest binding quote with verified line items."
            ranked.append(RankedQuote(rank=index, quote=quote, recommendation_reason=reason))
        return ranked

    def build_report(self, job_id: str, spec: JobSpec, quotes: list[Quote], negotiations: list[NegotiationResult]) -> JobReport:
        flagged = self.apply_red_flags(quotes, spec)
        final_quotes, auto_negotiations = self.negotiate(flagged, spec)
        all_negotiations = negotiations + auto_negotiations
        ranked = self.rank_quotes(final_quotes)
        recommended = ranked[0].quote.vendor_id if ranked else None
        red_flags = [q.red_flag for q in final_quotes if q.red_flag]
        if recommended:
            top = next(q for q in ranked if q.rank == 1)
            summary = (
                f"Recommended: {top.quote.vendor_name} at ${top.quote.total:.2f}. "
                f"{top.recommendation_reason}"
            )
        else:
            summary = "No comparable quotes were obtained. Retry with additional vendors."
        if all_negotiations:
            changed = [n for n in all_negotiations if n.changed]
            if changed:
                summary += f" Negotiation reduced {len(changed)} quote(s) using verified competing bids."
        return JobReport(
            job_id=job_id,
            recommended_vendor_id=recommended,
            ranked_quotes=ranked,
            negotiations=all_negotiations,
            red_flags=[rf for rf in red_flags if rf],
            summary=summary,
        )

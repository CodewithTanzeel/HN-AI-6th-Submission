import asyncio

from app.config.loader import VerticalConfig
from app.models.job_spec import JobSpec, Quote, QuoteOutcome
from app.services.call_list import CallListService
from app.services.quote_builder import QuoteBuilder


class CallerService:
    def __init__(self, config: VerticalConfig):
        self.config = config
        self.call_list = CallListService(config)
        self.quote_builder = QuoteBuilder(config)

    async def _call_counterparty(self, counterparty, spec: JobSpec) -> Quote:
        await asyncio.sleep(0)
        if counterparty.negotiation_style == "stonewaller":
            return Quote(
                vendor_id=counterparty.id,
                vendor_name=counterparty.name,
                negotiation_style=counterparty.negotiation_style,
                line_items=[],
                total=0,
                outcome=QuoteOutcome.CALLBACK,
                transcript_url=f"/static/transcripts/{counterparty.id}.txt",
            )
        return self.quote_builder.build_quote(counterparty, spec)

    async def gather_quotes(self, spec: JobSpec) -> list[Quote]:
        counterparties = self.call_list.get_counterparties()
        tasks = [self._call_counterparty(cp, spec) for cp in counterparties]
        return list(await asyncio.gather(*tasks))

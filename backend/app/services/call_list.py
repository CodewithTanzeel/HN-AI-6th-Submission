from app.config.loader import VerticalConfig, DemoMoverConfig


class CallListService:
    def __init__(self, config: VerticalConfig):
        self.config = config

    def get_demo_movers(self, limit: int = 3) -> list[DemoMoverConfig]:
        return self.config.demo_movers[:limit]

    def get_counterparties(self) -> list:
        return self.config.counterparties

    def build_call_list(self, origin: str | None = None, limit: int = 3) -> list[dict]:
        movers = self.get_demo_movers(limit=limit)
        return [
            {
                "id": mover.id,
                "name": mover.name,
                "phone": mover.phone,
                "rating": mover.rating,
                "origin_filter": origin,
            }
            for mover in movers
        ]

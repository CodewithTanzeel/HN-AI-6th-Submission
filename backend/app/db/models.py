import json
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class JobRecord(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    voice_spec_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_spec_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    merged_spec_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quotes_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    negotiations_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def set_json_field(self, field: str, value: object) -> None:
        setattr(self, field, json.dumps(value, default=str))

    def get_json_field(self, field: str) -> object | None:
        raw = getattr(self, field)
        if raw is None:
            return None
        return json.loads(raw)

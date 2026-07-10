import datetime

from sqlalchemy import Column, DateTime, String

from core.database import Base


class ProcessedWebhook(Base):
    """
    Idempotency state machine lock for Stripe Webhooks.
    Guarantees absolute idempotency by preventing duplicate event_id processing.
    """
    __tablename__ = "processed_webhooks"

    event_id = Column(String(255), primary_key=True, unique=True, index=True)
    processed_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

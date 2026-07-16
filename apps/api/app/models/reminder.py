import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base

class ReminderLog(Base):
    __tablename__ = "reminder_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    reminder_type = Column(String, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

from sqlalchemy import Column, Date, Numeric, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base
import uuid

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    amount = Column(Numeric, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String, nullable=False, default="sent")
    description = Column(String, nullable=True, default="")

    
    def __repr__(self):
        return f"<Invoice(id={self.id}, user_id={self.user_id}, client_id={self.client_id}, amount={self.amount}, due_date={self.due_date}, status={self.status})>"
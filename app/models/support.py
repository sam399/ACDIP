from sqlalchemy import Column, DateTime, Integer, String, Text
from app.database import Base
from app.models.common import utc_now


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, default="Open", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

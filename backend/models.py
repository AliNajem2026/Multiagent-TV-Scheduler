from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime
from backend.database import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    day = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    schedule_data = Column(JSON, nullable=False)


from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime, timezone
from database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Execution(Base):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, index=True)
    pipeline_id = Column(Integer, nullable=False, index=True)
    pipeline_name = Column(String(150), nullable=False)

    status = Column(String(30), nullable=False)
    retry_count = Column(Integer, default=0)
    simulate_failure = Column(Boolean, default=False)

    start_time = Column(DateTime(timezone=True), default=utc_now)
    end_time = Column(DateTime(timezone=True), nullable=True)

    error_message = Column(String(500), nullable=True)

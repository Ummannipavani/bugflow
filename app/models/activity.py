from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.database.database import Base


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)

    issue_id = Column(
    Integer,
    ForeignKey("issues.id", ondelete="CASCADE"),
    index=True
)

    action = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow)
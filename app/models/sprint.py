from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database.database import Base


class Sprint(Base):

    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)

    start_date = Column(Date)

    end_date = Column(Date)

    status = Column(String, default="Active",index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    issues = relationship("Issue", back_populates="sprint")
from sqlalchemy import Column, Integer, String, Text, Date
from app.database.database import Base


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(200))

    project = Column(String(100))

    priority = Column(String(20))

    severity = Column(String(20))

    description = Column(Text)

    screenshot = Column(String(255), nullable=True)

    status = Column(String(20), default="Reported")
    
    due_date = Column(Date)
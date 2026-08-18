from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

from app.database.database import Base


class Attachment(Base):

    __tablename__ = "attachments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    issue_id = Column(
        Integer,
        ForeignKey("issues.id"),
        nullable=False
    )

    filename = Column(
        String(255),
        nullable=False
    )

    original_filename = Column(
        String(255),
        nullable=False
    )

    file_path = Column(
        String(500),
        nullable=False
    )

    uploaded_at = Column(
        DateTime,
        default=datetime.utcnow
    )
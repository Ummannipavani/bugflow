from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database.database import Base
from datetime import datetime


class Issue(Base):

    __tablename__ = "issues"

    # ==========================
    # BASIC ISSUE INFORMATION
    # ==========================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(200)
    )

    project = Column(
        String(100),
        index=True
    )

    description = Column(
        Text
    )

    # ==========================
    # AI / DEFECT ANALYSIS
    # ==========================

    category = Column(
        String(50),
        nullable=True,
        index=True
    )

    defect_type = Column(
        String(50),
        nullable=True,
        index=True
    )

    module = Column(
        String(100),
        nullable=True,
        index=True
    )
    ai_summary = Column(
        Text,
        nullable=True
    )
    embedding = Column(
        Vector(3072),
        nullable=True
    )
    # ==========================
    # AI RESOLUTION ASSISTANCE
    # ==========================

    ai_root_cause = Column(
        Text,
        nullable=True
    )

    ai_suggested_fix = Column(
        Text,
        nullable=True
    )

    ai_recommended_solution = Column(
        Text,
        nullable=True
    )

    ai_investigation_steps = Column(
        Text,
        nullable=True
    )

    ai_confidence = Column(
        String(20),
        nullable=True
    )

    ai_explanation = Column(
        Text,
        nullable=True
    )

    ai_prevention = Column(
        Text,
        nullable=True
    )
    # ==========================
    # PRIORITY & SEVERITY
    # ==========================

    priority = Column(
        String(20),
        index=True
    )

    severity = Column(
        String(20),
        index=True
    )

    # ==========================
    # STATUS
    # ==========================

    status = Column(
        String(20),
        default="Reported",
        index=True
    )
    # ==========================
# TIMESTAMPS
# ==========================

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    resolved_at = Column(
        DateTime,
        nullable=True
    )

    closed_at = Column(
        DateTime,
        nullable=True
    )
    # ==========================
    # SCREENSHOT
    # ==========================

    screenshot = Column(
        String(255),
        nullable=True
    )

    # ==========================
    # DUE DATE
    # ==========================

    due_date = Column(
        Date
    )

    # ==========================
    # SPRINT
    # ==========================

    sprint_id = Column(
        Integer,
        ForeignKey("sprints.id"),
        nullable=True,
        index=True
    )

    sprint = relationship(
        "Sprint",
        back_populates="issues"
    )

    # ==========================
    # ASSIGNEE
    # ==========================

    assigned_to = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    assignee = relationship(
        "User",
        foreign_keys=[assigned_to]
    )
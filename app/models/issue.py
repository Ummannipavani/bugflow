from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database.database import Base


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
        String(100)
    )

    description = Column(
        Text
    )

    # ==========================
    # AI / DEFECT ANALYSIS
    # ==========================

    category = Column(
        String(50),
        nullable=True
    )

    defect_type = Column(
        String(50),
        nullable=True
    )

    module = Column(
        String(100),
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
        String(20)
    )

    severity = Column(
        String(20)
    )

    # ==========================
    # STATUS
    # ==========================

    status = Column(
        String(20),
        default="Reported"
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
        nullable=True
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
        nullable=True
    )

    assignee = relationship(
        "User",
        foreign_keys=[assigned_to]
    )
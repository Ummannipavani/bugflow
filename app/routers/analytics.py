from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.database import get_db
from app.models.issue import Issue
from app.models.user import User

templates = Jinja2Templates(
    directory="templates"
)
router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

@router.get("")
def analytics_page(
    request: Request
):
    return templates.TemplateResponse(
        request=request,
        name="analytics.html",
        context={
            "request": request
        }
    )
# =========================================================
# ANALYTICS SUMMARY
# =========================================================

@router.get("/summary")
def analytics_summary(
    db: Session = Depends(get_db)
):

    total = db.query(Issue).count()

    open_count = db.query(Issue).filter(
        Issue.status == "Open"
    ).count()

    in_progress = db.query(Issue).filter(
        Issue.status == "In Progress"
    ).count()

    in_review = db.query(Issue).filter(
        Issue.status == "In Review"
    ).count()

    resolved = db.query(Issue).filter(
        Issue.status == "Resolved"
    ).count()

    verified = db.query(Issue).filter(
        Issue.status == "Verified"
    ).count()

    closed = db.query(Issue).filter(
        Issue.status == "Closed"
    ).count()

    reopened = db.query(Issue).filter(
        Issue.status == "Reopened"
    ).count()

    return {

        "total": total,

        "open": open_count,

        "in_progress": in_progress,

        "in_review": in_review,

        "resolved": resolved,

        "verified": verified,

        "closed": closed,

        "reopened": reopened

    }
# =========================================================
# DEFECTS BY SEVERITY
# =========================================================

@router.get("/severity")
def analytics_severity(
    db: Session = Depends(get_db)
):

    results = (
        db.query(
            Issue.severity,
            func.count(Issue.id)
        )
        .group_by(Issue.severity)
        .all()
    )

    return {
        "severity": [
            {
                "name": severity or "Unknown",
                "count": count
            }
            for severity, count in results
        ]
    }
# =========================================================
# DEFECTS BY CATEGORY
# =========================================================

@router.get("/category")
def analytics_category(
    db: Session = Depends(get_db)
):

    results = (
        db.query(
            Issue.category,
            func.count(Issue.id)
        )
        .group_by(Issue.category)
        .all()
    )

    return {
        "categories": [
            {
                "name": category or "Unknown",
                "count": count
            }
            for category, count in results
        ]
    }
# =========================================================
# DEFECTS BY STATUS
# =========================================================

@router.get("/status")
def analytics_status(
    db: Session = Depends(get_db)
):

    results = (
        db.query(
            Issue.status,
            func.count(Issue.id)
        )
        .group_by(Issue.status)
        .all()
    )

    return {
        "statuses": [
            {
                "name": status or "Unknown",
                "count": count
            }
            for status, count in results
        ]
    }
# =========================================================
# DEVELOPER WORKLOAD
# =========================================================

@router.get("/developers")
def developer_workload(
    db: Session = Depends(get_db)
):

    results = (
        db.query(
            User.id,
            User.name,
            func.count(Issue.id)
        )
        .join(
            Issue,
            Issue.assigned_to == User.id
        )
        .filter(
            User.role == "Developer"
        )
        .group_by(
            User.id,
            User.name
        )
        .all()
    )

    return {
        "developers": [
            {
                "id": user_id,
                "name": name,
                "issues": count
            }
            for user_id, name, count in results
        ]
    }
# =========================================================
# AVERAGE RESOLUTION TIME
# =========================================================

@router.get("/resolution-time")
def average_resolution_time(
    db: Session = Depends(get_db)
):

    issues = (
        db.query(Issue)
        .filter(
            Issue.resolved_at.isnot(None),
            Issue.created_at.isnot(None)
        )
        .all()
    )

    if not issues:

        return {
            "average_hours": 0
        }

    total_seconds = 0

    for issue in issues:

        difference = (
            issue.resolved_at -
            issue.created_at
        )

        total_seconds += (
            difference.total_seconds()
        )

    average_seconds = (
        total_seconds / len(issues)
    )

    average_hours = (
        average_seconds / 3600
    )

    return {
        "average_hours": round(
            average_hours,
            2
        )
    }
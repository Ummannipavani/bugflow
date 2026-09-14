from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.sprint import Sprint


from app.auth.dependencies import get_current_user
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
    request: Request,
    current_user: dict = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
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
# =========================================================
# MOST AFFECTED MODULES / COMPONENTS
# =========================================================

@router.get("/modules")
def most_affected_modules(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    results = (
        db.query(
            Issue.module,
            func.count(Issue.id).label("count")
        )
        .filter(
            Issue.module.isnot(None),
            Issue.module != ""
        )
        .group_by(Issue.module)
        .order_by(
            func.count(Issue.id).desc()
        )
        .all()
    )

    return {
        "modules": [
            {
                "name": module,
                "count": count
            }
            for module, count in results
        ]
    }


# =========================================================
# REPEATED DEFECTS
# =========================================================

@router.get("/repeated-defects")
def repeated_defects(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    results = (
        db.query(
            Issue.title,
            func.count(Issue.id).label("count")
        )
        .filter(
            Issue.title.isnot(None),
            Issue.title != ""
        )
        .group_by(Issue.title)
        .having(
            func.count(Issue.id) > 1
        )
        .order_by(
            func.count(Issue.id).desc()
        )
        .all()
    )

    return {
        "repeated_defects": [
            {
                "title": title,
                "count": count
            }
            for title, count in results
        ]
    }


# =========================================================
# CRITICAL DEFECT TRENDS
# =========================================================

@router.get("/critical-trends")
def critical_defect_trends(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    results = (
        db.query(
            func.date_trunc(
                "month",
                Issue.created_at
            ).label("month"),
            func.count(Issue.id).label("count")
        )
        .filter(
            Issue.severity == "Critical",
            Issue.created_at.isnot(None)
        )
        .group_by(
            func.date_trunc(
                "month",
                Issue.created_at
            )
        )
        .order_by(
            func.date_trunc(
                "month",
                Issue.created_at
            )
        )
        .all()
    )

    return {
        "critical_trends": [
            {
                "month": month.strftime("%Y-%m")
                if month else "Unknown",
                "count": count
            }
            for month, count in results
        ]
    }


# =========================================================
# DEFECT BACKLOG
# =========================================================

@router.get("/backlog")
def defect_backlog(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    backlog_statuses = [
        "Open",
        "Reported",
        "In Progress",
        "In Review",
        "Reopened"
    ]

    backlog = (
        db.query(Issue)
        .filter(
            Issue.status.in_(backlog_statuses)
        )
        .count()
    )

    resolved_or_closed = (
        db.query(Issue)
        .filter(
            Issue.status.in_(
                [
                    "Resolved",
                    "Verified",
                    "Closed"
                ]
            )
        )
        .count()
    )

    return {
        "backlog": backlog,
        "resolved_or_closed": resolved_or_closed
    }


# =========================================================
# RESOLUTION TRENDS
# =========================================================

@router.get("/resolution-trends")
def resolution_trends(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    created_results = (
        db.query(
            func.date_trunc(
                "month",
                Issue.created_at
            ).label("month"),
            func.count(Issue.id).label("count")
        )
        .filter(
            Issue.created_at.isnot(None)
        )
        .group_by(
            func.date_trunc(
                "month",
                Issue.created_at
            )
        )
        .all()
    )

    resolved_results = (
        db.query(
            func.date_trunc(
                "month",
                Issue.resolved_at
            ).label("month"),
            func.count(Issue.id).label("count")
        )
        .filter(
            Issue.resolved_at.isnot(None)
        )
        .group_by(
            func.date_trunc(
                "month",
                Issue.resolved_at
            )
        )
        .all()
    )

    created_map = {
        month.strftime("%Y-%m"): count
        for month, count in created_results
        if month
    }

    resolved_map = {
        month.strftime("%Y-%m"): count
        for month, count in resolved_results
        if month
    }

    months = sorted(
        set(created_map.keys()) |
        set(resolved_map.keys())
    )

    return {
        "resolution_trends": [
            {
                "month": month,
                "created": created_map.get(
                    month,
                    0
                ),
                "resolved": resolved_map.get(
                    month,
                    0
                )
            }
            for month in months
        ]
    }


# =========================================================
# SPRINT DEFECT TRENDS
# =========================================================

@router.get("/sprint-trends")
def sprint_defect_trends(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    results = (
        db.query(
            Sprint.id,
            Sprint.name,
            func.count(Issue.id).label("total"),
            func.sum(
                case(
                    (
                        Issue.status.in_(
                            [
                                "Resolved",
                                "Verified",
                                "Closed"
                            ]
                        ),
                        1
                    ),
                    else_=0
                )
            ).label("resolved"),
            func.sum(
                case(
                    (
                        Issue.status.in_(
                            [
                                "Open",
                                "Reported",
                                "In Progress",
                                "In Review",
                                "Reopened"
                            ]
                        ),
                        1
                    ),
                    else_=0
                )
            ).label("active")
        )
        .outerjoin(
            Issue,
            Issue.sprint_id == Sprint.id
        )
        .group_by(
            Sprint.id,
            Sprint.name
        )
        .order_by(
            Sprint.id
        )
        .all()
    )

    return {
        "sprint_trends": [
            {
                "id": sprint_id,
                "name": name,
                "total": total or 0,
                "resolved": resolved or 0,
                "active": active or 0
            }
            for (
                sprint_id,
                name,
                total,
                resolved,
                active
            ) in results
        ]
    }
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

# Routers
from app.routers.user import router as user_router
from app.routers.issue import router as issue_router
from app.routers.project import router as project_router
from app.routers.ai import router as ai_router
from app.routers.comment import router as comment_router
from app.routers.sprint import router as sprint_router
from app.routers.attachment import router as attachment_router
from app.routers.analytics import router as analytics_router
# Database
from app.database.database import Base, engine, SessionLocal
from sqlalchemy.orm import joinedload

# Models
from app.models.user import User
from app.models.issue import Issue
from app.models.project import Project
from app.models.activity import Activity
from app.models.comment import Comment
from app.models.sprint import Sprint
from app.models.attachment import Attachment

from starlette.middleware.sessions import SessionMiddleware
from datetime import date
load_dotenv()

SESSION_SECRET = os.getenv("SECRET_KEY")

if not SESSION_SECRET:
    raise RuntimeError(
        "SECRET_KEY is not configured in the environment."
    )
app = FastAPI(
    title="BugFlow API",
    description="""
    BugFlow - Intelligent Software Defect Tracking System

    REST API for managing:
    - Users and authentication
    - Software defects
    - Projects
    - Sprints
    - Comments
    - Attachments
    - Analytics
    - AI-assisted defect resolution
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(user_router)
app.include_router(issue_router)
app.include_router(project_router)
app.include_router(ai_router)
app.include_router(comment_router)
app.include_router(sprint_router)
app.include_router(attachment_router)
app.include_router(analytics_router)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="static/uploads"), name="uploads")
# Templates
templates = Jinja2Templates(directory="templates")


# ==========================
# Login Page
# ==========================
@app.get("/")
def login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html"
    )


# ==========================
# Register Page
# ==========================
@app.get("/register")
def register(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="register.html"
    )


@app.get("/dashboard")
def dashboard(request: Request):

    user = request.session.get("user")
    if not user:
        return RedirectResponse(
            url="/",
            status_code=302
        )
    db = SessionLocal()

    # =========================================================
    # ALL ISSUES
    # =========================================================

    all_issues = (
        db.query(Issue)
        .order_by(Issue.id.desc())
        .all()
    )

    # =========================================================
    # LATEST 5 ISSUES
    # =========================================================

    issues = (
        db.query(Issue)
        .order_by(Issue.id.desc())
        .limit(5)
        .all()
    )

    today = date.today()

    # =========================================================
    # NOTIFICATIONS
    # =========================================================

    generated_notifications = []

    for issue in all_issues:

        if issue.status not in [
            "Resolved",
            "Verified",
            "Closed"
        ]:

            if issue.due_date:

                days = (
                    issue.due_date - today
                ).days

                if days < 0:

                    generated_notifications.append(
                        f"🔴 {issue.title} is overdue by {-days} day(s)."
                    )

                elif days == 0:

                    generated_notifications.append(
                        f"⚠ {issue.title} is due today."
                    )

                elif days == 1:

                    generated_notifications.append(
                        f"📅 {issue.title} is due tomorrow."
                    )

            if issue.severity == "Critical":

                generated_notifications.append(
                    f"🚨 Critical issue: {issue.title}"
                )

    # =========================================================
    # REMOVE NOTIFICATIONS ALREADY VIEWED
    # =========================================================

    read_notifications = request.session.get(
        "read_notifications",
        []
    )

    notifications = [
        notification
        for notification in generated_notifications
        if notification not in read_notifications
    ]

    # Save current notifications
    # for the "View All" button

    request.session["current_notifications"] = (
        generated_notifications
    )

    # =========================================================
    # RECENT ACTIVITY
    # =========================================================

    activities = (
        db.query(Activity)
        .order_by(Activity.id.desc())
        .limit(6)
        .all()
    )

    # =========================================================
    # BASIC STATISTICS
    # =========================================================

    total_issues = len(all_issues)

    total_projects = db.query(Project).count()

    critical_bugs = sum(
        1
        for issue in all_issues
        if issue.severity == "Critical"
    )

    # =========================================================
    # STATUS COUNTS
    # =========================================================

    reported = sum(
        1
        for issue in all_issues
        if issue.status in ["Reported", "Open"]
    )

    in_progress = sum(
        1
        for issue in all_issues
        if issue.status == "In Progress"
    )

    in_review = sum(
        1
        for issue in all_issues
        if issue.status == "In Review"
    )

    resolved = sum(
        1
        for issue in all_issues
        if issue.status == "Resolved"
    )

    reopened = sum(
        1
        for issue in all_issues
        if issue.status == "Reopened"
    )

    verified = sum(
        1
        for issue in all_issues
        if issue.status == "Verified"
    )

    closed = sum(
        1
        for issue in all_issues
        if issue.status == "Closed"
    )

    # =========================================================
    # ACTIVE / COMPLETED
    # =========================================================

    active_issues = sum(
        1
        for issue in all_issues
        if issue.status not in [
            "Resolved",
            "Verified",
            "Closed"
        ]
    )

    completed_issues = (
        resolved +
        verified +
        closed
    )

    # =========================================================
    # OVERDUE ISSUES
    # =========================================================

    overdue_issues = sum(
        1
        for issue in all_issues
        if (
            issue.due_date
            and issue.due_date < today
            and issue.status not in [
                "Resolved",
                "Verified",
                "Closed"
            ]
        )
    )

    # =========================================================
    # UNASSIGNED ISSUES
    # =========================================================

    unassigned_issues = sum(
        1
        for issue in all_issues
        if issue.assigned_to is None
    )

    # =========================================================
    # HIGH PRIORITY ISSUES
    # =========================================================

    high_priority = sum(
        1
        for issue in all_issues
        if issue.priority in ["P1", "P2"]
    )

    # =========================================================
    # PRIORITY COUNTS
    # =========================================================

    p1_count = sum(
        1
        for issue in all_issues
        if issue.priority == "P1"
    )

    p2_count = sum(
        1
        for issue in all_issues
        if issue.priority == "P2"
    )

    p3_count = sum(
        1
        for issue in all_issues
        if issue.priority == "P3"
    )

    # =========================================================
    # MY ASSIGNED ISSUES
    # =========================================================

    my_assigned_issues = 0
    my_active_issues = 0

    if user:

        current_user_id = user.get("id")

        if current_user_id is not None:

            my_assigned_issues = sum(
                1
                for issue in all_issues
                if str(issue.assigned_to)
                == str(current_user_id)
            )

            my_active_issues = sum(
                1
                for issue in all_issues
                if (
                    str(issue.assigned_to)
                    == str(current_user_id)
                    and issue.status not in [
                        "Resolved",
                        "Verified",
                        "Closed"
                    ]
                )
            )

    # =========================================================
    # PROJECT DISTRIBUTION
    # =========================================================

    project_counts = {}

    for issue in all_issues:

        project_name = issue.project or "Unknown"

        if project_name not in project_counts:

            project_counts[project_name] = 0

        project_counts[project_name] += 1

    project_stats = sorted(
        project_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    # =========================================================
    # LIFECYCLE TOTAL
    # =========================================================

    lifecycle_total = (
        total_issues
        if total_issues > 0
        else 1
    )

    # =========================================================
    # CLOSE DATABASE
    # =========================================================

    db.close()

    # =========================================================
    # DASHBOARD
    # =========================================================

    return templates.TemplateResponse(

        request=request,

        name="dashboard.html",

        context={

            "user": user,

            # Issues
            "issues": issues,

            # Activity
            "activities": activities,

            # Notifications
            "notifications": notifications,

            # Basic statistics
            "total_issues": total_issues,
            "total_projects": total_projects,
            "critical_bugs": critical_bugs,

            # Lifecycle
            "reported": reported,
            "in_progress": in_progress,
            "in_review": in_review,
            "resolved": resolved,
            "reopened": reopened,
            "verified": verified,
            "closed": closed,

            # Overall
            "active_issues": active_issues,
            "completed_issues": completed_issues,

            # Additional statistics
            "overdue_issues": overdue_issues,
            "unassigned_issues": unassigned_issues,
            "high_priority": high_priority,

            # Priority
            "p1_count": p1_count,
            "p2_count": p2_count,
            "p3_count": p3_count,

            # User workload
            "my_assigned_issues": my_assigned_issues,
            "my_active_issues": my_active_issues,

            # Projects
            "project_stats": project_stats,

            # Lifecycle percentage denominator
            "lifecycle_total": lifecycle_total
        }
    )
    # =========================================================
# MARK DASHBOARD NOTIFICATIONS AS READ
# =========================================================

@app.post("/notifications/clear")
def clear_notifications(request: Request):

    current_notifications = request.session.get(
        "current_notifications",
        []
    )

    read_notifications = request.session.get(
        "read_notifications",
        []
    )

    for notification in current_notifications:

        if notification not in read_notifications:

            read_notifications.append(
                notification
            )

    request.session["read_notifications"] = (
        read_notifications
    )

    request.session["current_notifications"] = []

    return {
        "message": "Notifications marked as read"
    }


# =========================================================
# LOGOUT
# =========================================================

@app.get("/logout")
def logout(request: Request):

    request.session.clear()

    return RedirectResponse(
        url="/",
        status_code=302
    )
# ==========================
# Report Issue Page
# ==========================
@app.get("/report-issue")
def report_issue(request: Request):
    user = request.session.get("user")

    db = SessionLocal()

    projects = db.query(Project).all()
    sprints = db.query(Sprint).all()
    developers = db.query(User).filter(
    User.role == "Developer"
).all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="report_issue.html",
        context={
            "projects": projects,
            "sprints": sprints,
            "users": developers,
            "user": user
        }
    )

# ==========================
# Issues Page
# ==========================
@app.get("/issues")
def issues(request: Request):

    user = request.session.get("user")

    # -----------------------------------------
    # Authentication check
    # -----------------------------------------

    if not user:
        return RedirectResponse("/", status_code=302)

    db = SessionLocal()

    role = user.get("role")
    email = user.get("email")

    # -----------------------------------------
    # Base query
    # -----------------------------------------

    query = (
        db.query(Issue)
        .options(
            joinedload(Issue.sprint),
            joinedload(Issue.assignee)
        )
    )

    # -----------------------------------------
    # ROLE BASED FILTERING
    # -----------------------------------------

    if role == "Admin":

        # Admin can see everything
        issues = query.all()

    elif role == "Project Manager":

        # Project Manager can see all issues
        # for now.
        #
        # Later we can restrict this to only
        # projects managed by this PM.

        issues = query.all()

    elif role == "Developer":

        # Developer can see only issues
        # assigned to them.

        issues = (
            query
            .join(User, Issue.assigned_to == User.id)
            .filter(User.email == email)
            .all()
        )

    elif role == "QA / Tester":

        # QA can see all issues for testing.
        issues = query.all()

    elif role == "Reporter":

        # Reporter can currently see issues
        # they reported.
        #
        # This requires Issue to have a
        # reported_by/created_by field.
        #
        # Until that field exists, don't filter
        # incorrectly.
        issues = query.all()

    else:

        # Unknown role = no issues
        issues = []

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="issues.html",
        context={
            "issues": issues,
            "user": user
        }
    )
@app.get("/issue/{issue_id}")
def issue_details(issue_id: int, request: Request):

    user = request.session.get("user")

    # =========================================
    # AUTHENTICATION CHECK
    # =========================================

    if not user:
        return RedirectResponse("/", status_code=302)

    db = SessionLocal()

    # =========================================
    # GET ISSUE
    # =========================================

    issue = (
        db.query(Issue)
        .options(
            joinedload(Issue.assignee),
            joinedload(Issue.sprint)
        )
        .filter(Issue.id == issue_id)
        .first()
    )

    if not issue:
        db.close()
        return RedirectResponse("/issues", status_code=302)

    # =========================================
    # RBAC CHECK
    # =========================================

    role = user.get("role")
    email = user.get("email")

    # Developer can only access issues
    # assigned to that developer.
    if role == "Developer":

        if not issue.assignee:

            db.close()

            raise HTTPException(
                status_code=403,
                detail="You are not assigned to this issue."
            )

        if issue.assignee.email != email:

            db.close()

            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this issue."
            )

    # =========================================
    # LOAD REQUIRED DATA
    # =========================================

    users = db.query(User).all()

    sprints = db.query(Sprint).all()

    comments = (
        db.query(Comment)
        .filter(Comment.issue_id == issue_id)
        .order_by(Comment.id.desc())
        .all()
    )

    attachments = (
        db.query(Attachment)
        .filter(Attachment.issue_id == issue_id)
        .order_by(Attachment.id.desc())
        .all()
    )

    activities = (
        db.query(Activity)
        .filter(Activity.issue_id == issue_id)
        .order_by(Activity.id.desc())
        .all()
    )

    # =========================================
    # RENDER ISSUE DETAILS
    # =========================================

    response = templates.TemplateResponse(
        request=request,
        name="issue_details.html",
        context={
            "issue": issue,
            "comments": comments,
            "attachments": attachments,
            "activities": activities,
            "user": user,
            "users": users,
            "sprints": sprints
        }
    )

    db.close()

    return response
# ==========================
# Projects Page
# ==========================
@app.get("/projects")
def projects(request: Request):
    user = request.session.get("user")
    db = SessionLocal()

    projects = []

    all_projects = db.query(Project).all()

    for project in all_projects:

        total = db.query(Issue).filter(
            Issue.project == project.name
        ).count()

        critical = db.query(Issue).filter(
            Issue.project == project.name,
            Issue.severity == "Critical"
        ).count()

        projects.append({
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "total": total,
            "critical": critical
        })

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="projects.html",
        context={
            "projects": projects,
            "user":user
        }
    )
@app.get("/sprints")
def sprints_page(request: Request):

    user = request.session.get("user")

    db = SessionLocal()

    sprint_list = db.query(Sprint).order_by(Sprint.id.desc()).all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="sprints.html",
        context={
            "sprints": sprint_list,
            "user": user
        }
    )
@app.get("/sprints/{sprint_id}")
def sprint_details(sprint_id: int, request: Request):

    user = request.session.get("user")

    db = SessionLocal()

    # Get the sprint
    sprint = db.query(Sprint).filter(
        Sprint.id == sprint_id
    ).first()

    if not sprint:
        db.close()
        return RedirectResponse("/sprints", status_code=302)

    # Get issues belonging to this sprint
    issues = (
        db.query(Issue)
        .options(
            joinedload(Issue.assignee),
            joinedload(Issue.sprint)
        )
        .filter(Issue.sprint_id == sprint_id)
        .order_by(Issue.id.desc())
        .all()
        )

    # Sprint statistics
    total_issues = len(issues)

    resolved_issues = sum(
        1 for issue in issues
        if issue.status == "Resolved"
    )

    open_issues = sum(
        1 for issue in issues
        if issue.status == "Open"
    )

    in_progress_issues = sum(
        1 for issue in issues
        if issue.status == "In Progress"
    )

    critical_issues = sum(
        1 for issue in issues
        if issue.severity == "Critical"
    )

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="sprint_details.html",
        context={
            "sprint": sprint,
            "issues": issues,
            "user": user,

            # Statistics
            "total_issues": total_issues,
            "resolved_issues": resolved_issues,
            "open_issues": open_issues,
            "in_progress_issues": in_progress_issues,
            "critical_issues": critical_issues
        }
    )
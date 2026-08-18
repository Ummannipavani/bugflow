from fastapi import FastAPI, Request
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

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key="bugflow-secret-key"
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

    db = SessionLocal()

    # =========================================================
    # ALL ISSUES
    # Used for notifications
    # =========================================================

    all_issues = (
        db.query(Issue)
        .order_by(Issue.id.desc())
        .all()
    )

    # =========================================================
    # LATEST 5 ISSUES
    # Used only for dashboard Recent Issues table
    # =========================================================

    issues = (
        db.query(Issue)
        .order_by(Issue.id.desc())
        .limit(5)
        .all()
    )

    today = date.today()

    notifications = []

    # Use ALL issues for notifications
    for issue in all_issues:

        if issue.status != "Resolved":

            if issue.due_date:

                days = (issue.due_date - today).days

                if days < 0:

                    notifications.append(
                        f"🔴 {issue.title} is overdue by {-days} day(s)."
                    )

                elif days == 0:

                    notifications.append(
                        f"⚠ {issue.title} is due today."
                    )

                elif days == 1:

                    notifications.append(
                        f"📅 {issue.title} is due tomorrow."
                    )

            if issue.severity == "Critical":

                notifications.append(
                    f"🚨 Critical issue: {issue.title}"
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
    # DASHBOARD STATISTICS
    # =========================================================

    total_issues = db.query(Issue).count()

    total_projects = db.query(Project).count()

    critical_bugs = db.query(Issue).filter(
        Issue.severity == "Critical"
    ).count()

    resolved = db.query(Issue).filter(
        Issue.status == "Resolved"
    ).count()

    db.close()

    # =========================================================
    # DASHBOARD
    # =========================================================

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,

            # Only latest 5 are sent to Recent Issues
            "issues": issues,

            "activities": activities,
            "notifications": notifications,

            "total_issues": total_issues,
            "total_projects": total_projects,
            "critical_bugs": critical_bugs,
            "resolved": resolved
        }
    )


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
    users = db.query(User).all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="report_issue.html",
        context={
            "projects": projects,
            "sprints": sprints,
            "users": users,
            "user": user
        }
    )

# ==========================
# Issues Page
# ==========================
@app.get("/issues")
def issues(request: Request):
    user = request.session.get("user")

    db = SessionLocal()

    issues = (
        db.query(Issue)
        .options(joinedload(Issue.sprint), joinedload(Issue.assignee)
        )
        .all()
    )

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="issues.html",
        context={
            "issues": issues,
            "user":user
        }
    )
@app.get("/issue/{issue_id}")
def issue_details(issue_id: int, request: Request):

    user = request.session.get("user")

    db = SessionLocal()

    issue = (
        db.query(Issue)
        .options(
            joinedload(Issue.assignee),
            joinedload(Issue.sprint)
        )
        .filter(Issue.id == issue_id)
        .first()
    )
    users = db.query(User).all()
    sprints = db.query(Sprint).all()

    if not issue:
        db.close()
        return RedirectResponse("/issues", status_code=302)

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

    response = templates.TemplateResponse(
        request=request,
        name="issue_details.html",
        context={
            "request": request,
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
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

# Routers
from app.routers.user import router as user_router
from app.routers.issue import router as issue_router
from app.routers.project import router as project_router
from app.routers.ai import router as ai_router

# Database
from app.database.database import Base, engine, SessionLocal

# Models
from app.models.user import User
from app.models.issue import Issue
from app.models.project import Project
from app.models.activity import Activity

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


# ==========================
# Dashboard
# ==========================
@app.get("/dashboard")
def dashboard(request: Request):

    user = request.session.get("user")

    db = SessionLocal()

    issues = db.query(Issue).order_by(Issue.id.desc()).all()

    today = date.today()

    notifications = []

    for issue in issues:

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

    activities = (
        db.query(Activity)
        .order_by(Activity.id.desc())
        .limit(6)
        .all()
    )

    total_issues = db.query(Issue).count()

    total_projects = db.query(Project).count()

    critical_bugs = db.query(Issue).filter(
        Issue.severity == "Critical"
    ).count()

    resolved = db.query(Issue).filter(
        Issue.status == "Resolved"
    ).count()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
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

    return RedirectResponse(url="/", status_code=302)

# ==========================
# Report Issue Page
# ==========================
@app.get("/report-issue")
def report_issue(request: Request):
    user = request.session.get("user")
    db = SessionLocal()

    projects = db.query(Project).all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="report_issue.html",
        context={
            "projects": projects,
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

    issues = db.query(Issue).all()

    db.close()

    return templates.TemplateResponse(
        request=request,
        name="issues.html",
        context={
            "issues": issues,
            "user":user
        }
    )


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
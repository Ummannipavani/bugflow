from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.issue import Issue
from app.models.project import Project
from app.models.activity import Activity
from datetime import date

import os
import shutil
import uuid

router = APIRouter()


# ==========================
# Create Issue
# ==========================
@router.post("/issues")
def create_issue(
    title: str = Form(...),
    project: str = Form(...),
    priority: str = Form(...),
    severity: str = Form(...),
    description: str = Form(...),
    due_date: date = Form(...),
    screenshot: UploadFile = File(None),
    db: Session = Depends(get_db)
):

    filename = None

    if screenshot:
        ext = screenshot.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"

        with open(f"static/uploads/{filename}", "wb") as buffer:
            shutil.copyfileobj(screenshot.file, buffer)

    existing_project = db.query(Project).filter(
        Project.name == project
    ).first()

    if not existing_project:
        new_project = Project(
            name=project,
            description="Created while reporting an issue"
        )
        db.add(new_project)
        db.commit()

    new_issue = Issue(
        title=title,
        project=project,
        priority=priority,
        severity=severity,
        description=description,
        screenshot=filename,
        due_date=due_date
    )

    db.add(new_issue)
    db.commit()
    db.refresh(new_issue)

    activity = Activity(
        action=f"🐞 New issue '{title}' created"
    )

    db.add(activity)
    db.commit()

    return {
        "message": "Issue reported successfully!"
    }


# ==========================
# Get Single Issue
# ==========================
@router.get("/issues/{issue_id}")
def get_issue(issue_id: int, db: Session = Depends(get_db)):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()

    if not issue:
        return {"message": "Issue not found"}

    return issue


# ==========================
# Update Issue
# ==========================
@router.put("/issues/{issue_id}")
def update_issue(
    issue_id: int,
    title: str = Form(...),
    project: str = Form(...),
    priority: str = Form(...),
    severity: str = Form(...),
    description: str = Form(...),
    due_date: date = Form(...),
    screenshot: UploadFile = File(None),
    db: Session = Depends(get_db)
):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()

    if not issue:
        return {"message": "Issue not found"}

    issue.title = title
    issue.project = project
    issue.priority = priority
    issue.severity = severity
    issue.description = description
    issue.due_date = due_date

    if screenshot:

        ext = screenshot.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"

        with open(f"static/uploads/{filename}", "wb") as buffer:
            shutil.copyfileobj(screenshot.file, buffer)

        issue.screenshot = filename

    db.commit()

    activity = Activity(
        action=f"✏ Issue '{title}' updated"
    )

    db.add(activity)
    db.commit()

    return {
        "message": "Issue updated successfully!"
    }


# ==========================
# Delete Issue
# ==========================
@router.delete("/issues/{issue_id}")
def delete_issue(issue_id: int, db: Session = Depends(get_db)):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()

    if not issue:
        return {"message": "Issue not found"}

    issue_title = issue.title

    if issue.screenshot:
        path = f"static/uploads/{issue.screenshot}"

        if os.path.exists(path):
            os.remove(path)

    db.delete(issue)
    db.commit()

    activity = Activity(
        action=f"🗑 Issue '{issue_title}' deleted"
    )

    db.add(activity)
    db.commit()

    return {
        "message": "Issue deleted successfully!"
    }


# ==========================
# Update Status
# ==========================
@router.put("/issues/{issue_id}/status")
def update_status(issue_id: int, data: dict, db: Session = Depends(get_db)):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()

    if not issue:
        return {"message": "Issue not found"}

    issue.status = data["status"]

    db.commit()

    activity = Activity(
        action=f"✅ Issue '{issue.title}' marked as {issue.status}"
    )

    db.add(activity)
    db.commit()

    return {
        "message": "Status updated successfully"
    }
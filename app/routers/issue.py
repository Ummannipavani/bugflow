from fastapi import APIRouter, Depends, UploadFile, File, Form, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session


from app.database.database import get_db
from app.models.issue import Issue
from app.models.project import Project
from app.models.activity import Activity
from app.models.user import User
from app.models.sprint import Sprint
from app.models.attachment import Attachment
from app.models.comment import Comment
from app.ai.gemini import generate_embedding,analyze_bug

from datetime import date

import os
import shutil
import uuid


router = APIRouter()

templates = Jinja2Templates(
    directory="templates"
)


# =========================================================
# CREATE ISSUE
# =========================================================

@router.post("/issues")
def create_issue(
    title: str = Form(...),
    project: str = Form(...),

    priority: str = Form(...),
    severity: str = Form(...),

    category: str = Form(None),
    module: str = Form(None),
    defect_type: str = Form(None),

    description: str = Form(...),

    due_date: date = Form(...),

    sprint_id: int = Form(None),
    assigned_to: int = Form(None),

    screenshot: UploadFile = File(None),

    db: Session = Depends(get_db)
):

    print("Sprint ID received:", sprint_id)

    print("Category:", category)
    print("Module:", module)
    print("Defect Type:", defect_type)

    filename = None


    # =====================================================
    # SAVE SCREENSHOT
    # =====================================================

    if screenshot:

        ext = screenshot.filename.split(".")[-1]

        filename = f"{uuid.uuid4()}.{ext}"

        with open(
            f"static/uploads/{filename}",
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                screenshot.file,
                buffer
            )


    # =====================================================
    # CHECK PROJECT
    # =====================================================

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


    # =====================================================
    # CREATE ISSUE
    # =====================================================
    # =====================================================
    # AI DEFECT ANALYSIS
    # =====================================================

    ai_result = analyze_bug(
        title=title,
        project=project,
        description=description
    )

    print("\n========== AI DEFECT ANALYSIS ==========")

    print(
        "Category:",
        ai_result["category"]
    )

    print(
        "Module:",
        ai_result["module"]
    )

    print(
        "Defect Type:",
        ai_result["defect_type"]
    )

    print(
        "Priority:",
        ai_result["priority"]
    )

    print(
        "Severity:",
        ai_result["severity"]
    )

    print(
        "Improved Description:",
        ai_result["improved_description"]
    )

    print("========================================\n")

    # =====================================================
    # GENERATE AI EMBEDDING
    # =====================================================

    embedding = generate_embedding(
        title,
        description
    )

    print(
        "Embedding generated:",
        embedding is not None
    )

    if embedding:
        print(
            "Embedding dimensions:",
            len(embedding)
        )
    new_issue = Issue(

        title=title,

        project=project,

        # =================================================
        # AI-GENERATED CLASSIFICATION
        # =================================================

        priority=ai_result["priority"],

        severity=ai_result["severity"],

        category=ai_result["category"],

        module=ai_result["module"],

        defect_type=ai_result["defect_type"],

        
        # =================================================
        # AI-IMPROVED DESCRIPTION
        # =================================================

        description=ai_result["improved_description"],

        screenshot=filename,

        due_date=due_date,

        sprint_id=sprint_id if sprint_id else None,

        assigned_to=assigned_to if assigned_to else None,
        
        embedding=embedding
    )


    db.add(new_issue)

    db.commit()

    db.refresh(new_issue)


    # =====================================================
    # ACTIVITY
    # =====================================================

    activity = Activity(

        issue_id=new_issue.id,

        action=f"🐞 New issue '{title}' created"
    )


    db.add(activity)

    db.commit()


    return {

        "message":
            "Issue reported successfully!"

    }


# =========================================================
# GET SINGLE ISSUE
# =========================================================

@router.get("/issues/{issue_id}")
def get_issue(
    issue_id: int,
    db: Session = Depends(get_db)
):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        return {
            "message":
                "Issue not found"
        }


    return issue


# =========================================================
# ISSUE DETAILS PAGE
# =========================================================

@router.get("/issues/{issue_id}/details")
def issue_details(
    issue_id: int,
    request: Request,
    db: Session = Depends(get_db)
):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        return {
            "message":
                "Issue not found"
        }


    # =====================================================
    # ATTACHMENTS
    # =====================================================

    attachments = db.query(
        Attachment
    ).filter(
        Attachment.issue_id == issue_id
    ).all()


    # =====================================================
    # COMMENTS
    # =====================================================

    comments = db.query(
        Comment
    ).filter(
        Comment.issue_id == issue_id
    ).order_by(
        Comment.created_at.asc()
    ).all()


    # =====================================================
    # ACTIVITIES
    # =====================================================

    activities = db.query(
        Activity
    ).filter(
        Activity.issue_id == issue_id
    ).order_by(
        Activity.created_at.desc()
    ).all()


    # =====================================================
    # USERS & SPRINTS
    # =====================================================

    sprints = db.query(Sprint).all()

    users = db.query(User).all()


    print("\n==============================")

    print("ISSUE DETAILS ROUTE")

    print("==============================")

    print("Issue ID:", issue.id)

    print(
        "Sprints:",
        [(s.id, s.name) for s in sprints]
    )

    print(
        "Users:",
        [(u.id, u.name) for u in users]
    )

    print(
        "Issue sprint_id:",
        issue.sprint_id
    )

    print(
        "Issue assigned_to:",
        issue.assigned_to
    )

    print(
        "Category:",
        issue.category
    )

    print(
        "Module:",
        issue.module
    )

    print(
        "Defect Type:",
        issue.defect_type
    )

    print("==============================\n")


    return templates.TemplateResponse(

        request=request,

        name="issue_details.html",

        context={

            "request": request,

            "issue": issue,

            "attachments":
                attachments,

            "comments":
                comments,

            "activities":
                activities,

            "sprints":
                sprints,

            "users":
                users
        }
    )


# =========================================================
# UPDATE ISSUE
# =========================================================

@router.put("/issues/{issue_id}")
def update_issue(

    issue_id: int,

    title: str = Form(...),

    project: str = Form(...),

    priority: str = Form(...),

    severity: str = Form(...),

    category: str = Form(None),

    module: str = Form(None),

    defect_type: str = Form(None),

    description: str = Form(...),

    due_date: date = Form(...),

    sprint_id: int = Form(None),

    assigned_to: int = Form(None),

    screenshot: UploadFile = File(None),

    db: Session = Depends(get_db)

):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        return {
            "message":
                "Issue not found"
        }


    # =====================================================
    # UPDATE BASIC INFORMATION
    # =====================================================

    issue.title = title

    issue.project = project

    issue.priority = priority

    issue.severity = severity

    issue.category = category

    issue.module = module

    issue.defect_type = defect_type

    issue.description = description

    issue.due_date = due_date

    issue.sprint_id = (
        sprint_id
        if sprint_id
        else None
    )

    issue.assigned_to = (
        assigned_to
        if assigned_to
        else None
    )
    # =========================================================
    # CLEAR OLD AI ANALYSIS
    # =========================================================

    issue.ai_root_cause = None
    issue.ai_suggested_fix = None
    issue.ai_recommended_solution = None
    issue.ai_investigation_steps = None
    issue.ai_confidence = None
    issue.ai_explanation = None
    issue.ai_prevention = None


    # =========================================================
    # AUTOMATIC RE-EMBEDDING AFTER ISSUE EDIT
    # =========================================================

    try:

        new_embedding = generate_embedding(

            title=issue.title,

            description=issue.description or ""

        )

        if new_embedding:

            issue.embedding = new_embedding

            print(
                "Embedding regenerated successfully after issue update."
            )

        else:

            issue.embedding = None

            print(
                "Embedding generation returned no result."
            )

    except Exception as e:

        issue.embedding = None

        print(
            f"Embedding regeneration failed: {e}"
        )
    

    # =====================================================
    # UPDATE SCREENSHOT
    # =====================================================

    if screenshot:

        ext = screenshot.filename.split(".")[-1]

        filename = (
            f"{uuid.uuid4()}.{ext}"
        )


        with open(
            f"static/uploads/{filename}",
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                screenshot.file,
                buffer
            )


        # Delete old screenshot

        if issue.screenshot:

            old_path = (
                f"static/uploads/"
                f"{issue.screenshot}"
            )


            if os.path.exists(old_path):

                os.remove(old_path)


        issue.screenshot = filename


    # =====================================================
    # SAVE
    # =====================================================

    db.commit()

    db.refresh(issue)


    # =====================================================
    # ACTIVITY
    # =====================================================

    activity = Activity(

        issue_id=issue.id,

        action=
            f"✏ Issue '{title}' updated"
    )


    db.add(activity)

    db.commit()


    return {

        "message":
            "Issue updated successfully!"

    }


# =========================================================
# DELETE ISSUE
# =========================================================

@router.delete("/issues/{issue_id}")
def delete_issue(

    issue_id: int,

    db: Session = Depends(get_db)

):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        return {

            "message":
                "Issue not found"

        }


    issue_title = issue.title


    # =====================================================
    # DELETE SCREENSHOT
    # =====================================================

    if issue.screenshot:

        path = (
            f"static/uploads/"
            f"{issue.screenshot}"
        )


        if os.path.exists(path):

            os.remove(path)


    # Save information before deleting

    issue_id_value = issue.id


    db.delete(issue)

    db.commit()


    # =====================================================
    # ACTIVITY
    # =====================================================

    # NOTE:
    # If Activity has a foreign key to Issue,
    # creating this after deleting the Issue can
    # cause a foreign-key error.
    #
    # Keeping the existing behavior for now.


    return {

        "message":
            "Issue deleted successfully!"

    }


# =========================================================
# UPDATE STATUS
# =========================================================

@router.put("/issues/{issue_id}/status")
def update_status(

    issue_id: int,

    data: dict,

    db: Session = Depends(get_db)

):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        return {

            "message":
                "Issue not found"

        }


    new_status = data.get("status")


    if not new_status:

        return {

            "message":
                "Status is required"

        }


    # =====================================================
    # ALLOWED STATUSES
    # =====================================================

    allowed_statuses = [

        "Open",

        "In Progress",

        "In Review",

        "Resolved",

        "Reopened",

        "Verified",

        "Closed"

    ]


    if new_status not in allowed_statuses:

        return {

            "message":
                "Invalid status"

        }


    current_status = issue.status


    # =====================================================
    # VALID STATUS TRANSITIONS
    # =====================================================

    valid_transitions = {

        "Open":
            ["In Progress"],

        "In Progress":
            ["In Review"],

        "In Review":
            ["Resolved"],

        "Resolved":
            ["Verified","Reopened"],
        
        "Reopened": 
            ["In Progress"],

        "Verified":
            ["Closed","Reopened"],

        "Closed":
            []

    }


    if new_status not in (
        valid_transitions.get(
            current_status,
            []
        )
    ):

        return {

            "message":
                f"Cannot change status from "
                f"{current_status} to "
                f"{new_status}"

        }

    # =====================================================
    # UPDATE STATUS
    # =====================================================

    issue.status = new_status


    db.commit()

    db.refresh(issue)


    # =====================================================
    # ACTIVITY
    # =====================================================

    activity = Activity(

        issue_id=issue.id,

        action=
            f"🔄 Issue '{issue.title}' moved "
            f"from {current_status} to "
            f"{new_status}"

    )


    db.add(activity)

    db.commit()


    return {

        "message":
            "Status updated successfully",

        "status":
            new_status

    }


# =========================================================
# UPDATE ASSIGNEE
# =========================================================

@router.put("/issues/{issue_id}/assignee")
def update_assignee(

    issue_id: int,

    data: dict,

    db: Session = Depends(get_db)

):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        return {

            "message":
                "Issue not found"

        }


    new_assignee = data.get(
        "assigned_to"
    )


    # =====================================================
    # UNASSIGN
    # =====================================================

    if new_assignee in [
        None,
        "",
        0
    ]:

        old_assignee = (

            issue.assignee.name

            if issue.assignee

            else "Unassigned"

        )


        issue.assigned_to = None


        db.commit()


        activity = Activity(

            issue_id=issue.id,

            action=
                f"👤 Issue '{issue.title}' "
                f"was unassigned from "
                f"{old_assignee}"

        )


        db.add(activity)

        db.commit()


        return {

            "message":
                "Issue unassigned successfully",

            "assigned_to":
                None

        }


    # =====================================================
    # CHECK USER
    # =====================================================

    user = db.query(User).filter(

        User.id == int(new_assignee)

    ).first()


    if not user:

        return {

            "message":
                "User not found"

        }


    old_assignee = (

        issue.assignee.name

        if issue.assignee

        else "Unassigned"

    )


    issue.assigned_to = user.id


    db.commit()

    db.refresh(issue)


    # =====================================================
    # ACTIVITY
    # =====================================================

    activity = Activity(

        issue_id=issue.id,

        action=
            f"👤 Issue '{issue.title}' "
            f"assigned from "
            f"{old_assignee} to "
            f"{user.name}"

    )


    db.add(activity)

    db.commit()


    return {

        "message":
            "Assignee updated successfully",

        "assigned_to":
            user.id,

        "assignee":
            user.name

    }


# =========================================================
# ADD COMMENT
# =========================================================

@router.post("/issues/{issue_id}/comments")
def add_comment(

    issue_id: int,

    comment: str = Form(...),

    db: Session = Depends(get_db)

):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        return {

            "message":
                "Issue not found"

        }


    new_comment = Comment(

        issue_id=issue_id,

        comment=comment

    )


    db.add(new_comment)

    db.commit()


    return {

        "message":
            "Comment added successfully!"

    }


# =========================================================
# UPDATE SPRINT
# =========================================================

@router.put("/issues/{issue_id}/sprint")
def update_sprint(

    issue_id: int,

    data: dict,

    db: Session = Depends(get_db)

):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        return {

            "message":
                "Issue not found"

        }


    sprint_id = data.get(
        "sprint_id"
    )


    # =====================================================
    # REMOVE FROM SPRINT
    # =====================================================

    if sprint_id in [
        None,
        "",
        0
    ]:

        issue.sprint_id = None


        db.commit()


        activity = Activity(

            issue_id=issue.id,

            action=
                f"🏃 Issue '{issue.title}' "
                f"removed from sprint"

        )


        db.add(activity)

        db.commit()


        return {

            "message":
                "Sprint removed successfully"

        }


    # =====================================================
    # CHECK SPRINT
    # =====================================================

    sprint = db.query(Sprint).filter(

        Sprint.id == int(sprint_id)

    ).first()


    if not sprint:

        return {

            "message":
                "Sprint not found"

        }


    # =====================================================
    # UPDATE SPRINT
    # =====================================================

    issue.sprint_id = sprint.id


    db.commit()

    db.refresh(issue)


    # =====================================================
    # ACTIVITY
    # =====================================================

    activity = Activity(

        issue_id=issue.id,

        action=
            f"🏃 Issue '{issue.title}' "
            f"assigned to sprint "
            f"'{sprint.name}'"

    )


    db.add(activity)

    db.commit()


    return {

        "message":
            "Sprint updated successfully",

        "sprint_id":
            sprint.id,

        "sprint":
            sprint.name

    }

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    Request,
    HTTPException,
    status
)

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

from app.ai.gemini import (
    generate_embedding,
    analyze_bug
)

# IMPORTANT:
# rbac.py was renamed to dependencies.py
from app.auth.dependencies import require_roles
from app.schemas.issue import (
    IssueResponse,
    StatusUpdate,
    AssigneeUpdate,
    SprintUpdate,
    CommentCreate,
    MessageResponse
)
from datetime import date, datetime

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

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        require_roles(
            "Admin",
            "Project Manager",
            "Developer",
            "QA / Tester",
            "Reporter"
        )
    )
):

    print("Sprint ID received:", sprint_id)
    print("Category:", category)
    print("Module:", module)
    print("Defect Type:", defect_type)


    filename = None


    # =====================================================
    # SAVE SCREENSHOT
    # =====================================================

    if screenshot and screenshot.filename:

        ext = screenshot.filename.split(".")[-1]

        filename = f"{uuid.uuid4()}.{ext}"

        os.makedirs(
            "static/uploads",
            exist_ok=True
        )

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
    # CHECK ASSIGNED USER
    # =====================================================

    assigned_user = None


    if assigned_to:

        assigned_user = db.query(User).filter(
            User.id == assigned_to
        ).first()


        if not assigned_user:

            raise HTTPException(
                status_code=400,
                detail="Assigned user not found."
            )


        # Only developers should receive bug assignments
        if assigned_user.role != "Developer":

            raise HTTPException(
                status_code=400,
                detail="Issues can only be assigned to Developers."
            )


    # =====================================================
    # AI DEFECT ANALYSIS
    # =====================================================

    ai_result = analyze_bug(

        title=title,

        project=project,

        description=description
    )


    print(
        "\n========== AI DEFECT ANALYSIS =========="
    )


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


    print(
        "========================================\n"
    )


    # =====================================================
    # GENERATE EMBEDDING
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


    # =====================================================
    # AUTOMATIC INITIAL STATUS
    #
    # Assigned developer -> In Progress
    # No developer -> Open
    # =====================================================

    initial_status = (
        "In Progress"
        if assigned_user
        else "Open"
    )


    # =====================================================
    # CREATE ISSUE
    # =====================================================

    new_issue = Issue(

        title=title,

        project=project,

        priority=ai_result["priority"],

        severity=ai_result["severity"],

        category=ai_result["category"],

        module=ai_result["module"],

        defect_type=ai_result["defect_type"],

        description=ai_result["improved_description"],

        screenshot=filename,

        due_date=due_date,

        sprint_id=(
            sprint_id
            if sprint_id
            else None
        ),

        assigned_to=(
            assigned_to
            if assigned_user
            else None
        ),

        status=initial_status,

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

        action=(
            f"🐞 New issue '{title}' created "
            f"with status '{initial_status}'"
        )
    )


    db.add(activity)

    db.commit()


    # =====================================================
    # ASSIGNMENT ACTIVITY
    # =====================================================

    if assigned_user:

        activity = Activity(

            issue_id=new_issue.id,

            action=(
                f"👤 Issue assigned to "
                f"{assigned_user.name}"
            )
        )


        db.add(activity)

        db.commit()


    return {

        "message":
            "Issue reported successfully!",

        "issue_id":
            new_issue.id,

        "status":
            new_issue.status

    }


# =========================================================
# GET SINGLE ISSUE
# =========================================================

@router.get("/issues/{issue_id}")
def get_issue(

    issue_id: int,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        require_roles(
            "Admin",
            "Project Manager",
            "Developer",
            "QA / Tester",
            "Reporter"
        )
    )
):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        raise HTTPException(
            status_code=404,
            detail="Issue not found"
        )


    return issue


# =========================================================
# ISSUE DETAILS PAGE
# =========================================================

@router.get("/issues/{issue_id}/details")
def issue_details(

    issue_id: int,

    request: Request,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        require_roles(
            "Admin",
            "Project Manager",
            "Developer",
            "QA / Tester",
            "Reporter"
        )
    )
):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        raise HTTPException(
            status_code=404,
            detail="Issue not found"
        )


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
    # SPRINTS
    # =====================================================

    sprints = db.query(
        Sprint
    ).all()


    # =====================================================
    # USERS
    # =====================================================

    users = db.query(
        User
    ).all()


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
                users,

            "current_user":
                current_user
        }
    )


# =========================================================
# UPDATE ISSUE
#
# Admin:
#     Can edit any issue
#
# Project Manager:
#     Can edit any issue
#
# Developer:
#     Can edit ONLY assigned issues
#
# QA:
#     Cannot edit issue information
#     Can only manage testing status
#
# Reporter:
#     Cannot edit
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

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        require_roles(
            "Admin",
            "Project Manager",
            "Developer"
        )
    )
):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        raise HTTPException(
            status_code=404,
            detail="Issue not found"
        )


    role = current_user.get("role")


    # =====================================================
    # DEVELOPER RBAC
    #
    # Developer can ONLY update assigned issue
    # =====================================================

    if role == "Developer":

        if issue.assigned_to is None:

            raise HTTPException(
                status_code=403,
                detail=(
                    "You can only update "
                    "issues assigned to you."
                )
            )


        if str(issue.assigned_to) != str(
            current_user.get("id")
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "You can only update "
                    "issues assigned to you."
                )
            )


        # Developer cannot reassign the issue

        if assigned_to is not None:

            if str(assigned_to) != str(
                issue.assigned_to
            ):

                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Developers cannot "
                        "reassign issues."
                    )
                )


        # Developer cannot change sprint assignment

        if sprint_id is not None:

            if str(sprint_id) != str(
                issue.sprint_id
            ):

                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Developers cannot "
                        "change sprint assignment."
                    )
                )


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


    # =====================================================
    # SPRINT
    #
    # Only Admin / Project Manager can change it
    # =====================================================

    if role in [
        "Admin",
        "Project Manager"
    ]:

        issue.sprint_id = (
            sprint_id
            if sprint_id
            else None
        )


    # =====================================================
    # ASSIGNMENT
    #
    # Only Admin / Project Manager can change it
    # =====================================================

    if role in [
        "Admin",
        "Project Manager"
    ]:

        if assigned_to:

            user = db.query(User).filter(
                User.id == assigned_to
            ).first()


            if not user:

                raise HTTPException(
                    status_code=400,
                    detail="Assigned user not found."
                )


            if user.role != "Developer":

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Issues can only be "
                        "assigned to Developers."
                    )
                )


            old_assignee = issue.assigned_to

            issue.assigned_to = user.id


            # =================================================
            # AUTOMATIC STATUS
            #
            # Open/Reopened + developer assigned
            # -> In Progress
            # =================================================

            if (
                issue.status in [
                    "Open",
                    "Reopened"
                ]
            ):

                old_status = issue.status

                issue.status = "In Progress"


                db.add(
                    Activity(

                        issue_id=issue.id,

                        action=(
                            f"🔄 Issue status changed "
                            f"from {old_status} "
                            f"to In Progress because "
                            f"it was assigned to "
                            f"{user.name}"
                        )
                    )
                )


            if old_assignee != user.id:

                db.add(
                    Activity(

                        issue_id=issue.id,

                        action=(
                            f"👤 Issue assigned to "
                            f"{user.name}"
                        )
                    )
                )


        else:

            issue.assigned_to = None


    # =====================================================
    # CLEAR OLD AI ANALYSIS
    # =====================================================

    issue.ai_root_cause = None

    issue.ai_suggested_fix = None

    issue.ai_recommended_solution = None

    issue.ai_investigation_steps = None

    issue.ai_confidence = None

    issue.ai_explanation = None

    issue.ai_prevention = None


    # =====================================================
    # AUTOMATIC RE-EMBEDDING
    # =====================================================

    try:

        new_embedding = generate_embedding(

            title=issue.title,

            description=issue.description or ""
        )


        if new_embedding:

            issue.embedding = new_embedding

            print(
                "Embedding regenerated successfully "
                "after issue update."
            )

        else:

            issue.embedding = None

            print(
                "Embedding generation returned "
                "no result."
            )


    except Exception as e:

        issue.embedding = None

        print(
            f"Embedding regeneration failed: {e}"
        )


    # =====================================================
    # UPDATE SCREENSHOT
    # =====================================================

    if screenshot and screenshot.filename:

        ext = screenshot.filename.split(".")[-1]

        filename = (
            f"{uuid.uuid4()}.{ext}"
        )


        os.makedirs(
            "static/uploads",
            exist_ok=True
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

        action=(
            f"✏ Issue '{title}' updated "
            f"by {role}"
        )
    )


    db.add(activity)

    db.commit()


    return {

        "message":
            "Issue updated successfully!",

        "status":
            issue.status
    }


# =========================================================
# DELETE ISSUE
#
# Only Admin / Project Manager
# =========================================================

@router.delete("/issues/{issue_id}")
def delete_issue(

    issue_id: int,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        require_roles(
            "Admin",
            "Project Manager"
        )
    )
):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        raise HTTPException(
            status_code=404,
            detail="Issue not found"
        )


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


    # =====================================================
    # DELETE ATTACHMENTS
    # =====================================================

    attachments = db.query(
        Attachment
    ).filter(
        Attachment.issue_id == issue.id
    ).all()


    for attachment in attachments:

        if attachment.file_path:

            if os.path.exists(
                attachment.file_path
            ):

                os.remove(
                    attachment.file_path
                )


        db.delete(attachment)


    # =====================================================
    # DELETE ACTIVITIES
    # =====================================================

    db.query(Activity).filter(
        Activity.issue_id == issue.id
    ).delete(
        synchronize_session=False
    )


    # =====================================================
    # DELETE COMMENTS
    # =====================================================

    db.query(Comment).filter(
        Comment.issue_id == issue.id
    ).delete(
        synchronize_session=False
    )


    # =====================================================
    # DELETE ISSUE
    # =====================================================

    db.delete(issue)

    db.commit()


    return {

        "message":
            f"Issue '{issue_title}' deleted successfully!"
    }


# =========================================================
# UPDATE STATUS
#
# Developer:
#     In Progress -> In Review
#     Reopened -> In Progress
#
# QA / Tester:
#     In Review -> Resolved
#     Resolved -> Verified
#     Resolved -> Reopened
#
# Admin / Project Manager:
#     Can perform all valid transitions
# =========================================================

@router.put("/issues/{issue_id}/status")
def update_status(

    issue_id: int,

    data: dict,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        require_roles(
            "Admin",
            "Project Manager",
            "Developer",
            "QA / Tester"
        )
    )
):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        raise HTTPException(
            status_code=404,
            detail="Issue not found"
        )


    role = current_user.get("role")


    # =====================================================
    # GET NEW STATUS
    # =====================================================

    new_status = data.get("status")


    if not new_status:

        raise HTTPException(
            status_code=400,
            detail="Status is required"
        )


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

        raise HTTPException(
            status_code=400,
            detail="Invalid status"
        )


    current_status = issue.status


    # =====================================================
    # NO CHANGE
    # =====================================================

    if new_status == current_status:

        return {

            "message":
                "Issue is already in this status.",

            "status":
                current_status
        }


    # =====================================================
    # DEVELOPER OWNERSHIP CHECK
    # =====================================================

    if role == "Developer":

        if issue.assigned_to is None:

            raise HTTPException(
                status_code=403,
                detail=(
                    "You can only update "
                    "status of issues assigned to you."
                )
            )


        if str(issue.assigned_to) != str(
            current_user.get("id")
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "You can only update "
                    "status of issues assigned to you."
                )
            )


    # =====================================================
    # STATUS TRANSITIONS
    # =====================================================

    valid_transitions = {

        "Open": [

            "In Progress"

        ],

        "In Progress": [

            "In Review"

        ],

        "In Review": [

            "Resolved"

        ],

        "Resolved": [

            "Verified",

            "Reopened"

        ],

        "Reopened": [

            "In Progress"

        ],

        "Verified": [

            "Closed",

            "Reopened"

        ],

        "Closed": []

    }


    # =====================================================
    # ROLE-SPECIFIC STATUS CONTROL
    # =====================================================

    if role == "Developer":

        allowed_for_role = {

            "In Progress": [
                "In Review"
            ],

            "Reopened": [
                "In Progress"
            ]

        }


        if new_status not in allowed_for_role.get(
            current_status,
            []
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "Developers can move their "
                    "assigned issues only from "
                    "In Progress to In Review "
                    "or Reopened to In Progress."
                )
            )


    elif role == "QA / Tester":

        allowed_for_role = {

            "In Review": [
                "Resolved"
            ],

            "Resolved": [

                "Verified",

                "Reopened"
            ]

        }


        if new_status not in allowed_for_role.get(
            current_status,
            []
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "QA / Tester can move issues "
                    "from In Review to Resolved, "
                    "or from Resolved to Verified "
                    "or Reopened."
                )
            )


    else:

        # Admin / Project Manager

        if new_status not in valid_transitions.get(
            current_status,
            []
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot change status from "
                    f"{current_status} to "
                    f"{new_status}"
                )
            )


    # =====================================================
    # UPDATE STATUS
    # =====================================================

    issue.status = new_status
    # Record resolution time
    if new_status == "Resolved":
        issue.resolved_at = datetime.utcnow()

# Record closing time
    if new_status == "Closed":
        issue.closed_at = datetime.utcnow()
    # =====================================================
    # RESOLUTION TIMESTAMP
    # =====================================================

    if new_status == "Resolved":

        if issue.resolved_at is None:

            issue.resolved_at = datetime.utcnow()


# =====================================================
# CLOSED TIMESTAMP
# =====================================================

    if new_status == "Closed":

        if issue.closed_at is None:

            issue.closed_at = datetime.utcnow()


# =====================================================
# REOPENED ISSUE
# =====================================================

    if new_status == "Reopened":

        issue.resolved_at = None

        issue.closed_at = None
    db.commit()

    db.refresh(issue)


    # =====================================================
    # ACTIVITY
    # =====================================================

    activity = Activity(

        issue_id=issue.id,

        action=(
            f"🔄 Issue '{issue.title}' "
            f"moved from {current_status} "
            f"to {new_status} "
            f"by {role}"
        )
    )


    db.add(activity)

    db.commit()


    return {

        "message":
            "Status updated successfully",

        "old_status":
            current_status,

        "status":
            new_status
    }


# =========================================================
# UPDATE ASSIGNEE
#
# Only Admin / Project Manager
#
# Assigning an Open/Reopened issue to a Developer
# automatically changes status to In Progress.
# =========================================================

@router.put("/issues/{issue_id}/assignee")
def update_assignee(

    issue_id: int,

    data: dict,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        require_roles(
            "Admin",
            "Project Manager"
        )
    )
):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        raise HTTPException(
            status_code=404,
            detail="Issue not found"
        )


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

            action=(
                f"👤 Issue '{issue.title}' "
                f"was unassigned from "
                f"{old_assignee}"
            )
        )


        db.add(activity)

        db.commit()


        return {

            "message":
                "Issue unassigned successfully",

            "assigned_to":
                None,

            "status":
                issue.status
        }


    # =====================================================
    # CHECK USER
    # =====================================================

    try:

        new_assignee = int(
            new_assignee
        )

    except (TypeError, ValueError):

        raise HTTPException(
            status_code=400,
            detail="Invalid assignee."
        )


    user = db.query(User).filter(
        User.id == new_assignee
    ).first()


    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    # =====================================================
    # ONLY DEVELOPERS CAN BE ASSIGNED
    # =====================================================

    if user.role != "Developer":

        raise HTTPException(
            status_code=400,
            detail=(
                "Only users with the Developer "
                "role can be assigned to issues."
            )
        )


    old_assignee = (

        issue.assignee.name

        if issue.assignee

        else "Unassigned"
    )


    old_status = issue.status


    issue.assigned_to = user.id


    # =====================================================
    # AUTOMATIC STATUS
    #
    # Open/Reopened -> In Progress
    # =====================================================

    if issue.status in [
        "Open",
        "Reopened"
    ]:

        issue.status = "In Progress"


    db.commit()

    db.refresh(issue)


    # =====================================================
    # ASSIGNMENT ACTIVITY
    # =====================================================

    activity = Activity(

        issue_id=issue.id,

        action=(
            f"👤 Issue '{issue.title}' "
            f"assigned from "
            f"{old_assignee} to "
            f"{user.name}"
        )
    )


    db.add(activity)


    # =====================================================
    # STATUS ACTIVITY
    # =====================================================

    if old_status != issue.status:

        db.add(
            Activity(

                issue_id=issue.id,

                action=(
                    f"🔄 Issue status automatically "
                    f"changed from {old_status} "
                    f"to {issue.status} "
                    f"after assignment"
                )
            )
        )


    db.commit()


    return {

        "message":
            "Assignee updated successfully",

        "assigned_to":
            user.id,

        "assignee":
            user.name,

        "status":
            issue.status
    }


# =========================================================
# ADD COMMENT
#
# All authenticated roles can comment
# =========================================================

@router.post("/issues/{issue_id}/comments")
def add_comment(

    issue_id: int,

    comment: str = Form(...),

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        require_roles(
            "Admin",
            "Project Manager",
            "Developer",
            "QA / Tester",
            "Reporter"
        )
    )
):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        raise HTTPException(
            status_code=404,
            detail="Issue not found"
        )


    new_comment = Comment(

        issue_id=issue_id,

        comment=comment
    )


    db.add(new_comment)

    db.commit()


    # =====================================================
    # ACTIVITY
    # =====================================================

    db.add(
        Activity(

            issue_id=issue_id,

            action="💬 New comment added"
        )
    )


    db.commit()


    return {

        "message":
            "Comment added successfully!"
    }


# =========================================================
# UPDATE SPRINT
#
# Only Admin / Project Manager
# =========================================================

@router.put("/issues/{issue_id}/sprint")
def update_sprint(

    issue_id: int,

    data: dict,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        require_roles(
            "Admin",
            "Project Manager"
        )
    )
):

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()


    if not issue:

        raise HTTPException(
            status_code=404,
            detail="Issue not found"
        )


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

            action=(
                f"🏃 Issue '{issue.title}' "
                f"removed from sprint"
            )
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

    try:

        sprint_id = int(
            sprint_id
        )

    except (TypeError, ValueError):

        raise HTTPException(
            status_code=400,
            detail="Invalid sprint."
        )


    sprint = db.query(Sprint).filter(
        Sprint.id == sprint_id
    ).first()


    if not sprint:

        raise HTTPException(
            status_code=404,
            detail="Sprint not found"
        )


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

        action=(
            f"🏃 Issue '{issue.title}' "
            f"assigned to sprint "
            f"'{sprint.name}'"
        )
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


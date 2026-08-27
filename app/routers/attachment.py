from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.attachment import Attachment
from app.models.issue import Issue
from app.models.activity import Activity
from app.models.user import User

from app.auth.dependencies import get_current_user


import os
import shutil
import uuid


router = APIRouter()


# =========================================================
# RBAC HELPER
# =========================================================

def can_modify_issue(
    issue: Issue,
    current_user: dict,
    db: Session
):

    role = current_user.get("role")

    # -----------------------------------------------------
    # ADMIN
    # -----------------------------------------------------

    if role == "Admin":
        return True

    # -----------------------------------------------------
    # PROJECT MANAGER
    # -----------------------------------------------------

    if role == "Project Manager":
        return True

    # -----------------------------------------------------
    # DEVELOPER
    # Only assigned developer can modify
    # -----------------------------------------------------

    if role == "Developer":

        db_user = db.query(User).filter(
            User.email == current_user.get("email")
        ).first()

        if not db_user:
            return False

        if issue.assigned_to == db_user.id:
            return True

        return False

    # -----------------------------------------------------
    # ALL OTHER ROLES
    # -----------------------------------------------------

    return False


# =========================================================
# UPLOAD ATTACHMENT
# =========================================================

@router.post("/issues/{issue_id}/attachments")
def upload_attachment(

    issue_id: int,

    file: UploadFile = File(...),

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )

):

    # =====================================================
    # CHECK ISSUE
    # =====================================================

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()

    if not issue:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )


    # =====================================================
    # RBAC CHECK
    # =====================================================

    if not can_modify_issue(
        issue,
        current_user,
        db
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission to "
                "add attachments to this issue"
            )
        )


    # =====================================================
    # CHECK FILE
    # =====================================================

    if not file.filename:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file selected"
        )


    # =====================================================
    # CREATE UPLOAD DIRECTORY
    # =====================================================

    upload_folder = "static/uploads"

    os.makedirs(
        upload_folder,
        exist_ok=True
    )


    # =====================================================
    # ORIGINAL FILENAME
    # =====================================================

    original_filename = file.filename


    # =====================================================
    # FILE EXTENSION
    # =====================================================

    extension = ""

    if "." in original_filename:

        extension = (
            "." +
            original_filename.rsplit(".", 1)[1]
        )


    # =====================================================
    # UNIQUE FILENAME
    # =====================================================

    unique_filename = (
        f"{uuid.uuid4()}{extension}"
    )


    # =====================================================
    # FILE PATH
    # =====================================================

    file_path = os.path.join(
        upload_folder,
        unique_filename
    )


    # =====================================================
    # SAVE FILE
    # =====================================================

    try:

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Unable to save attachment: {str(e)}"
            )
        )


    # =====================================================
    # SAVE DATABASE RECORD
    # =====================================================

    attachment = Attachment(

        issue_id=issue_id,

        filename=unique_filename,

        original_filename=original_filename,

        file_path=file_path
    )

    db.add(attachment)

    db.commit()

    db.refresh(attachment)


    # =====================================================
    # ACTIVITY
    # =====================================================

    activity = Activity(

        issue_id=issue_id,

        action=(
            f"📎 File '{original_filename}' attached"
        )
    )

    db.add(activity)

    db.commit()


    # =====================================================
    # RETURN JSON
    # IMPORTANT:
    # Your frontend uses response.json()
    # =====================================================

    return {

        "message":
            "Attachment uploaded successfully",

        "attachment": {

            "id":
                attachment.id,

            "filename":
                attachment.filename,

            "original_filename":
                attachment.original_filename,

            "file_path":
                attachment.file_path
        }

    }


# =========================================================
# GET ISSUE ATTACHMENTS
# =========================================================

@router.get("/issues/{issue_id}/attachments")
def get_attachments(

    issue_id: int,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )

):

    # =====================================================
    # CHECK ISSUE
    # =====================================================

    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()

    if not issue:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )


    # =====================================================
    # GET ATTACHMENTS
    # =====================================================

    attachments = (

        db.query(Attachment)

        .filter(
            Attachment.issue_id == issue_id
        )

        .order_by(
            Attachment.id.desc()
        )

        .all()
    )


    return attachments


# =========================================================
# DELETE ATTACHMENT
# =========================================================

@router.delete("/attachments/{attachment_id}")
def delete_attachment(

    attachment_id: int,

    db: Session = Depends(get_db),

    current_user: dict = Depends(
        get_current_user
    )

):

    # =====================================================
    # FIND ATTACHMENT
    # =====================================================

    attachment = (

        db.query(Attachment)

        .filter(
            Attachment.id == attachment_id
        )

        .first()
    )


    if not attachment:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )


    # =====================================================
    # FIND ISSUE
    # =====================================================

    issue = db.query(Issue).filter(
        Issue.id == attachment.issue_id
    ).first()


    if not issue:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found"
        )


    # =====================================================
    # RBAC CHECK
    # =====================================================

    if not can_modify_issue(
        issue,
        current_user,
        db
    ):

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission to "
                "delete attachments from this issue"
            )
        )


    # =====================================================
    # SAVE INFORMATION BEFORE DELETE
    # =====================================================

    issue_id = attachment.issue_id

    original_filename = (
        attachment.original_filename
    )


    # =====================================================
    # DELETE PHYSICAL FILE
    # =====================================================

    if attachment.file_path:

        if os.path.exists(
            attachment.file_path
        ):

            try:

                os.remove(
                    attachment.file_path
                )

            except Exception as e:

                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Unable to delete file: {str(e)}"
                    )
                )


    # =====================================================
    # DELETE DATABASE RECORD
    # =====================================================

    db.delete(attachment)

    db.commit()


    # =====================================================
    # ACTIVITY
    # =====================================================

    activity = Activity(

        issue_id=issue_id,

        action=(
            f"🗑 Attachment "
            f"'{original_filename}' deleted"
        )
    )

    db.add(activity)

    db.commit()


    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        "message":
            "Attachment deleted successfully"

    }
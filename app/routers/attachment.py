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
# FILE UPLOAD SECURITY
# =========================================================

ALLOWED_ATTACHMENT_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".txt"
}

MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10 MB
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
# SAFE ORIGINAL FILENAME
# =====================================================

    original_filename = os.path.basename(file.filename).strip()

    if not original_filename:

        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid filename"
        )


# =====================================================
# CHECK FILE EXTENSION
# =====================================================

    extension = os.path.splitext(
        original_filename
    )[1].lower()

    if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:

        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "Unsupported file type. "
            "Allowed formats: PNG, JPG, JPEG, GIF, WEBP, "
            "PDF, DOC, DOCX, XLS, XLSX, CSV and TXT."
            )
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
    # SAVE FILE WITH SIZE LIMIT
    # =====================================================

    try:

        total_size = 0

        with open(
        file_path,
        "wb"
        ) as buffer:

            while True:

                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_ATTACHMENT_SIZE:

                    buffer.close()

                    if os.path.exists(file_path):
                        os.remove(file_path)

                    raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File size must not exceed 10 MB."
                    )

                buffer.write(chunk)

    except HTTPException:
        raise

    except Exception:

        if os.path.exists(file_path):

            try:
                os.remove(file_path)
            except Exception:
                pass

        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unable to save attachment."
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
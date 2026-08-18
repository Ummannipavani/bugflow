from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse

from app.database.database import get_db
from app.models.attachment import Attachment
from app.models.issue import Issue
from app.models.activity import Activity

import os
import shutil
import uuid


router = APIRouter()


# ==========================
# Upload Attachment
# ==========================

@router.post("/issues/{issue_id}/attachments")
def upload_attachment(
    issue_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # Check if issue exists
    issue = db.query(Issue).filter(
        Issue.id == issue_id
    ).first()

    if not issue:
        return {
            "message": "Issue not found"
        }

    # Check if a file was selected
    if not file.filename:
        return {
            "message": "No file selected"
        }

    # Create uploads folder if it doesn't exist
    upload_folder = "static/uploads"

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    # Get original filename
    original_filename = file.filename

    # Get file extension
    extension = ""

    if "." in original_filename:
        extension = "." + original_filename.split(".")[-1]

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{extension}"

    # Full file path
    file_path = os.path.join(
        upload_folder,
        unique_filename
    )

    # Save file
    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    # Save attachment information in database
    attachment = Attachment(
        issue_id=issue_id,
        filename=unique_filename,
        original_filename=original_filename,
        file_path=file_path
    )

    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    # Add activity history
    activity = Activity(
        issue_id=issue_id,
        action=f"📎 File '{original_filename}' attached"
    )

    db.add(activity)
    db.commit()

    return RedirectResponse(
        url=f"/issue/{issue_id}",
        status_code=303
    )


# ==========================
# Get Issue Attachments
# ==========================

@router.get("/issues/{issue_id}/attachments")
def get_attachments(
    issue_id: int,
    db: Session = Depends(get_db)
):

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


# ==========================
# Delete Attachment
# ==========================

@router.delete("/attachments/{attachment_id}")
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db)
):

    attachment = (
        db.query(Attachment)
        .filter(
            Attachment.id == attachment_id
        )
        .first()
    )

    if not attachment:
        return {
            "message": "Attachment not found"
        }

    issue_id = attachment.issue_id
    filename = attachment.original_filename

    # Delete physical file
    if attachment.file_path:

        if os.path.exists(
            attachment.file_path
        ):

            os.remove(
                attachment.file_path
            )

    # Delete database record
    db.delete(attachment)
    db.commit()

    # Add activity history
    activity = Activity(
        issue_id=issue_id,
        action=f"🗑 Attachment '{filename}' deleted"
    )

    db.add(activity)
    db.commit()

    return {
        "message": "Attachment deleted successfully"
    }
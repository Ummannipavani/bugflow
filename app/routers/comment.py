from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.comment import Comment
from app.models.issue import Issue          # <-- Add this import
from app.schemas.comment import CommentCreate
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.post("/comments")
def add_comment(
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Check if the issue exists
    issue = db.query(Issue).filter(Issue.id == comment.issue_id).first()

    if not issue:
        return {"message": "Issue not found"}

    # Create the comment
    new_comment = Comment(
        issue_id=comment.issue_id,
        comment=comment.comment
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return {
        "message": "Comment added successfully"
    }


@router.get("/comments/{issue_id}")
def get_comments(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    comments = db.query(Comment).filter(
        Comment.issue_id == issue_id
    ).all()

    return comments
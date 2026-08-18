from pydantic import BaseModel
from datetime import datetime


class CommentCreate(BaseModel):
    issue_id: int
    comment: str


class CommentResponse(BaseModel):
    id: int
    issue_id: int
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True
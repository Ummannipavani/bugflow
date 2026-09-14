from datetime import datetime
from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    issue_id: int = Field(..., gt=0)
    comment: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )


class CommentResponse(BaseModel):
    id: int
    issue_id: int
    comment: str
    created_at: datetime

    class Config:
        from_attributes = True
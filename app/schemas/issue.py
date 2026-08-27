from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date


# =========================================================
# CREATE ISSUE API SCHEMA
# =========================================================

class IssueCreate(BaseModel):

    title: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Title of the defect"
    )

    project: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Project name"
    )

    priority: str = Field(
        ...,
        description="Issue priority"
    )

    severity: str = Field(
        ...,
        description="Issue severity"
    )

    category: Optional[str] = Field(
        None,
        max_length=100
    )

    module: Optional[str] = Field(
        None,
        max_length=100
    )

    defect_type: Optional[str] = Field(
        None,
        max_length=100
    )

    description: str = Field(
        ...,
        min_length=10,
        description="Detailed defect description"
    )

    due_date: Optional[date] = Field(
        None,
        description="Issue due date"
    )

    sprint_id: Optional[int] = Field(
        None,
        gt=0,
        description="Sprint ID"
    )

    assigned_to: Optional[int] = Field(
        None,
        gt=0,
        description="Developer user ID"
    )


# =========================================================
# UPDATE ISSUE API SCHEMA
# =========================================================

class IssueUpdate(BaseModel):

    title: str = Field(
        ...,
        min_length=3,
        max_length=200
    )

    project: str = Field(
        ...,
        min_length=1,
        max_length=100
    )

    priority: str

    severity: str

    category: Optional[str] = None

    module: Optional[str] = None

    defect_type: Optional[str] = None

    description: str = Field(
        ...,
        min_length=10
    )

    due_date: Optional[date] = None

    sprint_id: Optional[int] = Field(
        None,
        gt=0
    )

    assigned_to: Optional[int] = Field(
        None,
        gt=0
    )


# =========================================================
# STATUS UPDATE
# =========================================================

class StatusUpdate(BaseModel):

    status: str = Field(
        ...,
        description="New issue status"
    )


# =========================================================
# ASSIGNEE UPDATE
# =========================================================

class AssigneeUpdate(BaseModel):

    assigned_to: Optional[int] = Field(
        None,
        gt=0,
        description="Developer user ID"
    )


# =========================================================
# SPRINT UPDATE
# =========================================================

class SprintUpdate(BaseModel):

    sprint_id: Optional[int] = Field(
        None,
        gt=0,
        description="Sprint ID"
    )


# =========================================================
# COMMENT CREATE
# =========================================================

class CommentCreate(BaseModel):

    comment: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Comment text"
    )


# =========================================================
# ISSUE RESPONSE
# =========================================================

class IssueResponse(BaseModel):

    id: int

    title: str

    project: str

    priority: str

    severity: str

    category: Optional[str] = None

    module: Optional[str] = None

    defect_type: Optional[str] = None

    description: str

    status: str

    due_date: Optional[date] = None

    sprint_id: Optional[int] = None

    assigned_to: Optional[int] = None

    model_config = ConfigDict(
        from_attributes=True
    )


# =========================================================
# SIMPLE API RESPONSE
# =========================================================

class MessageResponse(BaseModel):

    message: str


# =========================================================
# STATUS RESPONSE
# =========================================================

class StatusResponse(BaseModel):

    message: str

    old_status: Optional[str] = None

    status: str


# =========================================================
# ASSIGNEE RESPONSE
# =========================================================

class AssigneeResponse(BaseModel):

    message: str

    assigned_to: Optional[int] = None

    assignee: Optional[str] = None

    status: Optional[str] = None


# =========================================================
# SPRINT RESPONSE
# =========================================================

class SprintResponse(BaseModel):

    message: str

    sprint_id: Optional[int] = None

    sprint: Optional[str] = None
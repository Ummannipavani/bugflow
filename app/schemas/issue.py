from pydantic import BaseModel


class IssueCreate(BaseModel):
    title: str
    project: str
    priority: str
    severity: str
    description: str


class IssueResponse(BaseModel):
    id: int
    title: str
    project: str
    priority: str
    severity: str
    description: str
    status: str

    class Config:
        from_attributes = True
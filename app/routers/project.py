from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.project import Project
from app.models.activity import Activity
from app.schemas.project import ProjectCreate
from app.auth.dependencies import require_roles

router = APIRouter()


@router.post("/projects")
def create_project(project: ProjectCreate, db: Session = Depends(get_db), current_user: dict = Depends(require_roles("Admin", "Project Manager"))):

    new_project = Project(
        name=project.name,
        description=project.description
    )

    db.add(new_project)
    db.commit()
    activity = Activity(
        action=f"📁 Project '{project.name}' created"
    )

    db.add(activity)
    db.commit()
    db.refresh(new_project)

    return {
        "message": "Project created successfully!"
    }

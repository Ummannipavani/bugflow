from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate

router = APIRouter()


@router.post("/projects")
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):

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
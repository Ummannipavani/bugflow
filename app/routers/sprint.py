from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.sprint import Sprint

router = APIRouter()


# ==========================
# Create Sprint
# ==========================
@router.post("/sprints")
def create_sprint(data: dict, db: Session = Depends(get_db)):

    sprint = Sprint(
        name=data["name"],
        start_date=data["start_date"],
        end_date=data["end_date"],
        status="Active"
    )

    db.add(sprint)
    db.commit()
    db.refresh(sprint)

    return {
        "message": "Sprint created successfully!"
    }
@router.get("/api/sprints")
def get_sprints(db: Session = Depends(get_db)):

    return db.query(Sprint).order_by(Sprint.id.desc()).all()


@router.delete("/sprints/{sprint_id}")
def delete_sprint(
    sprint_id: int,
    db: Session = Depends(get_db)
):

    sprint = db.query(Sprint).filter(
        Sprint.id == sprint_id
    ).first()

    if not sprint:
        return {"message": "Sprint not found"}

    db.delete(sprint)
    db.commit()

    return {
        "message": "Sprint deleted successfully"
    }


# ==========================
# Get All Sprints
# ==========================
@router.get("/api/sprints")
def get_sprints(db: Session = Depends(get_db)):

    return db.query(Sprint).order_by(Sprint.id.desc()).all()


# ==========================
# Delete Sprint
# ==========================
@router.delete("/sprints/{sprint_id}")
def delete_sprint(sprint_id: int, db: Session = Depends(get_db)):

    sprint = db.query(Sprint).filter(
        Sprint.id == sprint_id
    ).first()

    if not sprint:
        return {"message": "Sprint not found"}

    db.delete(sprint)
    db.commit()

    return {
        "message": "Sprint deleted successfully"
    }
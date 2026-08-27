from fastapi import APIRouter, Depends,Request
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserLogin
from app.models.user import User
from app.database.database import get_db
from app.auth.security import hash_password, verify_password
from app.auth.jwt_handler import create_access_token

router = APIRouter()


# ===========================
# Register
# ===========================
@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:
        return {
            "message": "Email already registered!"
        }

    hashed_password = hash_password(user.password)

    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        role=user.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully!"
    }


# ===========================
# Login
# ===========================
@router.post("/login")
def login(request:Request,user: UserLogin, db: Session = Depends(get_db)):

    db_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if not db_user:
        return {
            "message": "Invalid email or password"
        }

    if not verify_password(user.password, db_user.password):
        return {
            "message": "Invalid email or password"
        }

    token = create_access_token(
        data={
            "id": db_user.id,
            "sub": db_user.email,
            "role": db_user.role
        }
    )
    request.session["user"] = {
        "id": db_user.id,
        "name": db_user.name,
        "email": db_user.email,
        "role": db_user.role
    }

    return {
        "access_token": token,
        "token_type": "bearer"
    }
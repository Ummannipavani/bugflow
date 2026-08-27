from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from app.auth.jwt_handler import SECRET_KEY, ALGORITHM


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login",
    auto_error=False
)


# =========================================================
# GET CURRENT USER
# =========================================================

def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme)
):

    # =====================================================
    # 1. CHECK SESSION FIRST
    # =====================================================

    session_user = request.session.get("user")

    if session_user:

        return {
            "id": session_user.get("id"),
            "name": session_user.get("name"),
            "email": session_user.get("email"),
            "role": session_user.get("role")
        }


    # =====================================================
    # 2. CHECK JWT TOKEN
    # =====================================================

    if not token:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )


    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )


    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )


        user_id = payload.get("id")
        email = payload.get("sub")
        role = payload.get("role")


        if user_id is None or email is None or role is None:

            raise credentials_exception


        return {
            "id": user_id,
            "email": email,
            "role": role
        }


    except JWTError:

        raise credentials_exception


# =========================================================
# ROLE CHECK
# =========================================================

def require_roles(*allowed_roles):

    def role_checker(
        current_user: dict = Depends(
            get_current_user
        )
    ):

        if current_user["role"] not in allowed_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action"
            )


        return current_user


    return role_checker
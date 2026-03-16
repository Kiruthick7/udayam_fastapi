from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from auth_utils import create_access_token, create_refresh_token
from jose import jwt, JWTError
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/refresh")
def refresh_token(payload: RefreshRequest, conn=Depends(get_db)):
    try:
        decoded = jwt.decode(
            payload.refresh_token,
            settings.get_jwt_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
            audience="mobile-app",
            issuer="trial-balance-api"
        )

        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        user_id = decoded.get("sub")
        session_id = decoded.get("session_id")
        if not user_id or not session_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Get user role and session_id from database
        with get_db() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute(
                    "SELECT role, session_id FROM USERS_APP WHERE id = %s",
                    (int(user_id),)
                )
                user = cursor.fetchone()

                if not user or user['session_id'] != session_id:
                    raise HTTPException(status_code=401, detail="Session invalidated. Please login again.")

                return {
                    "access_token": create_access_token({
                        "user_id": int(user_id),
                        "role": user['role'],
                        "session_id": session_id
                    }),
                    "refresh_token": create_refresh_token(int(user_id), session_id),
                    "token_type": "bearer"
                }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

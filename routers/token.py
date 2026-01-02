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
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        return {
            "access_token": create_access_token({
                "user_id": int(user_id),
                "role": "user"
            }),
            "refresh_token": create_refresh_token(int(user_id)),
            "token_type": "bearer"
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from auth_utils import create_refresh_token, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, conn=Depends(get_db)):
    cursor = None

    try:
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, email, username, password_hash, role FROM USERS_APP WHERE email = %s",
            (request.email,)
        )

        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=403, detail="Invalid email or password")

        if not verify_password(request.password, user['password_hash']):
            raise HTTPException(status_code=403, detail="Invalid email or password")

        access_token = create_access_token({
            "user_id": user['id'],
            "role": user['role']
        })

        refresh_token = create_refresh_token(user['id'])

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user['id'],
                "email": user['email'],
                "username": user.get('username', user['email']),
                "role": user['role']
            }
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

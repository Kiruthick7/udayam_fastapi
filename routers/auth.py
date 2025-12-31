import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from auth import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    token_type: str
    user: dict

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, conn=Depends(get_db)):
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT id, email, password_hash, role FROM USERS_APP WHERE email = %s",
            (request.email,)
        )
        user = cursor.fetchone()

        if not user or not verify_password(request.password, user['password_hash']): # type: ignore
            raise HTTPException(status_code=403, detail="Invalid email or password")

        token = create_access_token({
            "user_id": user['id'],
            "role": user['role'],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }) # type: ignore

        return LoginResponse(
            token=token,
            token_type="bearer",
            user={"id": user['id'], "email": user['email'], "role": user['role']}
        )

    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        cursor.close()
        conn.close()

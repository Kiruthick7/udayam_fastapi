from fastapi import APIRouter, Depends, HTTPException
from auth_utils import verify_token, hash_token
from database import get_db
from datetime import datetime
from jose import jwt
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/logout")
def logout(
    token_data=Depends(verify_token),
    conn=Depends(get_db),
):
    if conn is None:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = None
    auth_header = token_data.get("raw_token")
    if not auth_header:
        raise HTTPException(status_code=400, detail="Missing token")

    try:
        cursor = conn.cursor()

        decoded = jwt.decode(
            auth_header,
            settings.get_jwt_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
            audience="mobile-app",
            issuer="trial-balance-api",
        )

        exp = datetime.fromtimestamp(decoded["exp"])
        token_hash = hash_token(auth_header)

        cursor.execute(
            """
            INSERT INTO revoked_tokens (token_hash, expires_at)
            VALUES (%s, %s)
            """,
            (token_hash, exp),
        )
        conn.commit()

        return {"message": "Logged out successfully"}

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

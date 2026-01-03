from datetime import datetime, timedelta
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings
import hashlib
from database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Standardize user_id to 'sub' claim
    if 'user_id' in to_encode:
        to_encode['sub'] = str(to_encode['user_id'])
        to_encode['role'] = to_encode.get('role', 'user')
        del to_encode['user_id']

    to_encode.update({
        "exp": expire,
        "type": "access",
        "iss": "trial-balance-api",
        "aud": "mobile-app"
    })

    return jwt.encode(
        to_encode,
        settings.get_jwt_secret_value(),
        algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(user_id: int):
    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "iss": "trial-balance-api",
        "aud": "mobile-app"
    }

    return jwt.encode(
        payload,
        settings.get_jwt_secret_value(),
        algorithm=settings.JWT_ALGORITHM
    )


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn=Depends(get_db)
):
    token = credentials.credentials
    token_hash = hash_token(token)

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT 1 FROM revoked_tokens
            WHERE token_hash = %s AND expires_at > NOW()
            """,
            (token_hash,),
        )

        if cursor.fetchone():
            raise HTTPException(status_code=401, detail="Token revoked")

        # Verify JWT token
        try:
            payload = jwt.decode(
                token,
                settings.get_jwt_secret_value(),
                algorithms=[settings.JWT_ALGORITHM],
                audience="mobile-app",
                issuer="trial-balance-api"
            )

            # Verify it's an access token
            if payload.get("type") != "access":
                raise HTTPException(status_code=401, detail="Invalid token type")

            # Return token data with raw token
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token - missing user ID")

            return {
                "user_id": int(user_id),
                "role": payload.get("role", "user"),
                "email": payload.get("email"),
                "raw_token": token,
                "payload": payload
            }
        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    finally:
        cursor.close()
        conn.close()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

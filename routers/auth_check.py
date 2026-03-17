from fastapi import APIRouter, Depends
from auth_utils import verify_token

router = APIRouter(prefix="/auth-check", tags=["auth"])

@router.get("/check")
def check_auth(current_user: dict = Depends(verify_token)):
    """
    Returns 200 OK if the token/session is valid. Returns 401/403 if not.
    """
    return {"status": "ok", "user_id": current_user.get("user_id"), "role": current_user.get("role")}

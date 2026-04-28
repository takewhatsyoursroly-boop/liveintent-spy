from fastapi import Header, HTTPException
from liveintent_shared.config import get_settings

def require_admin(authorization: str = Header(..., alias="Authorization")) -> None:
    expected = f"Bearer {get_settings().admin_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="invalid admin token")

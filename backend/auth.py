import os
import time
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "super-secret-key-jobhunt-pro")
JWT_ALGORITHM = "HS256"

# We use HTTPBearer security scheme
security = HTTPBearer(auto_error=False)

def create_access_token(data: dict, expires_in: int = 3600) -> str:
    """
    Generates a JWT access token for testing and user identification.
    """
    payload = data.copy()
    payload.update({"exp": time.time() + expires_in})
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

async def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    """
    FastAPI dependency to validate Bearer tokens.
    Raises HTTPException(401) on failure.
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing or invalid scheme"
        )
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

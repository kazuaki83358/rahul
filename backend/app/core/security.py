# path: backend/app/core/security.py
import hashlib
from datetime import datetime, timedelta
from typing import Any, Union, Optional
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.base import get_db
from app.models.user import User

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

try:
    from jose import jwt, JWTError
    def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=1440))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    def decode_token(token: str) -> Optional[dict]:
        try: return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except: return None
except ImportError:
    import json, base64
    def create_access_token(data: dict, expires_delta: Any = None):
        return "token_" + base64.b64encode(json.dumps(data).encode()).decode()
    def decode_token(token: str) -> Optional[dict]:
        try:
            if not token.startswith("token_"): return None
            return json.loads(base64.b64decode(token[6:]).decode())
        except: return None

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    payload = decode_token(token)
    if not payload or not payload.get("sub"): raise credentials_exception
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user: raise credentials_exception
    return user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

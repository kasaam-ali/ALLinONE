"""Job: ALLinONE Backend. Purpose: JWT auth, password hashing, and role authz helpers."""
import os
import datetime as dt
import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .db import get_db
from .models import User

SECRET = os.getenv("JWT_SECRET", "dev-only-change-me-use-32+chars!!")
ALG = "HS256"
bearer = HTTPBearer(auto_error=False)

# Architect authz: viewer=read; operator=start/cancel/approve/publish + write; admin=users+disable
PERMS = {
    "admin": {"read", "write", "approve", "admin"},
    "operator": {"read", "write", "approve"},
    "viewer": {"read"},
}


def hash_pw(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_pw(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def make_token(user: User, hours: int = 12) -> str:
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "type": "access",
        "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=hours),
    }
    return jwt.encode(payload, SECRET, algorithm=ALG)


def make_refresh_token(user: User, days: int = 7) -> str:
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "type": "refresh",
        "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=days),
    }
    return jwt.encode(payload, SECRET, algorithm=ALG)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALG])
    except jwt.PyJWTError as exc:
        raise HTTPException(401, "Invalid token") from exc


def current_user(
    cred: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not cred:
        raise HTTPException(401, "Not authenticated")
    data = decode_token(cred.credentials)
    if data.get("type") not in (None, "access"):
        # allow access tokens; reject pure refresh misuse on protected routes
        if data.get("type") == "refresh":
            raise HTTPException(401, "Access token required")
    user = db.get(User, int(data["sub"]))
    if not user or not user.is_active:
        raise HTTPException(401, "User not found")
    return user


def require(perm: str):
    def dep(user: User = Depends(current_user)) -> User:
        if perm not in PERMS.get(user.role, set()):
            raise HTTPException(403, f"Missing permission: {perm}")
        return user
    return dep

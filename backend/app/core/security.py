from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, workspace_id: str | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    payload: Dict[str, Any] = {
        "sub": subject,
        "exp": expire,
    }

    if workspace_id:
        payload["workspace_id"] = workspace_id

    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> Dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc

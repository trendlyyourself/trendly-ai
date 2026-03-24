import re

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.db.sqlite import get_db
from app.deps.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def slugify(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "workspace"


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (payload.email.lower(),),
        ).fetchone()

        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        cursor = conn.execute(
            """
            INSERT INTO users (full_name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (
                payload.full_name.strip(),
                payload.email.lower(),
                hash_password(payload.password),
            ),
        )
        user_id = cursor.lastrowid

        base_slug = slugify(payload.full_name)
        slug = base_slug
        counter = 2
        while conn.execute("SELECT id FROM workspaces WHERE slug = ?", (slug,)).fetchone():
            slug = f"{base_slug}-{counter}"
            counter += 1

        workspace_name = f"{payload.full_name.strip()}'s Workspace"
        conn.execute(
            """
            INSERT INTO workspaces (user_id, name, slug)
            VALUES (?, ?, ?)
            """,
            (user_id, workspace_name, slug),
        )
        conn.commit()

        user = conn.execute(
            "SELECT id, full_name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    token = create_access_token(user["email"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "created_at": user["created_at"],
        },
    }


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    with get_db() as conn:
        user = conn.execute(
            """
            SELECT id, full_name, email, password_hash, created_at
            FROM users
            WHERE email = ?
            """,
            (payload.email.lower(),),
        ).fetchone()

    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user["email"])

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "created_at": user["created_at"],
        },
    }

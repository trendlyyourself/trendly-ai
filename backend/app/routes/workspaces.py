import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.db.sqlite import get_db
from app.deps.auth import get_current_user

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    slug: str
    created_at: str


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


def slugify(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "workspace"


@router.get("", response_model=list[WorkspaceResponse])
def list_workspaces(current_user=Depends(get_current_user)):
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT id, name, slug, created_at
            FROM workspaces
            WHERE user_id = ?
            ORDER BY id ASC
            """,
            (current_user["id"],),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "name": row["name"],
            "slug": row["slug"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(payload: CreateWorkspaceRequest, current_user=Depends(get_current_user)):
    with get_db() as conn:
        base_slug = slugify(payload.name)
        slug = base_slug
        counter = 2

        while conn.execute("SELECT id FROM workspaces WHERE slug = ?", (slug,)).fetchone():
            slug = f"{base_slug}-{counter}"
            counter += 1

        cursor = conn.execute(
            """
            INSERT INTO workspaces (user_id, name, slug)
            VALUES (?, ?, ?)
            """,
            (current_user["id"], payload.name.strip(), slug),
        )
        conn.commit()

        row = conn.execute(
            """
            SELECT id, name, slug, created_at
            FROM workspaces
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    return {
        "id": row["id"],
        "name": row["name"],
        "slug": row["slug"],
        "created_at": row["created_at"],
    }

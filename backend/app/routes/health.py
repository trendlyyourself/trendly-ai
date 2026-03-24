from fastapi import APIRouter

from app.db.sqlite import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    with get_db() as conn:
        conn.execute("SELECT 1").fetchone()

    return {
        "status": "ok",
        "database": "sqlite",
    }

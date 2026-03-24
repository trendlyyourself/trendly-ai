from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.sqlite import init_db
from app.routes.auth import router as auth_router
from app.routes.health import router as health_router
from app.routes.workspaces import router as workspaces_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(workspaces_router)


@app.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "env": settings.app_env,
        "status": "running",
        "database": "sqlite",
    }

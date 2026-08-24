from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.deps.auth import get_current_user
from app.core.config import get_settings
from app.services.openai_service import OpenAIService

router = APIRouter(prefix="/ai", tags=["ai"])


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)


class GenerateResponse(BaseModel):
    text: str


@router.post("/generate", response_model=GenerateResponse)
async def generate_text(payload: GenerateRequest, current_user=Depends(get_current_user)):
    del current_user

    try:
        service = OpenAIService()
        text = await service.generate(payload.prompt)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI request failed",
        ) from exc

    return {"text": text}

from fastapi import Header

@router.post("/internal/generate", response_model=GenerateResponse)
async def internal_generate(
    payload: GenerateRequest,
    x_internal_service_key: str | None = Header(default=None),
):
    settings = get_settings()

    if not settings.internal_service_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal AI service key is not configured",
        )

    if x_internal_service_key != settings.internal_service_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal service key",
        )

    try:
        service = OpenAIService()
        text = await service.generate(payload.prompt)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="OpenAI request failed",
        ) from exc

    return {"text": text}

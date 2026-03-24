from pydantic import BaseModel, ConfigDict


class APIMessage(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    app: str
    db: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict
    workspace: dict | None = None


class ErrorResponse(BaseModel):
    detail: str


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

from openai import AsyncOpenAI

from app.core.config import get_settings


class OpenAIService:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def generate(self, prompt: str) -> str:
        response = await self.client.responses.create(
            model=self.model,
            input=prompt,
        )
        return response.output_text.strip()

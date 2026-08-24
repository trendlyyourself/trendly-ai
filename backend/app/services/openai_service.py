class OpenAIService:
    def __init__(self) -> None:
        pass

    async def generate(self, prompt: str) -> str:
        raise RuntimeError(
            "AI provider is not configured. OpenAI has been removed."
        )

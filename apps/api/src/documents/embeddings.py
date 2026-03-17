from openai import AsyncOpenAI, OpenAIError

from src.core.config import OpenAIProviderSettings


class EmbeddingError(Exception):
    pass


class OpenAIEmbeddingClient:
    provider_name = "openai"

    def __init__(self, settings: OpenAIProviderSettings) -> None:
        self._settings = settings
        self._client = AsyncOpenAI(
            api_key=settings.api_key.get_secret_value(),
            timeout=settings.request_timeout_seconds,
        )

    @property
    def model_name(self) -> str:
        return self._settings.embedding_model

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self._settings.is_configured:
            raise EmbeddingError("OpenAI API settings are incomplete for embeddings.")
        if not texts:
            return []

        try:
            response = await self._client.embeddings.create(
                model=self._settings.embedding_model,
                input=texts,
            )
        except OpenAIError as exc:
            raise EmbeddingError("OpenAI embeddings request failed.") from exc

        return [list(item.embedding) for item in response.data]

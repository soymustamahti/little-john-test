import base64
from typing import Any, cast

from openai import AsyncOpenAI, OpenAIError

from src.core.config import OpenAIProviderSettings

OCR_PROMPT = (
    "Extract the full readable text from this document. Preserve the natural reading order, "
    "keep headings and table-like rows on separate lines when possible, and do not summarize."
)


class OcrError(Exception):
    pass


class OpenAIDocumentOcrClient:
    provider_name = "openai"

    def __init__(self, settings: OpenAIProviderSettings) -> None:
        self._settings = settings
        self._client = AsyncOpenAI(
            api_key=settings.api_key.get_secret_value(),
            timeout=settings.request_timeout_seconds,
        )

    @property
    def model_name(self) -> str:
        return self._settings.ocr_model

    async def extract_text_from_image(
        self,
        *,
        content: bytes,
        content_type: str,
    ) -> str:
        image_url = self._build_data_url(content=content, content_type=content_type)
        return await self._extract_output_text(
            input_items=[
                {"type": "input_text", "text": OCR_PROMPT},
                {"type": "input_image", "image_url": image_url},
            ]
        )

    async def extract_text_from_pdf(
        self,
        *,
        content: bytes,
        filename: str,
    ) -> str:
        encoded_pdf = base64.b64encode(content).decode("utf-8")
        return await self._extract_output_text(
            input_items=[
                {"type": "input_text", "text": OCR_PROMPT},
                {
                    "type": "input_file",
                    "filename": filename,
                    "file_data": encoded_pdf,
                },
            ]
        )

    async def _extract_output_text(self, *, input_items: list[dict]) -> str:
        if not self._settings.is_configured:
            raise OcrError("OpenAI API settings are incomplete for OCR.")

        try:
            response = await self._client.responses.create(
                model=self._settings.ocr_model,
                input=cast(Any, [{"role": "user", "content": input_items}]),
            )
        except OpenAIError as exc:
            raise OcrError("OpenAI OCR request failed.") from exc

        output_text = (response.output_text or "").strip()
        if not output_text:
            raise OcrError("OpenAI OCR returned no text.")
        return output_text

    @staticmethod
    def _build_data_url(*, content: bytes, content_type: str) -> str:
        encoded = base64.b64encode(content).decode("utf-8")
        return f"data:{content_type};base64,{encoded}"

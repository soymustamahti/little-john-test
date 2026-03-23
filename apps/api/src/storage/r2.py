import asyncio
import logging
from typing import Any, Mapping
from urllib.parse import urlparse

from boto3.session import Session
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from src.core.config import R2Settings
from src.storage.object_store import (
    ObjectStorage,
    ObjectStorageError,
    RetrievedObject,
    StoredObject,
)


class R2ObjectStorage(ObjectStorage):
    provider_name = "cloudflare_r2"

    def __init__(self, settings: R2Settings) -> None:
        self._settings = settings
        self._client = self._build_client()

    async def upload_object(
        self,
        *,
        key: str,
        content: bytes,
        content_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> StoredObject:
        self._ensure_configured()

        try:
            await asyncio.to_thread(
                self._put_object,
                key=key,
                content=content,
                content_type=content_type,
                metadata=metadata,
            )
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageError("Failed to upload document to Cloudflare R2.") from exc

        return StoredObject(
            provider=self.provider_name,
            bucket=self._settings.bucket_name,
            key=key,
            public_url=self._build_public_url(key),
        )

    async def delete_object(self, *, key: str) -> None:
        self._ensure_configured()

        try:
            await asyncio.to_thread(self._delete_object, key=key)
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageError("Failed to delete document from Cloudflare R2.") from exc

    async def download_object(self, *, key: str) -> RetrievedObject:
        self._ensure_configured()

        try:
            return await asyncio.to_thread(self._get_object, key=key)
        except (BotoCoreError, ClientError) as exc:
            raise ObjectStorageError("Failed to fetch document from Cloudflare R2.") from exc

    def _put_object(
        self,
        *,
        key: str,
        content: bytes,
        content_type: str,
        metadata: Mapping[str, str] | None,
    ) -> None:
        self._client.put_object(
            Bucket=self._settings.bucket_name,
            Key=key,
            Body=content,
            ContentType=content_type,
            Metadata=dict(metadata or {}),
        )

    def _delete_object(self, *, key: str) -> None:
        self._client.delete_object(Bucket=self._settings.bucket_name, Key=key)

    def _get_object(self, *, key: str) -> RetrievedObject:
        response = self._client.get_object(Bucket=self._settings.bucket_name, Key=key)
        body = response["Body"]
        try:
            content = body.read()
        finally:
            body.close()

        return RetrievedObject(
            content=content,
            content_type=response.get("ContentType"),
        )

    def _build_client(self) -> Any:
        return Session().client(
            service_name="s3",
            endpoint_url=self._settings.endpoint_url,
            aws_access_key_id=self._settings.access_key_id,
            aws_secret_access_key=self._settings.secret_access_key.get_secret_value(),
            region_name="auto",
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def _build_public_url(self, key: str) -> str | None:
        base_url = (self._settings.public_url or "").strip()
        if not base_url:
            return None

        parsed = urlparse(base_url)
        if parsed.netloc.endswith(".r2.cloudflarestorage.com"):
            logging.warning(
                "R2_PUBLIC_URL points at the S3 API endpoint, so no direct public object URL "
                "will be exposed for uploaded documents."
            )
            return None

        return f"{base_url.rstrip('/')}/{key.lstrip('/')}"

    def _ensure_configured(self) -> None:
        if self._settings.is_configured:
            return

        raise ObjectStorageError(
            "Cloudflare R2 settings are incomplete. Set R2_ACCOUNT_ID, "
            "R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, and R2_BUCKET_NAME."
        )

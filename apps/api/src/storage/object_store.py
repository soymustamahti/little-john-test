from dataclasses import dataclass
from typing import Mapping, Protocol


class ObjectStorageError(Exception):
    """Raised when the object storage adapter cannot complete an operation."""


@dataclass(frozen=True)
class StoredObject:
    provider: str
    bucket: str
    key: str
    public_url: str | None = None


class ObjectStorage(Protocol):
    async def upload_object(
        self,
        *,
        key: str,
        content: bytes,
        content_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> StoredObject: ...

    async def delete_object(self, *, key: str) -> None: ...

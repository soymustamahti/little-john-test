import hashlib
import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from src.documents.schemas import DocumentKind

SUPPORTED_EXTENSIONS = (
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".tif",
    ".tiff",
    ".bmp",
    ".docx",
    ".xlsx",
    ".xls",
    ".ods",
    ".csv",
)
GENERIC_CONTENT_TYPES = {"application/octet-stream", "binary/octet-stream"}
OLE_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")


@dataclass(frozen=True)
class AllowedFileType:
    kind: DocumentKind
    content_types: tuple[str, ...]
    default_content_type: str


ALLOWED_FILE_TYPES: dict[str, AllowedFileType] = {
    ".pdf": AllowedFileType(
        kind=DocumentKind.PDF,
        content_types=("application/pdf",),
        default_content_type="application/pdf",
    ),
    ".png": AllowedFileType(
        kind=DocumentKind.IMAGE,
        content_types=("image/png",),
        default_content_type="image/png",
    ),
    ".jpg": AllowedFileType(
        kind=DocumentKind.IMAGE,
        content_types=("image/jpeg", "image/jpg", "image/pjpeg"),
        default_content_type="image/jpeg",
    ),
    ".jpeg": AllowedFileType(
        kind=DocumentKind.IMAGE,
        content_types=("image/jpeg", "image/jpg", "image/pjpeg"),
        default_content_type="image/jpeg",
    ),
    ".webp": AllowedFileType(
        kind=DocumentKind.IMAGE,
        content_types=("image/webp",),
        default_content_type="image/webp",
    ),
    ".tif": AllowedFileType(
        kind=DocumentKind.IMAGE,
        content_types=("image/tiff",),
        default_content_type="image/tiff",
    ),
    ".tiff": AllowedFileType(
        kind=DocumentKind.IMAGE,
        content_types=("image/tiff",),
        default_content_type="image/tiff",
    ),
    ".bmp": AllowedFileType(
        kind=DocumentKind.IMAGE,
        content_types=("image/bmp",),
        default_content_type="image/bmp",
    ),
    ".docx": AllowedFileType(
        kind=DocumentKind.DOCX,
        content_types=("application/vnd.openxmlformats-officedocument.wordprocessingml.document",),
        default_content_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
    ),
    ".xlsx": AllowedFileType(
        kind=DocumentKind.SPREADSHEET,
        content_types=("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",),
        default_content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ),
    ".xls": AllowedFileType(
        kind=DocumentKind.SPREADSHEET,
        content_types=("application/vnd.ms-excel",),
        default_content_type="application/vnd.ms-excel",
    ),
    ".ods": AllowedFileType(
        kind=DocumentKind.SPREADSHEET,
        content_types=("application/vnd.oasis.opendocument.spreadsheet",),
        default_content_type="application/vnd.oasis.opendocument.spreadsheet",
    ),
    ".csv": AllowedFileType(
        kind=DocumentKind.SPREADSHEET,
        content_types=("text/csv", "application/csv", "application/vnd.ms-excel"),
        default_content_type="text/csv",
    ),
}


class DocumentValidationError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class ValidatedDocumentUpload:
    original_filename: str
    sanitized_stem: str
    content: bytes
    content_type: str
    file_extension: str
    file_kind: DocumentKind
    size_bytes: int
    sha256: str


def validate_uploaded_document(
    *,
    filename: str,
    content_type: str | None,
    content: bytes,
    max_size_bytes: int,
) -> ValidatedDocumentUpload:
    original_filename = _normalize_filename(filename)
    size_bytes = len(content)

    if size_bytes == 0:
        raise DocumentValidationError("Uploaded file is empty.", status_code=400)

    if size_bytes > max_size_bytes:
        raise DocumentValidationError(
            f"Uploaded file exceeds the {max_size_bytes} byte limit.",
            status_code=413,
        )

    file_extension = Path(original_filename).suffix.lower()
    allowed_type = ALLOWED_FILE_TYPES.get(file_extension)
    if allowed_type is None:
        supported_types = ", ".join(SUPPORTED_EXTENSIONS)
        raise DocumentValidationError(
            f"Unsupported file type '{file_extension}'. Supported types: {supported_types}.",
            status_code=415,
        )

    normalized_content_type = _normalize_content_type(content_type)
    allowed_content_types = set(allowed_type.content_types)
    if normalized_content_type and normalized_content_type not in GENERIC_CONTENT_TYPES:
        if normalized_content_type not in allowed_content_types:
            raise DocumentValidationError(
                (
                    f"File content type '{normalized_content_type}' does not match the "
                    f"supported MIME types for '{file_extension}'."
                ),
                status_code=415,
            )

    _validate_file_signature(file_extension=file_extension, content=content)

    final_content_type = (
        normalized_content_type
        if normalized_content_type and normalized_content_type not in GENERIC_CONTENT_TYPES
        else allowed_type.default_content_type
    )

    return ValidatedDocumentUpload(
        original_filename=original_filename,
        sanitized_stem=_sanitize_stem(Path(original_filename).stem),
        content=content,
        content_type=final_content_type,
        file_extension=file_extension,
        file_kind=allowed_type.kind,
        size_bytes=size_bytes,
        sha256=hashlib.sha256(content).hexdigest(),
    )


def build_storage_key(*, document_id: UUID, sanitized_stem: str, file_extension: str) -> str:
    return f"documents/{document_id}/{sanitized_stem}{file_extension}"


def _normalize_filename(filename: str) -> str:
    normalized = (filename or "").replace("\\", "/").split("/")[-1].strip()
    if not normalized:
        raise DocumentValidationError("Uploaded file must include a filename.", status_code=400)
    if any(ord(char) < 32 or ord(char) == 127 for char in normalized):
        raise DocumentValidationError(
            "Uploaded filename contains invalid control characters.",
            status_code=400,
        )
    return normalized


def _normalize_content_type(content_type: str | None) -> str:
    if content_type is None:
        return ""
    return content_type.split(";", maxsplit=1)[0].strip().lower()


def _sanitize_stem(stem: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", stem).strip("._-").lower()
    return sanitized or "document"


def _validate_file_signature(*, file_extension: str, content: bytes) -> None:
    if file_extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise DocumentValidationError(
                "Uploaded file does not contain a valid PDF header.",
                status_code=415,
            )
        return

    if file_extension in {".jpg", ".jpeg"}:
        if not content.startswith(b"\xff\xd8\xff"):
            raise DocumentValidationError("Uploaded JPEG file is invalid.", status_code=415)
        return

    if file_extension == ".png":
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise DocumentValidationError("Uploaded PNG file is invalid.", status_code=415)
        return

    if file_extension == ".webp":
        if not (content.startswith(b"RIFF") and content[8:12] == b"WEBP"):
            raise DocumentValidationError("Uploaded WEBP file is invalid.", status_code=415)
        return

    if file_extension in {".tif", ".tiff"}:
        if not (content.startswith(b"II*\x00") or content.startswith(b"MM\x00*")):
            raise DocumentValidationError("Uploaded TIFF file is invalid.", status_code=415)
        return

    if file_extension == ".bmp":
        if not content.startswith(b"BM"):
            raise DocumentValidationError("Uploaded BMP file is invalid.", status_code=415)
        return

    if file_extension == ".docx":
        archive_entries = _load_archive_entries(content)
        if "[Content_Types].xml" not in archive_entries or not any(
            entry.startswith("word/") for entry in archive_entries
        ):
            raise DocumentValidationError("Uploaded DOCX file is invalid.", status_code=415)
        return

    if file_extension == ".xlsx":
        archive_entries = _load_archive_entries(content)
        if "[Content_Types].xml" not in archive_entries or not any(
            entry.startswith("xl/") for entry in archive_entries
        ):
            raise DocumentValidationError("Uploaded XLSX file is invalid.", status_code=415)
        return

    if file_extension == ".ods":
        archive_entries = _load_archive_entries(content)
        mimetype = archive_entries.get("mimetype")
        if mimetype != b"application/vnd.oasis.opendocument.spreadsheet":
            raise DocumentValidationError("Uploaded ODS file is invalid.", status_code=415)
        return

    if file_extension == ".xls":
        if not content.startswith(OLE_SIGNATURE):
            raise DocumentValidationError("Uploaded XLS file is invalid.", status_code=415)
        return

    if file_extension == ".csv" and b"\x00" in content[:4096]:
        raise DocumentValidationError(
            "Uploaded CSV file appears to contain binary data.",
            status_code=415,
        )


def _load_archive_entries(content: bytes) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = {name: b"" for name in archive.namelist()}
            if "mimetype" in entries:
                entries["mimetype"] = archive.read("mimetype")
            return entries
    except zipfile.BadZipFile as exc:
        raise DocumentValidationError("Uploaded Office file is invalid.", status_code=415) from exc

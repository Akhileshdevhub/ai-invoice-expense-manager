"""Upload validation.

Runs before anything else touches the file. A financial tool that accepts
arbitrary uploads without checking them is a liability, not a feature —
so this rejects the obvious bad cases (wrong type, too large, empty,
corrupted) before OCR ever opens the file.
"""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB — generous for a phone photo of a receipt


@dataclass
class ValidationResult:
    is_valid: bool
    error: str | None = None


def validate_upload(file_path: str, file_bytes: bytes) -> ValidationResult:
    """Validate a file before it enters the OCR pipeline.

    file_bytes is passed in explicitly (rather than re-reading the path)
    because Streamlit hands us an in-memory buffer for uploaded files.
    """
    suffix = Path(file_path).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return ValidationResult(
            False, f"Unsupported file type '{suffix}'. Allowed: PDF, JPG, PNG."
        )

    if len(file_bytes) == 0:
        return ValidationResult(False, "The uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        size_mb = len(file_bytes) / (1024 * 1024)
        return ValidationResult(
            False,
            f"File is {size_mb:.1f} MB, which exceeds the 15 MB limit.",
        )

    if suffix == ".pdf":
        # A real corruption check happens later when pdf2image tries to
        # rasterize it, but we can catch an obviously-not-a-PDF file here.
        if not file_bytes.startswith(b"%PDF"):
            return ValidationResult(False, "File has a .pdf extension but isn't a valid PDF.")
    else:
        if not _is_readable_image(file_bytes):
            return ValidationResult(False, "Image file is corrupted or unreadable.")

    return ValidationResult(True)


def _is_readable_image(file_bytes: bytes) -> bool:
    import io

    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, OSError):
        return False

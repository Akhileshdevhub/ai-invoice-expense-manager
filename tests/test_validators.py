from app.utils.validators import validate_upload, MAX_FILE_SIZE_BYTES


def test_rejects_unsupported_extension():
    result = validate_upload("receipt.txt", b"hello")
    assert not result.is_valid
    assert "Unsupported" in result.error


def test_rejects_empty_file():
    result = validate_upload("receipt.png", b"")
    assert not result.is_valid
    assert "empty" in result.error.lower()


def test_rejects_oversized_file():
    oversized = b"0" * (MAX_FILE_SIZE_BYTES + 1)
    result = validate_upload("receipt.jpg", oversized)
    assert not result.is_valid
    assert "exceeds" in result.error


def test_rejects_pdf_extension_with_non_pdf_content():
    result = validate_upload("receipt.pdf", b"not actually a pdf")
    assert not result.is_valid


def test_rejects_corrupted_image():
    result = validate_upload("receipt.png", b"this is not a valid png file")
    assert not result.is_valid


def test_accepts_minimal_valid_pdf_header():
    # A real PDF also needs a valid trailer to render, but the validator's
    # job is only to catch obviously-wrong uploads before OCR touches them.
    result = validate_upload("receipt.pdf", b"%PDF-1.4 minimal fake content")
    assert result.is_valid

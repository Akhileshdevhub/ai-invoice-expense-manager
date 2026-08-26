"""Image preprocessing before OCR.

Tesseract's accuracy is very sensitive to image quality. These steps are
the standard, well-documented ones for receipt/document OCR — each is
here because it measurably helps Tesseract on phone-camera photos, not
because "more preprocessing" is inherently better:

- grayscale: color information doesn't help text recognition and slows
  everything down.
- upscaling small images: Tesseract is trained mostly on ~300 DPI
  documents; a small phone photo downsized by messaging apps often needs
  to be scaled up first.
- denoising: phone cameras in low light introduce grain that Tesseract
  can mistake for character strokes.
- adaptive thresholding (binarization): converts to pure black/white using
  a locally-computed threshold, which handles uneven receipt lighting
  (e.g. a shadow across half the paper) far better than a single global
  threshold would.
"""

import cv2
import numpy as np
from PIL import Image

MIN_DIMENSION_FOR_UPSCALE = 1000


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """Run the full preprocessing pipeline and return a PIL image ready for Tesseract."""
    img = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = _upscale_if_small(gray)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    binarized = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=15,
    )
    return Image.fromarray(binarized)


def _upscale_if_small(gray: np.ndarray) -> np.ndarray:
    h, w = gray.shape
    if max(h, w) >= MIN_DIMENSION_FOR_UPSCALE:
        return gray
    scale = MIN_DIMENSION_FOR_UPSCALE / max(h, w)
    new_size = (int(w * scale), int(h * scale))
    return cv2.resize(gray, new_size, interpolation=cv2.INTER_CUBIC)

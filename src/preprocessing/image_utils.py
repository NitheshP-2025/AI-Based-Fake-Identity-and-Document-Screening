from pathlib import Path

import cv2
import numpy as np

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
MAX_FILE_SIZE_MB = 15
OCR_WIDTH = 1600                 # images are resized to this width before OCR
MRZ_BOTTOM_FRACTION = 0.30       # the MRZ sits in the bottom part of the data page


class ImageLoadError(Exception):
    """Raised when an image is missing, unsupported, too large, or unreadable."""


def load_image(path):
    """Load an image from disk as a BGR array, with input checks."""
    path = Path(path)
    if not path.exists():
        raise ImageLoadError(f"File not found: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ImageLoadError(
            f"Unsupported file type '{path.suffix}'. Use one of: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")
    if path.stat().st_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ImageLoadError(f"File is larger than {MAX_FILE_SIZE_MB} MB.")

    # np.fromfile + imdecode also works with non-English characters in the path.
    data = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if image is None:
        raise ImageLoadError(f"Could not read '{path.name}'. The file may be corrupt.")
    return image


def to_grayscale(image):
    """Convert a colour image to grayscale (grayscale input is returned unchanged)."""
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def resize_to_width(image, width=OCR_WIDTH):
    """Resize an image to a fixed width, keeping the aspect ratio."""
    height, current_width = image.shape[:2]
    if current_width == width:
        return image
    scale = width / current_width
    method = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
    return cv2.resize(image, (width, int(round(height * scale))), interpolation=method)


def crop_bottom(image, fraction=MRZ_BOTTOM_FRACTION):
    """Keep only the bottom part of the image, where the MRZ is located."""
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be greater than 0 and at most 1.")
    top = int(image.shape[0] * (1 - fraction))
    return image[top:]


def denoise(gray):
    """Remove noise from a grayscale image."""
    return cv2.fastNlMeansDenoising(gray, None, 7, 7, 21)


def enhance_contrast(gray):
    """Improve local contrast with CLAHE."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def preprocess_for_ocr(image, bottom_fraction=MRZ_BOTTOM_FRACTION, width=OCR_WIDTH):
    """Prepare an image for MRZ reading: resize, crop, grayscale, denoise, contrast."""
    resized = resize_to_width(image, width)
    region = crop_bottom(resized, bottom_fraction)
    gray = to_grayscale(region)
    return enhance_contrast(denoise(gray))

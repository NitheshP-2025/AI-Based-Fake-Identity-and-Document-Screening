from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from src.ocr.engine import EasyOcrEngine, OcrEngineError
from src.ocr.mrz_reader import MrzExtraction, MrzNotFoundError, extract_mrz
from src.preprocessing.image_utils import ImageLoadError, load_image, preprocess_for_ocr
from src.validation.passport_validator import PassportReport, validate_passport


@dataclass
class ScreeningResult:
    """Everything produced while screening one passport image."""
    image_path: str
    extraction: Optional[MrzExtraction] = None
    report: Optional[PassportReport] = None
    error: Optional[str] = None
    raw_rows: list = field(default_factory=list)     # text rows exactly as OCR returned them

    @property
    def status(self) -> str:
        if self.error or self.report is None:
            return "ERROR"
        return "VALID" if self.report.is_valid else "SUSPICIOUS"


def screen_passport_image(path, engine=None, today: Optional[date] = None) -> ScreeningResult:
    """Screen one passport image. Problems are returned in the result, not raised."""
    result = ScreeningResult(image_path=str(path))
    try:
        image = load_image(path)
        processed = preprocess_for_ocr(image)
        engine = engine if engine is not None else EasyOcrEngine()
        rows = engine.read_rows(processed)
        result.raw_rows = list(rows)
        result.extraction = extract_mrz(rows)
        result.report = validate_passport(result.extraction.line1, result.extraction.line2, today)
    except (ImageLoadError, MrzNotFoundError, OcrEngineError, ValueError) as exc:
        result.error = str(exc)
    return result

from statistics import median

from .mrz_reader import ALLOWED_CHARS


class OcrEngineError(Exception):
    """Raised when the OCR engine cannot be started."""


def group_into_rows(detections) -> list:
    """Join the text boxes found by OCR into rows, from top to bottom.

    Each detection is (box, text, confidence), where box is four (x, y) points.
    Boxes with a similar vertical position belong to the same row and are joined
    from left to right.
    """
    items = []
    for detection in detections:
        box, text = detection[0], detection[1]
        ys = [point[1] for point in box]
        xs = [point[0] for point in box]
        items.append({"y": sum(ys) / len(ys), "x": min(xs), "h": max(ys) - min(ys), "text": text})
    if not items:
        return []

    tolerance = 0.6 * median(item["h"] for item in items)
    items.sort(key=lambda item: item["y"])
    rows = [[items[0]]]
    for item in items[1:]:
        row_y = sum(i["y"] for i in rows[-1]) / len(rows[-1])
        if abs(item["y"] - row_y) <= tolerance:
            rows[-1].append(item)
        else:
            rows.append([item])
    return ["".join(i["text"] for i in sorted(row, key=lambda i: i["x"])) for row in rows]


class EasyOcrEngine:
    """Reads the text rows of an image with EasyOCR (model loaded on first use)."""

    def __init__(self, gpu: bool = False):
        self.gpu = gpu
        self._reader = None

    def _get_reader(self):
        if self._reader is None:
            try:
                import easyocr
            except ImportError as exc:
                raise OcrEngineError("EasyOCR is not installed. Run: pip install easyocr") from exc
            self._reader = easyocr.Reader(["en"], gpu=self.gpu, verbose=False)
        return self._reader

    def read_rows(self, image) -> list:
        detections = self._get_reader().readtext(
            image, detail=1, paragraph=False, allowlist=ALLOWED_CHARS)
        return group_into_rows(detections)

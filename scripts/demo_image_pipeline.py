import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ocr.engine import EasyOcrEngine                 # noqa: E402
from src.pipeline import screen_passport_image           # noqa: E402

SAMPLES = Path(__file__).resolve().parents[1] / "data" / "samples"


def show(path, engine):
    start = time.time()
    result = screen_passport_image(path, engine)
    seconds = time.time() - start

    print("=" * 70)
    print(f"IMAGE: {Path(path).name}   ({seconds:.1f} s)")
    print("=" * 70)

    if result.extraction:
        print("MRZ read from the image:")
        print("  ", result.extraction.line1)
        print("  ", result.extraction.line2)
        print(f"   (OCR characters repaired: {result.extraction.corrections})")
    if result.error:
        print("ERROR:", result.error)
        if result.raw_rows:
            print("Text rows read by OCR:")
            for row in result.raw_rows:
                print("  ", row)
        print()
        return

    report = result.report
    fields = report.fields
    print(f"Name: {fields['given_names']} {fields['surname']}   Passport: {fields['passport_number']}")
    print("-" * 70)
    for check in report.checks:
        print(f"  {check.name:<26}printed {check.found}  expected {check.expected:<3} "
              f"{'PASS' if check.passed else 'FAIL'}")
    print(f"  Rules passed: {sum(r.passed for r in report.rules)} of {len(report.rules)}")
    print("-" * 70)
    if report.is_valid:
        print("RESULT: VALID - no problems found")
    else:
        print(f"RESULT: SUSPICIOUS - {report.failed_count} problem(s):")
        for reason in report.reasons:
            print("  -", reason)
        print("  (A failed check can also be an OCR reading error, so the officer should verify.)")
    print()


if __name__ == "__main__":
    paths = [Path(p) for p in sys.argv[1:]] or sorted(SAMPLES.glob("sample_*.png"))
    if not paths:
        print("No images found. Run: python scripts\\make_sample_passports.py")
        sys.exit(1)
    print("Loading OCR model (the first run downloads it)...")
    engine = EasyOcrEngine()
    for p in paths:
        show(p, engine)

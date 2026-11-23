import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.validation.mrz_checksum import build_td3_line1, build_td3_line2   # noqa: E402
from src.validation.passport_validator import validate_passport_text       # noqa: E402

LINE1 = build_td3_line1("P", "UTO", "SHARMA", "PRIYA")


def make_line2(**changes):
    values = {"passport_number": "K1234567", "nationality": "UTO", "date_of_birth": "900515",
              "sex": "F", "date_of_expiry": "310915"}
    values.update(changes)
    return build_td3_line2(**values)


def show(title: str, mrz_text: str) -> None:
    report = validate_passport_text(mrz_text)      # raw text goes straight in
    f = report.fields
    print("=" * 70)
    print(title)
    print("=" * 70)
    print(f"Name: {f['given_names']} {f['surname']}   Passport: {f['passport_number']}   "
          f"DOB: {f['date_of_birth']}   Expiry: {f['date_of_expiry']}")
    print("-" * 70)
    print("CHECK DIGITS")
    for c in report.checks:
        print(f"  {c.name:<26}printed {c.found}  expected {c.expected:<3} {'PASS' if c.passed else 'FAIL'}")
    print("RULES")
    for r in report.rules:
        print(f"  {r.name:<36}{'PASS' if r.passed else 'FAIL'}  {r.detail}")
    print("-" * 70)
    if report.is_valid:
        print("RESULT: VALID - no problems found")
    else:
        print(f"RESULT: SUSPICIOUS - {report.failed_count} problem(s):")
        for reason in report.reasons:
            print("  -", reason)
    print()


if __name__ == "__main__":
    genuine = make_line2()
    # Same passport with the day of birth edited and the check digit NOT updated.
    edited = genuine[:13] + "900516" + genuine[19:]

    show("TEST 1: Valid synthetic passport", LINE1 + "\n" + genuine)
    show("TEST 2: Date of birth edited (check digit not updated)", LINE1 + "\n" + edited)
    show("TEST 3: Expired passport (digits are correct)", LINE1 + "\n" + make_line2(date_of_expiry="200915"))
    show("TEST 4: Expiry extended to 2045, digits recalculated by the forger",
         LINE1 + "\n" + make_line2(date_of_expiry="450915"))

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.validation.mrz_checksum import validate_td3   # noqa: E402

LINE1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
GENUINE_LINE2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
# Same passport, but the day of birth was changed from 12 to 13.
EDITED_LINE2 = "L898902C36UTO7408132F1204159ZE184226B<<<<<10"


def show(title: str, line1: str, line2: str) -> None:
    result = validate_td3(line1, line2)
    fields = result.fields
    print("=" * 62)
    print(title)
    print("=" * 62)
    print(f"Name            : {fields['given_names']} {fields['surname']}")
    print(f"Passport number : {fields['passport_number']}")
    print(f"Nationality     : {fields['nationality']}")
    print(f"Date of birth   : {fields['date_of_birth']} (YYMMDD)")
    print(f"Date of expiry  : {fields['date_of_expiry']} (YYMMDD)")
    print("-" * 62)
    print(f"{'Check':<26}{'Printed':<10}{'Expected':<10}Result")
    for c in result.checks:
        status = "PASS" if c.passed else "FAIL"
        print(f"{c.name:<26}{c.found:<10}{c.expected:<10}{status}")
    print("-" * 62)
    if result.is_valid:
        print("RESULT: all check digits are valid")
    else:
        print("RESULT: SUSPICIOUS - the following checks failed:")
        for reason in result.reasons:
            print("  -", reason)
    print()


if __name__ == "__main__":
    show("TEST 1: Genuine specimen passport", LINE1, GENUINE_LINE2)
    show("TEST 2: Passport with an edited date of birth", LINE1, EDITED_LINE2)

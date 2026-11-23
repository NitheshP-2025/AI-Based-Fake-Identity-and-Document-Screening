from dataclasses import dataclass
from datetime import date

MAX_VALIDITY_YEARS = 10          # assumed longest validity of an adult passport
VALID_SEX_CODES = ("M", "F", "X", "<")


@dataclass
class RuleResult:
    """The outcome of one rule."""
    name: str
    passed: bool
    detail: str


def _is_digits(text: str) -> bool:
    return len(text) > 0 and all("0" <= ch <= "9" for ch in text)


def _add_years(day: date, years: int) -> date:
    """Add years to a date, handling 29 February."""
    try:
        return day.replace(year=day.year + years)
    except ValueError:
        return day.replace(year=day.year + years, day=28)


def parse_mrz_date(yymmdd: str, kind: str, today: date = None):
    """Convert an MRZ date (YYMMDD) to a real date, or None if it is not valid.

    The MRZ has only two year digits, so the century must be guessed:
    - 'birth': a year larger than the current two-digit year means the 1900s,
      otherwise the 2000s.
    - 'expiry': always the 2000s.
    """
    if len(yymmdd) != 6 or not _is_digits(yymmdd):
        return None
    today = today or date.today()
    yy, mm, dd = int(yymmdd[0:2]), int(yymmdd[2:4]), int(yymmdd[4:6])
    if kind == "birth":
        year = 1900 + yy if yy > today.year % 100 else 2000 + yy
    else:
        year = 2000 + yy
    try:
        return date(year, mm, dd)
    except ValueError:        # for example month 13 or 30 February
        return None


def validate_dates(fields: dict, today: date = None) -> list:
    """Apply date rules to the parsed MRZ fields."""
    today = today or date.today()
    results = []

    birth = parse_mrz_date(fields["date_of_birth"], "birth", today)
    results.append(RuleResult(
        "Date of birth is a real date", birth is not None,
        f"{birth.isoformat()}" if birth else f"'{fields['date_of_birth']}' is not a valid date"))
    if birth:
        results.append(RuleResult(
            "Date of birth is not in the future", birth <= today,
            f"Born {birth.isoformat()}" if birth <= today
            else f"Date of birth {birth.isoformat()} is in the future"))

    expiry = parse_mrz_date(fields["date_of_expiry"], "expiry", today)
    results.append(RuleResult(
        "Date of expiry is a real date", expiry is not None,
        f"{expiry.isoformat()}" if expiry else f"'{fields['date_of_expiry']}' is not a valid date"))
    if expiry:
        results.append(RuleResult(
            "Passport is not expired", expiry >= today,
            f"Valid until {expiry.isoformat()}" if expiry >= today
            else f"Passport expired on {expiry.isoformat()}"))
        latest = _add_years(today, MAX_VALIDITY_YEARS)
        results.append(RuleResult(
            f"Expiry within {MAX_VALIDITY_YEARS} years", expiry <= latest,
            "Validity period is plausible" if expiry <= latest
            else f"Expiry {expiry.isoformat()} is more than {MAX_VALIDITY_YEARS} years away"))
    return results


def validate_fields(fields: dict) -> list:
    """Apply format rules to the parsed MRZ fields."""
    def is_country_code(code: str) -> bool:
        return len(code) == 3 and all("A" <= ch <= "Z" for ch in code)

    number = fields["passport_number"]
    return [
        RuleResult("Document type is a passport", fields["document_type"].startswith("P"),
                   f"Document type is '{fields['document_type']}'"),
        RuleResult("Issuing country code", is_country_code(fields["issuing_country"]),
                   f"Found '{fields['issuing_country']}'"),
        RuleResult("Nationality code", is_country_code(fields["nationality"]),
                   f"Found '{fields['nationality']}'"),
        RuleResult("Sex field", fields["sex"] in VALID_SEX_CODES,
                   f"Found '{fields['sex']}'" if fields["sex"] in VALID_SEX_CODES
                   else f"Found '{fields['sex']}', expected one of M, F, X, <"),
        RuleResult("Passport number format", number.isalnum() and number.isascii(),
                   f"Found '{number}'" if number else "Passport number is empty"),
    ]

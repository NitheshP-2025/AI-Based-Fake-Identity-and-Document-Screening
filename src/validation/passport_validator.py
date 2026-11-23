from dataclasses import dataclass, field
from datetime import date

from .mrz_checksum import split_mrz_text, validate_td3
from .rules import validate_dates, validate_fields


@dataclass
class PassportReport:
    """Combined result of all validation steps for one passport."""
    fields: dict
    checks: list = field(default_factory=list)   # check-digit results
    rules: list = field(default_factory=list)    # date and format rule results

    @property
    def is_valid(self) -> bool:
        return all(c.passed for c in self.checks) and all(r.passed for r in self.rules)

    @property
    def reasons(self) -> list:
        """Plain-language reasons for every failed check or rule."""
        reasons = [
            f"{c.name}: check digit is {c.found}, expected {c.expected}"
            for c in self.checks if not c.passed
        ]
        reasons += [f"{r.name}: {r.detail}" for r in self.rules if not r.passed]
        return reasons

    @property
    def failed_count(self) -> int:
        return len(self.reasons)


def validate_passport(line1: str, line2: str, today: date = None) -> PassportReport:
    """Run all validation steps on the two MRZ lines of a passport."""
    checksum_result = validate_td3(line1, line2)
    fields = checksum_result.fields
    rules = validate_fields(fields) + validate_dates(fields, today)
    return PassportReport(fields=fields, checks=checksum_result.checks, rules=rules)


def validate_passport_text(text: str, today: date = None) -> PassportReport:
    """Same as validate_passport, but takes raw MRZ text (for example OCR output)."""
    line1, line2 = split_mrz_text(text)
    return validate_passport(line1, line2, today)

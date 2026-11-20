from dataclasses import dataclass, field

WEIGHTS = (7, 3, 1)       # the weights repeat in this order: 7, 3, 1, 7, 3, 1, ...
TD3_LINE_LENGTH = 44      # each passport MRZ line has 44 characters


def char_value(ch: str) -> int:
    if "0" <= ch <= "9":
        return int(ch)
    if "A" <= ch <= "Z":
        return ord(ch) - ord("A") + 10
    if ch == "<":
        return 0
    raise ValueError(f"Invalid MRZ character: {ch!r}")


def compute_check_digit(data: str) -> int:
    total = 0
    for position, ch in enumerate(data):
        total += char_value(ch) * WEIGHTS[position % 3]
    return total % 10


@dataclass
class CheckResult:
    name: str
    passed: bool
    expected: str   # the digit we calculated
    found: str      # the digit printed in the MRZ


@dataclass
class ValidationResult:
    fields: dict
    checks: list = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def reasons(self) -> list:
        return [
            f"{c.name}: check digit is {c.found}, expected {c.expected}"
            for c in self.checks if not c.passed
        ]


def parse_td3(line1: str, line2: str) -> dict:
    line1, line2 = line1.strip().upper(), line2.strip().upper()
    if len(line1) != TD3_LINE_LENGTH or len(line2) != TD3_LINE_LENGTH:
        raise ValueError(
            f"Each MRZ line must have {TD3_LINE_LENGTH} characters "
            f"(got {len(line1)} and {len(line2)})."
        )

    name_parts = line1[5:].split("<<", 1)
    surname = name_parts[0].replace("<", " ").strip()
    given_names = name_parts[1].replace("<", " ").strip() if len(name_parts) > 1 else ""

    return {
        "document_type": line1[0:2].replace("<", ""),
        "issuing_country": line1[2:5],
        "surname": surname,
        "given_names": given_names,
        "passport_number": line2[0:9].rstrip("<"),
        "nationality": line2[10:13],
        "date_of_birth": line2[13:19],      # YYMMDD
        "sex": line2[20],
        "date_of_expiry": line2[21:27],     # YYMMDD
        "personal_number": line2[28:42].rstrip("<"),
    }


def _check(name: str, data: str, found: str) -> CheckResult:
    # An empty optional field may use '<' as its check digit.
    if found == "<" and set(data) == {"<"}:
        return CheckResult(name, True, "<", found)
    try:
        expected = str(compute_check_digit(data))
    except ValueError:
        return CheckResult(name, False, "invalid characters", found)
    return CheckResult(name, found == expected, expected, found)


def validate_td3(line1: str, line2: str) -> ValidationResult:
    fields = parse_td3(line1, line2)
    line2 = line2.strip().upper()

    # The composite check covers: passport number + check, DOB + check,
    # expiry + check, and personal number + check.
    composite_data = line2[0:10] + line2[13:20] + line2[21:43]

    checks = [
        _check("Passport number", line2[0:9], line2[9]),
        _check("Date of birth", line2[13:19], line2[19]),
        _check("Date of expiry", line2[21:27], line2[27]),
        _check("Personal number", line2[28:42], line2[42]),
        _check("Composite (whole line)", composite_data, line2[43]),
    ]
    return ValidationResult(fields=fields, checks=checks)

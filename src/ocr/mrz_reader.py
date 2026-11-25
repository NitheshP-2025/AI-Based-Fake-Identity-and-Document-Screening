from dataclasses import dataclass, field

TD3_LENGTH = 44
ALLOWED_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<"
FILLER_LOOKALIKES = "\u00ab\u2039\u3008\uff1c"   # characters OCR may output instead of '<'

# Letters that OCR often returns where a digit belongs...
TO_DIGIT = str.maketrans({"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1",
                          "Z": "2", "S": "5", "G": "6", "B": "8"})
# ...and digits that OCR often returns where a letter belongs.
TO_LETTER = str.maketrans({"0": "O", "1": "I", "2": "Z", "5": "S", "6": "G", "8": "B"})

# Positions in line 2 that must be digits (dates and check digits) or letters (nationality).
LINE2_DIGIT_POSITIONS = [9] + list(range(13, 20)) + list(range(21, 28)) + [42, 43]
LINE2_LETTER_POSITIONS = [10, 11, 12]


class MrzNotFoundError(Exception):
    """Raised when two usable MRZ lines cannot be found in the OCR text."""


@dataclass
class MrzExtraction:
    """The two cleaned MRZ lines plus information about how they were obtained."""
    line1: str
    line2: str
    corrections: int = 0                       # characters repaired by position rules
    raw_rows: list = field(default_factory=list)   # all text rows OCR returned


def normalize_line(text: str) -> str:
    """Remove spaces, uppercase, and turn unknown characters into the filler '<'."""
    text = "".join(text.split()).upper()
    for ch in FILLER_LOOKALIKES:
        text = text.replace(ch, "<")
    return "".join(ch if ch in ALLOWED_CHARS else "<" for ch in text)


def find_mrz_rows(rows) -> tuple:
    """Return the last two rows that look like MRZ lines (long and rich in '<')."""
    normalized = [normalize_line(row) for row in rows]
    candidates = [row for row in normalized if len(row) >= 30 and row.count("<") >= 3]
    if len(candidates) < 2:
        raise MrzNotFoundError(
            f"Could not find two MRZ lines in the image (found {len(candidates)} candidate line(s)).")
    return candidates[-2], candidates[-1]


MAX_LENGTH_ERROR = 6     # lines further from 44 characters than this are not repaired


def _fit_line2(line: str) -> str:
    """Repair a line 2 whose run of '<' fillers was miscounted by OCR.

    Line 2 ends with a 14-character personal-number field (usually all '<') and two
    check digits. OCR often reads too few or too many '<' in that long run, so the
    field is rebuilt to exactly 14 characters. The characters before and after it
    are not changed, and any other damage still shows up as a failed check digit.
    """
    head, middle, tail = line[:28], line[28:-2], line[-2:]
    if middle.strip("<") == "":
        middle = "<" * 14
    elif len(middle) < 14:
        middle = middle.ljust(14, "<")
    elif set(middle[14:]) == {"<"}:
        middle = middle[:14]
    else:
        raise MrzNotFoundError(f"MRZ line2 has {len(line)} characters, expected {TD3_LENGTH}.")
    return head + middle + tail


def _fit_length(line: str, name: str) -> str:
    """Make a line exactly 44 characters long where that can be done safely."""
    if len(line) == TD3_LENGTH:
        return line
    if name == "line2":
        if abs(len(line) - TD3_LENGTH) > MAX_LENGTH_ERROR:
            raise MrzNotFoundError(f"MRZ line2 has {len(line)} characters, expected {TD3_LENGTH}.")
        return _fit_line2(line)
    # Line 1 ends with a run of fillers, so missing or extra fillers do no harm.
    if len(line) < TD3_LENGTH:
        return line.ljust(TD3_LENGTH, "<")
    if set(line[TD3_LENGTH:]) == {"<"}:
        return line[:TD3_LENGTH]
    raise MrzNotFoundError(f"MRZ line1 has {len(line)} characters, expected {TD3_LENGTH}.")


def _translate_positions(line: str, positions, table) -> tuple:
    chars, changed = list(line), 0
    for i in positions:
        if i < len(chars):
            new = chars[i].translate(table)
            if new != chars[i]:
                chars[i], changed = new, changed + 1
    return "".join(chars), changed


def correct_line1(line: str) -> tuple:
    """Line 1 holds only letters and '<', so digits are turned into look-alike letters."""
    return _translate_positions(line, range(len(line)), TO_LETTER)


def correct_line2(line: str) -> tuple:
    """Fix letter/digit confusions in line 2 using the known field positions."""
    line, n_digits = _translate_positions(line, LINE2_DIGIT_POSITIONS, TO_DIGIT)
    line, n_letters = _translate_positions(line, LINE2_LETTER_POSITIONS, TO_LETTER)
    return line, n_digits + n_letters


def extract_mrz(rows) -> MrzExtraction:
    """Turn the text rows read from an image into two clean MRZ lines."""
    line1, line2 = find_mrz_rows(rows)
    line1 = _fit_length(line1, "line1")
    line2 = _fit_length(line2, "line2")
    line1, fixed1 = correct_line1(line1)
    line2, fixed2 = correct_line2(line2)
    return MrzExtraction(line1=line1, line2=line2, corrections=fixed1 + fixed2, raw_rows=list(rows))

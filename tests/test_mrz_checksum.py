import pytest

from src.validation.mrz_checksum import (
    char_value, compute_check_digit, parse_td3, validate_td3,
)

LINE1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
LINE2 = "L898902C36UTO7408122F1204159ZE184226B<<<<<10"


def test_char_value():
    assert char_value("7") == 7
    assert char_value("A") == 10
    assert char_value("Z") == 35
    assert char_value("<") == 0


def test_invalid_character_raises():
    with pytest.raises(ValueError):
        char_value("#")


def test_known_check_digits():
    assert compute_check_digit("L898902C3") == 6
    assert compute_check_digit("740812") == 2   
    assert compute_check_digit("120415") == 9     


def test_parse_fields():
    fields = parse_td3(LINE1, LINE2)
    assert fields["surname"] == "ERIKSSON"
    assert fields["given_names"] == "ANNA MARIA"
    assert fields["passport_number"] == "L898902C3"
    assert fields["nationality"] == "UTO"
    assert fields["date_of_birth"] == "740812"
    assert fields["sex"] == "F"
    assert fields["date_of_expiry"] == "120415"


def test_valid_passport_passes_all_checks():
    result = validate_td3(LINE1, LINE2)
    assert result.is_valid
    assert len(result.checks) == 5
    assert result.reasons == []


def test_changed_date_of_birth_is_detected():
    tampered = LINE2.replace("7408122", "7408132")   
    result = validate_td3(LINE1, tampered)
    assert not result.is_valid
    failed = [c.name for c in result.checks if not c.passed]
    assert "Date of birth" in failed
    assert "Composite (whole line)" in failed


def test_changed_passport_number_is_detected():
    tampered = "M" + LINE2[1:]                       
    result = validate_td3(LINE1, tampered)
    assert not result.is_valid
    assert any(c.name == "Passport number" and not c.passed for c in result.checks)


def test_wrong_length_raises():
    with pytest.raises(ValueError):
        validate_td3(LINE1, LINE2[:-1])


def test_lowercase_input_is_accepted():
    assert validate_td3(LINE1.lower(), LINE2.lower()).is_valid


def test_ocr_garbage_fails_instead_of_crashing():
    garbled = LINE2[:13] + "7408#2" + LINE2[19:]
    result = validate_td3(LINE1, garbled)
    assert not result.is_valid

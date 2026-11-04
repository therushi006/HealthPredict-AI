import pytest
from datetime import date
from validation import (
    validate_patient_data,
    parse_and_validate_dob,
    validate_email_address,
    validate_numeric_marker,
    CLINICAL_BOUNDS
)


def test_valid_patient_data():
    """Verify that a well-formed patient record passes validation and normalizes date."""
    data = {
        'full_name': 'Robyn Pears',
        'date_of_birth': '28.01.1960',
        'email': 'robyn@gmail.com',
        'glucose': '232',
        'haemoglobin': '13.5',
        'cholesterol': '180'
    }
    is_valid, cleaned, errors = validate_patient_data(data)
    assert is_valid is True
    assert len(errors) == 0
    assert cleaned['full_name'] == 'Robyn Pears'
    assert cleaned['date_of_birth'] == date(1960, 1, 28)
    assert cleaned['email'] == 'robyn@gmail.com'
    assert cleaned['glucose'] == 232.0
    assert cleaned['haemoglobin'] == 13.5
    assert cleaned['cholesterol'] == 180.0


def test_dotted_and_slashed_dates():
    """Verify acceptance of both DD.MM.YYYY and DD/MM/YYYY formats."""
    d1, err1 = parse_and_validate_dob('28.01.1960')
    assert err1 is None
    assert d1 == date(1960, 1, 28)

    d2, err2 = parse_and_validate_dob('12/11/1993')
    assert err2 is None
    assert d2 == date(1993, 11, 12)


def test_invalid_calendar_date_rejection():
    """Verify that non-existent calendar dates like 31.11.2001 (Nov has 30 days) are rejected."""
    # Official Assessment Record 4
    d, err = parse_and_validate_dob('31.11.2001')
    assert d is None
    assert err is not None
    assert 'not a real calendar date' in err or 'Invalid' in err


def test_future_dob_rejection():
    """Verify that future dates of birth (e.g. 19.10.2030) are strictly rejected."""
    # Official Assessment Record 8
    d, err = parse_and_validate_dob('19.10.2030')
    assert d is None
    assert err is not None
    assert 'cannot be in the future' in err


def test_invalid_email_syntax():
    """Verify that incomplete emails and emails missing @ are rejected."""
    # Official Assessment Record 2: hunter@gmail (missing .com TLD)
    e1, err1 = validate_email_address('hunter@gmail')
    assert e1 is None
    assert err1 is not None

    # Official Assessment Record 8: Kris.wu.gmail.com (missing @)
    e2, err2 = validate_email_address('Kris.wu.gmail.com')
    assert e2 is None
    assert err2 is not None

    # Additional invalid emails
    assert validate_email_address('plainaddress')[0] is None
    assert validate_email_address('@missinguser.com')[0] is None
    assert validate_email_address('user@')[0] is None


def test_valid_emails():
    """Verify standard valid emails pass."""
    assert validate_email_address('robyn@gmail.com')[0] == 'robyn@gmail.com'
    assert validate_email_address('timd@smh.com.au')[0] == 'timd@smh.com.au'
    assert validate_email_address('gokul@infocare.com')[0] == 'gokul@infocare.com'


def test_blood_markers_non_numeric():
    """Verify that non-numeric values are rejected."""
    val, err = validate_numeric_marker('abc', 'glucose')
    assert val is None
    assert 'valid numeric value' in err


def test_blood_markers_clinical_boundary():
    """Verify that values outside clinical boundaries are rejected."""
    # Glucose min is 20, max is 600
    val_low, err_low = validate_numeric_marker('10', 'glucose')
    assert val_low is None
    assert 'outside physiologically plausible range' in err_low

    val_high, err_high = validate_numeric_marker('999', 'glucose')
    assert val_high is None
    assert 'outside physiologically plausible range' in err_high


def test_missing_fields_validation():
    """Verify that empty submissions trigger validation errors for all required fields."""
    empty_data = {}
    is_valid, cleaned, errors = validate_patient_data(empty_data)
    assert is_valid is False
    assert 'full_name' in errors
    assert 'date_of_birth' in errors
    assert 'email' in errors
    assert 'glucose' in errors
    assert 'haemoglobin' in errors
    assert 'cholesterol' in errors

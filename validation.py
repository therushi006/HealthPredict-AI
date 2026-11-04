import re
from datetime import datetime, date
from typing import Dict, Any, Tuple, Optional
from models import Patient

# Sensible clinical boundary ranges documented for HealthPredict AI
CLINICAL_BOUNDS = {
    'glucose': {
        'min': 20.0,
        'max': 600.0,
        'unit': 'mg/dL',
        'label': 'Blood Glucose'
    },
    'haemoglobin': {
        'min': 2.0,
        'max': 25.0,
        'unit': 'g/dL',
        'label': 'Haemoglobin'
    },
    'cholesterol': {
        'min': 50.0,
        'max': 600.0,
        'unit': 'mg/dL',
        'label': 'Total Cholesterol'
    }
}

# Strict practical email regex requiring valid local-part, @, domain name, and TLD (>=2 characters)
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$'
)


def parse_and_validate_dob(dob_raw: Any) -> Tuple[Optional[date], Optional[str]]:
    """
    Parses and validates Date of Birth.
    Supports formats: DD.MM.YYYY, DD/MM/YYYY, and YYYY-MM-DD.
    - Rejects non-existent calendar dates (e.g., 31.11.2001 -> Nov has only 30 days).
    - Rejects future dates (e.g., 19.10.2030).
    Returns (date_obj, None) if valid, or (None, error_message).
    """
    if not dob_raw or not str(dob_raw).strip():
        return None, "Date of birth is required."

    dob_str = str(dob_raw).strip()
    parsed_date = None

    # Try supported formats
    # Note: Assessment data provides dates like 28.01.1960 and forms may send DD/MM/YYYY or YYYY-MM-DD
    supported_formats = ['%d.%m.%Y', '%d/%m/%Y', '%Y-%m-%d']
    
    for fmt in supported_formats:
        try:
            parsed_date = datetime.strptime(dob_str, fmt).date()
            break
        except ValueError:
            continue

    if not parsed_date:
        # Check specifically if invalid day for month was attempted
        # e.g., 31.11.2001 has format DD.MM.YYYY but Nov has 30 days
        parts = re.split(r'[./-]', dob_str)
        if len(parts) == 3:
            return None, f"'{dob_str}' is not a real calendar date (check days in month or leap year)."
        return None, "Invalid date format. Please use DD/MM/YYYY."

    # Validate against future dates using today's system date
    today = date.today()
    if parsed_date > today:
        return None, f"Date of birth cannot be in the future (entered: {parsed_date.strftime('%d/%m/%Y')}, today: {today.strftime('%d/%m/%Y')})."

    # Validate reasonable minimum age (e.g., not older than 130 years)
    if (today.year - parsed_date.year) > 130:
        return None, "Date of birth indicates age greater than 130 years. Please check the year."

    return parsed_date, None


def validate_email_address(email_raw: Any) -> Tuple[Optional[str], Optional[str]]:
    """
    Validates email syntax.
    Rejects:
    - Missing '@' (e.g. Kris.wu.gmail.com)
    - Incomplete domains without top-level domain (e.g. hunter@gmail)
    Returns (cleaned_email, None) if valid, or (None, error_message).
    """
    if not email_raw or not str(email_raw).strip():
        return None, "Email address is required."

    email = str(email_raw).strip().lower()

    if '@' not in email:
        return None, "Invalid email address: missing '@' symbol."

    parts = email.split('@')
    if len(parts) != 2:
        return None, "Invalid email syntax: multiple '@' symbols found."

    local_part, domain_part = parts

    if not local_part:
        return None, "Invalid email syntax: missing username before '@'."

    if not domain_part:
        return None, "Invalid email syntax: missing domain after '@'."

    if '.' not in domain_part:
        return None, f"Invalid domain '{domain_part}': missing top-level domain (e.g. .com, .org)."

    if not EMAIL_REGEX.match(email):
        return None, f"Invalid email format '{email}'. Example of valid email: patient@domain.com."

    return email, None


def validate_numeric_marker(value_raw: Any, field_name: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Validates a blood test numeric value against required clinical boundary constraints.
    Returns (float_value, None) if valid, or (None, error_message).
    """
    config = CLINICAL_BOUNDS.get(field_name)
    label = config['label'] if config else field_name.capitalize()
    unit = config['unit'] if config else ''

    if value_raw is None or str(value_raw).strip() == '':
        return None, f"{label} is required."

    try:
        val = float(str(value_raw).strip())
    except (ValueError, TypeError):
        return None, f"{label} must be a valid numeric value."

    if config:
        if val < config['min'] or val > config['max']:
            return None, (
                f"{label} ({val} {unit}) is outside physiologically plausible range "
                f"[{config['min']} - {config['max']} {unit}]."
            )

    return val, None


def validate_patient_data(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], Dict[str, str]]:
    """
    Comprehensive validation for patient creation and updates.
    Returns:
        (is_valid: bool, cleaned_data: dict, errors: dict)
    """
    cleaned: Dict[str, Any] = {}
    errors: Dict[str, str] = {}

    # 1. Full Name
    raw_name = data.get('full_name', '')
    if not raw_name or not str(raw_name).strip():
        errors['full_name'] = "Full name is required."
    else:
        name_clean = str(raw_name).strip()
        if len(name_clean) < 2:
            errors['full_name'] = "Full name must be at least 2 characters."
        elif len(name_clean) > 100:
            errors['full_name'] = "Full name cannot exceed 100 characters."
        else:
            cleaned['full_name'] = name_clean

    # 2. Date of Birth
    dob_obj, dob_err = parse_and_validate_dob(data.get('date_of_birth'))
    if dob_err:
        errors['date_of_birth'] = dob_err
    else:
        cleaned['date_of_birth'] = dob_obj

    # 3. Email
    email_clean, email_err = validate_email_address(data.get('email'))
    if email_err:
        errors['email'] = email_err
    else:
        cleaned['email'] = email_clean

    # 4. Blood Test Values
    for field in ['glucose', 'haemoglobin', 'cholesterol']:
        val, err = validate_numeric_marker(data.get(field), field)
        if err:
            errors[field] = err
        else:
            cleaned[field] = val

    is_valid = len(errors) == 0
    return is_valid, cleaned, errors


def check_duplicate_patient(cleaned_data: Dict[str, Any], exclude_id: Optional[int] = None) -> Optional[str]:
    """
    Checks if an identical patient record exists in SQLite.
    Per assessment requirements, duplicates are NOT rejected, but a helpful warning is provided.
    """
    query = Patient.query.filter_by(
        full_name=cleaned_data.get('full_name'),
        date_of_birth=cleaned_data.get('date_of_birth'),
        email=cleaned_data.get('email'),
        glucose=cleaned_data.get('glucose'),
        haemoglobin=cleaned_data.get('haemoglobin'),
        cholesterol=cleaned_data.get('cholesterol')
    )
    if exclude_id:
        query = query.filter(Patient.id != exclude_id)

    existing = query.first()
    if existing:
        return (
            f"Duplicate Warning: An identical record for '{existing.full_name}' "
            f"already exists as Record #{existing.id}. Stored as a separate entry per requirements."
        )
    return None

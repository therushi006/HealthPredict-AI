import pytest
from unittest.mock import patch
from app import create_app
from config import TestingConfig
from database import db
from models import Patient


@pytest.fixture
def app():
    """Create and configure a clean test application with an in-memory SQLite database."""
    test_app = create_app(TestingConfig)
    
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for HTTP requests."""
    return app.test_client()


@pytest.fixture
def mock_ai_service():
    """Mock the external Gemini AI service so automated tests do not make external calls."""
    with patch('app.generate_health_remarks') as mock_ai:
        mock_ai.return_value = (
            True,
            "1. General Assessment: Normal values.\n2. Potential Risk Indicators: None.\n3. Recommendation: Annual checkup.\n4. Medical Disclaimer: Informational only.",
            "completed"
        )
        yield mock_ai


def test_dashboard_route(client):
    """Verify that dashboard renders with 0 initial records."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'HealthPredict' in response.data
    assert b'Total Records' in response.data


def test_create_patient(client, app, mock_ai_service):
    """Test Operation 1 - CREATE: Patient registration and database insertion."""
    patient_data = {
        'full_name': 'Robyn Pears',
        'date_of_birth': '28.01.1960',
        'email': 'robyn@gmail.com',
        'glucose': '232',
        'haemoglobin': '13.5',
        'cholesterol': '180'
    }

    response = client.post('/patients/add', data=patient_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Robyn Pears' in response.data

    with app.app_context():
        patient = Patient.query.filter_by(email='robyn@gmail.com').first()
        assert patient is not None
        assert patient.full_name == 'Robyn Pears'
        assert patient.glucose == 232.0
        assert patient.ai_status == 'completed'
        assert mock_ai_service.called


def test_read_patient(client, app, mock_ai_service):
    """Test Operation 2 - READ: Retrieval via Web UI and JSON API."""
    with app.app_context():
        p = Patient(
            full_name='Sam Kerr',
            date_of_birth=Patient.date_of_birth.type.python_type(2006, 12, 9),
            email='sam@news.com.au',
            glucose=198.0,
            haemoglobin=8.9,
            cholesterol=192.0,
            ai_remarks='Assessment sample remarks',
            ai_status='completed'
        )
        db.session.add(p)
        db.session.commit()
        p_id = p.id

    # Web UI Table
    res_web = client.get('/patients')
    assert res_web.status_code == 200
    assert b'Sam Kerr' in res_web.data
    assert b'sam@news.com.au' in res_web.data

    # Details page
    res_detail = client.get(f'/patients/{p_id}')
    assert res_detail.status_code == 200
    assert b'Sam Kerr' in res_detail.data

    # REST API List
    res_api = client.get('/api/patients')
    assert res_api.status_code == 200
    data = res_api.get_json()
    assert data['success'] is True
    assert data['count'] >= 1

    # REST API Individual
    res_single = client.get(f'/api/patients/{p_id}')
    assert res_single.status_code == 200
    single_data = res_single.get_json()
    assert single_data['patient']['full_name'] == 'Sam Kerr'


def test_update_patient_email(client, app, mock_ai_service):
    """
    Test Operation 3 - UPDATE:
    Change patient email to 'gokul@infocare.com'.
    Verify email is updated in SQLite and AI service is NOT called if blood markers are unchanged.
    """
    with app.app_context():
        p = Patient(
            full_name='Darryl Tim',
            date_of_birth=Patient.date_of_birth.type.python_type(1993, 11, 12),
            email='timd@smh.com.au',
            glucose=240.0,
            haemoglobin=18.6,
            cholesterol=326.0,
            ai_remarks='Existing AI Remarks',
            ai_status='completed'
        )
        db.session.add(p)
        db.session.commit()
        p_id = p.id

    mock_ai_service.reset_mock()

    # Update only the email address to 'gokul@infocare.com'
    update_data = {
        'full_name': 'Darryl Tim',
        'date_of_birth': '12/11/1993',
        'email': 'gokul@infocare.com',
        'glucose': '240.0',
        'haemoglobin': '18.6',
        'cholesterol': '326.0'
    }

    response = client.post(f'/patients/edit/{p_id}', data=update_data, follow_redirects=True)
    assert response.status_code == 200
    assert b'gokul@infocare.com' in response.data

    with app.app_context():
        updated = db.session.get(Patient, p_id)
        assert updated.email == 'gokul@infocare.com'
        # Crucial requirement: blood test values were unchanged, so AI service was NOT unnecessarily invoked
        assert not mock_ai_service.called


def test_delete_patient(client, app):
    """Test Operation 4 - DELETE: Safely delete record via POST request."""
    with app.app_context():
        p = Patient(
            full_name='Tenille Singh',
            date_of_birth=Patient.date_of_birth.type.python_type(1991, 11, 30),
            email='Tenille@yahoo.com',
            glucose=101.0,
            haemoglobin=15.0,
            cholesterol=310.0,
            ai_remarks='Remarks',
            ai_status='completed'
        )
        db.session.add(p)
        db.session.commit()
        p_id = p.id

    # Confirm record exists
    assert client.get(f'/patients/{p_id}').status_code == 200

    # Delete record
    del_res = client.post(f'/patients/delete/{p_id}', follow_redirects=True)
    assert del_res.status_code == 200
    assert b'deleted successfully' in del_res.data

    # Confirm record is gone
    with app.app_context():
        assert db.session.get(Patient, p_id) is None


def test_duplicate_patient_stored_separately(client, app, mock_ai_service):
    """
    Test duplicate handling:
    Record 1 and Record 6 are both Robyn Pears with identical details.
    Both must be accepted and stored as separate records with unique IDs.
    """
    patient_data = {
        'full_name': 'Robyn Pears',
        'date_of_birth': '28.01.1960',
        'email': 'robyn@gmail.com',
        'glucose': '232',
        'haemoglobin': '13.5',
        'cholesterol': '180'
    }

    # First entry
    client.post('/patients/add', data=patient_data)
    # Second entry (duplicate)
    client.post('/patients/add', data=patient_data)

    with app.app_context():
        patients = Patient.query.filter_by(full_name='Robyn Pears').all()
        assert len(patients) == 2
        assert patients[0].id != patients[1].id


def test_official_assessment_runner(client, mock_ai_service):
    """
    Test the 10 official assessment records supplied by Gokul Infocare.
    Under assessment rules, exactly 7 records must be accepted and 3 rejected.
    """
    response = client.post('/assessment/run')
    assert response.status_code == 200
    data = response.get_json()

    assert data['total_processed'] == 10
    assert data['accepted_count'] == 7
    assert data['rejected_count'] == 3

    # Check rejected records
    rejected = [r for r in data['results'] if r['status'] == 'REJECTED']
    assert len(rejected) == 3
    rejected_record_nums = [r['record_num'] for r in rejected]
    assert 2 in rejected_record_nums  # hunter@gmail
    assert 4 in rejected_record_nums  # 31.11.2001
    assert 8 in rejected_record_nums  # 19.10.2030 + Kris.wu.gmail.com

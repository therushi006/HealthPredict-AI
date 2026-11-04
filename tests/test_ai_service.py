import pytest
from unittest.mock import patch, MagicMock
import requests
from ai_service import (
    build_prompt,
    generate_health_remarks,
    MEDICAL_DISCLAIMER
)
from app import create_app
from config import TestingConfig
from database import db
from models import Patient


def test_build_prompt_privacy_and_structure():
    """
    Verify prompt includes only clinical blood markers and omits patient PII.
    Verify required sections are instructed in the prompt.
    """
    prompt = build_prompt(glucose=232.0, haemoglobin=13.5, cholesterol=180.0)

    # Contains blood values
    assert "Glucose: 232.0" in prompt
    assert "Haemoglobin: 13.5" in prompt
    assert "Cholesterol: 180.0" in prompt

    # Asserts required instructions
    assert "General Assessment" in prompt
    assert "Potential Risk Indicators" in prompt
    assert "Recommendation" in prompt
    assert "Medical Disclaimer" in prompt

    # Strictly verifies privacy (no PII in prompt generator signature or output)
    assert "Robyn Pears" not in prompt
    assert "robyn@gmail.com" not in prompt


def test_missing_api_key_handling():
    """Verify that absent or default placeholder API key fails gracefully without crashing."""
    success, remarks, status = generate_health_remarks(
        glucose=100.0,
        haemoglobin=14.0,
        cholesterol=190.0,
        api_key=""
    )
    assert success is False
    assert status == "failed"
    assert "not configured" in remarks


def test_invalid_api_key_rest_handling():
    """Verify that an invalid API key returns a clear failure message."""
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {
        'error': {'message': 'API_KEY_INVALID: Key not found'}
    }

    with patch('requests.post', return_value=mock_resp), \
         patch('google.generativeai.GenerativeModel.generate_content', side_effect=Exception('API_KEY_INVALID')):
        success, remarks, status = generate_health_remarks(
            glucose=100.0,
            haemoglobin=14.0,
            cholesterol=190.0,
            api_key="invalid_dummy_key"
        )
        assert success is False
        assert status == "failed"
        assert "Invalid" in remarks or "API Key" in remarks


def test_quota_exceeded_handling():
    """Verify that HTTP 429 quota error is caught and reported gracefully."""
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.json.return_value = {'error': {'message': 'Quota exceeded'}}

    with patch('requests.post', return_value=mock_resp), \
         patch('google.generativeai.GenerativeModel.generate_content', side_effect=Exception('Quota exceeded')):
        success, remarks, status = generate_health_remarks(
            glucose=100.0,
            haemoglobin=14.0,
            cholesterol=190.0,
            api_key="valid_looking_key"
        )
        assert success is False
        assert status == "failed"
        assert "quota" in remarks.lower()


def test_timeout_handling():
    """Verify that request timeout fails safely."""
    with patch('requests.post', side_effect=requests.exceptions.Timeout("Connection timed out")), \
         patch('google.generativeai.GenerativeModel.generate_content', side_effect=Exception("Timeout")):
        success, remarks, status = generate_health_remarks(
            glucose=100.0,
            haemoglobin=14.0,
            cholesterol=190.0,
            api_key="valid_looking_key"
        )
        assert success is False
        assert status == "failed"
        assert "timed out" in remarks.lower() or "timeout" in remarks.lower()


def test_successful_ai_generation():
    """Verify that a successful response returns status 'completed' and remarks text."""
    expected_text = (
        "1. General Assessment: Glucose and cholesterol are within range.\n"
        "2. Potential Risk Indicators: None detected.\n"
        "3. Recommendation: Follow up in 12 months.\n"
        "4. Medical Disclaimer: Informational only."
    )

    mock_resp = MagicMock()
    mock_resp.text = expected_text

    with patch('google.generativeai.GenerativeModel.generate_content', return_value=mock_resp):
        success, remarks, status = generate_health_remarks(
            glucose=94.0,
            haemoglobin=15.0,
            cholesterol=200.0,
            api_key="test_real_key"
        )
        assert success is True
        assert status == "completed"
        assert "General Assessment" in remarks


def test_retry_ai_route():
    """Verify that the retry route updates a failed record upon success."""
    test_app = create_app(TestingConfig)
    with test_app.app_context():
        db.create_all()
        patient = Patient(
            full_name='Test Retry Patient',
            date_of_birth=Patient.date_of_birth.type.python_type(1985, 5, 20),
            email='retry@test.com',
            glucose=110.0,
            haemoglobin=14.2,
            cholesterol=195.0,
            ai_remarks='Initial Failure Message',
            ai_status='failed'
        )
        db.session.add(patient)
        db.session.commit()
        pid = patient.id

        client = test_app.test_client()

        with patch('app.generate_health_remarks') as mock_gen:
            mock_gen.return_value = (True, "Retried remarks successful.", "completed")
            res = client.post(f'/patients/{pid}/retry-ai', follow_redirects=True)
            assert res.status_code == 200

            updated = db.session.get(Patient, pid)
            assert updated.ai_status == 'completed'
            assert updated.ai_remarks == 'Retried remarks successful.'

        db.session.remove()
        db.drop_all()

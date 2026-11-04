import os
import logging
from typing import Tuple, Dict, Any, Optional
import requests

# Set up logger without leaking sensitive patient data
logger = logging.getLogger(__name__)

# Official Medical Disclaimer required across the application
MEDICAL_DISCLAIMER = (
    "MEDICAL DISCLAIMER: HealthPredict AI is an educational demonstration tool and does not provide medical "
    "diagnoses, treatment advice, or clinical prescriptions. All AI-generated remarks are general educational "
    "information only. Always consult a qualified physician or healthcare specialist for interpretation of laboratory "
    "results and personal medical decisions."
)


def build_prompt(glucose: float, haemoglobin: float, cholesterol: float) -> str:
    """
    Constructs the exact structured prompt required by assessment guidelines.
    Only blood test markers are included; patient PII (name, email, DOB) is omitted for privacy.
    """
    prompt = f"""You are an educational health information assistant. Review the supplied patient blood test values and provide a cautious, general informational interpretation.

Patient information:
Glucose: {glucose}
Haemoglobin: {haemoglobin}
Cholesterol: {cholesterol}

Provide:
A brief summary of the supplied values.
Any possible health risk indicators that may warrant further attention.
A recommendation to consult a qualified healthcare professional.
A note explaining that interpretation depends on units, reference ranges, fasting status, age, and other clinical information.

Do not claim a confirmed disease or diagnosis.
Do not prescribe medication or treatment.
Do not invent laboratory reference ranges or units.
If units or necessary clinical context are missing, clearly state that interpretation is limited.
Use simple, professional language.

Structure your response clearly with these exact headings:
1. General Assessment:
2. Potential Risk Indicators:
3. Recommendation:
4. Educational Note:
5. Medical Disclaimer:"""
    return prompt


def generate_health_remarks(
    glucose: float,
    haemoglobin: float,
    cholesterol: float,
    api_key: Optional[str] = None
) -> Tuple[bool, str, str]:
    """
    Sends blood test markers to Google Gemini API to generate informational health remarks.
    
    Returns:
        Tuple[success: bool, remarks: str, status: str]
        status is 'completed' or 'failed'.
        
    Handles API key absence, timeouts, quota limits, invalid keys, and network failures.
    NEVER generates fabricated or hardcoded fake AI responses on failure.
    """
    # Retrieve API key from parameter or environment
    key = (api_key or os.environ.get('GEMINI_API_KEY', '')).strip()

    if not key or key == 'your_api_key_here':
        return (
            False,
            "AI Analysis Pending: Google Gemini API key is not configured. "
            "Please configure GEMINI_API_KEY in your .env file and click 'Retry AI Analysis'.",
            "failed"
        )

    prompt_text = build_prompt(glucose, haemoglobin, cholesterol)
    model_name = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash').strip()

    # Approach 1: Try official google.generativeai SDK
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt_text)
        
        if response and response.text:
            cleaned_text = response.text.strip()
            return True, cleaned_text, "completed"
        else:
            return False, "AI Service Error: Empty response received from Gemini API.", "failed"

    except Exception as sdk_err:
        err_str = str(sdk_err).lower()
        logger.warning("SDK call to Gemini failed (%s), attempting REST fallback...", type(sdk_err).__name__)

        # Approach 2: Direct REST fallback to ensure resilience
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt_text}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 800
                }
            }
            
            resp = requests.post(url, json=payload, timeout=12)
            
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        return True, parts[0]["text"].strip(), "completed"
                return False, "AI Service Error: Unrecognized response structure from Gemini REST API.", "failed"

            elif resp.status_code == 400:
                error_data = resp.json().get('error', {})
                msg = error_data.get('message', 'Bad Request')
                if 'API_KEY_INVALID' in msg or 'API key not valid' in msg:
                    return False, "AI Service Error: Invalid Google Gemini API Key provided.", "failed"
                return False, f"AI Service Error (400): {msg}", "failed"

            elif resp.status_code == 403:
                return False, "AI Service Error: Access forbidden. Verify API key permissions and enabled APIs.", "failed"

            elif resp.status_code == 429:
                return False, "AI Service Error: Google Gemini API quota or rate limit exceeded. Please retry shortly.", "failed"

            else:
                return False, f"AI Service Error: Gemini API returned HTTP status {resp.status_code}.", "failed"

        except requests.exceptions.Timeout:
            return False, "AI Service Error: Request to Gemini API timed out after 12 seconds. Please check your connection and retry.", "failed"
        except requests.exceptions.ConnectionError:
            return False, "AI Service Error: Unable to connect to Google Gemini API servers. Network unreachable.", "failed"
        except Exception as rest_err:
            # Fall back to parsed SDK error if informative
            if 'api_key_invalid' in err_str or 'api key not valid' in err_str:
                return False, "AI Service Error: Invalid Google Gemini API Key.", "failed"
            if 'resource_exhausted' in err_str or 'quota' in err_str:
                return False, "AI Service Error: Gemini API quota exceeded.", "failed"
            return False, f"AI Service Error: Communication failure ({type(rest_err).__name__}).", "failed"

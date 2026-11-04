# HealthPredict AI – Patient Health Prediction & Management System

> **Technical Assessment Project for Gokul Infocare**  
> **Position:** AI Growth & Automation Associate  
> **Task 2:** Patient Health Prediction & Clinical Management Application  

---

## 1. Project Overview & Objectives

**HealthPredict AI** is a production-ready, full-stack Python healthcare web application designed to capture patient demographic details, record vital laboratory blood markers (Glucose, Haemoglobin, Cholesterol), enforce rigorous dual-layer validation, and integrate with the **Google Gemini Generative AI API** to produce structured, educational health remarks.

The system is developed with a strict focus on:
- **Full CRUD Management**: Create, Read, Update, and Delete operations persisting to a local SQLite database (`healthpredict.db`).
- **Data Integrity & Validation**: Complete frontend and backend validation adhering to calendar constraints, email syntax RFC standards, and physiological blood marker bounds.
- **Privacy-Centric AI Architecture**: Transmitting only numeric blood markers to Google Gemini while strictly retaining Personally Identifiable Information (PII) on the local server.
- **Resilient AI Failure Handling**: Graceful fallback and user-driven retries when network conditions fail or API keys are absent, with zero fabricated AI remarks.
- **Compliance & Safety**: Prominent educational medical disclaimers displayed consistently across every interface.

---

## 2. Technology Stack

| Domain | Technology | Purpose & Implementation Details |
| :--- | :--- | :--- |
| **Backend Runtime** | **Python 3.12** | Core language for business logic, data normalization, and API integration. |
| **Web Framework** | **Flask 3.0.3** | Lightweight WSGI micro-framework managing routing, sessions, templates, and REST APIs. |
| **Database & ORM** | **SQLite & SQLAlchemy 2.0 / Flask-SQLAlchemy 3.1** | Relational persistence with parameterized queries, schema auto-migration, and ACID guarantees. |
| **Form Security** | **Flask-WTF 1.2** | CSRF (Cross-Site Request Forgery) protection across all state-mutating POST operations. |
| **AI Integration** | **Google Gemini API** (`google-generativeai 0.8.3` + REST fallback) | Generates structured educational health observations based on laboratory blood values. |
| **Frontend UI** | **HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons** | Responsive, modern healthcare dashboard with navy and teal palette. |
| **Client Scripting** | **Vanilla JavaScript (ES6)** | Real-time input validation, modal dialogs, and AJAX assessment execution. |
| **Automated Testing**| **pytest 8.2** | Automated unit and integration testing with mocked AI responses and in-memory DB. |

---

## 3. Project Directory Structure

```text
HealthPredict-AI/
├── app.py                  # Flask Application Factory, Web Routes & REST API Endpoints
├── config.py               # Centralized configuration (BaseConfig & TestingConfig)
├── database.py             # SQLAlchemy instance and schema auto-initialization
├── models.py               # Patient relational database model
├── validation.py           # Backend validation logic, regex, and clinical boundaries
├── ai_service.py           # Google Gemini AI service integration and prompt builder
├── pytest.ini              # Pytest configuration and pythonpath settings
├── requirements.txt        # Pinned project dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules for secrets, DB, and cache files
├── README.md               # Comprehensive project documentation
├── INTERVIEW_GUIDE.md      # Beginner-friendly code guide & 20+ interview Q&As
├── VIDEO_DEMO_GUIDE.md     # 3–5 minute video demonstration script & screen actions
├── templates/              # Jinja2 HTML Templates
│   ├── base.html           # Master layout with navy sidebar, top navbar & disclaimer
│   ├── dashboard.html      # Executive dashboard with live summary cards
│   ├── patients.html       # Patient records table with live search & CRUD actions
│   ├── add_patient.html    # Patient registration form with validation feedback
│   ├── edit_patient.html   # Patient edit form (avoids AI calls if markers unchanged)
│   ├── patient_details.html# Comprehensive patient report & full AI remarks
│   ├── ai_analysis.html    # AI status hub & structured prompt breakdown
│   ├── assessment.html     # Gokul Infocare 10-record automated test runner
│   └── errors/
│       ├── 404.html        # Friendly Page/Record Not Found error page
│       └── 500.html        # Secure Internal Server Error page (no stack traces)
├── static/
│   ├── css/
│   │   └── style.css       # Custom modern healthcare styling (navy & teal)
│   └── js/
│       └── script.js       # Client validation, sidebar toggling & modal helpers
└── tests/
    ├── test_validation.py  # Unit tests for dates, emails, boundaries, and missing fields
    ├── test_crud.py        # Integration tests for CRUD operations & assessment dataset
    └── test_ai_service.py   # Unit tests for prompt structure, timeouts, errors & retries
```

---

## 4. Installation & Local Setup

### Step 1: Clone or Navigate to the Repository
Open a terminal in the application root folder:
```bash
cd "C:\Users\sai\Desktop\python assement"
```

### Step 2: Create and Activate Python Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If you encounter execution policy restrictions in PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

**On Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to create `.env`:
```bash
# On Windows
copy .env.example .env

# On Linux/macOS
cp .env.example .env
```
Open `.env` in any text editor and supply your Google Gemini API key:
```ini
GEMINI_API_KEY=AIzaSy...your_actual_gemini_key_here
SECRET_KEY=healthpredict-secret-key-change-in-production-2026
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1
```
> **Note:** If an API key is not supplied immediately, the application continues to run without crashing! Any record submitted will store all patient and blood data safely in SQLite, assign `ai_status = 'failed'`, and provide a convenient "Retry AI Analysis" button.

### Step 5: Run the Application
```bash
python app.py
```
Open your web browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 5. Complete CRUD Operations Guide

The application implements all 4 CRUD operations accessible via the Web UI and REST API:

### 1. CREATE (Add Patient)
- Navigate to **"Add Patient"** or visit `http://127.0.0.1:5000/patients/add`.
- Fill in Full Name, Date of Birth, Email Address, Glucose, Haemoglobin, and Cholesterol.
- The system checks both client-side and server-side rules.
- If valid, the blood markers are sent to Google Gemini API.
- The patient data and generated remarks are stored in `healthpredict.db`.
- Automatic redirect to the Patient Records table with a confirmation notification.

### 2. READ (View Records)
- Navigate to **"Patient Records"** (`/patients`).
- All stored patients are rendered in a clean Bootstrap table displaying ID, Name, DOB, Email, Blood Markers, AI Remarks preview, AI Status badge, and Action buttons.
- Use the search bar to filter instantly by patient name, email, or record ID.
- Click the eye icon (**"View"**) to view the full clinical report, individual blood test ranges, and complete multi-paragraph AI remarks.
- Programmatic JSON access is available at `GET /api/patients` and `GET /api/patients/<id>`.

### 3. UPDATE (Edit Record)
- On any patient row, click the pencil icon (**"Edit"**).
- The form is pre-populated with current database values.
- **Smart AI Optimization**: If you only change personal details (such as updating email to `gokul@infocare.com`), existing AI remarks are retained and an unnecessary API call to Google Gemini is avoided. If blood test values are changed, the AI remarks are automatically regenerated.
- Changes are safely committed to SQLite with parameterized updates.

### 4. DELETE (Remove Record)
- On any patient row, click the trash icon (**"Delete"**).
- An interactive confirmation modal appears asking for explicit verification.
- Upon confirmation, a `POST /patients/delete/<id>` request safely deletes the record from SQLite. Destructive GET requests are strictly avoided.

---

## 6. Official Assessment Test Dataset (Gokul Infocare)

The official technical assessment specifies 10 test records with strict validation expectations. The application includes a dedicated **Assessment Runner** (`/assessment`) that processes all 10 records through the identical backend validation and AI pipeline:

| Record # | Full Name | Date of Birth | Email | Glucose | Hb | Chol | Validation Outcome | Rejection / Acceptance Reason |
| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **1** | Robyn Pears | 28.01.1960 | `robyn@gmail.com` | 232 | 13.5 | 180 | **ACCEPTED** | Valid clinical entry. |
| **2** | John Hunter | 10.12.1990 | `hunter@gmail` | 94 | 15.0 | 200 | **REJECTED** | Incomplete email syntax; missing domain TLD. |
| **3** | Darryl Tim | 12.11.1993 | `timd@smh.com.au` | 240 | 18.6 | 326 | **ACCEPTED** | Valid clinical entry. |
| **4** | Peter Larry | 31.11.2001 | `Larry@hotmail.com` | 88 | 11.5 | 165 | **REJECTED** | Invalid calendar date; November has only 30 days. |
| **5** | Sam Kerr | 09.12.2006 | `sam@news.com.au` | 198 | 8.9 | 192 | **ACCEPTED** | Valid clinical entry. |
| **6** | Robyn Pears | 28.01.1960 | `robyn@gmail.com` | 232 | 13.5 | 180 | **ACCEPTED** | Identical to Record 1; accepted as a separate record with new unique ID and duplicate notice. |
| **7** | Madison XI | 12.09.1998 | `madison@hotmail.com` | 85 | 7.6 | 163 | **ACCEPTED** | Valid clinical entry. |
| **8** | Kris Wu | 19.10.2030 | `Kris.wu.gmail.com` | 79 | 16.5 | 197 | **REJECTED** | Future DOB (2030) + Invalid email missing `@`. |
| **9** | Tenille Singh | 30.11.1991 | `Tenille@yahoo.com` | 101 | 15.0 | 310 | **ACCEPTED** | Valid calendar date (November 30 exists). |
| **10** | Prem Kumar | 28.04.1990 | `prem@telstra.com` | 155 | 12.5 | 265 | **ACCEPTED** | Valid clinical entry. |

### Summary of Assessment Results:
- **Total Submissions Attempted:** 10
- **Accepted Records Stored in SQLite:** 7 (Records 1, 3, 5, 6, 7, 9, 10)
- **Rejected Records with Clear Errors:** 3 (Records 2, 4, 8)

---

## 7. Required Assessment Operations Walkthrough

During your evaluation or video demonstration, perform these 4 exact operations:
1. **Operation 1 – CREATE:** Execute all 10 records via the Assessment Runner or manual form. Confirm 7 records succeed and 3 records fail with detailed error feedback.
2. **Operation 2 – READ:** Open `/patients`. Observe all 7 created records in the table with their respective blood values and AI statuses.
3. **Operation 3 – UPDATE:** Select Record #3 (Darryl Tim) or any accepted patient. Click Edit. Change the email address to `gokul@infocare.com`. Save and observe the updated email in the table while verifying that the blood values and AI remarks remained intact.
4. **Operation 4 – DELETE:** Select any record (e.g. Record #6, the duplicate Robyn Pears). Click Delete and confirm the modal. Confirm the table refreshes showing the remaining 6 records.

---

## 8. External AI API Integration (`ai_service.py`)

The application integrates with **Google Gemini** using a dedicated modular service:
1. **Prompt Construction**:
   The prompt instructs Gemini to act as an educational health assistant and review Glucose, Haemoglobin, and Cholesterol values without diagnosing or prescribing medications.
2. **Expected Response Format**:
   - `General Assessment`
   - `Potential Risk Indicators`
   - `Recommendation`
   - `Educational Note`
   - `Medical Disclaimer`
3. **Data Minimization & Patient Privacy**:
   Full names, emails, and birth dates are **never sent** over the wire to Google Gemini. Only the three numeric blood test markers are included in the prompt payload.
4. **Resilient Failure Handling**:
   - Absent API key: marks `ai_status = 'failed'` with instructions to add key in `.env`.
   - Timeout (12s limit) or network error: marks `ai_status = 'failed'`.
   - Quota limit: marks `ai_status = 'failed'`.
   - **Zero Hallucination Policy**: The app **never** produces fake or mock AI responses in production. A "Retry AI Analysis" button is provided for real retries.

---

## 9. Automated Testing with Pytest

To run the automated test suite:
```powershell
.\venv\Scripts\pytest -v
```
All **23 unit and integration tests** execute in under 7 seconds using an in-memory SQLite database and mocked AI endpoints:
- `tests/test_validation.py`: Tests date parsing, leap years, 30-day months (31.11 rejection), future dates, strict email syntax, blood marker ranges, and empty fields.
- `tests/test_crud.py`: Tests Dashboard metrics, Patient creation, Web & REST API retrieval, Email update without AI call, Deletion via POST, Duplicate record retention, and the 10-record Assessment runner.
- `tests/test_ai_service.py`: Tests prompt privacy (no PII), missing API keys, invalid keys, quota exceeded handling, timeouts, and retry endpoints.

---

## 10. Git & GitHub Preparation

To push the clean project to your GitHub repository:
```bash
# 1. Initialize git repository
git init

# 2. Verify git status (.env and database should be ignored)
git status

# 3. Add all tracked project files
git add .

# 4. Commit with a professional message
git commit -m "feat: complete HealthPredict AI patient management system with Gemini API for Gokul Infocare assessment"

# 5. Link to your remote GitHub repository
git remote add origin https://github.com/YOUR_USERNAME/HealthPredict-AI.git

# 6. Push to main branch
git branch -M main
git push -u origin main
```

---

## 11. Mandatory Medical Disclaimer

> **MEDICAL DISCLAIMER:** HealthPredict AI is an educational demonstration tool developed exclusively for technical evaluation and does not provide medical diagnoses, clinical treatment plans, or pharmaceutical prescriptions. All AI-generated remarks are general informational interpretations. Always consult a licensed healthcare practitioner or physician for medical advice and interpretation of clinical laboratory results.

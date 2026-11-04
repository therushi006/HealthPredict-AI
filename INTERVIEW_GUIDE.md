# HealthPredict AI – Technical Interview Preparation Guide

> **Prepared for:** Gokul Infocare  
> **Role:** AI Growth & Automation Associate  
> **Project:** HealthPredict AI – Patient Health Prediction & Management System  

---

## 1. What is HealthPredict AI? (Project Elevator Pitch)

"**HealthPredict AI** is a complete, full-stack Python healthcare web application. It allows a clinic or healthcare team to register patients, enter laboratory blood test markers (Glucose, Haemoglobin, and Cholesterol), validate all input against strict clinical and syntax rules, and securely send that blood test data to the Google Gemini AI API. 

The AI generates a structured, informational health interpretation covering a general summary, potential risk indicators, and recommendations to consult a doctor. All patient details, blood markers, and AI remarks are stored permanently in a local SQLite database using SQLAlchemy ORM. The application also provides full CRUD capabilities (Create, Read, Update, Delete) and an automated assessment runner testing the 10 official patient records provided by Gokul Infocare."

---

## 2. Core Concepts Explained in Simple English

### What is Python and why did we use it?
**Python** is one of the world's most popular, readable, and versatile programming languages. It was chosen for this project because:
1. It is the industry standard for backend development, AI integration, and automation workflows.
2. It has an extensive ecosystem of well-maintained packages (such as Flask, SQLAlchemy, and official Google AI SDKs).
3. Python's clear syntax allows a developer to write maintainable, bug-free code that can be easily understood and explained during technical interviews.

### What is Flask?
**Flask** is a lightweight Python web framework (often called a "micro-framework"). Unlike heavier frameworks like Django that force rigid directory structures and default admin tools, Flask gives the developer complete control. It handles:
- **Routing:** Mapping web URLs (e.g., `/patients/add`) to Python functions.
- **Request & Response Cycle:** Reading form submissions and returning rendered HTML or JSON.
- **Template Rendering:** Using Jinja2 to dynamically insert patient data into HTML.
- **Session & Security:** Managing user notifications (flash messages) and CSRF protection.

### What is SQLite?
**SQLite** is a lightweight, serverless relational database engine. Instead of requiring a separate background server process (like PostgreSQL or MySQL), SQLite stores the entire database in a single local disk file (`healthpredict.db`). It is zero-configuration, ACID-compliant, supports standard SQL, and is built directly into Python's standard library (`sqlite3`).

### What is CRUD?
**CRUD** stands for the four foundational operations of any persistent software system:
- **C – Create:** Adding a new patient record into the database via the registration form (`POST /patients/add`).
- **R – Read:** Viewing all stored patients in a table (`GET /patients`) or viewing a single patient's detailed AI report (`GET /patients/<id>`).
- **U – Update:** Editing an existing patient's details (`POST /patients/edit/<id>`).
- **D – Delete:** Permanently removing a patient record (`POST /patients/delete/<id>`).

### How does SQLAlchemy work?
**SQLAlchemy** is an Object-Relational Mapper (ORM). Instead of writing raw SQL strings (e.g. `SELECT * FROM patients WHERE id = 1`), which can be error-prone and vulnerable to SQL Injection, SQLAlchemy allows us to represent database tables as Python classes (like the `Patient` model in `models.py`). 
- When we create a `patient = Patient(...)` object and call `db.session.add(patient)` and `db.session.commit()`, SQLAlchemy automatically translates that into parameterized SQL `INSERT` statements.
- This guarantees type safety, automatic escaping, and database portability.

### How does the Google Gemini AI API integration work?
1. When a patient record passes backend validation, the application extracts only the three numeric blood markers (`glucose`, `haemoglobin`, `cholesterol`).
2. A structured prompt is built in `ai_service.py` asking Gemini to act as an educational health assistant.
3. The prompt is sent to Google's servers using the official SDK or REST endpoint with the API key retrieved securely from an environment variable (`GEMINI_API_KEY`).
4. Google Gemini returns a response formatted into 5 sections: General Assessment, Potential Risk Indicators, Recommendation, Educational Note, and Medical Disclaimer.
5. The text is cleaned and saved into the SQLite database alongside the patient record, marked with `ai_status = 'completed'`.

### Why and how is patient privacy protected during AI calls?
Patient privacy is a critical healthcare design decision. **HealthPredict AI omits all Personally Identifiable Information (PII)—including Full Name, Date of Birth, and Email Address—from the AI payload.** Only the raw numbers (Glucose, Haemoglobin, Cholesterol) are transmitted. The patient's identity remains solely on the local server in `healthpredict.db`.

### How does the application handle invalid records?
The application implements dual-layer validation (client-side in JavaScript for fast feedback, and server-side in Python for security).
If any field fails (e.g. invalid email syntax like `hunter@gmail`, a non-existent date like `31.11.2001`, or a future date like `19.10.2030`):
1. The submission is blocked.
2. The database transaction is **not** performed.
3. The external AI API is **not** called (preventing wasted API quota and money).
4. The user is returned to the form with clear, field-level error messages explaining exactly what was wrong.

### How does the application protect the API key?
- The API key is stored in a `.env` file that is excluded from Git via `.gitignore`.
- It is never hardcoded in any Python file or exposed in frontend JavaScript.
- A `.env.example` file is provided to document what variables are required without revealing secrets.

### What happens if the Gemini AI API is unavailable or the key is missing?
The application is engineered with defensive programming:
- It **never crashes** if the internet is down, the API key is absent, or quota is exceeded.
- It **never produces fabricated or fake AI responses**.
- Instead, the patient's record is safely saved in SQLite, `ai_status` is marked as `'failed'` or `'pending'`, and the exact error (e.g. "API Key not configured" or "Request timed out") is recorded.
- A "Retry AI Analysis" button is provided on the patient row and details page to retry the call once connectivity or credentials are restored.

---

## 3. Explanation of Every Important Project File

### 1. `config.py`
- Centralizes all environment configuration.
- Reads `.env` using `python-dotenv`.
- Defines `Config` (for production/development with SQLite path and Gemini model name) and `TestingConfig` (with in-memory SQLite and CSRF disabled for fast automated tests).

### 2. `database.py`
- Instantiates `db = SQLAlchemy()`.
- Defines `init_db(app)` which connects the database to the Flask application and automatically calls `db.create_all()` to generate tables on startup if they do not already exist.

### 3. `models.py`
- Defines the `Patient` database model.
- Contains all required columns: `id`, `full_name`, `date_of_birth`, `email`, `glucose`, `haemoglobin`, `cholesterol`, `ai_remarks`, `ai_status`, `created_at`, `updated_at`.
- Provides convenience properties: `formatted_dob` (DD/MM/YYYY) and `to_dict()` for the REST API.

### 4. `validation.py`
- Contains all pure validation functions.
- `parse_and_validate_dob`: Handles dotted dates (`28.01.1960`) and slashes (`28/01/1960`), rejects invalid dates (like November 31), and rejects future dates against the live system clock.
- `validate_email_address`: Enforces standard email syntax requiring `@` and a valid domain with a top-level domain (TLD), rejecting `hunter@gmail` and `Kris.wu.gmail.com`.
- `validate_numeric_marker`: Validates numbers and checks physiologically plausible clinical boundaries (Glucose 20–600, Hb 2–25, Cholesterol 50–600).
- `check_duplicate_patient`: Detects identical patient entries and generates a warning while still allowing separate creation per assessment requirements.

### 5. `ai_service.py`
- Contains the AI logic.
- `build_prompt`: Constructs the educational prompt containing only the blood values.
- `generate_health_remarks`: Calls Gemini via the official SDK with a direct REST fallback. Handles timeouts, invalid keys, and network failures gracefully.

### 6. `app.py`
- The Flask application factory.
- Defines all web routes: `/`, `/patients`, `/patients/add`, `/patients/edit/<id>`, `/patients/delete/<id>`, `/patients/<id>`, `/patients/<id>/retry-ai`, `/assessment`, `/analysis`, and `/about`.
- Defines REST API endpoints: `/api/patients` and `/api/patients/<id>`.
- Implements custom 404 and 500 error handlers that protect stack traces from being exposed to the user.

---

## 4. 20+ Technical Interview Questions & Beginner-Friendly Answers

### Q1: What was your role in building HealthPredict AI?
**Answer:** "I designed and implemented the entire full-stack application as part of the technical assessment for Gokul Infocare. I built the Flask backend, structured the SQLite database using SQLAlchemy, implemented frontend and backend validation, integrated the Google Gemini AI API, created a responsive Bootstrap 5 dashboard, and authored the automated pytest test suite."

### Q2: What happens when the user clicks 'Submit' on the Add Patient form?
**Answer:** "First, client-side JavaScript validates that all fields are non-empty, the email has a valid domain, the date is a real calendar date not in the future, and blood markers are numbers. When submitted, the Flask `POST /patients/add` route re-validates all fields on the backend. If validation passes, `ai_service.py` builds a structured prompt with the blood values and calls Google Gemini API. Once remarks are received, a new `Patient` record is committed to SQLite and the user is redirected to the records list with a success notification."

### Q3: Why is backend validation necessary if you already have frontend validation?
**Answer:** "Frontend validation is for user experience—it provides immediate feedback before page reload. However, frontend validation can be easily bypassed by disabling JavaScript, modifying DOM elements, or sending a direct POST request using Postman or cURL. Backend validation is mandatory because the server must act as the ultimate gatekeeper of data integrity and database security."

### Q4: How did you handle the date format requirement and the dotted dates in the test data?
**Answer:** "The assessment data used dates with dots, such as `28.01.1960`, while requiring `DD/MM/YYYY` display and validation. In `validation.py`, I created a date parser that accepts `DD.MM.YYYY`, `DD/MM/YYYY`, and `YYYY-MM-DD`. It parses the string into a native Python `datetime.date` object. This allowed us to process the official test data without altering any characters, while storing it consistently in SQLite and displaying it as `DD/MM/YYYY` using the model's `formatted_dob` property."

### Q5: Why was Record 4 (Peter Larry, 31.11.2001) rejected?
**Answer:** "Record 4 has a date of November 31st, 2001. In the Gregorian calendar, November only has 30 days. When `datetime.strptime('31.11.2001', '%d.%m.%Y')` is executed, Python raises a `ValueError`. Our validation function catches this and returns a user-friendly error: `'31.11.2001' is not a real calendar date (check days in month)`."

### Q6: Why was Record 8 (Kris Wu) rejected?
**Answer:** "Record 8 failed two separate validation checks. First, the date of birth was `19.10.2030`, which is in the future. Second, the email was `Kris.wu.gmail.com`, which is completely missing the `@` symbol. Both violations were caught and reported to the user."

### Q7: Why was Record 2 (John Hunter, hunter@gmail) rejected?
**Answer:** "Record 2 provided `hunter@gmail`. While it contains `@`, it lacks a top-level domain (TLD) like `.com` or `.org`. Our email validation regex requires a dot and a valid top-level domain after the domain name."

### Q8: How did you handle the duplicate Record 6 (Robyn Pears)?
**Answer:** "The assessment data repeated Record 1 as Record 6 with identical information. Per requirements, the system must not discard duplicates silently. Instead, the application stores both as separate entries with distinct primary keys (`id`), but displays a warning notice stating that an identical record already exists."

### Q9: What optimization did you implement when editing a patient's record?
**Answer:** "In `edit_patient` (`POST /patients/edit/<id>`), the application compares the newly submitted blood values (`glucose`, `haemoglobin`, `cholesterol`) against the existing values in the database. If only personal fields like email or name changed (such as in Assessment Operation 3 where we changed the email to `gokul@infocare.com`), the application preserves the existing AI remarks and does not make an unnecessary API call to Google Gemini. This saves API costs and reduces page response time."

### Q10: How do you prevent SQL Injection in HealthPredict AI?
**Answer:** "We use SQLAlchemy ORM for all database transactions. SQLAlchemy uses parameterized queries where user inputs are sent as parameters separated from the SQL statement itself. The database driver treats user input strictly as literal data, preventing malicious SQL code injection."

### Q11: How do you protect against Cross-Site Request Forgery (CSRF)?
**Answer:** "We integrated `Flask-WTF`'s `CSRFProtect`. Every HTML form includes a hidden `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">` field. For AJAX requests (like the assessment runner), the CSRF token is sent in the `X-CSRFToken` request header. Flask validates this token on every POST request to guarantee the submission originated from our application."

### Q12: Why did you create a separate `ai_service.py` file?
**Answer:** "Separation of Concerns. By placing AI logic in `ai_service.py`, the core Flask routes in `app.py` remain clean and focused on HTTP requests and responses. If we ever decide to change the AI model from Gemini to another model or adjust the prompt, we only modify `ai_service.py` without touching the web routes or database logic."

### Q13: What prompt did you send to the Google Gemini API?
**Answer:** "I constructed the prompt required by the assessment guidelines: 'You are an educational health information assistant. Review the supplied patient blood test values and provide a cautious, general informational interpretation...' I included instructions to provide a General Assessment, Potential Risk Indicators, Recommendation, and Medical Disclaimer, while strictly forbidding medical prescriptions or disease diagnoses."

### Q14: How does the application handle a missing or invalid Gemini API key?
**Answer:** "The `generate_health_remarks` function checks if `GEMINI_API_KEY` is present. If missing or default, it immediately returns `(False, error_message, 'failed')`. If an invalid key is supplied and Gemini returns an HTTP 400 error, it catches the exception and returns a clear message: 'AI Service Error: Invalid Google Gemini API Key'. The patient record is safely saved with `ai_status = 'failed'`, and a 'Retry AI Analysis' button is provided."

### Q15: Why didn't you mock or hardcode fake AI responses when the API fails?
**Answer:** "Because the assessment rules explicitly stated: 'Do not create fake functionality or hardcoded AI responses. If the AI service fails, do not generate fake AI remarks.' Faking AI output in a healthcare tool is unethical and violates assessment guidelines. Real applications must report the actual status and offer a retry mechanism."

### Q16: How did you test the application?
**Answer:** "I wrote 23 automated tests using `pytest` organized into three files:
1. `test_validation.py` for date parsing, leap years, 30-day months, emails, and blood marker boundaries.
2. `test_crud.py` for Create, Read, Update, Delete, duplicate handling, and the 10-record assessment suite.
3. `test_ai_service.py` for prompt verification, missing keys, timeouts, quota errors, and retry handling.
I used an in-memory SQLite database and mocked the external Gemini API using Python's `unittest.mock.patch` so tests run instantaneously without consuming API quota."

### Q17: What HTTP status codes are returned by your API endpoints?
**Answer:** 
- `GET /api/patients` returns `200 OK` with the JSON list.
- `GET /api/patients/<id>` returns `200 OK` if found, or `404 Not Found` if the ID does not exist.
- Form submissions return `302 Found` (redirect) upon success or `200 OK` with validation errors highlighted upon failure.
- Custom error handlers catch `404` and `500` and return user-friendly HTML error pages without exposing Python stack traces.

### Q18: What is the purpose of the Assessment Runner feature?
**Answer:** "The Assessment Runner (`/assessment`) is an interactive verification engine built specifically for Gokul Infocare's review. Instead of having to type all 10 records by hand, the reviewer or candidate can click 'Run Official Assessment'. It passes all 10 records through the live validation and AI pipeline, displaying a step-by-step audit table showing exactly 7 accepted and 3 rejected records."

### Q19: What are the physiological boundaries for the blood markers in your validation?
**Answer:** 
- **Glucose:** 20.0 to 600.0 mg/dL (accounting for extreme clinical conditions like severe hypoglycemia to hyperosmolar hyperglycemic state).
- **Haemoglobin:** 2.0 to 25.0 g/dL (accounting for severe anemia to polycythemia).
- **Cholesterol:** 50.0 to 600.0 mg/dL (accounting for hypocholesterolemia to severe familial hypercholesterolemia).
Any value outside these bounds or non-numeric input is rejected.

### Q20: What would you do to deploy this application to production?
**Answer:** 
1. Use a production WSGI application server such as **Gunicorn** or **Waitress** behind a reverse proxy like **Nginx**.
2. Migrate from SQLite to **PostgreSQL** or **MySQL** for high concurrent write performance.
3. Configure environment variables securely on the hosting provider (e.g. AWS, Render, or Google Cloud Run).
4. Enforce HTTPS with an SSL/TLS certificate.
5. Set up Celery or Redis background queues for asynchronous AI processing so long AI calls do not block web workers.

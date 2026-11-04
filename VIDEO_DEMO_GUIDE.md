# HealthPredict AI – 3 to 5 Minute Video Demonstration Guide

> **Prepared for:** Gokul Infocare Technical Assessment (Task 2)  
> **Position:** AI Growth & Automation Associate  
> **Topic:** HealthPredict AI – Patient Health Prediction & Management System  

This guide provides an exact, step-by-step recording plan. It includes what to click on your screen, what to show, and the exact words to speak.

---

## Pre-Recording Checklist
1. Ensure your virtual environment is active and run the application:
   ```powershell
   python app.py
   ```
2. Open your web browser to `http://127.0.0.1:5000`.
3. Have your terminal, browser, and VS Code open side-by-side or ready to switch.
4. If testing with a clean database, you can delete `healthpredict.db` beforehand so your dashboard starts fresh at 0 records.

---

## Video Timeline & Script (Total Time: ~4 Minutes)

### Minute 0:00 – 0:35 | Introduction & Dashboard Overview
- **Screen Action:** Show the HealthPredict AI Dashboard (`http://127.0.0.1:5000`). Point cursor to the top navbar, the dark navy sidebar, summary cards, and the Medical Disclaimer banner at the bottom.
- **Spoken Script:**
  > "Hello everyone. My name is [Your Name], and this is my video demonstration of **HealthPredict AI** for the AI Growth & Automation Associate technical assessment at Gokul Infocare.
  > 
  > HealthPredict AI is a full-stack Python application built with Flask, SQLAlchemy, SQLite, Bootstrap 5, and Google Gemini AI.
  > 
  > Looking at the dashboard, we have real-time dynamic metric cards showing Total Records, Valid Records, AI Analysis Completed, and Validation Errors. At the bottom of every page, we display our mandatory medical disclaimer emphasizing that all AI remarks are informational and educational."

---

### Minute 0:35 – 1:30 | Operation 1 – CREATE & The 10 Official Test Records
- **Screen Action:** 
  1. Click on **"Assessment Runner"** in the sidebar (`/assessment`).
  2. Scroll through the 10 official test records table to show that the exact test data provided by Gokul Infocare is loaded.
  3. Click the teal button: **"Run Official Assessment"**.
  4. Show the live audit log table appear with 7 accepted records and 3 rejected records.
- **Spoken Script:**
  > "For Operation 1 (CREATE), Gokul Infocare provided 10 official test records to evaluate our data validation and AI integration. Rather than modifying or skipping any data, we run them through our live backend validation pipeline.
  > 
  > When I click 'Run Official Assessment', all 10 records are processed:
  > - **Exactly 7 records are accepted** and committed to our SQLite database.
  > - **Exactly 3 records are rejected** according to the official rules.
  > 
  > Let's examine the 3 rejections:
  > 1. **Record 2 (John Hunter)** is rejected because `hunter@gmail` is missing its top-level domain extension like `.com`.
  > 2. **Record 4 (Peter Larry)** is rejected because `31.11.2001` is not a real calendar date—November has only 30 days.
  > 3. **Record 8 (Kris Wu)** is rejected because the date of birth `19.10.2030` is in the future, and the email `Kris.wu.gmail.com` is missing the `@` symbol.
  > 
  > In addition, **Record 6 (Robyn Pears)** is a duplicate of Record 1. Our application follows instructions by storing it as a separate record with a unique ID, while displaying a duplicate warning."

---

### Minute 1:30 – 2:15 | Operation 2 – READ (Patient Records & Full AI Report)
- **Screen Action:**
  1. Click **"Patient Records"** in the sidebar (`/patients`).
  2. Show all 7 records in the Bootstrap table with ID, Name, DOB, Email, Blood Markers, and AI Status badges.
  3. Type `Robyn` into the search box to demonstrate the live filter. Then clear the search.
  4. Click the eye icon on Record #1 (or Darryl Tim) to open `/patients/<id>`.
  5. Scroll down to show the formatted Google Gemini AI remarks.
- **Spoken Script:**
  > "Now for Operation 2 (READ). In the Patient Records registry, we can see all 7 stored patients in a clean table with their ID, contact info, blood values, and AI status badges. We also have a search bar that filters dynamically by name, email, or record ID.
  > 
  > When we click 'View Details' on a patient, we see their complete profile, clinical blood marker indicators, and the **Google Gemini AI Health Remarks**.
  > 
  > The remarks are structured into 5 sections: General Assessment, Potential Risk Indicators, Recommendation, Educational Note, and Medical Disclaimer.
  > 
  > Notice our privacy architecture: we only transmitted the numbers—Glucose 232, Haemoglobin 13.5, and Cholesterol 180—to Google Gemini. The patient's full name, email, and date of birth were kept strictly confidential on our local server."

---

### Minute 2:15 – 2:50 | Operation 3 – UPDATE (Change Email to gokul@infocare.com)
- **Screen Action:**
  1. Return to `/patients`.
  2. Click the pencil icon (**"Edit"**) on Record #3 (Darryl Tim).
  3. Change the email address field from `timd@smh.com.au` to `gokul@infocare.com`.
  4. Click **"Save Changes"**.
  5. Point out the success flash alert: `Patient #3 details updated successfully. Blood markers were unchanged; unnecessary AI API call avoided.`
  6. Point out that the email in the table now shows `gokul@infocare.com`.
- **Spoken Script:**
  > "Now let's demonstrate Operation 3 (UPDATE). The assessment instructions ask us to choose any one record and change its email to `gokul@infocare.com`.
  > 
  > I open the edit form for Darryl Tim, replace the email with `gokul@infocare.com`, and submit.
  > 
  > The record is immediately updated in SQLite, and our table now displays `gokul@infocare.com`. 
  > 
  > Notice an important optimization decision: because the blood test values were not changed, our backend smartly avoided calling the Gemini AI API again, saving quota and latency. If we had modified Glucose or Cholesterol, the AI remarks would have regenerated automatically."

---

### Minute 2:50 – 3:30 | Operation 4 – DELETE (Remove Patient Record)
- **Screen Action:**
  1. Find Record #6 (the duplicate Robyn Pears entry).
  2. Click the red trash icon (**"Delete"**).
  3. Show the confirmation modal appear: `Confirm Patient Deletion: Are you sure you want to permanently delete patient record Robyn Pears (ID: #6)?`
  4. Click the red **"Delete Record"** button inside the modal.
  5. Show the table update: total records drop from 7 to 6, and a green success alert confirms the deletion.
- **Spoken Script:**
  > "Next is Operation 4 (DELETE). To avoid accidental clicks, every delete action triggers a Bootstrap confirmation modal.
  > 
  > I select the duplicate Robyn Pears record (#6) and confirm the deletion. 
  > 
  > The patient and their stored AI remarks are permanently removed from SQLite via a safe POST request. The table refreshes immediately, and our total count updates to 6 remaining records."

---

### Minute 3:30 – 4:15 | Backend Architecture, Tests & Conclusion
- **Screen Action:**
  1. Switch to VS Code / terminal.
  2. Briefly show the clean modular structure: `app.py`, `models.py`, `validation.py`, `ai_service.py`.
  3. Run pytest in the terminal:
     ```powershell
     .\venv\Scripts\pytest -v
     ```
  4. Show all **23 tests passing with green checkmarks**.
- **Spoken Script:**
  > "Finally, let's look at the codebase. We followed professional software engineering practices:
  > - `models.py` defines our SQLAlchemy schema with parameterized queries.
  > - `validation.py` isolates all date, calendar, email, and clinical bounds logic.
  > - `ai_service.py` encapsulates the Google Gemini API with fallback and error handling.
  > - `config.py` protects our API key using environment variables.
  > 
  > Running `pytest -v`, all 23 unit and integration tests pass cleanly in just a few seconds, verifying validation rules, CRUD operations, duplicate handling, and AI error fallbacks with zero warnings.
  > 
  > HealthPredict AI is clean, secure, and ready for deployment. Thank you for your time, and I look forward to discussing the system further during the technical interview with Gokul Infocare."

---

## Demonstration Checklist Summary

| Step # | Operation | Target Action | Verification |
| :---: | :--- | :--- | :--- |
| **1** | **Dashboard** | Show metrics and disclaimer | Clean UI, 0 or existing metrics shown |
| **2** | **Create (10 Records)** | Click "Run Official Assessment" | 7 Accepted, 3 Rejected with clear error logs |
| **3** | **Read** | View records table & open patient report | 7 records displayed, full AI remarks visible |
| **4** | **Update** | Edit one email to `gokul@infocare.com` | Email updated; AI call skipped if blood unchanged |
| **5** | **Delete** | Delete Record #6 with confirmation modal | 6 records remain; safe POST deletion |
| **6** | **Testing** | Run `pytest -v` in terminal | 23 passed, 0 warnings |

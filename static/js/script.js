/**
 * HealthPredict AI - Client-side Interaction & Validation Script
 * Mirrors Python backend validation rules for responsive UX.
 */

document.addEventListener('DOMContentLoaded', function () {
    // -------------------------------------------------------------
    // 1. Mobile Sidebar Toggle
    // -------------------------------------------------------------
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('show');
        });
    }

    // -------------------------------------------------------------
    // 2. Client-Side Form Validation (Mirrors Python backend rules)
    // -------------------------------------------------------------
    const patientForm = document.getElementById('patientForm') || document.getElementById('editPatientForm');

    if (patientForm) {
        const fullNameInput = document.getElementById('full_name');
        const dobInput = document.getElementById('date_of_birth');
        const emailInput = document.getElementById('email');
        const glucoseInput = document.getElementById('glucose');
        const haemoglobinInput = document.getElementById('haemoglobin');
        const cholesterolInput = document.getElementById('cholesterol');

        // Validation helpers
        function setFieldValid(input, feedbackId) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            const feedback = document.getElementById(feedbackId);
            if (feedback) {
                feedback.textContent = '';
                feedback.style.display = 'none';
            }
        }

        function setFieldInvalid(input, feedbackId, message) {
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
            const feedback = document.getElementById(feedbackId);
            if (feedback) {
                feedback.textContent = message;
                feedback.style.display = 'block';
            }
        }

        // Validate Full Name
        function validateFullName() {
            const val = fullNameInput.value.trim();
            if (!val) {
                setFieldInvalid(fullNameInput, 'full_name_feedback', 'Full name is required.');
                return false;
            }
            if (val.length < 2) {
                setFieldInvalid(fullNameInput, 'full_name_feedback', 'Full name must be at least 2 characters.');
                return false;
            }
            if (val.length > 100) {
                setFieldInvalid(fullNameInput, 'full_name_feedback', 'Full name cannot exceed 100 characters.');
                return false;
            }
            setFieldValid(fullNameInput, 'full_name_feedback');
            return true;
        }

        // Validate DOB (Supports DD.MM.YYYY, DD/MM/YYYY, YYYY-MM-DD; checks calendar validity & future date)
        function validateDob() {
            const val = dobInput.value.trim();
            if (!val) {
                setFieldInvalid(dobInput, 'dob_feedback', 'Date of birth is required.');
                return false;
            }

            let day, month, year;
            const dotOrSlash = val.match(/^(\d{1,2})[./](\d{1,2})[./](\d{4})$/);
            const isoMatch = val.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);

            if (dotOrSlash) {
                day = parseInt(dotOrSlash[1], 10);
                month = parseInt(dotOrSlash[2], 10);
                year = parseInt(dotOrSlash[3], 10);
            } else if (isoMatch) {
                year = parseInt(isoMatch[1], 10);
                month = parseInt(isoMatch[2], 10);
                day = parseInt(isoMatch[3], 10);
            } else {
                setFieldInvalid(dobInput, 'dob_feedback', 'Invalid date format. Use DD/MM/YYYY or DD.MM.YYYY.');
                return false;
            }

            // Month boundary check
            if (month < 1 || month > 12) {
                setFieldInvalid(dobInput, 'dob_feedback', 'Month must be between 1 and 12.');
                return false;
            }

            // Calendar check: date validity (e.g. November 31, February 29 on non-leap years)
            const dateObj = new Date(year, month - 1, day);
            if (
                dateObj.getFullYear() !== year ||
                dateObj.getMonth() !== (month - 1) ||
                dateObj.getDate() !== day
            ) {
                setFieldInvalid(dobInput, 'dob_feedback', `'${val}' is not a real calendar date (check days in month).`);
                return false;
            }

            // Future date check
            const today = new Date();
            today.setHours(23, 59, 59, 999);
            if (dateObj > today) {
                setFieldInvalid(dobInput, 'dob_feedback', 'Date of birth cannot be in the future.');
                return false;
            }

            setFieldValid(dobInput, 'dob_feedback');
            return true;
        }

        // Validate Email
        function validateEmail() {
            const val = emailInput.value.trim();
            if (!val) {
                setFieldInvalid(emailInput, 'email_feedback', 'Email address is required.');
                return false;
            }

            if (!val.includes('@')) {
                setFieldInvalid(emailInput, 'email_feedback', "Invalid email: missing '@' symbol.");
                return false;
            }

            const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$/;
            if (!emailRegex.test(val)) {
                setFieldInvalid(emailInput, 'email_feedback', "Invalid email format (must include domain and TLD, e.g. name@domain.com).");
                return false;
            }

            setFieldValid(emailInput, 'email_feedback');
            return true;
        }

        // Validate Numeric Blood Markers
        function validateMarker(input, feedbackId, min, max, label, unit) {
            const valStr = input.value.trim();
            if (!valStr) {
                setFieldInvalid(input, feedbackId, `${label} is required.`);
                return false;
            }
            const num = parseFloat(valStr);
            if (isNaN(num)) {
                setFieldInvalid(input, feedbackId, `${label} must be a valid number.`);
                return false;
            }
            if (num < min || num > max) {
                setFieldInvalid(input, feedbackId, `${label} must be between ${min} and ${max} ${unit}.`);
                return false;
            }
            setFieldValid(input, feedbackId);
            return true;
        }

        // Attach blur event listeners for immediate user feedback
        if (fullNameInput) fullNameInput.addEventListener('blur', validateFullName);
        if (dobInput) dobInput.addEventListener('blur', validateDob);
        if (emailInput) emailInput.addEventListener('blur', validateEmail);
        if (glucoseInput) glucoseInput.addEventListener('blur', () => validateMarker(glucoseInput, 'glucose_feedback', 20, 600, 'Glucose', 'mg/dL'));
        if (haemoglobinInput) haemoglobinInput.addEventListener('blur', () => validateMarker(haemoglobinInput, 'haemoglobin_feedback', 2.0, 25.0, 'Haemoglobin', 'g/dL'));
        if (cholesterolInput) cholesterolInput.addEventListener('blur', () => validateMarker(cholesterolInput, 'cholesterol_feedback', 50, 600, 'Cholesterol', 'mg/dL'));

        // Form Submission Interception
        patientForm.addEventListener('submit', function (event) {
            const isNameValid = validateFullName();
            const isDobValid = validateDob();
            const isEmailValid = validateEmail();
            const isGlucoseValid = validateMarker(glucoseInput, 'glucose_feedback', 20, 600, 'Glucose', 'mg/dL');
            const isHbValid = validateMarker(haemoglobinInput, 'haemoglobin_feedback', 2.0, 25.0, 'Haemoglobin', 'g/dL');
            const isCholValid = validateMarker(cholesterolInput, 'cholesterol_feedback', 50, 600, 'Cholesterol', 'mg/dL');

            if (!isNameValid || !isDobValid || !isEmailValid || !isGlucoseValid || !isHbValid || !isCholValid) {
                event.preventDefault();
                event.stopPropagation();
            } else {
                // Show loading spinner on submit button
                const btnSubmit = document.getElementById('btnSubmit');
                if (btnSubmit) {
                    btnSubmit.disabled = true;
                    btnSubmit.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Analyzing & Saving...';
                }
            }
        });
    }
});

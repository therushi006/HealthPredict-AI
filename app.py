import os
import logging
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, abort, session
)
from flask_wtf.csrf import CSRFProtect

from config import Config
from database import db, init_db
from models import Patient
from validation import (
    validate_patient_data,
    check_duplicate_patient,
    CLINICAL_BOUNDS
)
from ai_service import generate_health_remarks, MEDICAL_DISCLAIMER

# Configure safe logging without sensitive data leaks
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] in %(module)s: %(message)s'
)
logger = logging.getLogger('healthpredict')


def create_app(config_class=Config):
    """Application factory pattern for HealthPredict AI."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CSRF Protection
    csrf = CSRFProtect(app)

    # Initialize Database & automatically create tables
    init_db(app)

    # Inject medical disclaimer and current date into all templates
    @app.context_processor
    def inject_global_template_vars():
        return {
            'medical_disclaimer': MEDICAL_DISCLAIMER,
            'current_date': datetime.now().strftime('%A, %d %B %Y'),
            'clinical_bounds': CLINICAL_BOUNDS
        }

    # -------------------------------------------------------------
    # WEB UI ROUTES
    # -------------------------------------------------------------

    @app.route('/')
    def dashboard():
        """
        Dashboard route: calculates real-time database metrics,
        shows recent records, quick action buttons, and medical disclaimer.
        """
        total_patients = Patient.query.count()
        ai_completed = Patient.query.filter_by(ai_status='completed').count()
        ai_pending = Patient.query.filter(Patient.ai_status.in_(['pending', 'failed'])).count()
        
        # Validation rejections tracked in user session or fallback
        validation_errors_count = session.get('validation_errors_count', 0)
        
        recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()

        return render_template(
            'dashboard.html',
            total_patients=total_patients,
            valid_records=total_patients,
            ai_completed=ai_completed,
            ai_pending=ai_pending,
            validation_errors_count=validation_errors_count,
            recent_patients=recent_patients,
            active_page='dashboard'
        )

    @app.route('/patients')
    def patient_list():
        """
        Display all patient records in a professional Bootstrap table.
        Supports search by name, email, or ID.
        """
        search_query = request.args.get('q', '').strip()
        query = Patient.query

        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                (Patient.full_name.ilike(search_pattern)) |
                (Patient.email.ilike(search_pattern)) |
                (Patient.id.cast(db.String).ilike(search_pattern))
            )

        patients = query.order_by(Patient.id.asc()).all()

        return render_template(
            'patients.html',
            patients=patients,
            search_query=search_query,
            total_count=len(patients),
            active_page='patients'
        )

    @app.route('/patients/add', methods=['GET', 'POST'])
    def add_patient():
        """
        Display registration form (GET) and validate & create patient record (POST).
        Invokes external Gemini AI service upon valid blood markers.
        """
        errors = {}
        form_data = {}

        if request.method == 'POST':
            form_data = request.form.to_dict()
            is_valid, cleaned, errors = validate_patient_data(form_data)

            if not is_valid:
                # Increment failed validation attempt metric in session
                session['validation_errors_count'] = session.get('validation_errors_count', 0) + len(errors)
                flash('Please correct the validation errors highlighted below.', 'danger')
                return render_template('add_patient.html', errors=errors, form_data=form_data, active_page='add_patient')

            # Check duplicate warning (allows insertion with warning)
            dup_warning = check_duplicate_patient(cleaned)
            if dup_warning:
                flash(dup_warning, 'warning')

            # Call External Gemini AI API
            api_key = app.config.get('GEMINI_API_KEY')
            ai_success, remarks, ai_status = generate_health_remarks(
                glucose=cleaned['glucose'],
                haemoglobin=cleaned['haemoglobin'],
                cholesterol=cleaned['cholesterol'],
                api_key=api_key
            )

            # Persist record in SQLite
            try:
                patient = Patient(
                    full_name=cleaned['full_name'],
                    date_of_birth=cleaned['date_of_birth'],
                    email=cleaned['email'],
                    glucose=cleaned['glucose'],
                    haemoglobin=cleaned['haemoglobin'],
                    cholesterol=cleaned['cholesterol'],
                    ai_remarks=remarks,
                    ai_status=ai_status
                )
                db.session.add(patient)
                db.session.commit()

                flash_msg = f"Patient record for '{patient.full_name}' created successfully (ID: #{patient.id})."
                if ai_status == 'completed':
                    flash(f"{flash_msg} AI Health Remarks generated.", 'success')
                else:
                    flash(f"{flash_msg} Note: {remarks}", 'info')

                return redirect(url_for('patient_list'))

            except Exception as e:
                db.session.rollback()
                logger.error("Database insertion failed: %s", type(e).__name__)
                flash('A database error occurred while saving the patient record. Please try again.', 'danger')

        return render_template('add_patient.html', errors=errors, form_data=form_data, active_page='add_patient')

    @app.route('/patients/<int:patient_id>')
    def patient_details(patient_id):
        """Display individual patient details and full AI remarks report."""
        patient = db.get_or_404(Patient, patient_id)
        return render_template('patient_details.html', patient=patient, active_page='patients')

    @app.route('/patients/edit/<int:patient_id>', methods=['GET', 'POST'])
    def edit_patient(patient_id):
        """
        Display edit form (GET) and update patient record (POST).
        Only calls AI API if blood test values were changed.
        """
        patient = db.get_or_404(Patient, patient_id)
        errors = {}

        if request.method == 'POST':
            form_data = request.form.to_dict()
            is_valid, cleaned, errors = validate_patient_data(form_data)

            if not is_valid:
                session['validation_errors_count'] = session.get('validation_errors_count', 0) + len(errors)
                flash('Please correct the validation errors highlighted below.', 'danger')
                return render_template('edit_patient.html', patient=patient, errors=errors, form_data=form_data, active_page='patients')

            # Check if blood test values changed
            blood_values_changed = (
                patient.glucose != cleaned['glucose'] or
                patient.haemoglobin != cleaned['haemoglobin'] or
                patient.cholesterol != cleaned['cholesterol']
            )

            # Update personal fields
            patient.full_name = cleaned['full_name']
            patient.date_of_birth = cleaned['date_of_birth']
            patient.email = cleaned['email']

            if blood_values_changed:
                patient.glucose = cleaned['glucose']
                patient.haemoglobin = cleaned['haemoglobin']
                patient.cholesterol = cleaned['cholesterol']
                
                # Regenerate AI remarks
                api_key = app.config.get('GEMINI_API_KEY')
                ai_success, remarks, ai_status = generate_health_remarks(
                    glucose=cleaned['glucose'],
                    haemoglobin=cleaned['haemoglobin'],
                    cholesterol=cleaned['cholesterol'],
                    api_key=api_key
                )
                patient.ai_remarks = remarks
                patient.ai_status = ai_status
                flash_message = f"Patient #{patient.id} updated. Blood test values changed, so AI analysis was refreshed."
            else:
                flash_message = f"Patient #{patient.id} details updated successfully. Blood markers were unchanged; unnecessary AI API call avoided."

            try:
                db.session.commit()
                flash(flash_message, 'success')
                return redirect(url_for('patient_list'))
            except Exception as e:
                db.session.rollback()
                logger.error("Database update failed: %s", type(e).__name__)
                flash('A database error occurred while updating the patient record.', 'danger')

        # Populate form with existing patient details
        form_data = {
            'full_name': patient.full_name,
            'date_of_birth': patient.formatted_dob,
            'email': patient.email,
            'glucose': patient.glucose,
            'haemoglobin': patient.haemoglobin,
            'cholesterol': patient.cholesterol
        }
        return render_template('edit_patient.html', patient=patient, errors=errors, form_data=form_data, active_page='patients')

    @app.route('/patients/delete/<int:patient_id>', methods=['POST'])
    def delete_patient(patient_id):
        """
        Safely delete a patient record using POST method (avoids destructive GET requests).
        """
        patient = db.get_or_404(Patient, patient_id)
        name = patient.full_name
        try:
            db.session.delete(patient)
            db.session.commit()
            flash(f"Patient record #{patient_id} ('{name}') was deleted successfully.", 'success')
        except Exception as e:
            db.session.rollback()
            logger.error("Database deletion failed: %s", type(e).__name__)
            flash('A database error occurred while deleting the patient record.', 'danger')

        return redirect(url_for('patient_list'))

    @app.route('/patients/<int:patient_id>/retry-ai', methods=['POST'])
    def retry_ai(patient_id):
        """
        Retry AI health analysis for a patient record whose status is failed or pending.
        """
        patient = db.get_or_404(Patient, patient_id)
        api_key = app.config.get('GEMINI_API_KEY')
        ai_success, remarks, ai_status = generate_health_remarks(
            glucose=patient.glucose,
            haemoglobin=patient.haemoglobin,
            cholesterol=patient.cholesterol,
            api_key=api_key
        )
        patient.ai_remarks = remarks
        patient.ai_status = ai_status

        try:
            db.session.commit()
            if ai_success:
                flash(f"AI remarks successfully generated for Patient #{patient.id}.", 'success')
            else:
                flash(f"AI analysis retry attempted for Patient #{patient.id}: {remarks}", 'warning')
        except Exception as e:
            db.session.rollback()
            logger.error("Failed to update AI remarks: %s", type(e).__name__)
            flash('Database error while saving retried AI analysis.', 'danger')

        # Return to referrer or patient list
        return redirect(request.referrer or url_for('patient_list'))

    @app.route('/analysis')
    def ai_analysis():
        """
        AI Health Analysis page summarizing AI statuses, risk distributions,
        and remarks for all patients.
        """
        patients = Patient.query.order_by(Patient.created_at.desc()).all()
        completed_count = sum(1 for p in patients if p.ai_status == 'completed')
        failed_count = sum(1 for p in patients if p.ai_status == 'failed')
        pending_count = sum(1 for p in patients if p.ai_status == 'pending')

        return render_template(
            'ai_analysis.html',
            patients=patients,
            completed_count=completed_count,
            failed_count=failed_count,
            pending_count=pending_count,
            active_page='analysis'
        )

    @app.route('/about')
    def about():
        """About Application page explaining technology stack and assessment objectives."""
        return render_template('about.html', active_page='about')

    # -------------------------------------------------------------
    # ASSESSMENT DEMO & BATCH TEST RUNNER
    # -------------------------------------------------------------

    @app.route('/assessment')
    def assessment_view():
        """
        Interactive Assessment Runner view for Gokul Infocare official test dataset.
        Demonstrates the 10 official test records, running each through the exact
        same validation and AI workflow as manual entry.
        """
        return render_template('assessment.html', active_page='assessment')

    @app.route('/assessment/run', methods=['POST'])
    def run_assessment():
        """
        Executes all 10 official assessment records supplied by Gokul Infocare
        without modifying their original values.
        Returns the step-by-step audit log showing 7 accepted and 3 rejected records.
        """
        official_records = [
            {
                'record_num': 1,
                'full_name': 'Robyn Pears',
                'date_of_birth': '28.01.1960',
                'email': 'robyn@gmail.com',
                'glucose': '232',
                'haemoglobin': '13.5',
                'cholesterol': '180'
            },
            {
                'record_num': 2,
                'full_name': 'John Hunter',
                'date_of_birth': '10.12.1990',
                'email': 'hunter@gmail',
                'glucose': '94',
                'haemoglobin': '15',
                'cholesterol': '200'
            },
            {
                'record_num': 3,
                'full_name': 'Darryl Tim',
                'date_of_birth': '12.11.1993',
                'email': 'timd@smh.com.au',
                'glucose': '240',
                'haemoglobin': '18.6',
                'cholesterol': '326'
            },
            {
                'record_num': 4,
                'full_name': 'Peter Larry',
                'date_of_birth': '31.11.2001',
                'email': 'Larry@hotmail.com',
                'glucose': '88',
                'haemoglobin': '11.5',
                'cholesterol': '165'
            },
            {
                'record_num': 5,
                'full_name': 'Sam Kerr',
                'date_of_birth': '09.12.2006',
                'email': 'sam@news.com.au',
                'glucose': '198',
                'haemoglobin': '8.9',
                'cholesterol': '192'
            },
            {
                'record_num': 6,
                'full_name': 'Robyn Pears',
                'date_of_birth': '28.01.1960',
                'email': 'robyn@gmail.com',
                'glucose': '232',
                'haemoglobin': '13.5',
                'cholesterol': '180'
            },
            {
                'record_num': 7,
                'full_name': 'Madison XI',
                'date_of_birth': '12.09.1998',
                'email': 'madison@hotmail.com',
                'glucose': '85',
                'haemoglobin': '7.6',
                'cholesterol': '163'
            },
            {
                'record_num': 8,
                'full_name': 'Kris Wu',
                'date_of_birth': '19.10.2030',
                'email': 'Kris.wu.gmail.com',
                'glucose': '79',
                'haemoglobin': '16.5',
                'cholesterol': '197'
            },
            {
                'record_num': 9,
                'full_name': 'Tenille Singh',
                'date_of_birth': '30.11.1991',
                'email': 'Tenille@yahoo.com',
                'glucose': '101',
                'haemoglobin': '15',
                'cholesterol': '310'
            },
            {
                'record_num': 10,
                'full_name': 'Prem Kumar',
                'date_of_birth': '28.04.1990',
                'email': 'prem@telstra.com',
                'glucose': '155',
                'haemoglobin': '12.5',
                'cholesterol': '265'
            }
        ]

        results = []
        accepted_count = 0
        rejected_count = 0
        api_key = app.config.get('GEMINI_API_KEY')

        for item in official_records:
            rec_id = item['record_num']
            # Run through the EXACT same validation function as manual form submission
            is_valid, cleaned, errors = validate_patient_data(item)

            if not is_valid:
                rejected_count += 1
                session['validation_errors_count'] = session.get('validation_errors_count', 0) + 1
                results.append({
                    'record_num': rec_id,
                    'full_name': item['full_name'],
                    'status': 'REJECTED',
                    'errors': errors,
                    'reason': '; '.join(errors.values())
                })
            else:
                accepted_count += 1
                dup_note = check_duplicate_patient(cleaned)
                
                # Call AI service for accepted records
                ai_success, remarks, ai_status = generate_health_remarks(
                    glucose=cleaned['glucose'],
                    haemoglobin=cleaned['haemoglobin'],
                    cholesterol=cleaned['cholesterol'],
                    api_key=api_key
                )

                patient = Patient(
                    full_name=cleaned['full_name'],
                    date_of_birth=cleaned['date_of_birth'],
                    email=cleaned['email'],
                    glucose=cleaned['glucose'],
                    haemoglobin=cleaned['haemoglobin'],
                    cholesterol=cleaned['cholesterol'],
                    ai_remarks=remarks,
                    ai_status=ai_status
                )
                db.session.add(patient)
                db.session.commit()

                results.append({
                    'record_num': rec_id,
                    'patient_id': patient.id,
                    'full_name': patient.full_name,
                    'status': 'ACCEPTED',
                    'warning': dup_note,
                    'ai_status': ai_status
                })

        return jsonify({
            'total_processed': len(official_records),
            'accepted_count': accepted_count,
            'rejected_count': rejected_count,
            'results': results
        })

    # -------------------------------------------------------------
    # REST API ENDPOINTS
    # -------------------------------------------------------------

    @app.route('/api/patients', methods=['GET'])
    def api_get_patients():
        """Return all patient records in JSON format."""
        patients = Patient.query.order_by(Patient.id.asc()).all()
        return jsonify({
            'success': True,
            'count': len(patients),
            'patients': [p.to_dict() for p in patients]
        }), 200

    @app.route('/api/patients/<int:patient_id>', methods=['GET'])
    def api_get_patient(patient_id):
        """Return an individual patient record in JSON format."""
        patient = db.session.get(Patient, patient_id)
        if not patient:
            return jsonify({'success': False, 'error': f'Patient #{patient_id} not found'}), 404
        return jsonify({
            'success': True,
            'patient': patient.to_dict()
        }), 200

    # -------------------------------------------------------------
    # ERROR HANDLERS (Safe, no stack traces exposed)
    # -------------------------------------------------------------

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        logger.error("Internal Server Error: %s", error)
        return render_template('errors/500.html'), 500

    return app


# Create application instance for WSGI servers and Flask CLI
app = create_app()

if __name__ == '__main__':
    # Run development server
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'
    print(f"\n* HealthPredict AI starting on http://127.0.0.1:{port}")
    print(f"* Medical Disclaimer active across all interfaces.\n")
    app.run(host='127.0.0.1', port=port, debug=debug_mode)

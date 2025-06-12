from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from flask_login import current_user, login_required
from app.routes.auth_routes import role_required
from app.models.db_utils import (
    create_grievance, get_student_grievances, get_grievance_by_id, 
    get_all_departments, create_department
)
from app.models.email_utils import send_new_grievance_notification
from werkzeug.utils import secure_filename
import os
import uuid

student_bp = Blueprint('student', __name__, url_prefix='/student')

# This list will serve as a fallback if no departments are defined in the database
DEFAULT_DEPARTMENTS = [
    'Academic Administration',
    'Admissions Office',
    'Finance Department',
    'Student Housing',
    'Financial Aid',
    'Faculty of Accounting and Informatics',
    'Faculty of Applied Sciences',
    'Faculty of Arts and Design',
    'Faculty of Engineering and the Built Environment',
    'Faculty of Health Sciences',
    'Faculty of Management Sciences',
    'Library Services',
    'IT Services',
    'International Office',
    'Student Counselling',
    'Sports Department',
    'Student Representative Council (SRC)'
]

def handle_file_upload(file, grievance_id):
    """
    Utility function to handle file upload validation and processing.
    Returns a tuple of (success, message, message_category, file_url)
    """
    if not file or not file.filename:
        return False, 'No file selected.', 'warning', None
    
    print(f"Attempting to upload file: {file.filename} for grievance: {grievance_id}")
        
    try:
        # Add more detailed logging
        print(f"File details - Name: {file.filename}, Size: {len(file.read())} bytes")
        file.seek(0)  # Reset file pointer after reading
        
        # Create directory if it doesn't exist
        upload_folder = os.path.join(current_app.root_path, 'uploads', str(grievance_id))
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save the file locally
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Create attachment record in database
        from app.models.models import db, Attachment
        attachment = Attachment(
            filename=filename,
            file_path=file_path,
            grievance_id=grievance_id
        )
        db.session.add(attachment)
        db.session.commit()
        
        # Return the local file path
        relative_path = os.path.join('uploads', str(grievance_id), filename)
        file_url = url_for('static', filename=relative_path, _external=True)
        
        print(f"Upload successful, URL: {file_url}")
        return True, f'Successfully uploaded {file.filename}', 'success', file_url
    except ValueError as ve:
        error_message = str(ve)
        print(f"Validation error during upload: {error_message}")
        return False, f'Validation error: {error_message}', 'warning', None
    except Exception as e:
        error_message = str(e)
        print(f"Unexpected error during upload: {error_message}")
        return False, f'An error occurred while uploading the file: {error_message}', 'danger', None

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    user_id = current_user.id
    grievances = get_student_grievances(user_id)
    
    # Count grievances by status
    status_counts = {
        'pending': 0,
        'in_progress': 0,
        'resolved': 0,
        'closed': 0
    }
    
    for grievance in grievances:
        status = grievance.status
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts[status] = 1
    
    return render_template('student/dashboard.html', 
                           grievances=grievances, 
                           status_counts=status_counts)

@student_bp.route('/new-grievance', methods=['GET', 'POST'])
@login_required
@role_required('student')
def new_grievance():
    # Get departments for the form
    departments_data = get_all_departments()
    
    # Create default departments if none exist
    if not departments_data:
        for dept_name in DEFAULT_DEPARTMENTS:
            create_department(dept_name, '')
        departments_data = get_all_departments()
    
    departments = [(dept.id, dept.name) for dept in departments_data]
    
    if request.method == 'POST':
        # Get form data
        description = request.form.get('description', '').strip()
        department_id = request.form.get('department', '')
        query_category = request.form.get('query_category', '')
        
        # Get user info from current_user
        user_id = current_user.id
        
        errors = []
        
        # Validate description
        if not description:
            errors.append('Description is required.')
        elif len(description) < 20:
            errors.append('Description must be at least 20 characters long.')
        elif len(description) > 3000:
            errors.append('Description must not exceed 3000 characters.')
        
        # Validate department
        if not department_id:
            errors.append('Department is required.')
        
        # Validate query category
        if not query_category:
            errors.append('Query category is required.')
        
        # Ensure department_id is an integer and valid
        from app.models.models import Department
        try:
            department_id = int(department_id)
        except (ValueError, TypeError):
            errors.append('Invalid department selected.')
            department_id = None
        department = Department.query.get(department_id) if department_id else None
        if not department:
            errors.append('Invalid department selected.')
        
        # If there are validation errors, show them and return to form
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('student/new_grievance.html', 
                                departments=departments,
                                form_data={
                                    'description': description,
                                    'department': department_id or '',
                                    'query_category': query_category
                                })
        
        try:
            # Create grievance record first
            grievance_id = create_grievance(user_id, None, description, department_id, query_category)
            if not grievance_id:
                raise ValueError("Failed to create grievance record")
            
            # Handle file uploads
            uploaded_files = []
            failed_files = []
            
            if 'attachments' in request.files:
                files = request.files.getlist('attachments')
                valid_files = [f for f in files if f and f.filename]
                total_files = len(valid_files)
                
                # Check total number of files
                if total_files > 5:
                    flash('You can upload a maximum of 5 files per grievance.', 'warning')
                    valid_files = valid_files[:5]  # Only process the first 5 files
                
                for file in valid_files:
                    try:
                        success, message, category, file_url = handle_file_upload(file, grievance_id)
                        if success:
                            uploaded_files.append(file.filename)
                        else:
                            failed_files.append((file.filename, message))
                    except Exception as e:
                        failed_files.append((file.filename, str(e)))
                
                # Provide detailed feedback about uploads
                if uploaded_files:
                    if len(uploaded_files) == total_files:
                        flash(f'Successfully uploaded all {len(uploaded_files)} attachment(s): {", ".join(uploaded_files)}', 'success')
                    else:
                        flash(f'Successfully uploaded {len(uploaded_files)} out of {total_files} files: {", ".join(uploaded_files)}', 'success')
                
                # Report failed uploads
                for filename, error in failed_files:
                    flash(f'Failed to upload {filename}: {error}', 'warning')
            
            # Send email notification
            user_email = current_user.email
            if user_email:
                try:
                    send_new_grievance_notification(user_email, grievance_id)
                except Exception as e:
                    print(f"Error sending email notification: {str(e)}")
                    # Don't show this error to the user as it's not critical
            
            # Show appropriate success message
            if not failed_files:
                flash('Your grievance has been submitted successfully!', 'success')
            else:
                flash('Your grievance has been submitted, but some attachments failed to upload.', 'warning')
            
            return redirect(url_for('student.grievance_detail', grievance_id=grievance_id))
            
        except ValueError as ve:
            print(f"Validation error in new_grievance: {str(ve)}")
            flash(str(ve), 'danger')
        except Exception as e:
            print(f"Error submitting grievance: {str(e)}")
            flash('An error occurred while submitting your grievance. Please try again.', 'danger')
        
        # If we get here, there was an error, so return to form with data
        return render_template('student/new_grievance.html', 
                            departments=departments,
                            form_data={
                                'description': description,
                                'department': department_id or '',
                                'query_category': query_category
                            })
    
    # GET request - show empty form
    return render_template('student/new_grievance.html', 
                         departments=departments,
                         form_data={
                             'description': '',
                             'department': '',
                             'query_category': ''
                         })

@student_bp.route('/grievance/<grievance_id>')
@login_required
@role_required('student')
def grievance_detail(grievance_id):
    user_id = current_user.id
    grievance = get_grievance_by_id(grievance_id)
    
    # Check if grievance exists and belongs to current user
    if not grievance or grievance.student_id != user_id:
        flash('Grievance not found.', 'danger')
        return redirect(url_for('student.dashboard'))
    
    return render_template('student/grievance_detail.html', grievance=grievance)

@student_bp.route('/add-attachment/<grievance_id>', methods=['POST'])
@login_required
@role_required('student')
def add_attachment(grievance_id):
    user_id = current_user.id
    grievance = get_grievance_by_id(grievance_id)
    
    # Check if grievance exists and belongs to current user
    if not grievance or grievance.student_id != user_id:
        flash('Grievance not found.', 'danger')
        return redirect(url_for('student.dashboard'))
    
    if 'file' not in request.files:
        flash('No file selected.', 'warning')
        return redirect(url_for('student.grievance_detail', grievance_id=grievance_id))
    
    file = request.files['file']
    
    if not file or not file.filename:
        flash('No file selected.', 'warning')
        return redirect(url_for('student.grievance_detail', grievance_id=grievance_id))
    
    success, message, category, file_url = handle_file_upload(file, grievance_id)
    flash(message, category)
    
    return redirect(url_for('student.grievance_detail', grievance_id=grievance_id)) 
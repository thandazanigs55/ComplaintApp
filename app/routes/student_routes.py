from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from app.routes.auth_routes import login_required
from app.models.firebase_utils import (
    create_grievance, get_student_grievances, get_grievance_by_id, 
    upload_attachment, get_all_departments
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
        
        file_url = upload_attachment(file, grievance_id)
        if file_url:
            print(f"Upload successful, URL: {file_url}")
            print(f"Upload successful, URL: {file_url}")
            return True, f'Successfully uploaded {file.filename}', 'success', file_url
        
        print("Upload failed: upload_attachment returned None")
        return False, 'Failed to upload attachment. Please try again.', 'danger', None
    except ValueError as ve:
        error_message = str(ve)
        print(f"Validation error during upload: {error_message}")
        return False, f'Validation error: {error_message}', 'warning', None
        error_message = str(ve)
        print(f"Validation error during upload: {error_message}")
        return False, f'Validation error: {error_message}', 'warning', None
    except Exception as e:
        error_message = str(e)
        print(f"Unexpected error during upload: {error_message}")
        return False, f'An error occurred while uploading the file: {error_message}', 'danger', None
        error_message = str(e)
        print(f"Unexpected error during upload: {error_message}")
        return False, f'An error occurred while uploading the file: {error_message}', 'danger', None

@student_bp.route('/dashboard')
@login_required(role='student')
def dashboard():
    user_id = session.get('user')
    grievances = get_student_grievances(user_id)
    
    # Count grievances by status
    status_counts = {
        'pending': 0,
        'in_progress': 0,
        'resolved': 0,
        'closed': 0
    }
    
    for grievance in grievances:
        status = grievance.get('status', 'pending')
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts[status] = 1
    
    return render_template('student/dashboard.html', 
                           grievances=grievances, 
                           status_counts=status_counts)

@student_bp.route('/new-grievance', methods=['GET', 'POST'])
@login_required(role='student')
def new_grievance():
    # Get departments for the form
    departments_data = get_all_departments()
    departments = [dept['name'] for dept in departments_data] if departments_data else DEFAULT_DEPARTMENTS
    
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        department = request.form.get('department', '').strip()
        
        # Get user info from session
        user_id = session.get('user')
        if not user_id:
            flash('Your session has expired. Please log in again.', 'danger')
            return redirect(url_for('auth.login'))
        
        errors = []
        
        # Validate title
        if not title:
            errors.append('Title is required.')
        elif len(title) < 5:
            errors.append('Title must be at least 5 characters long.')
        elif len(title) > 200:
            errors.append('Title must not exceed 200 characters.')
            
        # Validate description
        if not description:
            errors.append('Description is required.')
        elif len(description) < 20:
            errors.append('Description must be at least 20 characters long.')
        elif len(description) > 3000:
            errors.append('Description must not exceed 3000 characters.')
            
        # Validate department
        if not department:
            errors.append('Department is required.')
        elif department not in departments:
            errors.append('Please select a valid department.')
        
        # If there are validation errors, show them and return to form
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('student/new_grievance.html', 
                                departments=departments,
                                form_data={
                                    'title': title,
                                    'description': description,
                                    'department': department
                                })
        
        try:
            # Create grievance record first
            grievance_id = create_grievance(user_id, title, description, department)
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
            user_email = session.get('email')
            if user_email:
                try:
                    send_new_grievance_notification(user_email, grievance_id, title)
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
                                'title': title,
                                'description': description,
                                'department': department
                            })
    
    # GET request - show empty form
    return render_template('student/new_grievance.html', 
                         departments=departments,
                         form_data={
                             'title': '',
                             'description': '',
                             'department': ''
                         })

@student_bp.route('/grievance/<grievance_id>')
@login_required(role='student')
def grievance_detail(grievance_id):
    user_id = session.get('user')
    grievance = get_grievance_by_id(grievance_id)
    
    # Check if grievance exists and belongs to current user
    if not grievance or grievance.get('studentId') != user_id:
        flash('Grievance not found.', 'danger')
        return redirect(url_for('student.dashboard'))
    
    return render_template('student/grievance_detail.html', grievance=grievance)

@student_bp.route('/add-attachment/<grievance_id>', methods=['POST'])
@login_required(role='student')
def add_attachment(grievance_id):
    user_id = session.get('user')
    grievance = get_grievance_by_id(grievance_id)
    
    # Check if grievance exists and belongs to current user
    if not grievance or grievance.get('studentId') != user_id:
        flash('Grievance not found.', 'danger')
        return redirect(url_for('student.dashboard'))
    
    # Check if grievance is closed
    if grievance.get('status') == 'closed':
        flash('Cannot add attachments to a closed grievance.', 'warning')
        return redirect(url_for('student.grievance_detail', grievance_id=grievance_id))
    
    # Handle file upload
    if 'attachment' not in request.files:
        flash('No file part in the request.', 'danger')
        return redirect(url_for('student.grievance_detail', grievance_id=grievance_id))
    
    file = request.files['attachment']
    success, message, category, file_url = handle_file_upload(file, grievance_id)
    flash(message, category)
    
    return redirect(url_for('student.grievance_detail', grievance_id=grievance_id)) 
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.routes.auth_routes import login_required
from app.models.firebase_utils import (
    get_department_grievances, get_grievance_by_id,
    submit_department_response, get_user_by_id
)

department_bp = Blueprint('department', __name__, url_prefix='/department')

@department_bp.route('/dashboard')
@login_required(role='department')
def dashboard():
    """Department dashboard showing assigned grievances"""
    # Get department ID from session
    department_id = session.get('user_id')
    department = get_user_by_id(department_id)
    
    if not department:
        flash('Department not found.', 'danger')
        return redirect(url_for('auth.logout'))
    
    # Get grievances assigned to this department
    grievances = get_department_grievances(department.get('displayName', ''))
    
    return render_template('department/dashboard.html',
                         department=department,
                         grievances=grievances)

@department_bp.route('/grievance/<grievance_id>')
@login_required(role='department')
def view_grievance(grievance_id):
    """View a specific grievance and its details"""
    department_id = session.get('user_id')
    department = get_user_by_id(department_id)
    
    if not department:
        flash('Department not found.', 'danger')
        return redirect(url_for('auth.logout'))
    
    grievance = get_grievance_by_id(grievance_id)
    
    if not grievance:
        flash('Grievance not found.', 'danger')
        return redirect(url_for('department.dashboard'))
    
    # Check if grievance belongs to this department
    if grievance.get('department') != department.get('displayName'):
        flash('You do not have permission to view this grievance.', 'danger')
        return redirect(url_for('department.dashboard'))
    
    # Get student information
    student_id = grievance.get('studentId')
    student = get_user_by_id(student_id) if student_id else None
    
    return render_template('department/grievance_detail.html',
                         grievance=grievance,
                         department=department,
                         student=student)

@department_bp.route('/grievance/<grievance_id>/respond', methods=['POST'])
@login_required(role='department')
def submit_response(grievance_id):
    """Submit a response to a grievance"""
    department_id = session.get('user_id')
    department = get_user_by_id(department_id)
    
    if not department:
        flash('Department not found.', 'danger')
        return redirect(url_for('auth.logout'))
    
    response_text = request.form.get('response')
    
    if not response_text:
        flash('Response text is required.', 'danger')
        return redirect(url_for('department.view_grievance', grievance_id=grievance_id))
    
    # Submit the response
    success = submit_department_response(
        grievance_id=grievance_id,
        response_text=response_text,
        department_id=department_id
    )
    
    if success:
        flash('Response submitted successfully.', 'success')
    else:
        flash('Failed to submit response.', 'danger')
    
    return redirect(url_for('department.view_grievance', grievance_id=grievance_id)) 
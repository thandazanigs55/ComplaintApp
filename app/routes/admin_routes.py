from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.routes.auth_routes import role_required
from app.models.db_utils import (
    get_all_grievances, get_grievance_by_id, update_grievance_status,
    get_department_grievances, get_user_by_id, get_all_departments,
    create_department, update_department, delete_department, get_department_by_id,
    get_all_users, get_users_by_role, update_user, delete_user,
    get_student_grievances, get_open_grievances, get_resolved_grievances
)
from app.models.email_utils import send_grievance_status_update
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Status options for grievances
STATUS_OPTIONS = {
    'pending': 'Pending',
    'in_progress': 'In Progress',
    'assigned': 'Assigned to Department',
    'under_review': 'Under Review',
    'resolved': 'Resolved',
    'closed': 'Closed'
}

@admin_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    grievances = get_all_grievances()
    
    # Count grievances by status and department
    status_counts = {status: 0 for status in STATUS_OPTIONS.keys()}
    department_counts = {}
    
    for grievance in grievances:
        status = grievance.status
        department = grievance.department.name if grievance.department else 'Unknown'
        
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts[status] = 1
            
        if department in department_counts:
            department_counts[department] += 1
        else:
            department_counts[department] = 1
    
    return render_template('admin/dashboard.html', 
                          grievances=grievances, 
                          status_counts=status_counts,
                          department_counts=department_counts,
                          status_options=STATUS_OPTIONS)

@admin_bp.route('/grievance/<grievance_id>')
@login_required
@role_required('admin')
def grievance_detail(grievance_id):
    grievance = get_grievance_by_id(grievance_id)
    
    if not grievance:
        flash('Grievance not found.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Get student information
    student_id = grievance.student_id
    student = get_user_by_id(student_id) if student_id else None
    
    return render_template('admin/grievance_detail.html', 
                          grievance=grievance, 
                          student=student,
                          status_options=STATUS_OPTIONS)

@admin_bp.route('/update-status/<grievance_id>', methods=['POST'])
@login_required
@role_required('admin')
def update_status(grievance_id):
    new_status = request.form.get('status')
    note = request.form.get('note', '')
    
    if not new_status or new_status not in STATUS_OPTIONS:
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin.grievance_detail', grievance_id=grievance_id))
    
    # Update grievance status
    grievance = update_grievance_status(grievance_id, new_status, note)
    
    if grievance:
        # Get student's email for notification
        student = get_user_by_id(grievance.student_id)
        if student:
            # Send email notification
            send_grievance_status_update(student.email, grievance_id, STATUS_OPTIONS[new_status], grievance.title or "")
        
        flash('Grievance status updated successfully.', 'success')
    else:
        flash('Failed to update grievance status.', 'danger')
    
    return redirect(url_for('admin.grievance_detail', grievance_id=grievance_id))

@admin_bp.route('/department-grievances')
@login_required
@role_required('admin')
def list_department_grievances():
    department_id = request.args.get('department')
    
    if not department_id:
        return redirect(url_for('admin.dashboard'))
    
    department = get_department_by_id(department_id)
    if not department:
        flash('Department not found.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    grievances = get_department_grievances(department_id)
    
    return render_template('admin/department_grievances.html', 
                          grievances=grievances, 
                          department=department,
                          status_options=STATUS_OPTIONS)

@admin_bp.route('/reports')
@login_required
@role_required('admin')
def reports():
    # Get all grievances
    grievances = get_all_grievances()
    
    # Create reports data
    status_counts = {status: 0 for status in STATUS_OPTIONS.keys()}
    department_counts = defaultdict(int)
    monthly_counts = defaultdict(int)
    
    for grievance in grievances:
        # Count by status
        status = grievance.status
        if status in status_counts:
            status_counts[status] += 1
        
        # Count by department
        department = grievance.department.name if grievance.department else 'Unknown'
        department_counts[department] += 1
        
        # Count by month (if created_at is available)
        if grievance.created_at:
            month_key = grievance.created_at.strftime('%Y-%m')
            monthly_counts[month_key] += 1
    
    # Sort monthly counts chronologically
    sorted_monthly_counts = dict(sorted(monthly_counts.items()))
    
    return render_template('admin/reports.html', 
                          status_counts=status_counts,
                          department_counts=dict(department_counts),
                          monthly_counts=sorted_monthly_counts,
                          status_options=STATUS_OPTIONS)

# Department Management Routes
@admin_bp.route('/departments')
@login_required
@role_required('admin')
def departments():
    """List all departments"""
    departments = get_all_departments()
    return render_template('admin/departments.html', departments=departments)

@admin_bp.route('/departments/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_dept():
    """Add a new department"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not name:
            flash('Department name is required.', 'danger')
            return redirect(url_for('admin.add_dept'))
        
        try:
            dept_id = create_department(name, description)
            flash(f'Department "{name}" added successfully.', 'success')
            return redirect(url_for('admin.departments'))
        except Exception as e:
            flash(f'Failed to add department: {str(e)}', 'danger')
            
    return render_template('admin/add_department.html')

@admin_bp.route('/departments/edit/<dept_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_dept(dept_id):
    """Edit an existing department"""
    department = get_department_by_id(dept_id)
    if not department:
        flash('Department not found.', 'danger')
        return redirect(url_for('admin.departments'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not name:
            flash('Department name is required.', 'danger')
            return redirect(url_for('admin.edit_dept', dept_id=dept_id))
        
        try:
            updated_dept = update_department(dept_id, name, description)
            if updated_dept:
                flash('Department updated successfully.', 'success')
                return redirect(url_for('admin.departments'))
            else:
                flash('Failed to update department.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('admin/edit_department.html', department=department)

@admin_bp.route('/departments/delete/<dept_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_dept(dept_id):
    """Delete a department"""
    try:
        result = delete_department(dept_id)
        if result:
            flash('Department deleted successfully', 'success')
        else:
            flash('Cannot delete department with associated grievances', 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.departments'))

@admin_bp.route('/department-grievances/<dept_id>')
@login_required
@role_required('admin')
def view_department_grievances(dept_id):
    """View grievances for a specific department"""
    department = get_department_by_id(dept_id)
    if not department:
        flash('Department not found.', 'danger')
        return redirect(url_for('admin.departments'))
    
    grievances = get_department_grievances(dept_id)
    
    return render_template(
        'admin/grievances.html', 
        grievances=grievances,
        department=department,
        title=f'Grievances for {department.name}',
        status_options=STATUS_OPTIONS
    )

# User Management Routes
@admin_bp.route('/users')
@login_required
@role_required('admin')
def users():
    """List all users"""
    users = get_all_users()
    admin_count = len([u for u in users if u.role == 'admin'])
    student_count = len([u for u in users if u.role == 'student'])
    
    return render_template(
        'admin/users.html',
        users=users,
        admin_count=admin_count,
        student_count=student_count
    )

@admin_bp.route('/users/students')
@login_required
@role_required('admin')
def student_users():
    """List student users"""
    students = get_users_by_role('student')
    return render_template(
        'admin/users.html',
        users=students,
        title='Student Users',
        filter_role='student'
    )

@admin_bp.route('/users/edit/<user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    """Edit a user's information"""
    user = get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.users'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        display_name = request.form.get('display_name')
        role = request.form.get('role')
        
        if not email or not display_name or not role:
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        data = {
            'email': email,
            'display_name': display_name,
            'role': role
        }
        
        try:
            updated_user = update_user(user_id, data)
            if updated_user:
                flash('User updated successfully.', 'success')
                return redirect(url_for('admin.users'))
            else:
                flash('Failed to update user.', 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/users/reset-password/<user_id>', methods=['POST'])
@login_required
@role_required('admin')
def reset_password(user_id):
    """Reset a user's password"""
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    if not password or not confirm_password:
        flash('Password fields are required.', 'danger')
        return redirect(url_for('admin.users'))
    
    if password != confirm_password:
        flash('Passwords do not match.', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        user = get_user_by_id(user_id)
        if user:
            user.set_password(password)
            flash('Password reset successfully.', 'success')
            return redirect(url_for('admin.users'))
        else:
            flash('User not found.', 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/delete/<user_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user_route(user_id):
    """Delete a user"""
    try:
        result = delete_user(user_id)
        if result:
            flash('User deleted successfully.', 'success')
        else:
            flash('Cannot delete user with associated grievances.', 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/student-grievances/<student_id>')
@login_required
@role_required('admin')
def student_grievances(student_id):
    """View grievances for a specific student"""
    student = get_user_by_id(student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin.users'))
    
    grievances = get_student_grievances(student_id)
    
    # Group grievances by status
    status_groups = defaultdict(list)
    for grievance in grievances:
        status_groups[grievance.status].append(grievance)
    
    return render_template(
        'admin/student_grievances.html',
        student=student,
        grievances=grievances,
        status_groups=status_groups,
        status_options=STATUS_OPTIONS,
        total_count=len(grievances)
    )

@admin_bp.route('/grievances/open')
@login_required
@role_required('admin')
def open_grievances():
    """View all open grievances"""
    grievances = get_open_grievances()
    
    return render_template(
        'admin/grievances.html',
        grievances=grievances,
        title='Open Grievances',
        status_options=STATUS_OPTIONS
    )

@admin_bp.route('/grievances/resolved')
@login_required
@role_required('admin')
def resolved_grievances():
    """View all resolved grievances"""
    grievances = get_resolved_grievances()
    
    return render_template(
        'admin/grievances.html',
        grievances=grievances,
        title='Resolved Grievances',
        status_options=STATUS_OPTIONS
    )

@admin_bp.route('/grievances/all')
@login_required
@role_required('admin')
def all_grievances():
    """View all grievances"""
    grievances = get_all_grievances()
    
    return render_template(
        'admin/grievances.html',
        grievances=grievances,
        title='All Grievances',
        status_options=STATUS_OPTIONS
    ) 
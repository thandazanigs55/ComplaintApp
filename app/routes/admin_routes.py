from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from app.routes.auth_routes import login_required
from app.models.firebase_utils import (
    get_all_grievances, get_grievance_by_id, update_grievance_status,
    get_department_grievances, get_user_by_id, get_all_departments,
    add_department, update_department, delete_department, get_department_by_id,
    get_all_users, get_users_by_role, update_user, delete_user, reset_user_password,
    get_student_grievances, get_open_grievances, get_resolved_grievances
)
from app.models.email_utils import send_grievance_status_update
import firebase_admin
from firebase_admin import firestore

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
@login_required(role='admin')
def dashboard():
    grievances = get_all_grievances()
    
    # Count grievances by status and department
    status_counts = {status: 0 for status in STATUS_OPTIONS.keys()}
    department_counts = {}
    
    for grievance in grievances:
        status = grievance.get('status', 'pending')
        department = grievance.get('department', 'Unknown')
        
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
@login_required(role='admin')
def grievance_detail(grievance_id):
    grievance = get_grievance_by_id(grievance_id)
    
    if not grievance:
        flash('Grievance not found.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    # Get student information
    student_id = grievance.get('studentId')
    student = get_user_by_id(student_id) if student_id else None
    
    return render_template('admin/grievance_detail.html', 
                          grievance=grievance, 
                          student=student,
                          status_options=STATUS_OPTIONS)

@admin_bp.route('/update-status/<grievance_id>', methods=['POST'])
@login_required(role='admin')
def update_status(grievance_id):
    new_status = request.form.get('status')
    note = request.form.get('note', '')
    
    if not new_status or new_status not in STATUS_OPTIONS:
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin.grievance_detail', grievance_id=grievance_id))
    
    # Update grievance status
    success = update_grievance_status(grievance_id, new_status, note)
    
    if success:
        # Get grievance details for email notification
        grievance = get_grievance_by_id(grievance_id)
        if grievance:
            student_id = grievance.get('studentId')
            title = grievance.get('title', 'Untitled Grievance')
            
            # Get student's email
            student = get_user_by_id(student_id) if student_id else None
            if student and 'email' in student:
                # Send email notification
                send_grievance_status_update(student['email'], grievance_id, STATUS_OPTIONS[new_status], title)
        
        flash('Grievance status updated successfully.', 'success')
    else:
        flash('Failed to update grievance status.', 'danger')
    
    return redirect(url_for('admin.grievance_detail', grievance_id=grievance_id))

@admin_bp.route('/department-grievances')
@login_required(role='admin')
def list_department_grievances():
    department = request.args.get('department')
    
    if not department:
        return redirect(url_for('admin.dashboard'))
    
    grievances = get_department_grievances(department)
    
    return render_template('admin/department_grievances.html', 
                          grievances=grievances, 
                          department=department,
                          status_options=STATUS_OPTIONS)

@admin_bp.route('/reports')
@login_required(role='admin')
def reports():
    # Get all grievances
    grievances = get_all_grievances()
    
    # Create reports data
    status_counts = {status: 0 for status in STATUS_OPTIONS.keys()}
    department_counts = {}
    monthly_counts = {}
    
    for grievance in grievances:
        # Count by status
        status = grievance.get('status', 'pending')
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts[status] = 1
        
        # Count by department
        department = grievance.get('department', 'Unknown')
        if department in department_counts:
            department_counts[department] += 1
        else:
            department_counts[department] = 1
        
        # Count by month (if createdAt is available)
        if 'createdAt' in grievance and grievance['createdAt']:
            created_at = grievance['createdAt']
            
            # If created_at is already a datetime object, use it directly
            if hasattr(created_at, 'strftime'):
                month_key = created_at.strftime('%Y-%m')
                if month_key in monthly_counts:
                    monthly_counts[month_key] += 1
                else:
                    monthly_counts[month_key] = 1
            else:
                # Try to convert string to datetime
                try:
                    from datetime import datetime
                    if isinstance(created_at, str):
                        # Try different date formats
                        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                            try:
                                dt = datetime.strptime(created_at[:19], fmt)
                                month_key = dt.strftime('%Y-%m')
                                if month_key in monthly_counts:
                                    monthly_counts[month_key] += 1
                                else:
                                    monthly_counts[month_key] = 1
                                break
                            except ValueError:
                                continue
                except Exception as e:
                    print(f"Error processing date {created_at}: {e}")
                    continue
    
    # Sort monthly counts by date
    monthly_counts = dict(sorted(monthly_counts.items()))
    
    return render_template('admin/reports.html', 
                          status_counts=status_counts,
                          department_counts=department_counts,
                          monthly_counts=monthly_counts,
                          status_options=STATUS_OPTIONS)

# Department Management Routes
@admin_bp.route('/departments')
@login_required(role='admin')
def departments():
    """List all departments"""
    departments = get_all_departments()
    return render_template('admin/departments.html', departments=departments)

@admin_bp.route('/departments/add', methods=['GET', 'POST'])
@login_required(role='admin')
def add_dept():
    """Add a new department"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        
        if not name:
            flash('Department name is required.', 'danger')
            return redirect(url_for('admin.add_dept'))
        
        success, result = add_department(name, description)
        
        if success:
            flash(f'Department "{name}" added successfully.', 'success')
            return redirect(url_for('admin.departments'))
        else:
            flash(f'Failed to add department: {result}', 'danger')
            
    return render_template('admin/add_department.html')

@admin_bp.route('/departments/edit/<dept_id>', methods=['GET', 'POST'])
@login_required(role='admin')
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
        
        success, message = update_department(dept_id, name, description)
        
        if success:
            flash('Department updated successfully.', 'success')
            return redirect(url_for('admin.departments'))
        else:
            flash(f'Failed to update department: {message}', 'danger')
    
    return render_template('admin/edit_department.html', department=department)

@admin_bp.route('/departments/delete/<dept_id>', methods=['POST'])
@login_required(role='admin')
def delete_dept(dept_id):
    """Delete a department"""
    try:
        success, message = delete_department(dept_id)
        if success:
            flash('Department deleted successfully', 'success')
        else:
            flash(message, 'danger')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('admin.departments'))

@admin_bp.route('/department-grievances/<department>')
@login_required(role='admin')
def view_department_grievances(department):
    """View grievances for a specific department"""
    grievances = get_all_grievances()
    # Filter grievances by department
    dept_grievances = [g for g in grievances if g.get('department') == department]
    
    return render_template(
        'admin/grievances.html', 
        grievances=dept_grievances,
        title=f"{department} Grievances",
        filter_type="department",
        filter_value=department
    )

# User Management Routes

@admin_bp.route('/users')
@login_required(role='admin')
def users():
    """View and manage all users"""
    all_users = get_all_users()
    
    # You could filter users by role
    role = request.args.get('role', 'all')
    if role != 'all':
        filtered_users = [user for user in all_users if user.get('role') == role]
    else:
        filtered_users = all_users
    
    return render_template(
        'admin/users.html',
        users=filtered_users,
        current_filter=role
    )

@admin_bp.route('/users/students')
@login_required(role='admin')
def student_users():
    """View and manage student users specifically"""
    students = get_users_by_role('student')
    
    return render_template(
        'admin/users.html',
        users=students,
        current_filter='student',
        title='Student Users'
    )

@admin_bp.route('/users/edit/<user_id>', methods=['GET', 'POST'])
@login_required(role='admin')
def edit_user(user_id):
    """Edit a user's information"""
    # Get all users
    all_users = get_all_users()
    
    # Find the specific user
    user = next((u for u in all_users if u.get('id') == user_id), None)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.users'))
    
    if request.method == 'POST':
        # Update user information
        data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'role': request.form.get('role'),
            # Add other fields as needed
        }
        
        success = update_user(user_id, data)
        
        if success:
            flash('User updated successfully', 'success')
            return redirect(url_for('admin.users'))
        else:
            flash('Failed to update user', 'danger')
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/users/reset-password/<user_id>', methods=['POST'])
@login_required(role='admin')
def reset_password(user_id):
    """Reset a user's password"""
    password = request.form.get('password')
    
    if not password:
        flash('Password is required', 'danger')
        return redirect(url_for('admin.edit_user', user_id=user_id))
    
    success, message = reset_user_password(user_id, password)
    
    if success:
        flash('Password reset successfully', 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin.edit_user', user_id=user_id))

@admin_bp.route('/users/delete/<user_id>', methods=['POST'])
@login_required(role='admin')
def delete_user_route(user_id):
    """Delete a user"""
    success, message = delete_user(user_id)
    
    if success:
        flash('User deleted successfully', 'success')
        return redirect(url_for('admin.users'))
    else:
        flash(message, 'danger')
        return redirect(url_for('admin.edit_user', user_id=user_id))

@admin_bp.route('/student-grievances/<student_id>')
@login_required(role='admin')
def student_grievances(student_id):
    """View grievances for a specific student"""
    # Get all users
    all_users = get_all_users()
    
    # Find the specific student
    student = next((u for u in all_users if u.get('id') == student_id), None)
    
    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('admin.users'))
    
    # Get student's grievances
    grievances = get_student_grievances(student_id)
    
    return render_template(
        'admin/grievances.html', 
        grievances=grievances,
        title=f"Grievances from {student.get('name')}",
        filter_type="student",
        filter_value=student_id
    )

@admin_bp.route('/grievances/open')
@login_required(role='admin')
def open_grievances():
    """View all open grievances"""
    grievances = get_open_grievances()
    return render_template(
        'admin/grievances.html',
        grievances=grievances,
        title="Open Grievances",
        filter_type="status",
        filter_value="open"
    )

@admin_bp.route('/grievances/resolved')
@login_required(role='admin')
def resolved_grievances():
    """View all resolved grievances"""
    grievances = get_resolved_grievances()
    return render_template(
        'admin/grievances.html',
        grievances=grievances,
        title="Resolved Grievances",
        filter_type="status",
        filter_value="resolved"
    )

@admin_bp.route('/grievances/all')
@login_required(role='admin')
def all_grievances():
    """View all grievances in the system"""
    grievances = get_all_grievances()
    return render_template(
        'admin/grievances.html',
        grievances=grievances,
        title="All Grievances",
        filter_type="all",
        filter_value="all"
    ) 
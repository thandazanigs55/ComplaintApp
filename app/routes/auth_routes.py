from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from app.models.db_utils import create_user, get_user_by_email, update_user
from app.models.models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def role_required(role):
    """Decorator to restrict access based on user role"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.role == role:
                flash('You do not have permission to access this page.', 'danger')
                if current_user.role == 'student':
                    return redirect(url_for('student.dashboard'))
                elif current_user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                else:
                    return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
            
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            user = get_user_by_email(email)
            
            if user and user.check_password(password):
                login_user(user)
                flash('Login successful!', 'success')
                
                if user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                else:
                    return redirect(url_for('student.dashboard'))
            else:
                flash('Invalid email or password.', 'danger')
                
        except Exception as e:
            flash('Login failed. Please try again.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        
        # Validate DUT email
        if not email.endswith('@dut4life.ac.za') and not email.endswith('@dut.ac.za'):
            flash('Please use your DUT email address to register.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Validate password match
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if user already exists
        if get_user_by_email(email):
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))
        
        try:
            # Create new user
            user_id = create_user(email, password, full_name, role='student')
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'Registration failed. {str(e)}', 'danger')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    user = current_user
    total_grievances = pending_grievances = resolved_grievances = 0
    if user.role == 'student':
        from app.models.db_utils import get_student_grievances
        grievances = get_student_grievances(user.id)
        total_grievances = len(grievances)
        pending_grievances = len([g for g in grievances if g.status == 'pending'])
        resolved_grievances = len([g for g in grievances if g.status in ['resolved', 'closed']])
    return render_template('auth/profile.html', user=user, total_grievances=total_grievances, pending_grievances=pending_grievances, resolved_grievances=resolved_grievances)

@auth_bp.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    display_name = request.form.get('display_name', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not display_name:
        flash('Name is required.', 'danger')
        return redirect(url_for('auth.profile'))

    data = {'display_name': display_name}
    if password:
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.profile'))
        data['password'] = password

    try:
        update_user(current_user.id, data)
        flash('Profile updated successfully.', 'success')
    except Exception as e:
        flash(f'Error updating profile: {str(e)}', 'danger')
    return redirect(url_for('auth.profile')) 
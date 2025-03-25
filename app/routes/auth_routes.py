from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from app.models.firebase_utils import create_user, login_user, get_user_by_id
import functools

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Decorator for requiring authentication
def login_required(role=None):
    def decorator(view):
        @functools.wraps(view)
        def wrapped_view(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('auth.login'))
            
            # If role is specified, check if the user has the required role
            if role and session.get('user_data', {}).get('role') != role:
                flash('You do not have permission to access this page.', 'danger')
                if session.get('user_data', {}).get('role') == 'student':
                    return redirect(url_for('student.dashboard'))
                elif session.get('user_data', {}).get('role') == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif session.get('user_data', {}).get('role') == 'department':
                    return redirect(url_for('department.dashboard'))
                else:
                    return redirect(url_for('auth.login'))
            
            return view(*args, **kwargs)
        return wrapped_view
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Basic validation
        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('auth/login.html')
            
        # Validate DUT email
        if not email.endswith('@dut4life.ac.za') and not email.endswith('@dut.ac.za'):
            flash('Please use your DUT email address to login.', 'danger')
            return render_template('auth/login.html')
        
        try:
            # Authenticate user with Firebase
            user = login_user(email, password)
            user_id = user['localId']
            
            # Get user data from Firestore
            user_data = get_user_by_id(user_id)
            
            if not user_data:
                flash('Account exists but user data not found. Please contact IT Helpdesk.', 'danger')
                return render_template('auth/login.html')
            
            # Store user info in session
            session['user'] = user_id
            session['user_data'] = user_data
            session['email'] = email
            session['role'] = user_data.get('role', '')
            
            # Redirect based on user role
            if user_data.get('role') == 'admin':
                flash('Welcome back, Administrator!', 'success')
                return redirect(url_for('admin.dashboard'))
            elif user_data.get('role') == 'student':
                flash(f'Welcome back, {user_data.get("displayName", "Student")}!', 'success')
                return redirect(url_for('student.dashboard'))
            elif user_data.get('role') == 'department':
                flash(f'Welcome back, {user_data.get("displayName", "Department")} Team!', 'success')
                return redirect(url_for('department.dashboard'))
            else:
                flash('Invalid user role. Please contact IT Helpdesk.', 'danger')
                session.clear()
                return render_template('auth/login.html')
            
        except ValueError as e:
            error_msg = str(e)
            print(f"Login error: {error_msg}")
            
            # Use the specific error message from Firebase utils
            flash(error_msg, 'danger')
            return render_template('auth/login.html')
            
        except Exception as e:
            error_msg = str(e)
            print(f"Unexpected login error: {error_msg}")
            flash('An unexpected error occurred. Please try again later.', 'danger')
            return render_template('auth/login.html')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
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
        
        try:
            # Create user with Firebase Authentication
            user_id = create_user(email, password, full_name, role='student')
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'Registration failed. {str(e)}', 'danger')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    # Clear session
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required()
def profile():
    user_data = session.get('user_data', {})
    return render_template('auth/profile.html', user=user_data) 
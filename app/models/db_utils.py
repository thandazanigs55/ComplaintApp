from datetime import datetime
import os
from werkzeug.utils import secure_filename
from .models import db, User, Department, Grievance, Attachment, StatusUpdate

# User Management Functions
def create_user(email, password, display_name, role='student'):
    """Create a new user"""
    try:
        user = User(
            email=email,
            display_name=display_name,
            role=role
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id
    except Exception as e:
        db.session.rollback()
        raise e

def get_user_by_id(user_id):
    """Get user by ID"""
    return User.query.get(user_id)

def get_user_by_email(email):
    """Get user by email"""
    return User.query.filter_by(email=email).first()

def get_all_users():
    """Get all users"""
    return User.query.all()

def get_users_by_role(role):
    """Get users by role"""
    return User.query.filter_by(role=role).all()

def update_user(user_id, data):
    """Update user information"""
    try:
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
            
        if 'email' in data:
            user.email = data['email']
        if 'display_name' in data:
            user.display_name = data['display_name']
        if 'role' in data:
            user.role = data['role']
        if 'password' in data:
            user.set_password(data['password'])
            
        db.session.commit()
        return user
    except Exception as e:
        db.session.rollback()
        raise e

def delete_user(user_id):
    """Delete a user"""
    try:
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

# Department Management Functions
def create_department(name, description=''):
    """Create a new department"""
    try:
        dept = Department(name=name, description=description)
        db.session.add(dept)
        db.session.commit()
        return dept.id
    except Exception as e:
        db.session.rollback()
        raise e

def get_all_departments():
    """Get all departments"""
    return Department.query.all()

def get_department_by_id(dept_id):
    """Get department by ID"""
    return Department.query.get(dept_id)

def update_department(dept_id, name, description):
    """Update department information"""
    try:
        dept = Department.query.get(dept_id)
        if not dept:
            raise ValueError("Department not found")
            
        dept.name = name
        dept.description = description
        db.session.commit()
        return dept
    except Exception as e:
        db.session.rollback()
        raise e

def delete_department(dept_id):
    """Delete a department if all linked grievances are resolved or closed."""
    try:
        from .models import Grievance  # Import here to avoid circular import
        dept = Department.query.get(dept_id)
        if dept:
            grievances = Grievance.query.filter_by(department_id=dept_id).all()
            # Only allow deletion if all grievances are resolved or closed
            for g in grievances:
                if g.status not in ['resolved', 'closed']:
                    raise Exception("Cannot delete department with open grievances. Only allowed if all are resolved or closed.")
            # Delete all grievances for this department
            for g in grievances:
                db.session.delete(g)
            db.session.delete(dept)
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        raise e

# Grievance Management Functions
def create_grievance(student_id, title, description, department_id, query_category, attachments=None):
    """Create a new grievance"""
    try:
        if not title:
            title = ''
        grievance = Grievance(
            student_id=student_id,
            title=title,
            description=description,
            department_id=department_id,
            query_category=query_category,
            status='pending'
        )
        db.session.add(grievance)
        
        # Add initial status update
        status_update = StatusUpdate(
            grievance=grievance,
            status='pending',
            note='Grievance submitted'
        )
        db.session.add(status_update)
        
        # Handle attachments
        if attachments:
            for attachment in attachments:
                filename = secure_filename(attachment.filename)
                file_path = os.path.join('uploads', filename)
                attachment.save(file_path)
                
                attach = Attachment(
                    filename=filename,
                    file_path=file_path,
                    grievance=grievance
                )
                db.session.add(attach)
        
        db.session.commit()
        return grievance.id
    except Exception as e:
        db.session.rollback()
        raise e

def get_grievance_by_id(grievance_id):
    """Get grievance by ID"""
    return Grievance.query.get(grievance_id)

def get_student_grievances(student_id):
    """Get all grievances for a student"""
    return Grievance.query.filter_by(student_id=student_id).all()

def get_department_grievances(department_id):
    """Get all grievances for a department"""
    return Grievance.query.filter_by(department_id=department_id).all()

def get_all_grievances():
    """Get all grievances"""
    return Grievance.query.all()

def get_open_grievances():
    """Get all open grievances"""
    return Grievance.query.filter(Grievance.status != 'resolved').all()

def get_resolved_grievances():
    """Get all resolved grievances"""
    return Grievance.query.filter_by(status='resolved').all()

def update_grievance_status(grievance_id, new_status, note=None):
    """Update grievance status"""
    try:
        grievance = Grievance.query.get(grievance_id)
        if not grievance:
            raise ValueError("Grievance not found")
            
        grievance.status = new_status
        grievance.updated_at = datetime.utcnow()
        
        # Add status update
        status_update = StatusUpdate(
            grievance=grievance,
            status=new_status,
            note=note
        )
        db.session.add(status_update)
        
        db.session.commit()
        return grievance
    except Exception as e:
        db.session.rollback()
        raise e 
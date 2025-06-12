#!/usr/bin/env python
"""
Create Test User Script for DUT Student Grievance Management System

This script creates a test admin user with predefined credentials, without requiring interactive input.
"""

import os
import sys
from flask import Flask
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app():
    """Create a Flask application for database setup"""
    app = Flask(__name__)
    
    # Create instance directory if it doesn't exist
    os.makedirs('instance', exist_ok=True)
    
    # Use absolute path for SQLite database
    db_path = os.path.abspath(os.path.join('instance', 'app.db'))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Import models
    from app.models.models import db, User
    
    # Initialize extensions
    db.init_app(app)
    
    return app, db

def main():
    """Main function to create a test user without prompts"""
    print("\n" + "="*70)
    print("DUT Student Grievance Management System - Create Test User")
    print("="*70)
    
    # Initialize Flask application
    app, db = create_app()
    
    # Predefined credentials
    admin_email = "admin@dut.ac.za"
    admin_password = "Admin@123456"
    admin_name = "System Administrator"
    student_email = "student1@dut4life.ac.za"
    student_password = "Student1@123"
    student_name = "Test Student"
    
    with app.app_context():
        # Check if database file exists
        db_path = os.path.abspath(os.path.join('instance', 'app.db'))
        if not os.path.exists(db_path):
            print(f"\n❌ Database does not exist at {db_path}. Creating it now.")
            
            # Create the instance directory if it doesn't exist
            os.makedirs('instance', exist_ok=True)
            
            # Create tables
            db.create_all()
            print(f"\n✅ Database created successfully at {db_path}.")
        
        # Import after db setup to avoid circular imports
        try:
            from app.models.db_utils import create_user, get_user_by_email
            from app.models.models import User
        except ImportError as e:
            print(f"Error importing required modules: {e}")
            print("Make sure you're running this script from the project root directory.")
            sys.exit(1)
        
        # Create admin user if not exists
        existing_admin = get_user_by_email(admin_email)
        if not existing_admin:
            try:
                admin_id = create_user(admin_email, admin_password, admin_name, role='admin')
                print(f"\n✅ Admin user created successfully!")
                print(f"  User ID: {admin_id}")
                print(f"  Email: {admin_email}")
                print(f"  Password: {admin_password}")
            except Exception as e:
                print(f"\n❌ Error creating admin user: {e}")
        else:
            print(f"\n✓ Admin user already exists: {admin_email}")
        
        # Create student user if not exists
        existing_student = get_user_by_email(student_email)
        if not existing_student:
            try:
                student_id = create_user(student_email, student_password, student_name, role='student')
                print(f"\n✅ Student user created successfully!")
                print(f"  User ID: {student_id}")
                print(f"  Email: {student_email}")
                print(f"  Password: {student_password}")
            except Exception as e:
                print(f"\n❌ Error creating student user: {e}")
        else:
            print(f"\n✓ Student user already exists: {student_email}")
        
        print("\nYou can now log in using these credentials at the login page:")
        print(f"  - Admin: {admin_email} / {admin_password}")
        print(f"  - Student: {student_email} / {student_password}")

if __name__ == "__main__":
    main() 
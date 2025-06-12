#!/usr/bin/env python
"""
Seed Admin User Script for DUT Student Grievance Management System

This script creates an admin user in the SQLite database.
Run this script once to create an admin account.
"""

import os
import sys
import getpass
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
    """Main function to create an admin user"""
    print("\n" + "="*70)
    print("DUT Student Grievance Management System - Admin User Setup")
    print("="*70)
    
    # Initialize Flask application
    app, db = create_app()
    
    with app.app_context():
        # Check if database file exists
        db_path = os.path.abspath(os.path.join('instance', 'app.db'))
        if not os.path.exists(db_path):
            print(f"\n❌ Database does not exist at {db_path}. Please create it first.")
            create_db = input("Do you want to create the database now? (y/n): ").lower().strip()
            if create_db == 'y':
                # Create the instance directory if it doesn't exist
                os.makedirs('instance', exist_ok=True)
                
                # Create tables
                db.create_all()
                print(f"\n✅ Database created successfully at {db_path}.")
            else:
                print("Admin user creation cancelled.")
                sys.exit(0)
        
        # Import after db setup to avoid circular imports
        try:
            from app.models.db_utils import create_user, get_user_by_email
            from app.models.models import User
        except ImportError as e:
            print(f"Error importing required modules: {e}")
            print("Make sure you're running this script from the project root directory.")
            sys.exit(1)
        
        # Check if admin user already exists
        existing_admins = User.query.filter_by(role='admin').all()
        if existing_admins:
            print("\nExisting admin users:")
            for admin in existing_admins:
                print(f"  - {admin.display_name} ({admin.email})")
            
            create_new = input("\nDo you want to create another admin user? (y/n): ").lower().strip()
            if create_new != 'y':
                print("Admin user creation cancelled.")
                sys.exit(0)
        
        # Get admin user details
        print("\nPlease provide details for the new admin user:")
        admin_email = input("Email (default: admin@dut.ac.za): ").strip() or "admin@dut.ac.za"
        
        # Check if email already exists
        existing_user = get_user_by_email(admin_email)
        if existing_user:
            print(f"\n❌ User with email {admin_email} already exists.")
            print(f"   Role: {existing_user.role}")
            sys.exit(1)
            
        admin_name = input("Name (default: System Administrator): ").strip() or "System Administrator"
        admin_password = getpass.getpass("Admin password (default: Admin@123456): ") or "Admin@123456"
        confirm_password = getpass.getpass("Confirm password: ")
        
        if admin_password != confirm_password:
            print("\n❌ Passwords do not match.")
            sys.exit(1)
        
        # Display a warning and get confirmation
        print("\n" + "="*70)
        print("WARNING: You are about to create an admin user with the following details:")
        print(f"  Email: {admin_email}")
        print(f"  Name: {admin_name}")
        print("="*70)
        
        confirm = input("\nDo you want to continue? (y/n): ").lower().strip()
        if confirm != 'y':
            print("Admin user creation cancelled.")
            sys.exit(0)
        
        # Create admin user
        try:
            admin_id = create_user(admin_email, admin_password, admin_name, role='admin')
            print("\n✅ Admin user created successfully!")
            print(f"  User ID: {admin_id}")
            print(f"  Email: {admin_email}")
            print("\nYou can now log in using these credentials at the login page.")
        except Exception as e:
            print(f"\n❌ Error creating admin user: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main() 
#!/usr/bin/env python
"""
Database Cleaning Script for DUT Student Grievance Management System

This script cleans the database by:
1. Removing all grievances
2. Removing all users except for specified users (admin, student, manager)
3. Deleting all attachments from Firebase Storage
4. Preserving department data

Usage: python clean_db.py
"""

import os
import sys
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth, storage
from dotenv import load_dotenv
import argparse
import pyrebase


service_account = os.getenv('SERVICE_ACCOUNT')
service_account_dict = json.loads(service_account)
cred = credentials.Certificate(service_account_dict)

# Load environment variables
load_dotenv()

# Users to preserve (by email)
PRESERVE_USERS = [
    'admin@dut.ac.za',      # Admin user
    'student@dut4life.ac.za', # Student user
    'manager@dut.ac.za'     # Manager user
]

# Default departments to reset to
DEFAULT_DEPARTMENTS = [
    {'name': 'Academic Administration', 'description': 'Handles academic administrative matters'},
    {'name': 'Admissions Office', 'description': 'Manages student admissions and registration'},
    {'name': 'Finance Department', 'description': 'Handles financial matters including fees and payments'},
    {'name': 'Student Housing', 'description': 'Manages student accommodation'},
    {'name': 'Financial Aid', 'description': 'Assists with bursaries, scholarships and financial support'},
    {'name': 'Faculty of Accounting and Informatics', 'description': 'Academic department for accounting and IT programs'},
    {'name': 'Faculty of Applied Sciences', 'description': 'Academic department for science programs'},
    {'name': 'Faculty of Arts and Design', 'description': 'Academic department for arts and design programs'},
    {'name': 'Faculty of Engineering and the Built Environment', 'description': 'Academic department for engineering programs'},
    {'name': 'Faculty of Health Sciences', 'description': 'Academic department for health science programs'},
    {'name': 'Faculty of Management Sciences', 'description': 'Academic department for management programs'},
    {'name': 'Library Services', 'description': 'Manages library resources and support'},
    {'name': 'IT Services', 'description': 'Provides IT infrastructure and support'},
    {'name': 'International Office', 'description': 'Supports international students and exchange programs'},
    {'name': 'Student Counselling', 'description': 'Provides counselling and psychological support'},
    {'name': 'Sports Department', 'description': 'Manages sports facilities and activities'},
    {'name': 'Student Representative Council (SRC)', 'description': 'Student governance and representation'}
]

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if Firebase app is already initialized
        try:
            return firebase_admin.get_app()
        except ValueError:
            return firebase_admin.initialize_app(cred, {
                'storageBucket': 'studentgrievancems.appspot.com'
            })
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        sys.exit(1)

def initialize_pyrebase():
    """Initialize Pyrebase for Storage operations"""
    try:
        config = {
            "apiKey": os.getenv("Web_API_Key"),
            "authDomain": "studentgrievancems.firebaseapp.com",
            "projectId": "studentgrievancems",
            "storageBucket": "studentgrievancems.appspot.com",
            "messagingSenderId": os.getenv("MESSAGING_SENDER_ID", ""),
            "appId": os.getenv("APP_ID", ""),
            "databaseURL": "https://studentgrievancems-default-rtdb.firebaseio.com",
            "serviceAccount": service_account_dict
        }
        firebase = pyrebase.initialize_app(config)
        return firebase.storage()
    except Exception as e:
        print(f"Warning: Could not initialize Pyrebase: {e}")
        return None

def clean_grievances(db):
    """Remove all grievances from the database"""
    print("\n-- Cleaning Grievances --")
    
    try:
        # Get all grievances
        grievances = db.collection('grievances').get()
        count = len(grievances)
        
        if count == 0:
            print("  No grievances found to delete")
            return
        
        # Delete each grievance
        for grievance in grievances:
            grievance.reference.delete()
            print(f"  Deleted grievance: {grievance.id}")
        
        print(f"\n✅ Successfully deleted {count} grievances")
    except Exception as e:
        print(f"\n❌ Error cleaning grievances: {e}")

def clean_users(db):
    """Remove all users except the preserved ones"""
    print("\n-- Cleaning Users --")
    preserved_count = 0
    deleted_count = 0
    
    try:
        # Get users from Firestore
        users = db.collection('users').get()
        
        if len(users) == 0:
            print("  No users found to process")
            return
            
        # Process each user
        for user in users:
            user_data = user.to_dict()
            user_email = user_data.get('email')
            
            if not user_email:
                print(f"  Warning: User {user.id} has no email address, skipping")
                continue
                
            if user_email in PRESERVE_USERS:
                print(f"  Preserving user: {user_email}")
                preserved_count += 1
            else:
                # Delete from Firestore
                user.reference.delete()
                
                # Try to delete from Authentication as well
                try:
                    user_record = auth.get_user_by_email(user_email)
                    auth.delete_user(user_record.uid)
                    print(f"  Deleted user: {user_email}")
                    deleted_count += 1
                except Exception as auth_error:
                    print(f"  Warning: Could not delete auth record for {user_email}: {auth_error}")
                    deleted_count += 1
        
        print(f"\n✅ Successfully preserved {preserved_count} users and deleted {deleted_count} users")
    except Exception as e:
        print(f"\n❌ Error cleaning users: {e}")

def clean_storage(storage_client):
    """Remove all files from Firebase Storage"""
    print("\n-- Cleaning Storage Attachments --")
    
    if not storage_client:
        print("  Storage client not available, skipping storage cleanup")
        return
        
    try:
        # List all files in the attachments directory
        try:
            attachments_dir = storage_client.child('attachments')
            grievance_dirs = attachments_dir.list_files()
            
            file_count = 0
            for file in grievance_dirs:
                storage_client.delete(file.name)
                print(f"  Deleted file: {file.name}")
                file_count += 1
                
            if file_count == 0:
                print("  No attachments found to delete")
            else:
                print(f"\n✅ Successfully deleted {file_count} attachment files")
        except Exception as list_error:
            print(f"  Note: No attachments directory found or empty: {list_error}")
    except Exception as e:
        print(f"\n❌ Error cleaning storage: {e}")

def reset_departments(db):
    """Reset departments to default values"""
    print("\n-- Resetting Departments --")
    
    try:
        # Delete existing departments
        departments = db.collection('departments').get()
        for dept in departments:
            dept.reference.delete()
            print(f"  Deleted department: {dept.id}")
        
        # Add default departments
        for dept in DEFAULT_DEPARTMENTS:
            db.collection('departments').add(dept)
            print(f"  Added default department: {dept['name']}")
        
        print(f"\n✅ Successfully reset {len(DEFAULT_DEPARTMENTS)} departments")
    except Exception as e:
        print(f"\n❌ Error resetting departments: {e}")

def main():
    parser = argparse.ArgumentParser(description='Clean the database but preserve specific users')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--skip-storage', action='store_true', help='Skip cleaning Storage files')
    parser.add_argument('--reset-departments', action='store_true', help='Reset departments to default values')
    args = parser.parse_args()
    
    # Initialize Firebase
    app = initialize_firebase()
    db = firestore.client()
    
    # Initialize Pyrebase for storage operations
    storage_client = None if args.skip_storage else initialize_pyrebase()
    
    # Display warning and get confirmation
    if not args.force:
        print("\n" + "="*70)
        print("WARNING: You are about to clean the database.")
        print("This will DELETE:")
        print("  - ALL grievances")
        print("  - ALL users except:")
        for user in PRESERVE_USERS:
            print(f"    - {user}")
        if not args.skip_storage:
            print("  - ALL attachment files in storage")
        if args.reset_departments:
            print("  - ALL departments (will be reset to defaults)")
        print("="*70)
        
        confirm = input("\nDo you want to continue? (y/n): ").lower().strip()
        if confirm != 'y':
            print("Database cleaning cancelled.")
            sys.exit(0)
    
    # Clean the database
    clean_grievances(db)
    clean_users(db)
    
    # Clean storage if not skipped
    if not args.skip_storage:
        clean_storage(storage_client)
        
    # Reset departments if requested
    if args.reset_departments:
        reset_departments(db)
    
    print("\n✅ Database cleaning complete!")

if __name__ == "__main__":
    main() 
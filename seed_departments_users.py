#!/usr/bin/env python
"""
Seed Department Users Script for DUT Student Grievance Management System

This script creates department users in the Firebase Authentication and Firestore database.
Each department will have its own login credentials.
"""

import os
import sys
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define department credentials
DEPARTMENTS = [
    {
        'name': 'Information Technology',
        'email': 'it.dept@dut.ac.za',
        'password': 'ITDept@2024',
        'display_name': 'Information Technology Department'
    },
    {
        'name': 'Engineering',
        'email': 'engineering.dept@dut.ac.za',
        'password': 'EngDept@2024',
        'display_name': 'Engineering Department'
    },
    {
        'name': 'Business Studies',
        'email': 'business.dept@dut.ac.za',
        'password': 'BusDept@2024',
        'display_name': 'Business Studies Department'
    },
    {
        'name': 'Applied Sciences',
        'email': 'science.dept@dut.ac.za',
        'password': 'SciDept@2024',
        'display_name': 'Applied Sciences Department'
    },
    {
        'name': 'Health Sciences',
        'email': 'health.dept@dut.ac.za',
        'password': 'HealthDept@2024',
        'display_name': 'Health Sciences Department'
    }
]

def main():
    # Check if Firebase app is already initialized
    if not firebase_admin._apps:
        # Initialize Firebase Admin SDK
        try:
            cred = credentials.Certificate("service_account.json")
            firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            sys.exit(1)
    
    # Import after Firebase initialization to avoid circular imports
    try:
        from app.models.firebase_utils import create_user
    except ImportError as e:
        print(f"Error importing required modules: {e}")
        print("Make sure you're running this script from the project root directory.")
        sys.exit(1)
    
    # Display a warning and get confirmation
    print("\n" + "="*70)
    print("WARNING: You are about to create department users with the following details:")
    for dept in DEPARTMENTS:
        print(f"\nDepartment: {dept['name']}")
        print(f"  Email: {dept['email']}")
        print(f"  Password: {dept['password']}")
    print("="*70)
    
    confirm = input("\nDo you want to continue? (y/n): ").lower().strip()
    if confirm != 'y':
        print("Department users creation cancelled.")
        sys.exit(0)
    
    # Create department users
    created_users = []
    failed_users = []
    
    for dept in DEPARTMENTS:
        try:
            dept_id = create_user(
                email=dept['email'],
                password=dept['password'],
                display_name=dept['display_name'],
                role='department'
            )
            created_users.append({**dept, 'id': dept_id})
            print(f"\n✅ Created user for {dept['name']}")
        except Exception as e:
            failed_users.append({**dept, 'error': str(e)})
            print(f"\n❌ Failed to create user for {dept['name']}: {e}")
    
    # Print summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    if created_users:
        print("\nSuccessfully created users:")
        for user in created_users:
            print(f"\n{user['name']}:")
            print(f"  Email: {user['email']}")
            print(f"  Password: {user['password']}")
            print(f"  User ID: {user['id']}")
    
    if failed_users:
        print("\nFailed to create users:")
        for user in failed_users:
            print(f"\n{user['name']}:")
            print(f"  Error: {user['error']}")
    
    print("\nMake sure to save these credentials in a secure place!")
    print("Department users can now log in using these credentials at the login page.")

if __name__ == "__main__":
    main() 
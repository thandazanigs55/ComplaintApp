#!/usr/bin/env python
"""
Seed Admin User Script for DUT Student Grievance Management System

This script creates an admin user in the Firebase Authentication and Firestore database.
Run this script once to create an admin account.
"""

import os
import sys
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
    
    # Admin user credentials - CHANGE THESE VALUES
    admin_email = "admin@dut.ac.za"
    admin_password = "Admin@123456"
    admin_name = "System Administrator"
    
    # Display a warning and get confirmation
    print("\n" + "="*70)
    print("WARNING: You are about to create an admin user with the following details:")
    print(f"  Email: {admin_email}")
    print(f"  Name: {admin_name}")
    print(f"  Password: {admin_password}")
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
        print(f"  Password: {admin_password}")
        print("\nYou can now log in using these credentials at the login page.")
    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        print("\nPossible reasons:")
        print("  - User with this email may already exist")
        print("  - Firebase configuration may be incorrect")
        print("  - Password might not meet strength requirements (min 6 characters)")
        sys.exit(1)

if __name__ == "__main__":
    main() 
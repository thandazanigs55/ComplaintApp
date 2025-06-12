#!/usr/bin/env python
"""
Master Setup Script for DUT Student Grievance Management System

This script coordinates the execution of all setup scripts in the correct order:
1. Create database and basic tables
2. Create initial admin user
3. Set up uploads directory structure
4. Seed sample student data and grievances (optional)
"""

import os
import sys
import subprocess
import time

def run_script(script_name, description):
    """Run a Python script and return the success status"""
    print("\n" + "="*70)
    print(f"Running: {description}")
    print("="*70)
    
    try:
        # Get absolute path to Python executable and script
        python_exe = sys.executable
        script_path = os.path.abspath(script_name)
        
        # Run script
        result = subprocess.run([python_exe, script_path], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running {script_name}: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error running {script_name}: {e}")
        return False

def main():
    """Main function to coordinate setup scripts"""
    print("\n" + "="*70)
    print("DUT Student Grievance Management System - Master Setup")
    print("="*70)
    
    # Get absolute paths for scripts
    current_dir = os.path.dirname(os.path.abspath(__file__))
    script_paths = {
        'create_db.py': os.path.join(current_dir, 'create_db.py'),
        'setup_uploads.py': os.path.join(current_dir, 'setup_uploads.py'),
        'seed_students.py': os.path.join(current_dir, 'seed_students.py')
    }
    
    # Check if scripts exist
    missing_scripts = []
    for script, path in script_paths.items():
        if not os.path.exists(path):
            missing_scripts.append(script)
    
    if missing_scripts:
        print("\n❌ Missing required script(s):")
        for script in missing_scripts:
            print(f"  - {script}")
        sys.exit(1)
    
    # 1. Create database and tables
    if not run_script(script_paths['create_db.py'], "Database Setup"):
        print("\n❌ Database setup failed. Stopping setup process.")
        sys.exit(1)
    
    # 2. Set up uploads directory
    if not run_script(script_paths['setup_uploads.py'], "Uploads Directory Setup"):
        print("\n⚠️ Uploads directory setup failed. Continuing with caution.")
    
    # 3. Ask if user wants to seed sample data
    if os.path.exists(script_paths['seed_students.py']):
        print("\n" + "="*70)
        print("Optional: Seed Sample Data")
        print("="*70)
        
        seed_data = input("\nDo you want to add sample student data and grievances? (y/n): ").lower().strip()
        if seed_data == 'y':
            if not run_script(script_paths['seed_students.py'], "Sample Data Setup"):
                print("\n⚠️ Sample data setup failed.")
        else:
            print("\nSkipping sample data setup.")
    
    # Setup complete
    print("\n" + "="*70)
    print("✅ Setup Complete!")
    print("="*70)
    print("\nYou can now run the application with 'python run.py'")
    print("Login with the admin credentials you provided during setup.")

if __name__ == "__main__":
    main() 
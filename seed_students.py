#!/usr/bin/env python
"""
Student and Grievance Seeding Script for DUT Student Grievance Management System

This script adds sample student accounts and grievances to the database for testing.
"""

import os
import sys
import random
from datetime import datetime, timedelta
from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    """Create a Flask application for database setup"""
    app = Flask(__name__)
    
    # Use absolute path for SQLite database
    db_path = os.path.abspath(os.path.join('instance', 'app.db'))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Import models
    from app.models.models import db, User, Department, Grievance
    
    # Initialize extensions
    db.init_app(app)
    
    return app, db

def generate_description(issue_type, dept_name):
    """Generate a realistic grievance description"""
    descriptions = {
        'administrative': [
            f"I submitted my documentation to the {dept_name} three weeks ago, but haven't received any confirmation. "
            f"I've tried contacting the office multiple times but haven't received a response. "
            f"This delay is affecting my ability to register for my courses and I'm concerned about missing deadlines.",
            
            f"There seems to be a discrepancy in my academic record with the {dept_name}. "
            f"My recent exam results are not reflecting correctly in the system. "
            f"I've attached my exam confirmation slip as proof of completion and the grade I received.",
            
            f"I'm experiencing issues with my registration process with {dept_name}. The system shows my fees are outstanding, "
            f"but I've already made the payment two weeks ago and sent proof to the finance department. "
            f"This is preventing me from accessing my course materials online."
        ],
        'facility': [
            f"The computer lab in the {dept_name} building has several workstations that have been out of order for over a month. "
            f"This is causing overcrowding and long wait times, which is affecting our ability to complete assignments on time. "
            f"I've reported this to the lab supervisor twice with no resolution.",
            
            f"The lecture hall B204 in the {dept_name} building has serious ventilation issues. "
            f"The air conditioning hasn't been working properly for weeks, making it extremely uncomfortable during lectures, "
            f"especially with full attendance. Several students have complained about feeling dizzy in class.",
            
            f"There are safety concerns in the {dept_name} practical laboratory. Some of the equipment appears to be damaged "
            f"and there are exposed electrical wires near one of the work stations. I'm concerned this poses a serious safety risk."
        ],
        'academic': [
            f"I have concerns about the grading in the {dept_name} module CODE101. The assessment criteria weren't clearly communicated "
            f"before the assignment was due, and the feedback provided doesn't explain the grading decisions. "
            f"I've tried to discuss this with the lecturer but haven't received a response to my emails.",
            
            f"The lecture content for the {dept_name} module SUBJ202 doesn't align with the prescribed textbook, "
            f"which is causing confusion among students. The lecturer acknowledges the discrepancy but hasn't provided "
            f"additional resources to help us bridge the gap in knowledge.",
            
            f"I missed an important exam in the {dept_name} due to a documented medical emergency. "
            f"I submitted my medical certificate to the department, but my request for a supplementary exam "
            f"has been pending for three weeks with no update. The semester is ending soon and I'm concerned about incomplete grades."
        ],
        'financial': [
            f"I applied for a fee adjustment with the {dept_name} based on my financial situation, but after two months, "
            f"I still haven't received any feedback. The payment deadline is approaching and I'm concerned about being blocked from registration.",
            
            f"My bursary payment was meant to be processed by the {dept_name} six weeks ago, but it's still not reflecting in my account. "
            f"I've received confirmation from my sponsor that the funds were transferred to the university a month ago. "
            f"This delay is causing me significant financial hardship.",
            
            f"There appears to be an error in my fee statement from the {dept_name}. I'm being charged for a module I didn't register for. "
            f"I've visited the finance office twice and each time I was told it would be corrected, but it still hasn't been resolved."
        ]
    }
    
    return random.choice(descriptions.get(issue_type, descriptions['administrative']))

def main():
    """Main function to seed the database with students and grievances"""
    print("\n" + "="*70)
    print("DUT Student Grievance Management System - Sample Data Setup")
    print("="*70)
    
    # Initialize Flask application
    app, db = create_app()
    
    # Get database path
    db_path = os.path.abspath(os.path.join('instance', 'app.db'))
    
    # Create database tables
    with app.app_context():
        # Check if database file exists
        if not os.path.exists(db_path):
            print(f"\n❌ Database does not exist at {db_path}. Please run create_db.py first.")
            return
            
        print(f"Using database at: {db_path}")
        
        # Import required functions
        from app.models.db_utils import create_user, create_grievance, get_all_departments
        from app.models.models import User, Grievance
        
        # Check if data already exists
        existing_students = User.query.filter_by(role='student').count()
        existing_grievances = Grievance.query.count()
        
        if existing_students > 0 or existing_grievances > 0:
            confirm = input(f"\nDatabase already contains {existing_students} students and {existing_grievances} grievances. Add more sample data? (y/n): ").lower().strip()
            if confirm != 'y':
                print("Operation cancelled.")
                return
        
        # Get departments
        departments = get_all_departments()
        if not departments:
            print("\n❌ No departments found. Please run create_db.py first.")
            return
        
        # Create sample students
        print("\n" + "-"*70)
        print("Creating sample student accounts")
        print("-"*70)
        
        sample_students = [
            {'email': 'student1@dut4life.ac.za', 'name': 'Thabo Ngubane', 'password': 'Student1@123'},
            {'email': 'student2@dut4life.ac.za', 'name': 'Nomcebo Dlamini', 'password': 'Student2@123'},
            {'email': 'student3@dut4life.ac.za', 'name': 'Joshua Peterson', 'password': 'Student3@123'},
            {'email': 'student4@dut4life.ac.za', 'name': 'Lerato Mthembu', 'password': 'Student4@123'},
            {'email': 'student5@dut4life.ac.za', 'name': 'Priya Singh', 'password': 'Student5@123'},
            {'email': 'student6@dut4life.ac.za', 'name': 'Mohammed Ali', 'password': 'Student6@123'},
            {'email': 'student7@dut4life.ac.za', 'name': 'Sarah Johnson', 'password': 'Student7@123'},
            {'email': 'student8@dut4life.ac.za', 'name': 'Thandeka Zulu', 'password': 'Student8@123'},
            {'email': 'student9@dut4life.ac.za', 'name': 'Lwazi Ndlovu', 'password': 'Student9@123'},
            {'email': 'student10@dut4life.ac.za', 'name': 'Anele Khumalo', 'password': 'Student10@123'}
        ]
        
        created_students = []
        for student in sample_students:
            try:
                # Check if student already exists
                existing_user = User.query.filter_by(email=student['email']).first()
                if existing_user:
                    print(f"✓ Student already exists: {student['name']} ({student['email']})")
                    created_students.append(existing_user)
                    continue
                    
                student_id = create_user(student['email'], student['password'], student['name'], role='student')
                created_students.append(User.query.get(student_id))
                print(f"✓ Created student: {student['name']} ({student['email']})")
            except Exception as e:
                print(f"❌ Error creating student {student['email']}: {e}")
        
        # Create sample grievances
        if not created_students:
            print("\n❌ No students created. Cannot create grievances.")
            return
            
        print("\n" + "-"*70)
        print("Creating sample grievances")
        print("-"*70)
        
        num_grievances = int(input("\nNumber of grievances to create (default: 20): ") or 20)
        
        # Issue types for varying grievance topics
        issue_types = ['administrative', 'facility', 'academic', 'financial']
        
        # Status options for grievances
        status_options = ['pending', 'in_progress', 'assigned', 'under_review', 'resolved', 'closed']
        
        # Titles for grievances
        grievance_titles = [
            "Issue with Course Registration",
            "Missing Grades in Student Portal",
            "Financial Aid Application Problem",
            "Accommodation Maintenance Issue",
            "Complaint about Lecture Facilities",
            "Library Access Problems",
            "Issue with Online Learning Platform",
            "Problems with Fee Payment System",
            "Concern about Course Content",
            "WiFi Connectivity Problems on Campus",
            "Issue with Laboratory Equipment",
            "Complaint about Administrative Process",
            "Delayed Response from Department",
            "Parking Facility Problems",
            "Concerns about Assessment Methods",
            "Issue with Student ID Card",
            "Problem with Exam Schedule",
            "Complaint about Campus Food Services",
            "Difficulty Accessing Academic Resources",
            "Issue with Practical Session Arrangements"
        ]
        
        for i in range(num_grievances):
            try:
                # Randomly select components
                student = random.choice(created_students)
                department = random.choice(departments)
                issue_type = random.choice(issue_types)
                title = random.choice(grievance_titles)
                
                # Generate description
                description = generate_description(issue_type, department.name)
                
                # Create grievance
                grievance_id = create_grievance(student.id, title, description, department.id)
                
                # Randomly set some grievances to different statuses
                grievance = Grievance.query.get(grievance_id)
                if random.random() > 0.4:  # 60% chance to change status
                    from app.models.db_utils import update_grievance_status
                    status = random.choice(status_options)
                    note = f"Status updated to {status}"
                    update_grievance_status(grievance_id, status, note)
                
                print(f"✓ Created grievance: '{title}' by {student.display_name} for {department.name}")
            except Exception as e:
                print(f"❌ Error creating grievance: {e}")
        
        print("\n✅ Sample data creation complete!")
        print(f"Created {len(created_students)} student accounts and attempted to create {num_grievances} grievances.")
        print("You can now run the application with 'python run.py' and login with:")
        print("  - Admin: admin@dut.ac.za / Admin@123456 (unless changed during setup)")
        print("  - Student: student1@dut4life.ac.za / Student1@123 (or any of the other sample accounts)")

if __name__ == "__main__":
    main() 
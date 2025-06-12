#!/usr/bin/env python
"""
Database Seeding Script for DUT Student Grievance Management System

This script adds default departments to the existing SQLite database.
"""

import os
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
    from app.models.models import db, Department
    db.init_app(app)
    return app, db

def main():
    print("\n" + "="*70)
    print("DUT Student Grievance Management System - Department Seeder")
    print("="*70)
    app, db = create_app()
    db_path = os.path.abspath(os.path.join('instance', 'app.db'))
    if not os.path.exists(db_path):
        print(f"\n❌ Database does not exist at {db_path}. Please create the database first.")
        return
    with app.app_context():
        from app.models.models import Department
        default_departments = [
            {'name': 'Academic Administration', 'description': 'Handles academic records, registration, and course administration.'},
            {'name': 'Admissions Office', 'description': 'Processes student applications and admissions.'},
            {'name': 'Finance Department', 'description': 'Handles student fees, payments, and financial aid.'},
            {'name': 'Student Housing', 'description': 'Manages student accommodation and residence issues.'},
            {'name': 'Financial Aid', 'description': 'Administers scholarships, bursaries, and financial assistance.'},
            {'name': 'Faculty of Accounting and Informatics', 'description': 'Academic matters related to accounting and informatics.'},
            {'name': 'Faculty of Applied Sciences', 'description': 'Academic matters related to applied sciences.'},
            {'name': 'Faculty of Arts and Design', 'description': 'Academic matters related to arts and design.'},
            {'name': 'Faculty of Engineering and the Built Environment', 'description': 'Academic matters related to engineering.'},
            {'name': 'Faculty of Health Sciences', 'description': 'Academic matters related to health sciences.'},
            {'name': 'Faculty of Management Sciences', 'description': 'Academic matters related to management sciences.'},
            {'name': 'Library Services', 'description': 'Handles library resources and services issues.'},
            {'name': 'IT Services', 'description': 'Manages IT infrastructure, support, and services.'},
            {'name': 'International Office', 'description': 'Supports international students and exchange programs.'},
            {'name': 'Student Counselling', 'description': 'Provides counselling and mental health support services.'},
            {'name': 'Sports Department', 'description': 'Manages sports facilities and programs.'},
            {'name': 'Student Representative Council (SRC)', 'description': 'Student leadership and representation.'}
        ]
        added = 0
        for dept in default_departments:
            if not Department.query.filter_by(name=dept['name']).first():
                db.session.add(Department(name=dept['name'], description=dept['description']))
                added += 1
        db.session.commit()
        print(f"\n✅ Departments added successfully. ({added} new, {len(default_departments)-added} already existed)")
        print("\nCurrent departments in the database:")
        departments = Department.query.all()
        for dept in departments:
            print(f"- {dept.id}: {dept.name}")
        print("\nDepartment seeding complete!")

if __name__ == "__main__":
    main() 
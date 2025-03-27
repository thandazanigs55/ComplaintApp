import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# DUT Departments organized by faculty
DUT_DEPARTMENTS = {
    "Faculty of Accounting and Informatics": [
        {
            "name": "Department of Information Technology",
            "description": "Offers programs in Software Development, Networks, and Information Systems"
        },
        {
            "name": "Department of Financial Accounting",
            "description": "Provides education in accounting, taxation, and financial management"
        }
    ],
    "Faculty of Applied Sciences": [
        {
            "name": "Department of Biotechnology and Food Technology",
            "description": "Focuses on biotechnology, food processing, and related research"
        },
        {
            "name": "Department of Chemistry",
            "description": "Offers programs in analytical, organic, and industrial chemistry"
        }
    ],
    "Faculty of Arts and Design": [
        {
            "name": "Department of Visual Communication Design",
            "description": "Covers graphic design, multimedia, and visual arts"
        },
        {
            "name": "Department of Fashion and Textiles",
            "description": "Focuses on fashion design, textile technology, and clothing management"
        }
    ],
    "Faculty of Engineering": [
        {
            "name": "Department of Mechanical Engineering",
            "description": "Offers programs in mechanical, industrial, and mechatronic engineering"
        },
        {
            "name": "Department of Civil Engineering",
            "description": "Focuses on structural, environmental, and construction engineering"
        }
    ],
    "Faculty of Health Sciences": [
        {
            "name": "Department of Nursing",
            "description": "Provides education in nursing and healthcare management"
        },
        {
            "name": "Department of Emergency Medical Care",
            "description": "Focuses on emergency medical services and paramedic training"
        }
    ],
    "Faculty of Management Sciences": [
        {
            "name": "Department of Public Management",
            "description": "Offers programs in public administration and governance"
        },
        {
            "name": "Department of Marketing and Retail",
            "description": "Focuses on marketing, retail management, and business strategy"
        }
    ],
    "Support Services": [
        {
            "name": "Student Housing",
            "description": "Manages student accommodation and residential life"
        },
        {
            "name": "Student Counselling",
            "description": "Provides mental health support and counselling services"
        },
        {
            "name": "Financial Aid Office",
            "description": "Handles student financial aid, bursaries, and scholarships"
        },
        {
            "name": "Academic Administration",
            "description": "Manages student records, registration, and academic processes"
        },
        {
            "name": "Library Services",
            "description": "Provides access to academic resources and research materials"
        }
    ]
}

def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized."""
    try:
        # Try to get existing app
        return firebase_admin.get_app()
    except ValueError:
        # If no app exists, initialize with credentials
        try:
            # Load service account
            service_account_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'service_account.json')
            cred = credentials.Certificate(service_account_path)
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            print("\nTroubleshooting tips:")
            print("1. Verify that 'service_account.json' exists in the project root directory")
            print("2. Check that the file has valid credentials")
            print("3. Ensure you have proper permissions to the Firebase project")
            sys.exit(1)

def seed_departments(db):
    """Seed the departments into Firestore."""
    # Reference to departments collection
    departments_ref = db.collection('departments')
    
    # Counter for departments added
    total_added = 0
    
    print("Starting to seed DUT departments...")
    
    # Delete existing departments
    existing_deps = departments_ref.get()
    for dep in existing_deps:
        dep.reference.delete()
    print("Cleared existing departments.")
    
    # Add new departments
    for faculty, departments in DUT_DEPARTMENTS.items():
        print(f"\nSeeding departments for {faculty}:")
        for dept in departments:
            dept_data = {
                "name": dept["name"],
                "description": dept["description"],
                "faculty": faculty
            }
            departments_ref.add(dept_data)
            print(f"Added: {dept['name']}")
            total_added += 1
    
    print(f"\nSeeding complete! Added {total_added} departments.")

def main():
    """Main function to run the seeding process."""
    print("DUT Department Seeding Script")
    print("============================")
    
    # Initialize Firebase
    try:
        app = initialize_firebase()
        print("Firebase initialized successfully.")
        db = firestore.client()
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return
    
    # Confirm before proceeding
    response = input("This will replace all existing departments. Continue? (y/n): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return
    
    # Seed departments
    try:
        seed_departments(db)
    except Exception as e:
        print(f"Error seeding departments: {e}")
        return

if __name__ == "__main__":
    main() 
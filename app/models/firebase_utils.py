import os
import pyrebase
import firebase_admin
from firebase_admin import auth, firestore, credentials
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import uuid
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Pyrebase configuration for client-side authentication
firebase_config = {
    "apiKey": os.getenv("Web_API_Key"),
    "authDomain": "studentgrievancems.firebaseapp.com",
    "projectId": "studentgrievancems",
    "storageBucket": "studentgrievancems.appspot.com",
    "messagingSenderId": "1015387144997",
    "appId": "1:1015387144997:web:c0c7a2b8d9c6a7c0c7a2b8",
    "databaseURL": "https://studentgrievancems-default-rtdb.firebaseio.com"
}

def initialize_firebase():
    """Initialize Firebase Admin SDK and Firestore"""
    try:
        # Try to get existing app
        return firebase_admin.get_app()
    except ValueError:
        # If no app exists, initialize with credentials
        try:
            # Get credentials from environment variable
            cred_json = os.getenv('FIREBASE_CREDENTIALS')
            if not cred_json:
                raise ValueError("FIREBASE_CREDENTIALS environment variable is not set")
            
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            
            return firebase_admin.initialize_app(cred)
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            raise

# Initialize Firebase services
try:
    # Initialize Firebase Admin SDK first
    app = initialize_firebase()
    
    # Initialize Firestore
    db = firestore.client()
    
    # Initialize Pyrebase only if we're not in a serverless environment
    if not os.getenv('VERCEL'):
        firebase = pyrebase.initialize_app(firebase_config)
        pyrebase_auth = firebase.auth()
        storage = firebase.storage()
    else:
        # In serverless environment, use dummy implementations
        class DummyAuth:
            def sign_in_with_email_and_password(self, *args, **kwargs):
                raise NotImplementedError("Pyrebase auth is not available in serverless environment")
        
        class DummyStorage:
            def child(self, path):
                print(f"Storage operation attempted on path {path} but storage is not available")
                return self
            
            def put(self, *args, **kwargs):
                print("Storage upload attempted but storage is not available")
                raise ValueError("Firebase Storage is not properly configured")
                
            def get_url(self, *args, **kwargs):
                print("Storage URL request attempted but storage is not available")
                return ""
                
            def delete(self, *args, **kwargs):
                print("Storage delete attempted but storage is not available")
                return False
        
        pyrebase_auth = DummyAuth()
        storage = DummyStorage()
    
    print("Firebase services initialized successfully")
except Exception as e:
    print(f"Error initializing Firebase services: {e}")
    raise

# Define a dummy storage class for development/testing
class DummyStorage:
    def child(self, path):
        print(f"Storage operation attempted on path {path} but storage is not available")
        return self
    
    def put(self, *args, **kwargs):
        print("Storage upload attempted but storage is not available")
        raise ValueError("Firebase Storage is not properly configured")
        
    def get_url(self, *args, **kwargs):
        print("Storage URL request attempted but storage is not available")
        return ""
        
    def delete(self, *args, **kwargs):
        print("Storage delete attempted but storage is not available")
        return False

# Initialize storage only after other services
try:
    storage = firebase.storage()
    print("Firebase Storage initialized successfully")
except Exception as e:
    print(f"Warning: Error initializing Firebase Storage: {str(e)}")
    # Use the dummy storage object
    storage = DummyStorage()

# User Authentication Functions
def create_user(email, password, display_name, role='student'):
    """Create a new user with Firebase Authentication"""
    try:
        # Create user in Firebase Auth
        user = auth.create_user(
            email=email,
            password=password,
            display_name=display_name
        )
        
        # Add user data to Firestore
        db.collection('users').document(user.uid).set({
            'email': email,
            'displayName': display_name,
            'role': role,
            'createdAt': firestore.SERVER_TIMESTAMP
        })
        
        return user.uid
    except Exception as e:
        print(f"Error creating user: {e}")
        raise e

def login_user(email, password):
    """Login a user with Firebase Authentication"""
    try:
        if os.getenv('VERCEL'):
            # In serverless environment, use Firebase Admin SDK
            user = auth.get_user_by_email(email)
            # Note: In production, you should implement proper password verification
            # This is just a placeholder for demonstration
            return {
                'localId': user.uid,
                'email': user.email,
                'displayName': user.display_name,
                'idToken': 'dummy_token'  # In production, generate a proper token
            }
        else:
            # In development environment, use Pyrebase
            user = pyrebase_auth.sign_in_with_email_and_password(email, password)
            auth.verify_id_token(user['idToken'])
            return user
            
    except auth.InvalidIdTokenError:
        print("Invalid ID token")
        raise ValueError("Authentication failed - invalid token")
    except Exception as e:
        error_message = str(e)
        print(f"Login error: {error_message}")
        
        # Map Firebase error codes to user-friendly messages
        if "INVALID_PASSWORD" in error_message:
            raise ValueError("Invalid password")
        elif "EMAIL_NOT_FOUND" in error_message:
            raise ValueError("Email not found")
        elif "INVALID_EMAIL" in error_message:
            raise ValueError("Invalid email format")
        elif "USER_DISABLED" in error_message:
            raise ValueError("Account has been disabled")
        else:
            raise ValueError("Authentication failed")

def get_user_by_id(uid):
    """Get user data from Firestore by user ID"""
    try:
        user_doc = db.collection('users').document(uid).get()
        if user_doc.exists:
            return user_doc.to_dict()
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

# Grievance Management Functions
def create_grievance(student_id, title, description, department, attachments=None):
    """Create a new grievance in Firestore"""
    try:
        # Validate required fields
        if not student_id or not title or not description or not department:
            raise ValueError("Missing required fields")

        # Create grievance document with a new ID
        grievance_ref = db.collection('grievances').document()
        
        # Get current timestamp and format as ISO string for consistent storage
        current_time = datetime.now().isoformat()
        
        # Create the initial status
        initial_status = {
            'status': 'pending',
            'note': 'Grievance submitted',
            'timestamp': current_time
        }
        
        # Prepare the complete grievance data
        grievance_data = {
            'studentId': student_id,
            'title': title,
            'description': description,
            'department': department,
            'status': 'pending',
            'createdAt': current_time,
            'updatedAt': current_time,
            'attachments': attachments if attachments else [],
            'statusHistory': [initial_status]
        }
        
        # Create the document
        grievance_ref.set(grievance_data)
        
        return grievance_ref.id
    except ValueError as ve:
        print(f"Validation error in create_grievance: {ve}")
        raise
    except Exception as e:
        print(f"Error creating grievance: {e}")
        raise

# Helper function to format timestamps for display
def format_timestamp(timestamp):
    """Format timestamp for display, converting ISO strings to datetime objects if needed"""
    if not timestamp:
        return None
    
    if isinstance(timestamp, str):
        try:
            # Try parsing ISO format first
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            try:
                # Try standard format
                return datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    # Try parsing just the date part if time is not included
                    return datetime.strptime(timestamp[:19], '%Y-%m-%dT%H:%M:%S')
                except ValueError:
                    return timestamp
    
    return timestamp

def get_student_grievances(student_id):
    """Get all grievances for a specific student"""
    try:
        grievances_ref = db.collection('grievances').where('studentId', '==', student_id)
        grievances = grievances_ref.get()
        
        result = []
        for grievance in grievances:
            grievance_data = grievance.to_dict()
            grievance_data['id'] = grievance.id
            
            # Format timestamps
            grievance_data['createdAt'] = format_timestamp(grievance_data.get('createdAt'))
            grievance_data['updatedAt'] = format_timestamp(grievance_data.get('updatedAt'))
            
            # Format timestamps in status history
            if 'statusHistory' in grievance_data and grievance_data['statusHistory']:
                for status_entry in grievance_data['statusHistory']:
                    if 'timestamp' in status_entry:
                        status_entry['timestamp'] = format_timestamp(status_entry['timestamp'])
            
            result.append(grievance_data)
            
        return result
    except Exception as e:
        print(f"Error getting student grievances: {e}")
        return []

def get_all_grievances():
    """Get all grievances from the database"""
    try:
        grievances_ref = db.collection('grievances')
        grievances = grievances_ref.get()
        
        result = []
        for grievance in grievances:
            grievance_data = grievance.to_dict()
            grievance_data['id'] = grievance.id
            
            # Format timestamps
            grievance_data['createdAt'] = format_timestamp(grievance_data.get('createdAt'))
            grievance_data['updatedAt'] = format_timestamp(grievance_data.get('updatedAt'))
            
            result.append(grievance_data)
            
        return result
    except Exception as e:
        print(f"Error getting grievances: {e}")
        return []

def get_open_grievances():
    """Get all open (non-resolved, non-closed) grievances"""
    try:
        # Get grievances that are not resolved or closed
        grievances_ref = db.collection('grievances').where('status', 'not-in', ['resolved', 'closed'])
        grievances = grievances_ref.get()
        
        result = []
        for grievance in grievances:
            grievance_data = grievance.to_dict()
            grievance_data['id'] = grievance.id
            
            # Format timestamps
            grievance_data['createdAt'] = format_timestamp(grievance_data.get('createdAt'))
            grievance_data['updatedAt'] = format_timestamp(grievance_data.get('updatedAt'))
            
            result.append(grievance_data)
            
        return result
    except Exception as e:
        print(f"Error getting open grievances: {e}")
        return []

def get_resolved_grievances():
    """Get all resolved or closed grievances"""
    try:
        # Get grievances that are resolved or closed
        grievances_ref = db.collection('grievances').where('status', 'in', ['resolved', 'closed'])
        grievances = grievances_ref.get()
        
        result = []
        for grievance in grievances:
            grievance_data = grievance.to_dict()
            grievance_data['id'] = grievance.id
            
            # Format timestamps
            grievance_data['createdAt'] = format_timestamp(grievance_data.get('createdAt'))
            grievance_data['updatedAt'] = format_timestamp(grievance_data.get('updatedAt'))
            
            result.append(grievance_data)
            
        return result
    except Exception as e:
        print(f"Error getting resolved grievances: {e}")
        return []

def get_department_grievances(department_name):
    """Get all grievances assigned to a specific department"""
    try:
        # Query grievances for the specific department
        grievances_ref = db.collection('grievances').where('department', '==', department_name)
        grievances = grievances_ref.get()
        
        result = []
        for grievance in grievances:
            grievance_data = grievance.to_dict()
            grievance_data['id'] = grievance.id
            
            # Format timestamps
            grievance_data['createdAt'] = format_timestamp(grievance_data.get('createdAt'))
            grievance_data['updatedAt'] = format_timestamp(grievance_data.get('updatedAt'))
            
            # Format timestamps in status history
            if 'statusHistory' in grievance_data and grievance_data['statusHistory']:
                for status_entry in grievance_data['statusHistory']:
                    if 'timestamp' in status_entry:
                        status_entry['timestamp'] = format_timestamp(status_entry['timestamp'])
            
            result.append(grievance_data)
        
        return result
    except Exception as e:
        print(f"Error getting department grievances: {e}")
        return []

def update_grievance_status(grievance_id, new_status, note=None):
    """Update the status of a grievance"""
    try:
        grievance_ref = db.collection('grievances').document(grievance_id)
        
        # Get current timestamp
        current_time = datetime.now().isoformat()
        
        # Add status change to history
        status_update = {
            'status': new_status,
            'timestamp': current_time,
            'note': note if note else f'Status updated to {new_status}'
        }
        
        grievance_ref.update({
            'status': new_status,
            'updatedAt': current_time,
            'statusHistory': firestore.ArrayUnion([status_update])
        })
        
        return True
    except Exception as e:
        print(f"Error updating grievance status: {e}")
        return False

def upload_file(file, folder='attachments'):
    """Upload a file to Firebase Storage"""
    try:
        if os.getenv('VERCEL'):
            # In serverless environment, return a dummy URL
            print("File upload attempted in serverless environment")
            return "https://example.com/dummy-file-url"
            
        if not file:
            return None
            
        # Secure the filename
        filename = secure_filename(file.filename)
        
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Upload to Firebase Storage
        storage_ref = storage.child(f"{folder}/{unique_filename}")
        storage_ref.put(file)
        
        # Get the download URL
        url = storage_ref.get_url(None)
        
        return url
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None

def get_grievance_by_id(grievance_id):
    """Get grievance details by ID"""
    try:
        grievance_doc = db.collection('grievances').document(grievance_id).get()
        if grievance_doc.exists:
            grievance_data = grievance_doc.to_dict()
            grievance_data['id'] = grievance_doc.id
            
            # Format timestamps
            grievance_data['createdAt'] = format_timestamp(grievance_data.get('createdAt'))
            grievance_data['updatedAt'] = format_timestamp(grievance_data.get('updatedAt'))
            
            # Ensure statusHistory exists and is properly formatted
            if 'statusHistory' not in grievance_data or not grievance_data['statusHistory']:
                grievance_data['statusHistory'] = []
            
            # Format timestamps in status history
            if grievance_data['statusHistory']:
                for status_entry in grievance_data['statusHistory']:
                    if 'timestamp' in status_entry:
                        status_entry['timestamp'] = format_timestamp(status_entry['timestamp'])
                        
            # Format timestamps in attachments
            if 'attachments' in grievance_data and grievance_data['attachments']:
                for attachment in grievance_data['attachments']:
                    if 'uploadedAt' in attachment:
                        attachment['uploadedAt'] = format_timestamp(attachment['uploadedAt'])
                        
            return grievance_data
        return None
    except Exception as e:
        print(f"Error getting grievance: {e}")
        return None

# Department Management Functions
def get_all_departments():
    """Get all departments from Firestore"""
    try:
        dept_collection = db.collection('departments').order_by('name').get()
        departments = [{'id': doc.id, **doc.to_dict()} for doc in dept_collection]
        
        # If no departments found in the dedicated collection, return default list
        if not departments:
            # Use set to get unique departments from grievances
            grievances = db.collection('grievances').get()
            department_set = set()
            
            for grievance in grievances:
                data = grievance.to_dict()
                if 'department' in data and data['department']:
                    department_set.add(data['department'])
            
            # Convert to list of dict objects
            departments = [{'id': None, 'name': dept, 'description': ''} for dept in sorted(department_set)]
            
            # Add these departments to Firestore if they don't exist
            for dept in departments:
                if not dept['id']:  # Only add departments that don't have an ID
                    add_department(dept['name'], dept['description'])
            
            # Get fresh list from database
            dept_collection = db.collection('departments').order_by('name').get()
            departments = [{'id': doc.id, **doc.to_dict()} for doc in dept_collection]
            
        return departments
    except Exception as e:
        print(f"Error getting departments: {e}")
        return []

def add_department(name, description=''):
    """Add a new department to Firestore"""
    try:
        # Check if department with same name already exists
        existing_dept = db.collection('departments').where('name', '==', name).limit(1).get()
        if len(list(existing_dept)) > 0:
            return False, "Department with this name already exists"
        
        # Add new department
        dept_data = {
            'name': name,
            'description': description,
            'createdAt': firestore.SERVER_TIMESTAMP
        }
        
        dept_ref = db.collection('departments').document()
        dept_ref.set(dept_data)
        return True, dept_ref.id
    except Exception as e:
        print(f"Error adding department: {e}")
        return False, str(e)

def update_department(dept_id, name, description):
    """Update an existing department in Firestore"""
    try:
        # Check if department exists
        dept_ref = db.collection('departments').document(dept_id)
        dept = dept_ref.get()
        
        if not dept.exists:
            return False, "Department not found"
        
        # Check if new name conflicts with another department
        if name != dept.to_dict().get('name'):
            existing_dept = db.collection('departments').where('name', '==', name).limit(1).get()
            if len(list(existing_dept)) > 0:
                return False, "Department with this name already exists"
        
        # Update department
        dept_ref.update({
            'name': name,
            'description': description,
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        
        return True, "Department updated successfully"
    except Exception as e:
        print(f"Error updating department: {e}")
        return False, str(e)

def delete_department(dept_id):
    """Delete a department from Firestore"""
    try:
        # Check for grievances using this department
        dept_doc = db.collection('departments').document(dept_id).get()
        if not dept_doc.exists:
            return False, "Department not found"
            
        dept_name = dept_doc.to_dict().get('name')
        grievances = db.collection('grievances').where('department', '==', dept_name).limit(1).get()
        
        if len(list(grievances)) > 0:
            return False, "Cannot delete department with associated grievances"
        
        # Delete the department
        db.collection('departments').document(dept_id).delete()
        return True, "Department deleted successfully"
    except Exception as e:
        print(f"Error deleting department: {e}")
        return False, str(e)

def get_department_by_id(dept_id):
    """Get a department by its ID"""
    try:
        dept_ref = db.collection('departments').document(dept_id)
        dept = dept_ref.get()
        if dept.exists:
            data = dept.to_dict()
            data['id'] = dept_id
            return data
        return None
    except Exception as e:
        print(f"Error getting department: {e}")
        return None

def get_all_users():
    """Get all users from the database"""
    try:
        users_ref = db.collection('users')
        users = users_ref.get()
        
        result = []
        for user in users:
            user_data = user.to_dict()
            user_data['id'] = user.id
            result.append(user_data)
            
        return result
    except Exception as e:
        print(f"Error getting users: {e}")
        return []

def get_users_by_role(role):
    """Get users by role (student, admin, etc.)"""
    try:
        users_ref = db.collection('users').where('role', '==', role)
        users = users_ref.get()
        
        result = []
        for user in users:
            user_data = user.to_dict()
            user_data['id'] = user.id
            result.append(user_data)
            
        return result
    except Exception as e:
        print(f"Error getting users by role: {e}")
        return []

def update_user(user_id, data):
    """Update a user's information in the database
    
    Args:
        user_id: The ID of the user to update
        data: Dictionary containing fields to update (name, email, role, etc.)
    
    Returns:
        Boolean indicating success or failure
    """
    try:
        # Remove sensitive fields that shouldn't be updated directly
        if 'password' in data:
            del data['password']
            
        if 'email' in data:
            # Email updates need to be handled through Firebase Auth
            try:
                auth.update_user(user_id, email=data['email'])
            except Exception as e:
                print(f"Error updating email in Auth: {e}")
                return False
                
        if 'name' in data:
            # Update display name in Firebase Auth
            try:
                auth.update_user(user_id, display_name=data['name'])
            except Exception as e:
                print(f"Error updating display name in Auth: {e}")

        # Update in Firestore
        db.collection('users').document(user_id).update(data)
        return True
    except Exception as e:
        print(f"Error updating user: {e}")
        return False

def delete_user(user_id):
    """Delete a user from the system
    
    Note: This will delete the user from both Auth and Firestore
    """
    try:
        # First check if user has any grievances
        grievances = get_student_grievances(user_id)
        if grievances and len(grievances) > 0:
            return False, "Cannot delete user with existing grievances"
        
        # Delete from Auth
        auth.delete_user(user_id)
        
        # Delete from Firestore
        db.collection('users').document(user_id).delete()
        
        return True, "User deleted successfully"
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False, f"Error: {str(e)}"

def reset_user_password(user_id, new_password):
    """Reset a user's password"""
    try:
        auth.update_user(user_id, password=new_password)
        return True, "Password reset successfully"
    except Exception as e:
        print(f"Error resetting password: {e}")
        return False, f"Error: {str(e)}"

def submit_department_response(grievance_id, response_text, department_id):
    """Submit a department's response to a grievance"""
    try:
        # Get current timestamp
        current_time = datetime.now().isoformat()
        
        # Get the grievance document
        grievance_ref = db.collection('grievances').document(grievance_id)
        grievance = grievance_ref.get()
        
        if not grievance.exists:
            raise ValueError("Grievance not found")
            
        grievance_data = grievance.to_dict()
        
        # Get department info
        department = get_user_by_id(department_id)
        department_name = department.get('displayName', 'Unknown Department')
        
        # Create response entry
        response_data = {
            'text': response_text,
            'departmentId': department_id,
            'departmentName': department_name,
            'timestamp': current_time,
            'status': 'pending_admin_review'  # New status to indicate admin needs to review
        }
        
        # Update grievance with response
        if 'departmentResponses' not in grievance_data:
            grievance_data['departmentResponses'] = []
        
        grievance_data['departmentResponses'].append(response_data)
        grievance_data['updatedAt'] = current_time
        
        # Update status to indicate response is pending admin review
        status_update = {
            'status': 'pending_admin_review',
            'note': f'Response submitted by {department_name}, awaiting admin review',
            'timestamp': current_time
        }
        
        if 'statusHistory' not in grievance_data:
            grievance_data['statusHistory'] = []
        
        grievance_data['statusHistory'].append(status_update)
        grievance_data['status'] = 'pending_admin_review'
        
        # Create admin notification
        notification_ref = db.collection('notifications').document()
        notification_data = {
            'type': 'department_response',
            'grievanceId': grievance_id,
            'departmentId': department_id,
            'departmentName': department_name,
            'timestamp': current_time,
            'status': 'unread',
            'message': f'New response from {department_name} requires review',
            'targetRole': 'admin'
        }
        
        # Update the documents in a batch
        batch = db.batch()
        batch.update(grievance_ref, grievance_data)
        batch.set(notification_ref, notification_data)
        batch.commit()
        
        return True
    except Exception as e:
        print(f"Error submitting department response: {e}")
        return False 
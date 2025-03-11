import os
import pyrebase
import firebase_admin
from firebase_admin import auth, firestore
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import uuid

# Load environment variables
load_dotenv()

# Pyrebase configuration for client-side authentication
firebase_config = {
    "apiKey": os.getenv("Web_API_Key"),
    "authDomain": "studentgrievancems.firebaseapp.com",
    "projectId": "studentgrievancems",
    "storageBucket": "studentgrievancems.appspot.com",
    "messagingSenderId": "your-message-sender-id",  # Not required for basic auth
    "databaseURL": "",  # Not required if not using realtime database
}

# Initialize Pyrebase
firebase = pyrebase.initialize_app(firebase_config)
pyrebase_auth = firebase.auth()
storage = firebase.storage()

# Initialize Firestore
db = firestore.client()

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
        user = pyrebase_auth.sign_in_with_email_and_password(email, password)
        return user
    except Exception as e:
        print(f"Login error: {e}")
        raise e

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

        # Create initial status history entry
        initial_status = {
            'status': 'pending',
            'timestamp': firestore.SERVER_TIMESTAMP,
            'note': 'Grievance submitted'
        }
        
        # Create grievance document
        grievance_ref = db.collection('grievances').document()
        
        # Set the data
        grievance_data = {
            'studentId': student_id,
            'title': title,
            'description': description,
            'department': department,
            'status': 'pending',
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP,
            'attachments': attachments if attachments else [],
            'statusHistory': [initial_status]
        }
        
        grievance_ref.set(grievance_data)
        
        return grievance_ref.id
    except ValueError as ve:
        print(f"Validation error in create_grievance: {ve}")
        raise
    except Exception as e:
        print(f"Error creating grievance: {e}")
        raise

def get_student_grievances(student_id):
    """Get all grievances for a specific student"""
    try:
        grievances_ref = db.collection('grievances').where('studentId', '==', student_id)
        grievances = grievances_ref.get()
        
        result = []
        for grievance in grievances:
            grievance_data = grievance.to_dict()
            grievance_data['id'] = grievance.id
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
            result.append(grievance_data)
            
        return result
    except Exception as e:
        print(f"Error getting resolved grievances: {e}")
        return []

def get_department_grievances(department):
    """Get all grievances for a specific department"""
    try:
        grievances = db.collection('grievances').where('department', '==', department).order_by('createdAt', direction=firestore.Query.DESCENDING).get()
        return [{'id': doc.id, **doc.to_dict()} for doc in grievances]
    except Exception as e:
        print(f"Error getting department grievances: {e}")
        return []

def update_grievance_status(grievance_id, new_status, note=None):
    """Update the status of a grievance"""
    try:
        grievance_ref = db.collection('grievances').document(grievance_id)
        
        # Add status change to history
        status_update = {
            'status': new_status,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'note': note if note else f'Status updated to {new_status}'
        }
        
        grievance_ref.update({
            'status': new_status,
            'updatedAt': firestore.SERVER_TIMESTAMP,
            'statusHistory': firestore.ArrayUnion([status_update])
        })
        
        return True
    except Exception as e:
        print(f"Error updating grievance status: {e}")
        return False

def upload_attachment(file, grievance_id):
    """Upload a file attachment to Firebase Storage"""
    try:
        # Ensure the file has a secure filename
        filename = secure_filename(file.filename)
        if not filename:
            raise ValueError("Invalid filename. Please use only letters, numbers, and common punctuation.")
            
        # Check file extension
        allowed_extensions = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
        if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            raise ValueError(f"Invalid file format. Allowed formats: {', '.join(allowed_extensions)}")
            
        # Generate a unique filename to prevent collisions
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = f"attachments/{grievance_id}/{unique_filename}"
        
        # Read file content and get size
        file_content = file.read()
        file_size = len(file_content)
        file.seek(0)  # Reset file pointer
        
        # Check file size (5MB limit)
        if file_size > 5 * 1024 * 1024:
            raise ValueError("File size exceeds 5MB limit. Please compress your file or choose a smaller one.")
        
        # Check if file is empty
        if file_size == 0:
            raise ValueError("File is empty. Please choose a valid file.")
        
        # Upload to Firebase Storage
        try:
            storage.child(file_path).put(file_content)
        except Exception as e:
            raise ValueError("Failed to upload file to storage. Please try again.")
        
        # Get the public URL
        try:
            file_url = storage.child(file_path).get_url(None)
        except Exception as e:
            raise ValueError("Failed to generate file URL. Please try again.")
        
        # Add file URL to grievance document
        grievance_ref = db.collection('grievances').document(grievance_id)
        attachment_data = {
            'name': filename,
            'url': file_url,
            'uploadedAt': firestore.SERVER_TIMESTAMP,
            'size': file_size,
            'type': file.content_type or 'application/octet-stream',
            'extension': filename.rsplit('.', 1)[1].lower()
        }
        
        try:
            grievance_ref.update({
                'attachments': firestore.ArrayUnion([attachment_data]),
                'updatedAt': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            # If we fail to update Firestore, try to delete the uploaded file
            try:
                storage.delete(file_path)
            except:
                pass
            raise ValueError("Failed to update grievance with attachment information.")
        
        return file_url
    except ValueError as ve:
        print(f"Validation error: {ve}")
        raise
    except Exception as e:
        print(f"Error uploading attachment: {e}")
        return None

def get_grievance_by_id(grievance_id):
    """Get grievance details by ID"""
    try:
        grievance_doc = db.collection('grievances').document(grievance_id).get()
        if grievance_doc.exists:
            return {'id': grievance_doc.id, **grievance_doc.to_dict()}
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
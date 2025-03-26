import os
from flask import Flask
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials
import datetime
import json

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
    
    # Initialize Firebase Admin SDK with flexible credential handling
    try:
        # First try to get credentials from environment variable
        cred_json = os.getenv('FIREBASE_CREDENTIALS')
        if cred_json:
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
        else:
            # Fallback to service account file
            service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT', 'service_account.json')
            cred = credentials.Certificate(service_account_path)
        
        # Initialize Firebase
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(cred)
            
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        # You might want to handle this error differently in production
        raise
    
    # Add context processor for datetime
    @app.context_processor
    def inject_now():
        return {'now': datetime.datetime.now()}
    
    # Add template filter for status colors
    @app.template_filter('status_color')
    def status_color(status):
        colors = {
            'pending': 'warning',
            'in_progress': 'info',
            'assigned': 'primary',
            'under_review': 'secondary',
            'resolved': 'success',
            'closed': 'dark',
            'pending_admin_review': 'info'
        }
        return colors.get(status, 'light')
    
    # Import and register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.student_routes import student_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.main_routes import main_bp
    from app.routes.department_routes import department_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(department_bp)
    
    return app 
import os
from flask import Flask
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials
import datetime

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)
    
    # Initialize Firebase Admin SDK
    cred = credentials.Certificate("service_account.json")
    firebase_admin.initialize_app(cred)
    
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
            'closed': 'dark'
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
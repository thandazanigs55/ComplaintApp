import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv
import datetime

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configure Flask app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Set up file upload folder
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize Login Manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Import models after db initialization
    from app.models.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Add context processor for datetime
    @app.context_processor
    def inject_now():
        return {'now': datetime.datetime.now()}
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Import and register blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.student_routes import student_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.main_routes import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    
    return app 
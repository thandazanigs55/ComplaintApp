from flask import Blueprint, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Redirect to the login page when someone visits the root URL
    return redirect(url_for('auth.login')) 
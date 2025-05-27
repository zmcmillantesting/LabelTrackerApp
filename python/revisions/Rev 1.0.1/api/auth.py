from flask import Blueprint, request, jsonify, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, db # Import User model and db instance

# Create a Blueprint object for authentication routes
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['POST'])
def login():
    """Handles user login."""
    if current_user.is_authenticated:
        # If user is already logged in, prevent re-login
        return jsonify({"message": "Already logged in", "user": current_user.username}), 200

    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"message": "Username and password required"}), 400

    username = data.get('username')
    password = data.get('password')
    remember = data.get('remember', False) # Optional "remember me" functionality

    # Find user by username (case-insensitive search might be better in production)
    user = db.session.scalars(db.select(User).filter_by(username=username)).first()

    # Validate user and password
    if user is None or not user.check_password(password):
        # flash('Invalid username or password') # Flashing is more for web forms
        return jsonify({"message": "Invalid username or password"}), 401 # Unauthorized

    # Log the user in using Flask-Login
    # The session cookie will be set by Flask-Login
    login_user(user, remember=remember)
    
    # Include user details in the response for the GUI client
    user_data = {
        "id": user.id,
        "username": user.username,
        "role": user.role.name.value,
        "department_id": user.department_id,
        "department_name": user.department.name if user.department else ""
    }
    
    current_app.logger.info(f"User '{username}' logged in successfully.")
    return jsonify({
        "message": "Login successful",
        "user": user_data
     }), 200

@auth.route('/logout', methods=['POST'])
@login_required # Ensure user is logged in to log out
def logout():
    """Handles user logout."""
    username = current_user.username
    logout_user() # Clears the session cookie
    current_app.logger.info(f"User '{username}' logged out.")
    return jsonify({"message": "Logout successful"}), 200

# Placeholder for user registration - can be implemented later
@auth.route('/register', methods=['POST'])
def register():
    """Handles user registration (Placeholder)."""
    # Admin/Manager role would likely be required to access this
    # Needs logic to check current_user role
    # Needs to receive username, password, role_id, department_id
    return jsonify({"message": "Registration endpoint not implemented"}), 501 # Not Implemented

# Simple endpoint to check login status and get current user info
@auth.route('/me', methods=['GET'])
@login_required
def me():
    """Returns current logged-in user information."""
    user_data = {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role.name.value,
        "department_id": current_user.department_id,
        "department_name": current_user.department.name if current_user.department else ""
    }
    return jsonify({"user": user_data}), 200 
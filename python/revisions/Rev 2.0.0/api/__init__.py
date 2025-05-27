# API main entry point 
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from .config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
# 'login' is the endpoint name for the login route, which we will define later
login_manager.login_view = 'auth.login' 
# Optional: Customize the message flashed when a user tries to access a protected page without being logged in
# login_manager.login_message = "Please log in to access this page."
# login_manager.login_message_category = "info"

def create_app(config_class=Config):
    """Factory function to create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- Explicitly set DB URI from environment --- 
    db_uri = os.environ.get('DATABASE_URL')
    if db_uri:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        print(f"[API Init Debug] Explicitly set SQLALCHEMY_DATABASE_URI from env var.")
    else:
        print("[API Init Debug] DATABASE_URL env var not found, relying on Config object.")
    # ---

    # Initialize Flask extensions here
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Import and register blueprints here
    # We need to create these blueprint files (e.g., auth.py, main.py) next
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint) # No prefix for main routes like /scan, /orders etc.

    # The user loader callback is used to reload the user object from the user ID stored in the session
    # We will define the User model in models.py
    # Need to ensure models.py is imported AFTER db is initialized but before it's used here.
    # Defining it inside create_app ensures app context.
    from .models import User 
    @login_manager.user_loader
    def load_user(user_id):
        # Since user_id is stored as a string in the session, convert it to an integer
        return User.query.get(int(user_id))

    return app 
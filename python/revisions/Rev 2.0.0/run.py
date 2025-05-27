import os
from dotenv import load_dotenv
import click # Import click for CLI commands

# --- Environment Loading ---
# Get the directory where run.py resides (project root)
project_root = os.path.abspath(os.path.dirname(__file__))
# Construct the absolute path to the .env file
dotenv_path = os.path.join(project_root, 'runner.env')
# Load the .env file explicitly
print(f"[run.py Debug] Attempting to load .env from: {dotenv_path}")
loaded = load_dotenv(dotenv_path=dotenv_path, verbose=True)
print(f"[run.py Debug] .env loaded: {loaded}")
# --- End Environment Loading ---

from api import create_app, db
from api.models import User, Order, Scan, Role, Department, Comment # Import ALL models
from flask_migrate import Migrate

app = create_app() # create_app will now use config potentially already populated by loaded env vars
migrate = Migrate(app, db)

# Add shell context processor to make db and models available in 'flask shell'
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Role': Role, 'Department': Department,
            'Order': Order, 'Scan': Scan, 'Comment': Comment}

# --- Custom CLI Commands ---
@app.cli.command("seed")
@click.option('--admin-pass', help='Set initial admin password.')
def seed_data(admin_pass):
    """Seeds the database with initial roles and admin user."""
    print("Seeding database...")
    # Set environment variable for admin password if provided
    if admin_pass:
        os.environ['ADMIN_PASSWORD'] = admin_pass
        print(f"Using provided password for admin user '{os.environ.get("ADMIN_USERNAME", "admin")}'.")
    elif not os.environ.get('ADMIN_PASSWORD'):
        print("Warning: ADMIN_PASSWORD environment variable not set. Using default 'password'.")
        print("It is highly recommended to set ADMIN_PASSWORD in your .env file or use the --admin-pass option.")

    # Ensure operations are within application context
    with app.app_context():
        # Restore Role.insert_roles()
        Role.insert_roles() # Create roles first
        User.create_admin() # Create admin user
    print("Database seeding complete.")
# --- End Custom CLI Commands ---

if __name__ == '__main__':
    # The app context is implicitly available when running via 'flask run' or app.run()
    # No need for explicit app.app_context() here for running the server
    
    # Optional: Create initial roles or admin user if they don't exist
    # with app.app_context():
    #     db.create_all() # Ensure tables exist (alternative to migrations for simple setups)
    #     Role.insert_roles() # We might add an insert_roles classmethod to Role model
    #     User.create_admin() # We might add a create_admin classmethod to User model
    
    app.run(host='0.0.0.0', port=5000, debug=True) # debug=True implies FLASK_ENV=development 
import os
# Remove dotenv import here, assuming run.py or similar entry point handles it
# from dotenv import load_dotenv 

# Determine project base directory relative to this file (api/config.py -> project_root)
project_basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

print(f"[Config Debug] Config class is being defined.")

class Config:
    """Base configuration settings.

    Reads configuration from environment variables.
    It assumes that load_dotenv() has been called by the application entry point
    (e.g., run.py) BEFORE this module is imported or the Config class is used.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-fallback-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Get DATABASE_URL directly from environment (populated by dotenv in run.py)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    print(f"[Config Debug] Initial DATABASE_URL from environment: {SQLALCHEMY_DATABASE_URI}")

    if not SQLALCHEMY_DATABASE_URI:
        print("[Config Debug] Warning: DATABASE_URL not found in environment. Falling back to default SQLite DB.")
        # Use the calculated project_basedir for the fallback SQLite path
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(project_basedir, 'default_app.db')
        print(f"[Config Debug] Using fallback SQLite URI: {SQLALCHEMY_DATABASE_URI}")
    else:
        # Optional: Mask password in printout for security
        try:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(SQLALCHEMY_DATABASE_URI)
            masked_uri = SQLALCHEMY_DATABASE_URI # Default to original
            if parsed.password:
                masked_netloc = f"{parsed.username}:********@{parsed.hostname}"
                if parsed.port:
                     masked_netloc += f":{parsed.port}"
                masked_uri = urlunparse((parsed.scheme, masked_netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
            print(f"[Config Debug] Using configured database URI (masked): {masked_uri}")
        except Exception:
             print(f"[Config Debug] Using configured database URI (unmasked): {SQLALCHEMY_DATABASE_URI}")

    # Add other configuration variables as needed
    # e.g., MAIL_SERVER, MAIL_PORT, etc. 
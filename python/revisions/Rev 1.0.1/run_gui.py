import sys
import logging
import os
import configparser
from PyQt6.QtWidgets import QApplication

# Import necessary components from the gui package
from gui.login_window import LoginWindow
from gui.main_window import MainWindow
from gui.api_client import ApiClient

# --- Logging Setup --- 

# Define the directory for feedback (logs are removed)
FEEDBACK_DIR = "errors-feedback"

def setup_logging():
    """Configures logging to console ONLY."""
    # Ensure the target directory exists (still needed for feedback file)
    os.makedirs(FEEDBACK_DIR, exist_ok=True)

    # Only need console formatter
    log_formatter_console = logging.Formatter('%(levelname)s: %(message)s')

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO) # Set root level to INFO

    # Remove File Handler

    # Console Handler - For INFO level and above
    # Remove existing handlers first to avoid duplicates if run again
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_formatter_console)
    logger.addHandler(console_handler)

    logging.info("Logging configured for console output.")

# --- Remove Global Exception Handler (handle_exception) ---
# --- Update Feedback Path ---
def get_feedback_file_path():
    """Returns the absolute path for the user feedback file."""
    # Ensure the directory exists when feedback is submitted too
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    return os.path.abspath(os.path.join(FEEDBACK_DIR, 'user_feedback.txt'))

# --- Function to Read GUI Configuration (Keep as is) ---
def load_gui_config():
    """Reads configuration from gui_config.ini."""
    config = configparser.ConfigParser()
    config_file = 'gui_config.ini'
    default_url = 'http://localhost:5000' # Fallback default
    
    if not os.path.exists(config_file):
        logging.warning(f"Configuration file '{config_file}' not found. Using default API URL: {default_url}")
        # Optionally create a default file here if desired
        return default_url
        
    try:
        config.read(config_file)
        api_url = config.get('API', 'base_url', fallback=default_url).strip()
        logging.info(f"Read API base URL from {config_file}: {api_url}")
        return api_url
    except Exception as e:
        logging.error(f"Error reading {config_file}: {e}. Using default API URL: {default_url}")
        return default_url

# --- Application Controller --- 
class ApplicationController:
    """Manages the flow between login and main windows."""

    def __init__(self, api_base_url):
        """Initializes the controller with the API base URL."""
        logging.info(f"Initializing ApplicationController with API base URL: {api_base_url}")
        # Initialize the API client with the loaded URL
        self.api_client = ApiClient(base_url=api_base_url) 
        
        self.login_window = None
        self.main_window = None

    def run(self):
        """Starts the application by showing the login window."""
        self.show_login_window()

    def show_login_window(self):
        """Creates and shows the login window."""
        if self.main_window:
            self.main_window.close() # Close main window if open
            self.main_window = None
            
        self.login_window = LoginWindow(self.api_client)
        self.login_window.login_successful.connect(self.show_main_window)
        self.login_window.show()

    def show_main_window(self, user_data):
        """
        Shows loading state on login window, creates main window, then swaps.
        
        Args:
            user_data (dict): Data about the logged-in user received from LoginWindow.
        """
        if self.login_window:
            # 1. Show loading state on LoginWindow
            logging.info("Login successful, showing loading state on login window...")
            self.login_window.show_loading_state()
            QApplication.processEvents() # Allow UI to update
        
        # 2. Create MainWindow (this takes time as it loads data)
        logging.info("Creating MainWindow instance and loading initial data...")
        self.main_window = MainWindow(user_data, self.api_client, get_feedback_file_path) 
        
        # 3. Hide LoginWindow *after* MainWindow is ready
        if self.login_window:
            logging.info("MainWindow ready, hiding login window.")
            self.login_window.hide()
            # Optionally destroy login window now if not needed for logout 
            # self.login_window.deleteLater() 
            # self.login_window = None 
        
        # 4. Connect logout signal and show MainWindow
        logging.info("Showing MainWindow.")
        self.main_window.logged_out.connect(self.show_login_window)
        self.main_window.show()


if __name__ == '__main__':
    # 1. Setup Logging FIRST (Simplified)
    setup_logging()

    # 2. Remove Exception Hook Setup
    # sys.excepthook = handle_exception

    # 3. Load GUI Configuration (API URL)
    api_url = load_gui_config()
    
    # 4. Create Qt Application
    app = QApplication(sys.argv)
    
    logging.info("Starting EMS Scan Application...") # Log application start
    
    # 5. Create the controller (passing the loaded URL) and run the app
    controller = ApplicationController(api_base_url=api_url)
    controller.run() # Start by showing the login window
    
    # 6. Start the Qt event loop
    exit_code = app.exec()
    logging.info(f"Application exited with code {exit_code}.") # Log application exit
    sys.exit(exit_code) 
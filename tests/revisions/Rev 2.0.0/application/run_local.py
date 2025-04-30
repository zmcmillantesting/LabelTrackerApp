import sys
import logging
import os
from PyQt6.QtWidgets import QApplication

# Import the data_manager and adapter
from data_manager import DataManager
from main_window_adapter import MainWindowAdapter
from gui.login_window import LoginWindow
from gui.main_window import MainWindow

# Define the directory for feedback
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

    # Remove existing handlers first to avoid duplicates if run again
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_formatter_console)
    logger.addHandler(console_handler)

    logging.info("Logging configured for console output.")

def get_feedback_file_path():
    """Returns the absolute path for the user feedback file."""
    # Use the data manager's function to get the path
    data_manager = DataManager()
    return os.path.join(data_manager.dev_path, "errors-feedback", "user_feedback.txt")

class ApplicationController:
    """Manages the flow between login and main windows."""

    def __init__(self):
        """Initializes the controller with the data manager."""
        logging.info("Initializing ApplicationController with local data manager")
        # Initialize the data manager
        self.data_manager = DataManager()
        
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
            
        self.login_window = LoginWindow(self.data_manager)
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
        
        # 2. Create adapter and MainWindow
        logging.info("Creating MainWindow instance and loading initial data...")
        adapter = MainWindowAdapter(self.data_manager)
        self.main_window = MainWindow(user_data, adapter, get_feedback_file_path) 
        
        # 3. Hide LoginWindow *after* MainWindow is ready
        if self.login_window:
            logging.info("MainWindow ready, hiding login window.")
            self.login_window.hide()
        
        # 4. Connect logout signal and show MainWindow
        logging.info("Showing MainWindow.")
        self.main_window.logged_out.connect(self.show_login_window)
        self.main_window.show()


if __name__ == '__main__':
    # 1. Setup Logging
    setup_logging()

    # 2. Create Qt Application
    app = QApplication(sys.argv)

    logging.info("Starting EMS Scan Application (Local Version)...") # Log application start
    
    # 3. Create the controller and run the app
    controller = ApplicationController()
    controller.run() # Start by showing the login window
    
    # 4. Start the Qt event loop
    exit_code = app.exec()
    logging.info(f"Application exited with code {exit_code}.") # Log application exit
    sys.exit(exit_code) 
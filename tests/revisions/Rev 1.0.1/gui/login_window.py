# GUI login window 

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QGridLayout, QSpacerItem, QSizePolicy,
    QProgressBar
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

# Import the ApiClient (assuming it's in the same directory)
try:
    from .api_client import ApiClient
except ImportError:
    # Handle case where script is run directly for testing
    from api_client import ApiClient 

class LoginWindow(QWidget):
    """Login window GUI."""
    
    # Signal emitted upon successful login, passing the user data
    login_successful = pyqtSignal(dict) 

    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api_client = api_client
        self.setWindowTitle("Label Tracker - Login")
        self.setMinimumWidth(350) # Set a reasonable minimum width

        self._init_ui()

    def _init_ui(self):
        """Initialize UI elements."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20) # Add some padding

        # Title Label
        title_label = QLabel("Label Tracker Login")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Grid layout for labels and fields
        grid_layout = QGridLayout()

        # Username
        username_label = QLabel("Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        grid_layout.addWidget(username_label, 0, 0)
        grid_layout.addWidget(self.username_input, 0, 1)

        # Password
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password) # Mask password
        self.password_input.setPlaceholderText("Enter password")
        grid_layout.addWidget(password_label, 1, 0)
        grid_layout.addWidget(self.password_input, 1, 1)
        
        # Add grid layout to main layout
        layout.addLayout(grid_layout)
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Login Button
        self.login_button = QPushButton("Login")
        self.login_button.setStyleSheet("QPushButton { padding: 10px; }") # Make button larger
        layout.addWidget(self.login_button)
        
        # Status Label (for error messages)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("QLabel { color: red; }") # Error messages in red
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # --- Add Loading Progress Bar (Initially Hidden) --- 
        self.loading_progress_bar = QProgressBar()
        self.loading_progress_bar.setRange(0, 0) # Indeterminate mode
        self.loading_progress_bar.setTextVisible(False)
        self.loading_progress_bar.hide() # Start hidden
        layout.addWidget(self.loading_progress_bar)
        # ---
        
        layout.addStretch() # Push elements towards the top

        # --- Connections ---
        self.login_button.clicked.connect(self.attempt_login)
        # Allow pressing Enter in password field to trigger login
        self.password_input.returnPressed.connect(self.attempt_login) 
        # Allow pressing Enter in username field to move to password field
        self.username_input.returnPressed.connect(self.password_input.setFocus) 

        self.setLayout(layout)

    def attempt_login(self):
        """Handles the login attempt when the button is clicked."""
        username = self.username_input.text().strip()
        password = self.password_input.text() # No strip on password
        
        if not username or not password:
            self.show_status_message("Username and password cannot be empty.")
            return

        # Disable button during login attempt
        self.login_button.setEnabled(False)
        self.login_button.setText("Logging in...")
        self.status_label.setText("") # Clear previous status

        # Perform API call
        login_result = self.api_client.login(username, password)

        # Re-enable button UNLESS successful (then show loading)
        if not login_result["success"]:
             self.login_button.setEnabled(True)
             self.login_button.setText("Login")

        if login_result["success"]:
            # DON'T close or show success message here anymore
            # self.show_status_message("Login Successful!", is_error=False) 
            user_data = login_result["data"]["user"]
            # Emit signal - Controller will handle UI changes
            self.login_successful.emit(user_data) 
            # --- Show loading state --- 
            # self.show_loading_state() # Moved to controller
            # --- 
            # self.close() # DON'T CLOSE HERE
        else:
            error_msg = login_result.get("message", "An unknown error occurred.")
            self.show_status_message(f"Login Failed: {error_msg}")
            # Clear password field on failure
            self.password_input.clear() 
            self.username_input.setFocus() # Focus back on username

    def show_status_message(self, message, is_error=True):
        """Displays a status message to the user."""
        if is_error:
             self.status_label.setStyleSheet("QLabel { color: red; }")
        else:
             self.status_label.setStyleSheet("QLabel { color: green; }")
        self.status_label.setText(message)
        # Optionally use QMessageBox for more prominent errors
        # if is_error:
        #    QMessageBox.warning(self, "Login Error", message)

    def show_loading_state(self):
        """Disables inputs and shows the loading progress bar."""
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.login_button.setEnabled(False)
        self.login_button.hide()
        self.status_label.hide()
        self.loading_progress_bar.show() # Show progress bar instead
        QApplication.processEvents() # Ensure UI updates immediately


# Example Usage (for testing the LoginWindow independently)
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Create a dummy ApiClient for testing the UI
    # In a real run, this would be the actual client connecting to the API
    dummy_client = ApiClient(base_url="http://dummyurl") 
    
    # --- Mock the login method for UI testing ---
    login_counter = 0
    def mock_login(username, password):
        global login_counter
        login_counter += 1
        print(f"Mock Login Attempt: {username} / {password}")
        if username == "admin" and password == "1234":
            print("-> Mock Success")
            return {
                "success": True, 
                "status_code": 200, 
                "data": {
                    "message": "Login successful", 
                    "user": {"id": 1, "username": "admin", "role": "Admin", "department": None}
                }
            }
        else:
            print("-> Mock Failure")
            # Simulate different errors
            if login_counter % 2 == 0:
                 return {"success": False, "status_code": 401, "message": "Invalid credentials"}
            else:
                 return {"success": False, "status_code": 500, "message": "Server error simulation"}
                 
    dummy_client.login = mock_login
    # --- End Mocking ---

    login_win = LoginWindow(dummy_client)
    
    # Connect the signal for testing
    def handle_login_success(user_data):
        print(f"Login successful signal received! User: {user_data}")
        # In a real app, this would trigger showing the main window
        QMessageBox.information(None, "Login Success", f"Welcome {user_data['username']}!")
        # Close the app for this test
        app.quit() 

    login_win.login_successful.connect(handle_login_success)
    
    login_win.show()
    sys.exit(app.exec()) 
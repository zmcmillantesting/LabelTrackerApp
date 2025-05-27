import sys
import traceback
from PyQt6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, QMessageBox, 
                            QWidget, QVBoxLayout, QLabel, QPushButton)
from data_manager import DataManager
from login_window import LoginWindow

# Simple placeholder panels for testing the login flow
class BasicPanel(QWidget):
    def __init__(self, title, on_logout=None):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Add a title label
        label = QLabel(f"{title} Panel")
        label.setStyleSheet("font-size: 18pt; font-weight: bold;")
        layout.addWidget(label)
        
        # Add a description
        desc = QLabel("This is a simplified panel for testing the login process.")
        layout.addWidget(desc)
        
        # Add a logout button
        logout_btn = QPushButton("Logout")
        logout_btn.setMinimumWidth(100)
        if callable(on_logout):
            logout_btn.clicked.connect(on_logout)
        layout.addWidget(logout_btn)
        
        # Add some spacing
        layout.addStretch()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Order Management System")
        self.setFixedSize(1200, 800)
        
        # Initialize DataManager
        self.data_manager = DataManager()
        
        # Create stacked widget to hold different screens
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create and add login window
        self.login_window = LoginWindow(self.data_manager, self.on_login_success)
        self.stacked_widget.addWidget(self.login_window)
        
        # Set login window as current
        self.stacked_widget.setCurrentWidget(self.login_window)
        
        print("MainWindow initialized with LoginWindow as current widget")

    def on_login_success(self, username):
        try:
            print(f"Login successful for: {username}")
            
            # Clear any existing widgets beyond the login window
            self._clear_stack()
            
            # For testing, we'll use a simplified panel
            if username == "admin":
                panel = BasicPanel("Admin", self.logout)
            else:
                panel = BasicPanel(f"User: {username}", self.logout)
            
            # Add and show the panel
            self.stacked_widget.addWidget(panel)
            self.stacked_widget.setCurrentWidget(panel)
            print(f"Switched to basic panel for {username}")
            
        except Exception as e:
            print(f"Error in on_login_success: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to process login: {str(e)}")
    
    def _clear_stack(self):
        # Remove all widgets except login window (at index 0)
        while self.stacked_widget.count() > 1:
            widget = self.stacked_widget.widget(1)
            self.stacked_widget.removeWidget(widget)
            if widget:
                widget.deleteLater()
    
    def logout(self):
        try:
            print("Logging out...")
            self._clear_stack()
            self.stacked_widget.setCurrentWidget(self.login_window)
            print("Returned to login screen")
        except Exception as e:
            print(f"Error during logout: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Apply a basic stylesheet
    app.setStyleSheet("""
        QWidget {
            background-color: white;
            color: black;
        }
        QPushButton {
            background-color: #f0f0f0;
            border: 1px solid #ddd;
            padding: 5px;
            min-width: 80px;
        }
        QLineEdit {
            border: 1px solid #ddd;
            padding: 5px;
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 
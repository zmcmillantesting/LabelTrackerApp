from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QCheckBox)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from data_manager import DataManager
import traceback

class LoginWindow(QWidget):
    def __init__(self, data_manager, on_login_success):
        super().__init__()
        self.data_manager = data_manager
        self.on_login_success = on_login_success
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Add title
        title = QLabel("Order Management System")
        title.setStyleSheet("font-size: 24pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Add some space
        layout.addSpacing(30)
        
        # Login form in a centered container
        form_container = QWidget()
        form_container.setMaximumWidth(400)
        form_layout = QVBoxLayout(form_container)
        
        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setMinimumWidth(100)
        self.username_entry = QLineEdit()
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_entry)
        form_layout.addLayout(username_layout)
        
        # Password
        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        password_label.setMinimumWidth(100)
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_entry.returnPressed.connect(self.verify_login)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_entry)
        form_layout.addLayout(password_layout)
        
        # Login button
        form_layout.addSpacing(20)
        login_button = QPushButton("Login")
        login_button.setMinimumHeight(40)
        login_button.clicked.connect(self.verify_login)
        form_layout.addWidget(login_button)
        
        # Add form to main layout with centering
        form_container_wrapper = QHBoxLayout()
        form_container_wrapper.addStretch()
        form_container_wrapper.addWidget(form_container)
        form_container_wrapper.addStretch()
        layout.addLayout(form_container_wrapper)
        
        # Add stretch at bottom to push form up
        layout.addStretch()
        
        # Info label at bottom
        info = QLabel("Default login: admin / password")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: gray;")
        layout.addWidget(info)

    def verify_login(self):
        try:
            username = self.username_entry.text().strip()
            password = self.password_entry.text().strip()
            
            if not username or not password:
                QMessageBox.warning(self, "Login Failed", "Please enter both username and password")
                return
            
            # Attempt to verify login
            if username in self.data_manager.users:
                user_data = self.data_manager.users[username]
                stored_password = user_data.get("password", "") if isinstance(user_data, dict) else user_data
                
                if stored_password == password:
                    print(f"Login successful for user: {username}")
                    self.username_entry.clear()
                    self.password_entry.clear()
                    
                    # Call the callback function with the username
                    if callable(self.on_login_success):
                        self.on_login_success(username)
                    else:
                        print("Warning: on_login_success is not callable")
                        QMessageBox.warning(self, "System Error", "Login callback not configured")
                else:
                    QMessageBox.warning(self, "Login Failed", "Invalid password")
            else:
                QMessageBox.warning(self, "Login Failed", f"Username '{username}' not found")
        except Exception as e:
            print(f"Error in verify_login: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Login Error", f"An error occurred during login: {str(e)}")

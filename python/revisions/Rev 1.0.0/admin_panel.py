from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QMessageBox,
                           QTabWidget, QComboBox, QTableWidget, QTableWidgetItem,
                           QCheckBox, QHeaderView, QAbstractItemView)
from data_manager import DataManager
import traceback

class AdminPanel(QWidget):
    def __init__(self, data_manager, on_logout=None):
        super().__init__()
        print("Initializing AdminPanel")
        self.data_manager = data_manager
        self.on_logout = on_logout
        
        # Initialize UI elements to None
        self.username_entry = None
        self.password_entry = None
        self.department_combo = None
        self.manager_checkbox = None
        self.users_table = None
        self.orders_table = None
        
        # Create UI
        self.init_ui()
        print("AdminPanel initialization complete")
    
    def init_ui(self):
        # Main layout for the entire panel
        main_layout = QVBoxLayout(self)
        
        # Top bar with logout button
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.addStretch()
        
        logout_button = QPushButton("Logout")
        logout_button.setMinimumWidth(100)
        if self.on_logout:
            logout_button.clicked.connect(self.on_logout)
        top_bar_layout.addWidget(logout_button)
        
        main_layout.addWidget(top_bar)
        
        # Tab widget for different admin functions
        tabs = QTabWidget()
        
        # User Management Tab
        user_tab = self.create_user_management_tab()
        tabs.addTab(user_tab, "User Management")
        
        # Order Management Tab
        order_tab = self.create_order_management_tab()
        tabs.addTab(order_tab, "Order Management")
        
        main_layout.addWidget(tabs)
    
    def create_user_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # User creation form
        form_layout = QHBoxLayout()
        
        # Username field
        username_label = QLabel("Username:")
        self.username_entry = QLineEdit()
        self.username_entry.setMinimumWidth(120)
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_entry)
        
        # Password field
        password_label = QLabel("Password:")
        self.password_entry = QLineEdit()
        self.password_entry.setMinimumWidth(120)
        self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_entry)
        
        # Department selection
        department_label = QLabel("Department:")
        self.department_combo = QComboBox()
        self.department_combo.setMinimumWidth(150)
        for dept_id, dept_info in self.data_manager.departments.items():
            self.department_combo.addItem(dept_info.get("name", dept_id), dept_id)
        form_layout.addWidget(department_label)
        form_layout.addWidget(self.department_combo)
        
        # Manager checkbox
        self.manager_checkbox = QCheckBox("Manager Authority")
        form_layout.addWidget(self.manager_checkbox)
        
        # Create button
        create_user_button = QPushButton("Create User")
        create_user_button.setMinimumWidth(100)
        create_user_button.clicked.connect(self.create_user)
        form_layout.addWidget(create_user_button)
        
        layout.addLayout(form_layout)
        
        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["Username", "Department", "Manager Status", "Actions"])
        self.users_table.setMinimumHeight(300)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.users_table.verticalHeader().setVisible(False)
        
        # Configure column widths
        self.users_table.setColumnWidth(0, 150)  # Username
        self.users_table.setColumnWidth(1, 200)  # Department
        self.users_table.setColumnWidth(2, 120)  # Manager Status
        self.users_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Actions
        
        layout.addWidget(self.users_table)
        
        # Populate the table
        self.update_users_table()
        
        return tab
    
    def create_order_management_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Orders table
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(3)
        self.orders_table.setHorizontalHeaderLabels(["Order Number", "Barcodes", "Actions"])
        self.orders_table.setMinimumHeight(300)
        self.orders_table.setAlternatingRowColors(True)
        self.orders_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.orders_table.verticalHeader().setVisible(False)
        
        # Configure column widths
        self.orders_table.setColumnWidth(0, 150)  # Order Number
        self.orders_table.setColumnWidth(1, 400)  # Barcodes
        self.orders_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Actions
        
        layout.addWidget(self.orders_table)
        
        # Populate the table
        self.update_orders_table()
        
        return tab
    
    def create_user(self):
        try:
            username = self.username_entry.text().strip()
            password = self.password_entry.text().strip()
            department = self.department_combo.currentData()
            is_manager = self.manager_checkbox.isChecked()
            
            if not username or not password:
                QMessageBox.warning(self, "Error", "Please enter both username and password")
                return
            
            success = self.data_manager.create_user(username, password, department, is_manager)
            
            if success:
                QMessageBox.information(self, "Success", f"User {username} created successfully")
                self.username_entry.clear()
                self.password_entry.clear()
                self.manager_checkbox.setChecked(False)
                self.update_users_table()
            else:
                QMessageBox.warning(self, "Error", "Username already exists")
        except Exception as e:
            print(f"Error creating user: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def update_users_table(self):
        try:
            # Clear the table
            self.users_table.setRowCount(0)
            
            # Get users
            users = self.data_manager.users
            if not users:
                print("No users found to display")
                return
                
            # Set row count
            self.users_table.setRowCount(len(users))
            
            # Populate rows
            for row, (username, user_data) in enumerate(users.items()):
                # Username
                self.users_table.setItem(row, 0, QTableWidgetItem(username))
                
                # Department
                department_id = user_data.get("department", "") if isinstance(user_data, dict) else ""
                department_name = self.data_manager.departments.get(department_id, {}).get("name", department_id)
                self.users_table.setItem(row, 1, QTableWidgetItem(department_name))
                
                # Manager status
                is_manager = user_data.get("is_manager", False) if isinstance(user_data, dict) else False
                manager_status = "Yes" if is_manager else "No"
                self.users_table.setItem(row, 2, QTableWidgetItem(manager_status))
                
                # Actions
                actions_widget = self.create_user_actions_widget(username, is_manager)
                self.users_table.setCellWidget(row, 3, actions_widget)
                
        except Exception as e:
            print(f"Error updating users table: {e}")
            traceback.print_exc()
    
    def create_user_actions_widget(self, username, is_manager):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Delete button
        delete_button = QPushButton("Delete")
        delete_button.setMinimumWidth(80)
        # Fixed lambda by removing 'checked' parameter
        delete_button.clicked.connect(lambda: self.delete_user(username))
        layout.addWidget(delete_button)
        
        # Toggle manager button (if not admin)
        if username != "admin":
            toggle_text = "Revoke Manager" if is_manager else "Make Manager"
            toggle_button = QPushButton(toggle_text)
            toggle_button.setMinimumWidth(120)
            # Fixed lambda by removing 'checked' parameter
            toggle_button.clicked.connect(lambda: self.toggle_manager_status(username))
            layout.addWidget(toggle_button)
        
        layout.addStretch()
        return widget
    
    def delete_user(self, username):
        if username == "admin":
            QMessageBox.warning(self, "Error", "Cannot delete admin user")
            return
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    f"Are you sure you want to delete user {username}?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.data_manager.delete_user(username):
                    QMessageBox.information(self, "Success", f"User {username} deleted successfully")
                    self.update_users_table()
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete user")
            except Exception as e:
                print(f"Error deleting user: {e}")
                traceback.print_exc()
                QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def toggle_manager_status(self, username):
        try:
            if username == "admin":
                QMessageBox.warning(self, "Error", "Cannot change admin's manager status")
                return
            
            current_status = self.data_manager.is_manager(username)
            new_status = not current_status
            
            if self.data_manager.set_manager_status(username, new_status):
                status_text = "granted" if new_status else "revoked"
                QMessageBox.information(self, "Success", f"Manager authority {status_text} for user {username}")
                self.update_users_table()
            else:
                QMessageBox.warning(self, "Error", "Failed to update manager status")
        except Exception as e:
            print(f"Error toggling manager status: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def update_orders_table(self):
        try:
            # Clear the table
            self.orders_table.setRowCount(0)
            
            # Get orders
            orders = self.data_manager.load_orders()
            if not orders:
                print("No orders found to display")
                return
                
            # Set row count
            self.orders_table.setRowCount(len(orders))
            
            # Populate rows
            for row, (order_number, order_data) in enumerate(orders.items()):
                # Order number
                self.orders_table.setItem(row, 0, QTableWidgetItem(order_number))
                
                # Barcodes
                barcodes = ", ".join(order_data.get("barcodes", []))
                self.orders_table.setItem(row, 1, QTableWidgetItem(barcodes))
                
                # Actions
                actions_widget = self.create_order_actions_widget(order_number)
                self.orders_table.setCellWidget(row, 2, actions_widget)
                
        except Exception as e:
            print(f"Error updating orders table: {e}")
            traceback.print_exc()
    
    def create_order_actions_widget(self, order_number):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Delete button
        delete_button = QPushButton("Delete")
        delete_button.setMinimumWidth(80)
        # Fixed lambda by removing 'checked' parameter
        delete_button.clicked.connect(lambda: self.delete_order(order_number))
        layout.addWidget(delete_button)
        
        layout.addStretch()
        return widget
    
    def delete_order(self, order_number):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                    f"Are you sure you want to delete order {order_number}?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.data_manager.delete_order(order_number):
                    QMessageBox.information(self, "Success", f"Order {order_number} deleted successfully")
                    self.update_orders_table()
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete order")
            except Exception as e:
                print(f"Error deleting order: {e}")
                traceback.print_exc()
                QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}") 
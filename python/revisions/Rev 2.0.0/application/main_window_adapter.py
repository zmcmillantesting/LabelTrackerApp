"""
Main Window Adapter

This module provides an adapter class that makes the existing MainWindow class
work with our new DataManager instead of the original ApiClient.
"""

class MainWindowAdapter:
    """
    Adapter that presents a DataManager with the same interface as ApiClient,
    allowing the MainWindow class to work without modification.
    """
    
    def __init__(self, data_manager):
        """
        Initialize the adapter with a DataManager instance.
        
        Args:
            data_manager: An instance of the DataManager class
        """
        self.data_manager = data_manager
        self.current_user = data_manager.current_user
    
    # --- Authentication Methods ---
    
    def login(self, username, password):
        """Pass-through for login method."""
        return self.data_manager.login(username, password)
    
    def logout(self):
        """Pass-through for logout method."""
        return self.data_manager.logout()
    
    def get_current_user_info(self):
        """Pass-through for get_current_user_info method."""
        return self.data_manager.get_current_user_info()
    
    def is_logged_in(self):
        """Pass-through for is_logged_in method."""
        return self.data_manager.is_logged_in()
    
    # --- Order Methods ---
    
    def get_orders(self):
        """Pass-through for get_orders method."""
        return self.data_manager.get_orders()
    
    def create_order(self, order_number, description=None):
        """Pass-through for create_order method."""
        return self.data_manager.create_order(order_number, description)
    
    def delete_order(self, order_id):
        """Pass-through for delete_order method."""
        return self.data_manager.delete_order(order_id)
    
    # --- Scan Methods ---
    
    def record_scan(self, barcode, status, order_id, notes=None):
        """Pass-through for record_scan method."""
        return self.data_manager.record_scan(barcode, status, order_id, notes)
    
    def get_scans(self, order_id=None, user_id=None, department_id=None):
        """Pass-through for get_scans method."""
        return self.data_manager.get_scans(order_id, user_id, department_id)
    
    def update_scan(self, scan_id, status=None, notes=None):
        """Pass-through for update_scan method."""
        return self.data_manager.update_scan(scan_id, status, notes)
    
    def delete_scan(self, scan_id):
        """Pass-through for delete_scan method."""
        return self.data_manager.delete_scan(scan_id)
    
    # --- Department Methods ---
    
    def create_department(self, name):
        """Pass-through for create_department method."""
        return self.data_manager.create_department(name)
    
    def get_departments(self):
        """Pass-through for get_departments method."""
        return self.data_manager.get_departments()
    
    def delete_department(self, department_id):
        """Pass-through for delete_department method."""
        return self.data_manager.delete_department(department_id)
    
    # --- User Methods ---
    
    def create_user(self, username, password, role_name, department_id=None):
        """Pass-through for create_user method."""
        return self.data_manager.create_user(username, password, role_name, department_id)
    
    def get_users(self):
        """Pass-through for get_users method."""
        return self.data_manager.get_users()
    
    def update_user(self, user_id, role_name=None, department_id=None):
        """Pass-through for update_user method."""
        return self.data_manager.update_user(user_id, role_name, department_id)
    
    def delete_user(self, user_id):
        """Pass-through for delete_user method."""
        return self.data_manager.delete_user(user_id)
    
    # --- Feedback Method ---
    
    def submit_feedback(self, feedback_text):
        """Pass-through for submit_feedback method."""
        return self.data_manager.submit_feedback(feedback_text) 
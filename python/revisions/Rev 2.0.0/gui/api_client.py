# Utility functions for API communication 

import requests
import json
import logging # For logging API interactions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ApiClient:
    """Handles communication with the backend Flask API."""

    def __init__(self, base_url="http://localhost:5000"):
        """
        Initializes the API client.

        Args:
            base_url (str): The base URL of the backend API.
        """
        if not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url
        # Use a requests Session object to persist cookies across requests
        self.session = requests.Session() 
        self.current_user = None # Store logged-in user details
        logging.info(f"ApiClient initialized with base URL: {self.base_url}")

    def _make_request(self, method, endpoint, data=None, params=None):
        """Helper method to make requests and handle common errors."""
        url = self.base_url + endpoint.lstrip('/')
        headers = {'Content-Type': 'application/json'}
        try:
            response = self.session.request(method, url, json=data, params=params, headers=headers, timeout=10) # Added timeout
            
            # Attempt to parse JSON, handle potential errors
            try:
                 response_data = response.json()
            except json.JSONDecodeError:
                logging.error(f"API response for {method} {url} was not valid JSON: {response.text[:100]}...") # Log snippet
                # For non-JSON errors (like 404 HTML pages), return a structured error
                return {"success": False, "status_code": response.status_code, "message": f"Server returned non-JSON response (Status: {response.status_code})", "raw_response": response.text}

            # Check for HTTP errors indicated by status code >= 400
            if not response.ok: # response.ok is False for status codes 4xx and 5xx
                 # Log error message from JSON if available
                 error_message = response_data.get("message", f"HTTP Error {response.status_code}")
                 logging.error(f"API Error ({method} {url}): {response.status_code} - {error_message}")
                 return {"success": False, "status_code": response.status_code, "message": error_message, "data": response_data}

            # Successful request
            logging.info(f"API Success ({method} {url}): {response.status_code}")
            return {"success": True, "status_code": response.status_code, "data": response_data}

        except requests.exceptions.RequestException as e:
            logging.error(f"API Connection Error ({method} {url}): {e}")
            return {"success": False, "status_code": None, "message": f"Connection error: {e}"}
            
    # --- Authentication Methods ---
    
    def login(self, username, password):
        """Attempts to log in the user."""
        logging.info(f"Attempting login for user: {username}")
        payload = {"username": username, "password": password}
        result = self._make_request("POST", "auth/login", data=payload)
        
        if result["success"]:
            # Store user details if login is successful
            self.current_user = result["data"].get("user")
            logging.info(f"Login successful for user: {username}. Role: {self.current_user.get('role') if self.current_user else 'N/A'}")
        else:
            self.current_user = None # Clear user on failed login
            logging.warning(f"Login failed for user: {username}. Reason: {result.get('message')}")
            
        return result # Return the full result dictionary

    def logout(self):
        """Logs out the current user."""
        if not self.current_user:
             logging.warning("Logout called but no user is logged in.")
             return {"success": False, "message": "Not logged in"}

        logging.info(f"Attempting logout for user: {self.current_user.get('username')}")
        result = self._make_request("POST", "auth/logout")
        
        if result["success"]:
            logging.info(f"Logout successful for user: {self.current_user.get('username')}")
            self.current_user = None # Clear user details on successful logout
        else:
            # Log error but maybe clear user anyway? Or handle based on error type.
            logging.error(f"Logout failed: {result.get('message')}")
            # Consider clearing self.current_user even on failure depending on desired behavior
            
        return result

    def get_current_user_info(self):
        """Fetches details for the currently logged-in user."""
        logging.info("Fetching current user info (/auth/me)")
        return self._make_request("GET", "auth/me")

    def is_logged_in(self):
        """Checks if there is a user logged in (based on stored info)."""
        # Note: This is a basic check. A more robust check might involve
        # verifying the session with the server using get_current_user_info().
        return self.current_user is not None

    # --- Order Methods ---
    def get_orders(self):
        """Fetches all orders."""
        logging.info("Fetching orders...")
        return self._make_request("GET", "orders")

    def create_order(self, order_number, description=None):
        """Creates a new order."""
        logging.info(f"Creating order: {order_number}")
        payload = {"order_number": order_number, "description": description}
        return self._make_request("POST", "orders", data=payload)

    def delete_order(self, order_id):
        """Deletes an order (Admin only)."""
        logging.warning(f"Attempting to delete order ID: {order_id}")
        return self._make_request("DELETE", f"orders/{order_id}")

    # --- Scan Methods ---
    def record_scan(self, barcode, status, order_id, notes=None):
        """Records a new scan."""
        logging.info(f"Recording scan for barcode: {barcode}")
        payload = {
            "barcode": barcode,
            "status": status, # Should be "Pass" or "Fail"
            "order_id": order_id,
            "notes": notes
        }
        return self._make_request("POST", "scans", data=payload)

    def get_scans(self, order_id=None, user_id=None, department_id=None):
        """Fetches scans, optionally filtered."""
        logging.info("Fetching scans...")
        params = {}
        if order_id:
            params['order_id'] = order_id
        if user_id:
            params['user_id'] = user_id
        if department_id:
            params['department_id'] = department_id
        return self._make_request("GET", "scans", params=params)

    def update_scan(self, scan_id, status=None, notes=None):
        """Updates a scan's status or notes (Admin/Manager)."""
        logging.info(f"Updating scan ID: {scan_id}")
        payload = {}
        if status is not None:
            payload["status"] = status
        if notes is not None:
            payload["notes"] = notes
        if not payload:
             return {"success": True, "message": "No update data provided."}
        return self._make_request("PUT", f"scans/{scan_id}", data=payload)

    def delete_scan(self, scan_id):
        """Deletes a scan (Admin/Manager)."""
        logging.warning(f"Attempting to delete scan ID: {scan_id}")
        return self._make_request("DELETE", f"scans/{scan_id}")

    # --- Department Methods ---
    def create_department(self, name):
        """Creates a new department (Admin only)."""
        logging.info(f"Creating department: {name}")
        return self._make_request("POST", "departments", data={"name": name})

    def get_departments(self):
        """Fetches all departments."""
        logging.info("Fetching departments...")
        return self._make_request("GET", "departments")

    def delete_department(self, department_id):
        """Deletes a department (Admin only)."""
        logging.warning(f"Attempting to delete department ID: {department_id}")
        return self._make_request("DELETE", f"departments/{department_id}")

    # --- User Methods (Admin Only) ---
    def create_user(self, username, password, role_name, department_id=None):
        """Creates a new user (Admin only)."""
        logging.info(f"Creating user: {username}")
        payload = {
            "username": username,
            "password": password,
            "role_name": role_name, # e.g., "Admin", "Manager", "Standard"
            "department_id": department_id
        }
        return self._make_request("POST", "users", data=payload)
        
    def get_users(self):
        """Fetches all users (Admin only)."""
        logging.info("Fetching users...")
        return self._make_request("GET", "users")
        
    def update_user(self, user_id, role_name=None, department_id=None):
        """Updates a user's role and/or department (Admin only)."""
        logging.info(f"Updating user ID: {user_id}")
        payload = {}
        if role_name is not None:
            payload['role_name'] = role_name
        # Pass department_id regardless of None status, API handles it
        if 'department_id' in payload or department_id is not None: # Ensure intent is clear
            payload['department_id'] = department_id

        if not payload:
             return {"success": True, "message": "No update fields provided."}

        return self._make_request("PUT", f"users/{user_id}", data=payload)

    def delete_user(self, user_id):
        """Deletes a user (Admin only)."""
        logging.warning(f"Attempting to delete user ID: {user_id}")
        return self._make_request("DELETE", f"users/{user_id}")

    # --- Remove Log Methods ---

    def submit_feedback(self, feedback_text):
        """Submits user feedback."""
        logging.info("Submitting feedback...")
        payload = {"feedback_text": feedback_text}
        return self._make_request("POST", "feedback", data=payload)

# Example Usage (for testing purposes)
if __name__ == '__main__':
    # NOTE: Ensure the Flask API server is running before executing this test block!
    # Remember to run the server with $env:DATABASE_URL='...' python run.py
    
    client = ApiClient() # Defaults to http://localhost:5000/

    # Test Login
    print("\n--- Testing Login ---")
    login_result = client.login("admin", "1234") # Use the correct password
    print(f"Login Result: {login_result}")
    print(f"Is Logged In: {client.is_logged_in()}")
    print(f"Current User: {client.current_user}")
    
    if client.is_logged_in():
        # Test Get Me (if logged in)
        print("\n--- Testing Get Me ---")
        me_result = client.get_current_user_info()
        print(f"Get Me Result: {me_result}")

        # Add tests for other endpoints here (e.g., get_orders)

        # Test Logout
        print("\n--- Testing Logout ---")
        logout_result = client.logout()
        print(f"Logout Result: {logout_result}")
        print(f"Is Logged In: {client.is_logged_in()}")
        print(f"Current User: {client.current_user}")

    # Test Get Me (after logout)
    print("\n--- Testing Get Me (After Logout) ---")
    me_result_after_logout = client.get_current_user_info()
    print(f"Get Me After Logout Result: {me_result_after_logout}") 
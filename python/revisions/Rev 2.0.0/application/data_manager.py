import os
import sqlite3
import logging
import json
from datetime import datetime
import bcrypt
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataManager:
    """Handles data storage and retrieval using local SQLite databases."""

    def __init__(self, base_path="P:/Development_Testing"):
        """
        Initializes the data manager.

        Args:
            base_path (str): The base path where data folders are located.
        """
        self.base_path = Path(base_path)
        self.data_path = self.base_path / "data"
        self.cont_path = self.base_path / "cont"
        self.dev_path = self.base_path / "dev"
        self.prev_path = self.base_path / "prev"
        
        # Ensure directories exist
        self.data_path.mkdir(exist_ok=True)
        self.cont_path.mkdir(exist_ok=True)
        self.dev_path.mkdir(exist_ok=True)
        self.prev_path.mkdir(exist_ok=True)
        
        # Path to user database
        self.users_db_path = self.cont_path / "users.db"
        
        # Initialize databases
        self._initialize_users_db()
        
        # Store current user
        self.current_user = None

    def _initialize_users_db(self):
        """Initialize the users database with necessary tables if they don't exist."""
        conn = sqlite3.connect(self.users_db_path)
        cursor = conn.cursor()
        
        # Create roles table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
        ''')
        
        # Create departments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
        ''')
        
        # Create users table with role and department foreign keys
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            department_id INTEGER,
            FOREIGN KEY (role_id) REFERENCES roles (id),
            FOREIGN KEY (department_id) REFERENCES departments (id)
        )
        ''')
        
        # Insert default roles if they don't exist
        roles = [('Admin',), ('Manager',), ('Standard',)]
        cursor.executemany(
            'INSERT OR IGNORE INTO roles (name) VALUES (?)', 
            roles
        )
        
        # Check if admin user exists, create if not
        cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
        if cursor.fetchone()[0] == 0:
            # Get the Admin role ID
            cursor.execute('SELECT id FROM roles WHERE name = ?', ('Admin',))
            admin_role_id = cursor.fetchone()[0]
            
            # Create default admin user
            hashed_pw = bcrypt.hashpw('1234'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                'INSERT INTO users (username, password_hash, role_id) VALUES (?, ?, ?)',
                ('admin', hashed_pw, admin_role_id)
            )
        
        conn.commit()
        conn.close()
        logging.info("Users database initialized")

    def _get_department_db_path(self, department_name):
        """Get the path to a specific department's database."""
        dept_dir = self.data_path / department_name
        dept_dir.mkdir(exist_ok=True)
        return dept_dir / f"{department_name.lower()}.db"

    def _initialize_department_db(self, department_name):
        """Initialize a department-specific database."""
        db_path = self._get_department_db_path(department_name)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create orders table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            order_number TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TEXT,
            created_by_user_id INTEGER NOT NULL
        )
        ''')
        
        # Create scans table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY,
            barcode TEXT NOT NULL,
            timestamp TEXT,
            status TEXT NOT NULL,
            notes TEXT,
            user_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
        ''')
        
        # Create indices for faster lookups
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scans_barcode ON scans (barcode)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_scans_timestamp ON scans (timestamp)')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_order_number ON orders (order_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders (created_at)')
        
        conn.commit()
        conn.close()
        logging.info(f"Department database initialized for: {department_name}")

    # --- Authentication Methods ---
    
    def login(self, username, password):
        """Attempt to log in a user."""
        logging.info(f"Attempting login for user: {username}")
        
        try:
            conn = sqlite3.connect(self.users_db_path)
            cursor = conn.cursor()
            
            # Get user details including role and department
            cursor.execute('''
                SELECT u.id, u.username, u.password_hash, r.name, d.name, u.department_id
                FROM users u
                JOIN roles r ON u.role_id = r.id
                LEFT JOIN departments d ON u.department_id = d.id
                WHERE u.username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                logging.warning(f"Login failed: User '{username}' not found")
                return {"success": False, "status_code": 401, "message": "Invalid username or password"}
            
            user_id, user_name, password_hash, role_name, department_name, department_id = user
            
            # Check password
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                # Store user details
                self.current_user = {
                    "id": user_id,
                    "username": user_name,
                    "role": role_name,
                    "department": department_name,
                    "department_id": department_id
                }
                
                logging.info(f"Login successful for user: {username}. Role: {role_name}")
                return {
                    "success": True, 
                    "status_code": 200, 
                    "data": {
                        "message": "Login successful",
                        "user": self.current_user
                    }
                }
            else:
                logging.warning(f"Login failed for user: {username}. Incorrect password.")
                return {"success": False, "status_code": 401, "message": "Invalid username or password"}
            
        except Exception as e:
            logging.error(f"Login error for user {username}: {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    def logout(self):
        """Log out the current user."""
        if not self.current_user:
            logging.warning("Logout called but no user is logged in.")
            return {"success": False, "message": "Not logged in"}
        
        logging.info(f"Logout successful for user: {self.current_user.get('username')}")
        self.current_user = None
        return {"success": True, "status_code": 200, "data": {"message": "Logged out successfully"}}

    def get_current_user_info(self):
        """Get information about the currently logged-in user."""
        if not self.current_user:
            return {"success": False, "status_code": 401, "message": "Not logged in"}
        
        return {
            "success": True, 
            "status_code": 200, 
            "data": {
                "user": self.current_user
            }
        }

    def is_logged_in(self):
        """Check if a user is currently logged in."""
        return self.current_user is not None

    # --- Department Methods ---
    
    def create_department(self, name):
        """Create a new department."""
        if not self.current_user or self.current_user.get('role') != 'Admin':
            return {"success": False, "status_code": 403, "message": "Requires Admin role"}
        
        try:
            # Add to users database
            conn = sqlite3.connect(self.users_db_path)
            cursor = conn.cursor()
            
            # Check if department already exists
            cursor.execute('SELECT id FROM departments WHERE name = ?', (name,))
            if cursor.fetchone():
                conn.close()
                return {"success": False, "status_code": 409, "message": f"Department '{name}' already exists"}
            
            cursor.execute('INSERT INTO departments (name) VALUES (?)', (name,))
            dept_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Initialize department database
            self._initialize_department_db(name)
            
            return {
                "success": True, 
                "status_code": 201, 
                "data": {
                    "message": "Department created successfully",
                    "department": {"id": dept_id, "name": name}
                }
            }
        except Exception as e:
            logging.error(f"Error creating department '{name}': {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    def get_departments(self):
        """Get all departments."""
        try:
            conn = sqlite3.connect(self.users_db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, name FROM departments ORDER BY name')
            departments = [{"id": id, "name": name} for id, name in cursor.fetchall()]
            conn.close()
            
            return {
                "success": True, 
                "status_code": 200, 
                "data": {
                    "departments": departments
                }
            }
        except Exception as e:
            logging.error(f"Error retrieving departments: {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    def delete_department(self, department_id):
        """Delete a department (Admin only)."""
        if not self.current_user or self.current_user.get('role') != 'Admin':
            return {"success": False, "status_code": 403, "message": "Requires Admin role"}
        
        try:
            conn = sqlite3.connect(self.users_db_path)
            cursor = conn.cursor()
            
            # Get department name for logging and file operations
            cursor.execute('SELECT name FROM departments WHERE id = ?', (department_id,))
            dept_result = cursor.fetchone()
            if not dept_result:
                conn.close()
                return {"success": False, "status_code": 404, "message": f"Department ID {department_id} not found"}
            
            dept_name = dept_result[0]
            
            # Check if department is in use by any users
            cursor.execute('SELECT COUNT(*) FROM users WHERE department_id = ?', (department_id,))
            if cursor.fetchone()[0] > 0:
                conn.close()
                return {
                    "success": False, 
                    "status_code": 400, 
                    "message": f"Cannot delete department '{dept_name}' because it is assigned to users"
                }
            
            # Delete department
            cursor.execute('DELETE FROM departments WHERE id = ?', (department_id,))
            conn.commit()
            conn.close()
            
            # Optional: Handle department database file deletion
            # db_path = self._get_department_db_path(dept_name)
            # if db_path.exists():
            #     db_path.unlink()
            
            return {
                "success": True, 
                "status_code": 200, 
                "data": {
                    "message": f"Department '{dept_name}' deleted successfully"
                }
            }
        except Exception as e:
            logging.error(f"Error deleting department ID {department_id}: {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    # --- User Methods ---
    
    def create_user(self, username, password, role_name, department_id=None):
        """Create a new user (Admin only)."""
        if not self.current_user or self.current_user.get('role') != 'Admin':
            return {"success": False, "status_code": 403, "message": "Requires Admin role"}
        
        try:
            conn = sqlite3.connect(self.users_db_path)
            cursor = conn.cursor()
            
            # Check if username already exists
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                conn.close()
                return {"success": False, "status_code": 409, "message": f"Username '{username}' already exists"}
            
            # Get role ID
            cursor.execute('SELECT id FROM roles WHERE name = ?', (role_name,))
            role_id_result = cursor.fetchone()
            if not role_id_result:
                conn.close()
                return {"success": False, "status_code": 400, "message": f"Invalid role name: {role_name}"}
            role_id = role_id_result[0]
            
            # Hash password
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Insert user
            if department_id:
                cursor.execute(
                    'INSERT INTO users (username, password_hash, role_id, department_id) VALUES (?, ?, ?, ?)',
                    (username, hashed_pw, role_id, department_id)
                )
            else:
                cursor.execute(
                    'INSERT INTO users (username, password_hash, role_id) VALUES (?, ?, ?)',
                    (username, hashed_pw, role_id)
                )
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                "success": True, 
                "status_code": 201, 
                "data": {
                    "message": "User created successfully",
                    "user": {
                        "id": user_id,
                        "username": username,
                        "role": role_name,
                        "department_id": department_id
                    }
                }
            }
        except Exception as e:
            logging.error(f"Error creating user '{username}': {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    def get_users(self):
        """Get all users (Admin only)."""
        if not self.current_user or self.current_user.get('role') != 'Admin':
            return {"success": False, "status_code": 403, "message": "Requires Admin role"}
        
        try:
            conn = sqlite3.connect(self.users_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.username, r.name, d.id, d.name 
                FROM users u
                JOIN roles r ON u.role_id = r.id
                LEFT JOIN departments d ON u.department_id = d.id
                ORDER BY u.username
            ''')
            
            users = []
            for user_id, username, role_name, dept_id, dept_name in cursor.fetchall():
                users.append({
                    "id": user_id,
                    "username": username,
                    "role": role_name,
                    "department_id": dept_id,
                    "department_name": dept_name
                })
            
            conn.close()
            
            return {
                "success": True, 
                "status_code": 200, 
                "data": {
                    "users": users
                }
            }
        except Exception as e:
            logging.error(f"Error retrieving users: {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    def update_user(self, user_id, role_name=None, department_id=None):
        """Update a user's role and/or department (Admin only)."""
        if not self.current_user or self.current_user.get('role') != 'Admin':
            return {"success": False, "status_code": 403, "message": "Requires Admin role"}
            
        try:
            conn = sqlite3.connect(self.users_db_path)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
            if not cursor.fetchone():
                conn.close()
                return {"success": False, "status_code": 404, "message": f"User ID {user_id} not found"}
            
            # Gather update fields
            update_parts = []
            params = []
            
            if role_name:
                # Get role id
                cursor.execute('SELECT id FROM roles WHERE name = ?', (role_name,))
                role_result = cursor.fetchone()
                if not role_result:
                    conn.close()
                    return {"success": False, "status_code": 400, "message": f"Invalid role name: {role_name}"}
                update_parts.append("role_id = ?")
                params.append(role_result[0])
            
            if department_id is not None:  # Allow setting None to remove department
                if department_id:  # If not None, validate department exists
                    cursor.execute('SELECT id FROM departments WHERE id = ?', (department_id,))
                    if not cursor.fetchone():
                        conn.close()
                        return {"success": False, "status_code": 404, "message": f"Department ID {department_id} not found"}
                update_parts.append("department_id = ?")
                params.append(department_id)
            
            if not update_parts:
                conn.close()
                return {"success": True, "status_code": 200, "message": "No updates provided"}
            
            # Build and execute update query
            query = f"UPDATE users SET {', '.join(update_parts)} WHERE id = ?"
            params.append(user_id)
            cursor.execute(query, params)
            
            conn.commit()
            
            # Get updated user info
            cursor.execute('''
                SELECT u.id, u.username, r.name, d.id, d.name 
                FROM users u
                JOIN roles r ON u.role_id = r.id
                LEFT JOIN departments d ON u.department_id = d.id
                WHERE u.id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                user_id, username, role, dept_id, dept_name = user
                return {
                    "success": True, 
                    "status_code": 200, 
                    "data": {
                        "message": "User updated successfully",
                        "user": {
                            "id": user_id,
                            "username": username,
                            "role": role,
                            "department_id": dept_id,
                            "department_name": dept_name
                        }
                    }
                }
            else:
                return {"success": False, "status_code": 500, "message": "Failed to retrieve updated user data"}
            
        except Exception as e:
            logging.error(f"Error updating user ID {user_id}: {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    def delete_user(self, user_id):
        """Delete a user (Admin only)."""
        if not self.current_user or self.current_user.get('role') != 'Admin':
            return {"success": False, "status_code": 403, "message": "Requires Admin role"}
        
        # Prevent deleting the current user
        if self.current_user.get('id') == user_id:
            return {"success": False, "status_code": 400, "message": "Cannot delete your own user account"}
        
        try:
            conn = sqlite3.connect(self.users_db_path)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            user_result = cursor.fetchone()
            if not user_result:
                conn.close()
                return {"success": False, "status_code": 404, "message": f"User ID {user_id} not found"}
            
            username = user_result[0]
            
            # Delete user
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            
            return {
                "success": True, 
                "status_code": 200, 
                "data": {
                    "message": f"User '{username}' deleted successfully"
                }
            }
        except Exception as e:
            logging.error(f"Error deleting user ID {user_id}: {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    # --- Order Methods ---
    
    def create_order(self, order_number, description=None):
        """Create a new order (Admin/Manager only)."""
        if not self.current_user:
            return {"success": False, "status_code": 401, "message": "Authentication required"}
        
        role = self.current_user.get('role')
        if role not in ('Admin', 'Manager'):
            return {"success": False, "status_code": 403, "message": "Requires Admin or Manager role"}
        
        # Determine department based on user
        department_name = self.current_user.get('department')
        if not department_name and role != 'Admin':
            return {"success": False, "status_code": 400, "message": "User must belong to a department to create orders"}
        
        # For Admin users without department, create order in a general database
        if role == 'Admin' and not department_name:
            department_name = "Admin"
        
        try:
            # Initialize department database if needed
            self._initialize_department_db(department_name)
            db_path = self._get_department_db_path(department_name)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if order number already exists
            cursor.execute('SELECT id FROM orders WHERE order_number = ?', (order_number,))
            if cursor.fetchone():
                conn.close()
                return {"success": False, "status_code": 409, "message": f"Order number '{order_number}' already exists"}
            
            # Create order
            now = datetime.now().isoformat()
            cursor.execute(
                'INSERT INTO orders (order_number, description, created_at, created_by_user_id) VALUES (?, ?, ?, ?)',
                (order_number, description, now, self.current_user.get('id'))
            )
            
            order_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                "success": True, 
                "status_code": 201, 
                "data": {
                    "message": "Order created successfully",
                    "order": {
                        "id": order_id,
                        "order_number": order_number,
                        "description": description,
                        "created_at": now,
                        "created_by_user_id": self.current_user.get('id')
                    }
                }
            }
        except Exception as e:
            logging.error(f"Error creating order '{order_number}': {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    def get_orders(self):
        """Get all orders."""
        if not self.current_user:
            return {"success": False, "status_code": 401, "message": "Authentication required"}
        
        try:
            orders_list = []
            
            # For Admin users, collect orders from all departments
            if self.current_user.get('role') == 'Admin':
                # Get all department names
                conn = sqlite3.connect(self.users_db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM departments')
                departments = [dept[0] for dept in cursor.fetchall()]
                conn.close()
                
                # Add Admin department for orders created by admins without department
                departments.append("Admin")
                
                # Collect orders from each department
                for dept_name in departments:
                    db_path = self._get_department_db_path(dept_name)
                    if not db_path.exists():
                        continue
                    
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT o.id, o.order_number, o.description, o.created_at, o.created_by_user_id
                        FROM orders o
                        ORDER BY o.created_at DESC
                    ''')
                    
                    for order_id, order_number, description, created_at, created_by_user_id in cursor.fetchall():
                        orders_list.append({
                            "id": order_id,
                            "order_number": order_number,
                            "description": description,
                            "created_at": created_at,
                            "created_by_user_id": created_by_user_id,
                            "department_name": dept_name
                        })
                    
                    conn.close()
            else:
                # Regular users only see orders from their department
                department_name = self.current_user.get('department')
                if not department_name:
                    return {
                        "success": True, 
                        "status_code": 200, 
                        "data": {
                            "orders": []
                        }
                    }
                
                db_path = self._get_department_db_path(department_name)
                if not db_path.exists():
                    return {
                        "success": True, 
                        "status_code": 200, 
                        "data": {
                            "orders": []
                        }
                    }
                
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT o.id, o.order_number, o.description, o.created_at, o.created_by_user_id
                    FROM orders o
                    ORDER BY o.created_at DESC
                ''')
                
                for order_id, order_number, description, created_at, created_by_user_id in cursor.fetchall():
                    orders_list.append({
                        "id": order_id,
                        "order_number": order_number,
                        "description": description,
                        "created_at": created_at,
                        "created_by_user_id": created_by_user_id,
                        "department_name": department_name
                    })
                
                conn.close()
            
            # Get creator usernames
            user_ids = set(order["created_by_user_id"] for order in orders_list)
            usernames = {}
            
            if user_ids:
                conn = sqlite3.connect(self.users_db_path)
                cursor = conn.cursor()
                
                for user_id in user_ids:
                    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
                    result = cursor.fetchone()
                    if result:
                        usernames[user_id] = result[0]
                
                conn.close()
            
            # Add creator usernames to orders
            for order in orders_list:
                creator_id = order["created_by_user_id"]
                order["creator_username"] = usernames.get(creator_id, "Unknown")
            
            return {
                "success": True, 
                "status_code": 200, 
                "data": {
                    "orders": orders_list
                }
            }
        except Exception as e:
            logging.error(f"Error retrieving orders: {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    def delete_order(self, order_id):
        """Delete an order (Admin only)."""
        if not self.current_user:
            return {"success": False, "status_code": 401, "message": "Authentication required"}
        
        if self.current_user.get('role') != 'Admin':
            return {"success": False, "status_code": 403, "message": "Requires Admin role"}
        
        # Since we need to search across departments, this is more complex
        try:
            # Get all department names
            conn = sqlite3.connect(self.users_db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM departments')
            departments = [dept[0] for dept in cursor.fetchall()]
            conn.close()
            
            # Add Admin department
            departments.append("Admin")
            
            # Search for the order in each department
            for dept_name in departments:
                db_path = self._get_department_db_path(dept_name)
                if not db_path.exists():
                    continue
                
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if order exists
                cursor.execute('SELECT order_number FROM orders WHERE id = ?', (order_id,))
                order_result = cursor.fetchone()
                
                if order_result:
                    order_number = order_result[0]
                    
                    # Delete associated scans first
                    cursor.execute('DELETE FROM scans WHERE order_id = ?', (order_id,))
                    
                    # Delete the order
                    cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))
                    conn.commit()
                    conn.close()
                    
                    return {
                        "success": True, 
                        "status_code": 200, 
                        "data": {
                            "message": f"Order '{order_number}' deleted successfully"
                        }
                    }
                
                conn.close()
            
            # If we get here, order was not found
            return {"success": False, "status_code": 404, "message": f"Order ID {order_id} not found"}
        except Exception as e:
            logging.error(f"Error deleting order ID {order_id}: {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    # --- Scan Methods ---
    
    def record_scan(self, barcode, status, order_id, notes=None):
        """Record a new scan."""
        if not self.current_user:
            return {"success": False, "status_code": 401, "message": "Authentication required"}
        
        department_name = self.current_user.get('department')
        if not department_name:
            return {"success": False, "status_code": 400, "message": "User must belong to a department to record scans"}
        
        try:
            db_path = self._get_department_db_path(department_name)
            if not db_path.exists():
                return {"success": False, "status_code": 404, "message": f"Department database not found for '{department_name}'"}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if order exists
            cursor.execute('SELECT id FROM orders WHERE id = ?', (order_id,))
            if not cursor.fetchone():
                conn.close()
                return {"success": False, "status_code": 404, "message": f"Order ID {order_id} not found"}
            
            # Check for duplicate barcode for this order
            cursor.execute('SELECT id FROM scans WHERE barcode = ? AND order_id = ?', (barcode, order_id))
            if cursor.fetchone():
                conn.close()
                return {
                    "success": False, 
                    "status_code": 409, 
                    "message": f"Barcode '{barcode}' has already been scanned for this order"
                }
            
            # Create scan record
            now = datetime.now().isoformat()
            cursor.execute(
                'INSERT INTO scans (barcode, timestamp, status, notes, user_id, order_id) VALUES (?, ?, ?, ?, ?, ?)',
                (barcode, now, status, notes, self.current_user.get('id'), order_id)
            )
            
            scan_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return {
                "success": True, 
                "status_code": 201, 
                "data": {
                    "message": "Scan recorded successfully",
                    "scan": {
                        "id": scan_id,
                        "barcode": barcode,
                        "timestamp": now,
                        "status": status,
                        "notes": notes,
                        "user_id": self.current_user.get('id'),
                        "department_id": self.current_user.get('department_id'),
                        "order_id": order_id
                    }
                }
            }
        except Exception as e:
            logging.error(f"Error recording scan for barcode '{barcode}': {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    def get_scans(self, order_id=None, user_id=None, department_id=None):
        """Get scans with optional filtering."""
        if not self.current_user:
            return {"success": False, "status_code": 401, "message": "Authentication required"}
        
        try:
            scans_list = []
            
            # Determine which departments to query
            departments_to_query = []
            
            if self.current_user.get('role') == 'Admin':
                # Admin can see scans from all departments
                if department_id:
                    # Get specific department name if department_id is provided
                    conn = sqlite3.connect(self.users_db_path)
                    cursor = conn.cursor()
                    cursor.execute('SELECT name FROM departments WHERE id = ?', (department_id,))
                    dept_result = cursor.fetchone()
                    conn.close()
                    
                    if dept_result:
                        departments_to_query.append(dept_result[0])
                else:
                    # Get all department names
                    conn = sqlite3.connect(self.users_db_path)
                    cursor = conn.cursor()
                    cursor.execute('SELECT name FROM departments')
                    departments_to_query = [dept[0] for dept in cursor.fetchall()]
                    conn.close()
            else:
                # Regular users only see scans from their department
                departments_to_query = [self.current_user.get('department')] if self.current_user.get('department') else []
            
            # Query each department
            for dept_name in departments_to_query:
                db_path = self._get_department_db_path(dept_name)
                if not db_path.exists():
                    continue
                
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Build query based on filters
                query = 'SELECT id, barcode, timestamp, status, notes, user_id, order_id FROM scans'
                params = []
                conditions = []
                
                if order_id:
                    conditions.append('order_id = ?')
                    params.append(order_id)
                
                if user_id:
                    conditions.append('user_id = ?')
                    params.append(user_id)
                
                if conditions:
                    query += ' WHERE ' + ' AND '.join(conditions)
                
                query += ' ORDER BY timestamp DESC'
                
                cursor.execute(query, params)
                
                for scan_id, barcode, timestamp, status, notes, scan_user_id, scan_order_id in cursor.fetchall():
                    # Get order number
                    cursor.execute('SELECT order_number FROM orders WHERE id = ?', (scan_order_id,))
                    order_result = cursor.fetchone()
                    order_number = order_result[0] if order_result else "Unknown"
                    
                    scans_list.append({
                        "id": scan_id,
                        "barcode": barcode,
                        "timestamp": timestamp,
                        "status": status,
                        "notes": notes,
                        "user_id": scan_user_id,
                        "order_id": scan_order_id,
                        "order_number": order_number,
                        "department_name": dept_name
                    })
                
                conn.close()
            
            # Get usernames for the scans
            user_ids = set(scan["user_id"] for scan in scans_list)
            usernames = {}
            
            if user_ids:
                conn = sqlite3.connect(self.users_db_path)
                cursor = conn.cursor()
                
                for user_id in user_ids:
                    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
                    result = cursor.fetchone()
                    if result:
                        usernames[user_id] = result[0]
                
                conn.close()
            
            # Add usernames to scans
            for scan in scans_list:
                scan_user_id = scan["user_id"]
                scan["username"] = usernames.get(scan_user_id, "Unknown")
            
            return {
                "success": True, 
                "status_code": 200, 
                "data": {
                    "scans": scans_list
                }
            }
        except Exception as e:
            logging.error(f"Error retrieving scans: {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    def update_scan(self, scan_id, status=None, notes=None):
        """Update a scan (Admin/Manager only)."""
        if not self.current_user:
            return {"success": False, "status_code": 401, "message": "Authentication required"}
        
        role = self.current_user.get('role')
        if role not in ('Admin', 'Manager'):
            return {"success": False, "status_code": 403, "message": "Requires Admin or Manager role"}
        
        try:
            # For Admin, search all departments, otherwise just user's department
            departments_to_search = []
            
            if role == 'Admin':
                # Get all department names
                conn = sqlite3.connect(self.users_db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM departments')
                departments_to_search = [dept[0] for dept in cursor.fetchall()]
                conn.close()
            else:
                # Manager can only edit scans in their department
                department_name = self.current_user.get('department')
                if department_name:
                    departments_to_search = [department_name]
            
            # Search for the scan in each department
            for dept_name in departments_to_search:
                db_path = self._get_department_db_path(dept_name)
                if not db_path.exists():
                    continue
                
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if scan exists
                cursor.execute('SELECT id FROM scans WHERE id = ?', (scan_id,))
                if not cursor.fetchone():
                    conn.close()
                    continue  # Try next department
                
                # Update scan
                update_parts = []
                params = []
                
                if status is not None:
                    update_parts.append('status = ?')
                    params.append(status)
                
                if notes is not None:
                    update_parts.append('notes = ?')
                    params.append(notes)
                
                if not update_parts:
                    conn.close()
                    return {"success": True, "status_code": 200, "message": "No updates provided"}
                
                query = f"UPDATE scans SET {', '.join(update_parts)} WHERE id = ?"
                params.append(scan_id)
                
                cursor.execute(query, params)
                conn.commit()
                
                # Get updated scan
                cursor.execute('''
                    SELECT s.id, s.barcode, s.timestamp, s.status, s.notes, s.user_id, s.order_id, o.order_number
                    FROM scans s
                    JOIN orders o ON s.order_id = o.id
                    WHERE s.id = ?
                ''', (scan_id,))
                
                scan = cursor.fetchone()
                conn.close()
                
                if scan:
                    scan_id, barcode, timestamp, status, notes, user_id, order_id, order_number = scan
                    
                    # Get username
                    conn = sqlite3.connect(self.users_db_path)
                    cursor = conn.cursor()
                    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
                    username_result = cursor.fetchone()
                    username = username_result[0] if username_result else "Unknown"
                    conn.close()
                    
                    return {
                        "success": True, 
                        "status_code": 200, 
                        "data": {
                            "message": "Scan updated successfully",
                            "scan": {
                                "id": scan_id,
                                "barcode": barcode,
                                "timestamp": timestamp,
                                "status": status,
                                "notes": notes,
                                "user_id": user_id,
                                "username": username,
                                "order_id": order_id,
                                "order_number": order_number,
                                "department_name": dept_name
                            }
                        }
                    }
            
            # If we get here, scan was not found
            return {"success": False, "status_code": 404, "message": f"Scan ID {scan_id} not found"}
        except Exception as e:
            logging.error(f"Error updating scan ID {scan_id}: {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    def delete_scan(self, scan_id):
        """Delete a scan (Admin/Manager only)."""
        if not self.current_user:
            return {"success": False, "status_code": 401, "message": "Authentication required"}
        
        role = self.current_user.get('role')
        if role not in ('Admin', 'Manager'):
            return {"success": False, "status_code": 403, "message": "Requires Admin or Manager role"}
        
        try:
            # For Admin, search all departments, otherwise just user's department
            departments_to_search = []
            
            if role == 'Admin':
                # Get all department names
                conn = sqlite3.connect(self.users_db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT name FROM departments')
                departments_to_search = [dept[0] for dept in cursor.fetchall()]
                conn.close()
            else:
                # Manager can only delete scans in their department
                department_name = self.current_user.get('department')
                if department_name:
                    departments_to_search = [department_name]
            
            # Search for the scan in each department
            for dept_name in departments_to_search:
                db_path = self._get_department_db_path(dept_name)
                if not db_path.exists():
                    continue
                
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if scan exists
                cursor.execute('SELECT barcode FROM scans WHERE id = ?', (scan_id,))
                scan_result = cursor.fetchone()
                
                if scan_result:
                    barcode = scan_result[0]
                    
                    # Delete the scan
                    cursor.execute('DELETE FROM scans WHERE id = ?', (scan_id,))
                    conn.commit()
                    conn.close()
                    
                    return {
                        "success": True, 
                        "status_code": 200, 
                        "data": {
                            "message": f"Scan for barcode '{barcode}' deleted successfully"
                        }
                    }
                
                conn.close()
            
            # If we get here, scan was not found
            return {"success": False, "status_code": 404, "message": f"Scan ID {scan_id} not found"}
        except Exception as e:
            logging.error(f"Error deleting scan ID {scan_id}: {e}")
            return {"success": False, "status_code": 500, "message": f"Database error: {str(e)}"}

    # --- Feedback Method ---
    
    def submit_feedback(self, feedback_text):
        """Submit user feedback."""
        if not self.current_user:
            return {"success": False, "status_code": 401, "message": "Authentication required"}
        
        try:
            # Create dev folder if it doesn't exist
            feedback_dir = self.dev_path / "errors-feedback"
            feedback_dir.mkdir(exist_ok=True)
            
            feedback_file = feedback_dir / "user_feedback.txt"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            username = self.current_user.get('username')
            
            feedback_entry = f"\n--- Feedback from {username} at {timestamp} ---\n{feedback_text}\n"
            
            # Append to feedback file
            with open(feedback_file, 'a', encoding='utf-8') as f:
                f.write(feedback_entry)
            
            return {
                "success": True, 
                "status_code": 200, 
                "data": {
                    "message": "Feedback submitted successfully"
                }
            }
        except Exception as e:
            logging.error(f"Error submitting feedback: {e}")
            return {"success": False, "status_code": 500, "message": f"Error: {str(e)}"} 
import json
import os
from datetime import datetime
import traceback

class DataManager:
    def __init__(self):
        self.users_file = "users.json"
        self.orders_file = "orders.json"
        self.departments_file = "departments.json"
        
        # Load data
        self.users = self.load_users()
        self.departments = self.load_departments()
        self.orders = {} # Empty initially for simplicity
    
    def load_users(self):
        try:
            # Default admin user as fallback
            default_users = {
                "admin": {
                    "password": "password",
                    "department": "admin",
                    "is_manager": True
                }
            }
            
            # Try to load from file
            if os.path.exists(self.users_file):
                with open(self.users_file, "r") as f:
                    users = json.load(f)
                    print(f"Loaded {len(users)} users from {self.users_file}")
                    return users
            else:
                print(f"Users file not found: {self.users_file}. Using default admin user.")
                return default_users
        except Exception as e:
            print(f"Error loading users: {e}")
            traceback.print_exc()
            return default_users

    def load_departments(self):
        try:
            # Default departments
            defaults = {
                "admin": {
                    "name": "Administration",
                    "permissions": ["manage_users", "manage_orders", "view_all", "view_all_orders", "create_orders"]
                }
            }
            
            # Try to load from file
            if os.path.exists(self.departments_file):
                with open(self.departments_file, "r") as f:
                    depts = json.load(f)
                    print(f"Loaded {len(depts)} departments from {self.departments_file}")
                    return depts
            else:
                print(f"Departments file not found: {self.departments_file}. Using defaults.")
                return defaults
        except Exception as e:
            print(f"Error loading departments: {e}")
            traceback.print_exc()
            return defaults
    
    def get_user_department(self, username):
        user_data = self.users.get(username, {})
        return user_data.get("department", None) if isinstance(user_data, dict) else None
    
    def is_manager(self, username):
        user_data = self.users.get(username, {})
        return user_data.get("is_manager", False) if isinstance(user_data, dict) else False
    
    def has_permission(self, username, permission):
        # Admin has all permissions
        if username == "admin":
            return True
        
        # Check if user is a manager with special permissions
        if self.is_manager(username) and permission in ["create_orders", "manage_orders", "view_all_orders"]:
            return True
        
        # Check department permissions
        department = self.get_user_department(username)
        if department:
            permissions = self.departments.get(department, {}).get("permissions", [])
            return permission in permissions
        
        return False
    
    def load_orders(self, force_reload=False):
        try:
            if hasattr(self, 'orders') and self.orders and not force_reload:
                return self.orders
            
            if not os.path.exists(self.orders_file):
                return {}
            
            with open(self.orders_file, "r") as f:
                orders = json.load(f)
                self.orders = orders
                return orders
        except Exception as e:
            print(f"Error loading orders: {e}")
            traceback.print_exc()
            return {}

    def save_orders(self, orders):
        try:
            with open(self.orders_file, "w") as f:
                json.dump(orders, f, indent=2)
            self.orders = orders
            return True
        except Exception as e:
            print(f"Error saving orders: {e}")
            traceback.print_exc()
            return False
    
    def save_users(self, users):
        try:
            with open(self.users_file, "w") as f:
                json.dump(users, f, indent=2)
            self.users = users
            return True
        except Exception as e:
            print(f"Error saving users: {e}")
            traceback.print_exc()
            return False
    
    def save_departments(self, departments):
        try:
            # print("DEBUG: Saving departments") # Reduced noise
            with open(self.departments_file, "w") as f:
                json.dump(departments, f, indent=2)
            self.departments = departments
            return True
        except Exception as e:
            print(f"Error saving departments: {e}")
            return False
    
    def create_order(self, order_number, quantity=None, customer_name=None, board_name=None, comments=None, created_by=None):
        """Create a new order with extended information.
        
        Args:
            order_number: Unique identifier for the order
            quantity: Total order quantity
            customer_name: Name of the customer
            board_name: Name of the board type for this order
            comments: Initial general comments for the order
            created_by: Username of the person creating the order
        
        Returns:
            True if successful, False if order already exists
        """
        orders = self.load_orders()
        if order_number in orders:
            print(f"Attempted to create duplicate order: {order_number}")
            return False # Order already exists
            
        # Create timestamp for order creation
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Initialize new order with extended information
        orders[order_number] = {
            "barcodes": [],
            "board_comments": {},  # Structure for board-specific comments
            "comments": [],        # General comments about the order
            "boards": {},          # Structure for board management
            "created_at": timestamp,
            "created_by": created_by,
            "quantity": quantity,
            "customer_name": customer_name,
            "board_name": board_name,
            "order_details": {
                "status": "Created",
                "last_updated": timestamp
            }
        }
        
        # Add initial comment if provided
        if comments and created_by:
            orders[order_number]["comments"].append({
                "text": comments,
                "user": created_by,
                "timestamp": timestamp
            })
            
        # print(f"DEBUG: Creating order '{order_number}'") # Reduced noise
        return self.save_orders(orders)
    
    def add_barcode(self, order_number, barcode, username=None):
        """Add a barcode to an order, creating board entry if needed."""
        try:
            orders = self.load_orders()
            if order_number not in orders:
                print(f"Order {order_number} not found for adding barcode {barcode}")
                return (False, "Order not found")

            order_data = orders[order_number]
            # Initialize lists/dicts if missing (robustness)
            if "barcodes" not in order_data: order_data["barcodes"] = []
            if "boards" not in order_data: order_data["boards"] = {}

            # Check if barcode already exists in THIS order
            if barcode in order_data["barcodes"]:
                msg = f"Barcode {barcode} already exists in order {order_number}"
                if barcode in order_data["boards"]:
                    orig_user = order_data["boards"][barcode].get("added_by", "Unknown")
                    orig_time = order_data["boards"][barcode].get("added_at", "N/A")
                    msg += f"\n(Scanned by {orig_user} at {orig_time})"
                # print(f"DEBUG: {msg}") # Reduced noise
                return (False, msg)

            # Check if barcode exists in ANY OTHER order
            other_order_info = self._check_barcode_in_other_orders(barcode, order_number, orders)

            # Add the barcode to the list
            order_data["barcodes"].append(barcode)

            # Add/Update the corresponding board entry
            if barcode not in order_data["boards"]:
                department = self.get_user_department(username) if username else "Unknown"
                order_data["boards"][barcode] = {
                    "description": "Added via barcode scanner",
                    "department": department,
                    "added_by": username or "Unknown",
                    "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                # print(f"DEBUG: Added barcode {barcode} as new board in order {order_number}") # Reduced noise
            else:
                # If board already existed (e.g., added manually before scan), maybe update scan time?
                # For now, we just ensure it's in the barcode list.
                # print(f"DEBUG: Barcode {barcode} already existed as board, added to barcode list in order {order_number}") # Reduced noise
                pass

            # Save changes
            success = self.save_orders(orders)
            if success:
                final_msg = f"Barcode {barcode} added to order {order_number}"
                if other_order_info:
                    final_msg += f".\n\n{other_order_info}"
                return (True, final_msg)
            else:
                return (False, "Failed to save updated order data")
        except Exception as e:
            print(f"Error adding barcode {barcode} to order {order_number}: {str(e)}")
            traceback.print_exc()
            return (False, f"Internal error adding barcode: {str(e)}")

    def _check_barcode_in_other_orders(self, barcode, current_order_number, all_orders):
        """Checks if a barcode exists in orders other than the current one."""
        for other_order, other_data in all_orders.items():
            if other_order == current_order_number: continue
            if barcode in other_data.get("barcodes", []):
                msg = f"Note: Barcode {barcode} also exists in order {other_order}"
                if barcode in other_data.get("boards", {}):
                    orig_user = other_data["boards"][barcode].get("added_by", "Unknown")
                    orig_time = other_data["boards"][barcode].get("added_at", "N/A")
                    msg += f"\n(Scanned by {orig_user} at {orig_time})"
                # print(f"DEBUG: {msg}") # Reduced noise
                return msg
        return "" # Not found in other orders

    def delete_barcode(self, order_number, barcode):
        """Deletes only the barcode entry, leaves board data if exists."""
        # This might be less useful now that adding barcode creates board.
        # Consider if this should delete the board too, or be removed.
        orders = self.load_orders()
        if order_number in orders and "barcodes" in orders[order_number]:
            try:
                orders[order_number]["barcodes"].remove(barcode)
                # print(f"DEBUG: Deleted barcode '{barcode}' from order '{order_number}'") # Reduced noise
                return self.save_orders(orders)
            except ValueError:
                # print(f"DEBUG: Barcode '{barcode}' not found in order '{order_number}' for deletion.") # Reduced noise
                return False # Barcode wasn't in the list
        return False
    
    def delete_order(self, order_number):
        try:
            orders = self.load_orders()
            if order_number in orders:
                del orders[order_number]
                # print(f"DEBUG: Deleting order '{order_number}'") # Reduced noise
                return self.save_orders(orders)
            # print(f"DEBUG: Order '{order_number}' not found for deletion.") # Reduced noise
            return False
        except Exception as e:
            print(f"Error deleting order: {e}")
            traceback.print_exc()
            return False
    
    def create_user(self, username, password, department, is_manager=False):
        try:
            users = self.load_users()
            if username in users:
                return False
            users[username] = {
                "password": password,
                "department": department,
                "is_manager": is_manager
            }
            return self.save_users(users)
        except Exception as e:
            print(f"Error creating user: {e}")
            traceback.print_exc()
            return False
    
    def delete_user(self, username):
        try:
            users = self.load_users()
            if username in users and username != "admin":
                del users[username]
                # print(f"DEBUG: Deleting user '{username}'") # Reduced noise
                return self.save_users(users)
            # print(f"DEBUG: User '{username}' not found for deletion.") # Reduced noise
            return False
        except Exception as e:
            print(f"Error deleting user: {e}")
            traceback.print_exc()
            return False
    
    def get_department_permissions(self, department_id):
        # Use cached departments
        return self.departments.get(department_id, {}).get("permissions", [])
    
    def add_comment(self, order_number, comment_text, username):
        """Adds a general order comment."""
        orders = self.load_orders()
        if order_number in orders:
            if "comments" not in orders[order_number]:
                orders[order_number]["comments"] = [] # Initialize if missing
            comment_data = {
                "text": comment_text,
                "user": username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            orders[order_number]["comments"].append(comment_data)
            # print(f"DEBUG: Added general comment to order '{order_number}' by '{username}'") # Reduced noise
            return self.save_orders(orders)
        # print(f"DEBUG: Order '{order_number}' not found to add general comment.") # Reduced noise
        return False
    
    def get_comments(self, order_number):
        """Gets general comments for an order."""
        orders = self.load_orders() # Consider using cache unless reload needed
        return orders.get(order_number, {}).get("comments", [])
    
    def add_board_comment(self, order_number, board_id, comment_text, username):
        """Adds a comment specific to a board within an order."""
        orders = self.load_orders()
        if order_number in orders:
            order_data = orders[order_number]
            if "board_comments" not in order_data: order_data["board_comments"] = {}
            if board_id not in order_data["board_comments"]: order_data["board_comments"][board_id] = []

            comment_data = {
                "text": comment_text,
                "user": username,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            order_data["board_comments"][board_id].append(comment_data)
            # print(f"DEBUG: Added comment to board '{board_id}' in order '{order_number}' by '{username}'") # Reduced noise
            return self.save_orders(orders)
        # print(f"DEBUG: Order '{order_number}' not found to add comment to board '{board_id}'.") # Reduced noise
        return False
    
    def get_board_comments(self, order_number, board_id):
        """Gets comments for a specific board within an order."""
        orders = self.load_orders() # Consider using cache
        return orders.get(order_number, {}).get("board_comments", {}).get(board_id, [])
    
    def get_boards_with_comments(self, order_number):
        """Gets a list of board IDs that have comments for a given order."""
        orders = self.load_orders() # Consider using cache
        return list(orders.get(order_number, {}).get("board_comments", {}).keys())
    
    def set_manager_status(self, username, is_manager):
        try:
            users = self.load_users()
            if username in users and username != "admin":
                users[username]["is_manager"] = is_manager
                # print(f"DEBUG: Setting manager status for '{username}' to {is_manager}") # Reduced noise
                return self.save_users(users)
            # print(f"DEBUG: Failed to set manager status for '{username}' (not found or admin)") # Reduced noise
            return False
        except Exception as e:
            print(f"Error setting manager status: {e}")
            traceback.print_exc()
            return False
    
    def add_board_to_order(self, order_number, board_id, description, username):
        """Adds a new board entry manually (not via barcode scan)."""
        try:
            orders = self.load_orders()
            if order_number not in orders:
                print(f"Order {order_number} not found for adding board {board_id}")
                return (False, "Order not found")

            order_data = orders[order_number]
            if "boards" not in order_data: order_data["boards"] = {}
            if "barcodes" not in order_data: order_data["barcodes"] = []

            # Check if board ID already exists in this order's boards
            if board_id in order_data["boards"]:
                orig_user = order_data["boards"][board_id].get("added_by", "Unknown")
                orig_time = order_data["boards"][board_id].get("added_at", "N/A")
                msg = f"Board {board_id} already exists in order {order_number}\n(Added by {orig_user} at {orig_time})"
                # print(f"DEBUG: {msg}") # Reduced noise
                return (False, msg)

            # Check if board ID exists in ANY OTHER order
            other_order_info = self._check_board_in_other_orders(board_id, order_number, orders)

            # Add the board data
            department = self.get_user_department(username) or "Unknown"
            order_data["boards"][board_id] = {
                "description": description or "Manually added", # Default description
                "department": department,
                "added_by": username,
                "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Also add to barcode list for consistency if not already there
            if board_id not in order_data["barcodes"]:
                order_data["barcodes"].append(board_id)
                # print(f"DEBUG: Added board '{board_id}' manually and to barcode list in order '{order_number}'") # Reduced noise
            else:
                 # print(f"DEBUG: Added board '{board_id}' manually (already in barcode list) in order '{order_number}'") # Reduced noise
                 pass

            # Save changes
            saved = self.save_orders(orders)
            if saved:
                final_msg = f"Board {board_id} added successfully to order {order_number}"
                if other_order_info:
                    final_msg += f".\n\n{other_order_info}"
                return (True, final_msg)
            else:
                return (False, "Failed to save updated order data")
        except Exception as e:
            print(f"Error adding board {board_id} to order {order_number}: {str(e)}")
            traceback.print_exc()
            return (False, f"Internal error adding board: {str(e)}")

    def _check_board_in_other_orders(self, board_id, current_order_number, all_orders):
        """Checks if a board ID exists in the 'boards' dict of other orders."""
        for other_order, other_data in all_orders.items():
            if other_order == current_order_number: continue
            if board_id in other_data.get("boards", {}):
                orig_user = other_data["boards"][board_id].get("added_by", "Unknown")
                orig_time = other_data["boards"][board_id].get("added_at", "N/A")
                msg = f"Note: Board {board_id} also exists in order {other_order}\n(Added by {orig_user} at {orig_time})"
                # print(f"DEBUG: {msg}") # Reduced noise
                return msg
        return ""

    def get_boards_for_order(self, order_number, force_reload=False):
        """Get all boards (from 'boards' dict) for a specific order."""
        try:
            orders = self.load_orders(force_reload=force_reload)
            order_data = orders.get(order_number, {})
            # Ensure 'boards' dict exists, create if not (data migration)
            if "boards" not in order_data:
                order_data["boards"] = {}
                # Optionally save back if migration occurred, but might be slow.
                # If saving, need to handle potential recursion if called during save.
                # self.save_orders(orders) # Be cautious with saving inside a load method
            return order_data.get("boards", {})
        except Exception as e:
            print(f"Error getting boards for order {order_number}: {str(e)}")
            traceback.print_exc()
            return {}

    def find_board_in_orders(self, board_id):
        """Finds a specific board ID across all orders (checks boards, then barcodes, then comments)."""
        # print(f"DEBUG: Searching for board ID: {board_id} across all orders") # Reduced noise
        orders = self.load_orders() # Use cache typically

        # 1. Check 'boards' dictionary first
        for order_number, order_data in orders.items():
            if board_id in order_data.get("boards", {}):
                # print(f"DEBUG: Board '{board_id}' found in boards dict of order '{order_number}'") # Reduced noise
                return (order_number, order_data["boards"][board_id])

        # 2. Check 'barcodes' list if not found in 'boards'
        for order_number, order_data in orders.items():
            if board_id in order_data.get("barcodes", []):
                # print(f"DEBUG: Board ID '{board_id}' found as barcode in order '{order_number}'") # Reduced noise
                # Return minimal info as it wasn't explicitly in 'boards'
                return (order_number, {"description": "Barcode only", "added_at": "N/A", "added_by": "N/A"})

        # 3. Check 'board_comments' if not found elsewhere
        for order_number, order_data in orders.items():
            if board_id in order_data.get("board_comments", {}):
                # print(f"DEBUG: Board ID '{board_id}' found with comments in order '{order_number}'") # Reduced noise
                # Return minimal info
                return (order_number, {"description": "Comments only", "added_at": "N/A", "added_by": "N/A"})

        # print(f"DEBUG: Board ID '{board_id}' not found in any order.") # Reduced noise
        return None

    def find_board_in_specific_order(self, board_id, order_number):
        """Finds a specific board ID in a specific order."""
        # print(f"DEBUG: Searching for board ID: {board_id} in order: {order_number}") # Reduced noise
        orders = self.load_orders() # Use cache typically
        order_data = orders.get(order_number)

        if not order_data:
            # print(f"DEBUG: Order {order_number} not found.") # Reduced noise
            return None

        # Check boards, then barcodes, then comments within this order
        if board_id in order_data.get("boards", {}):
             # print(f"DEBUG: Board '{board_id}' found in boards dict.") # Reduced noise
             return order_data["boards"][board_id]
        if board_id in order_data.get("barcodes", []):
            # print(f"DEBUG: Board ID '{board_id}' found as barcode.") # Reduced noise
            return {"description": "Barcode only", "added_at": "N/A", "added_by": "N/A"}
        if board_id in order_data.get("board_comments", {}):
            # print(f"DEBUG: Board ID '{board_id}' found with comments.") # Reduced noise
            return {"description": "Comments only", "added_at": "N/A", "added_by": "N/A"}

        # print(f"DEBUG: Board ID '{board_id}' not found in order {order_number}.") # Reduced noise
        return None

    def delete_board(self, order_number, board_id, username):
        """Delete a board from an order (requires manager permission) and logs the action."""
        # Permission check now done by has_permission
        if not self.has_permission(username, "delete_boards"):
             print(f"Permission denied for '{username}' to delete board '{board_id}' from order '{order_number}'")
             return (False, "Permission denied. Board deletion requires manager authority.")

        try:
            orders = self.load_orders(force_reload=True) # Force reload for critical operation
            if order_number not in orders:
                print(f"Order {order_number} not found for deleting board {board_id}")
                return (False, f"Order {order_number} not found")

            order_data = orders[order_number]
            board_info_text = ""
            found = False

            # Remove from 'boards' dict if exists
            if board_id in order_data.get("boards", {}):
                board_data = order_data["boards"][board_id]
                board_info_text = (
                    f"• Board information before deletion:\n"
                    f"  - Description: {board_data.get('description', 'N/A')}\n"
                    f"  - Department: {board_data.get('department', 'N/A')}\n"
                    f"  - Originally added by: {board_data.get('added_by', 'Unknown')} at {board_data.get('added_at', 'N/A')}"
                )
                del order_data["boards"][board_id]
                found = True
                # print(f"DEBUG: Deleted board '{board_id}' from boards dict in order '{order_number}'") # Reduced noise

            # Remove from 'barcodes' list if exists
            if board_id in order_data.get("barcodes", []):
                order_data["barcodes"].remove(board_id)
                found = True # Mark as found even if only in barcodes
                # print(f"DEBUG: Deleted board ID '{board_id}' from barcodes list in order '{order_number}'") # Reduced noise
                if not board_info_text: # If it was only a barcode
                     board_info_text = "• Board existed only as a barcode entry before deletion."

            # Remove from 'board_comments' if exists
            if board_id in order_data.get("board_comments", {}):
                del order_data["board_comments"][board_id]
                found = True # Mark as found even if only in comments
                # print(f"DEBUG: Deleted comments for board ID '{board_id}' in order '{order_number}'") # Reduced noise
                if not board_info_text: # If it only had comments
                     board_info_text = "• Board existed only with comments before deletion."

            if not found:
                print(f"Board {board_id} not found in order {order_number} for deletion.")
                return (False, f"Board {board_id} not found in order {order_number}")

            # Add a general comment logging the deletion
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            comment_text = (
                f"BOARD DELETED: {board_id}\n"
                f"• Order: {order_number}\n"
                f"• Deleted by: {username}\n"
                f"• Deleted at: {timestamp}\n"
                f"{board_info_text}"
            )
            # Use the add_comment method to append to general comments
            if "comments" not in order_data: order_data["comments"] = []
            order_data["comments"].append({
                "text": comment_text, "user": username, "timestamp": timestamp
            })

            # Save the modified orders data
            self.save_orders(orders)
            return (True, f"Board {board_id} successfully deleted from order {order_number}")

        except Exception as e:
            print(f"Error deleting board {board_id} from order {order_number}: {str(e)}")
            traceback.print_exc()
            return (False, f"Internal error deleting board: {str(e)}") 
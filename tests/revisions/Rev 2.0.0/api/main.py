from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user, login_user, logout_user
from functools import wraps
from .models import db, Order, User, Scan, ScanStatus, RoleType, Role, Department, Comment
import logging

main = Blueprint('main', __name__)

# --- Re-add Decorators for Role Checks ---
def role_required(role_enum):
    """Decorator to require a specific role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not hasattr(current_user, 'role') or current_user.role.name != role_enum:
                return jsonify({"message": f"Requires {role_enum.value} role"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def roles_required(*role_enums):
    """Decorator to require one of several roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not hasattr(current_user, 'role'):
                return jsonify({"message": "Authentication required"}), 401
            user_role_name = current_user.role.name
            if user_role_name not in role_enums:
                allowed_roles_str = ', '.join([r.value for r in role_enums])
                return jsonify({"message": f"Requires one of the following roles: {allowed_roles_str}"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Basic Index Route (Keep) ---
@main.route('/')
def index():
    """Placeholder for the main index or status route."""
    return jsonify({"message": "API is running"})


# --- Order Routes ---
@main.route('/orders', methods=['POST'])
@login_required
@roles_required(RoleType.ADMIN, RoleType.MANAGER)
def create_order():
    """Creates a new order."""
    data = request.get_json()
    if not data or not data.get('order_number'):
        return jsonify({"message": "Missing required field: order_number"}), 400

    order_number = data.get('order_number')
    description = data.get('description')

    # Check if order number already exists
    existing_order = db.session.scalars(db.select(Order).filter_by(order_number=order_number)).first()
    if existing_order:
        return jsonify({"message": f"Order number '{order_number}' already exists"}), 409 # Conflict

    new_order = Order(
        order_number=order_number,
        description=description,
        created_by_user_id=current_user.id # Link to the logged-in user
    )
    db.session.add(new_order)
    try:
        db.session.commit()
        current_app.logger.info(f"Order '{order_number}' created by user '{current_user.username}'.")
        # Return the created order data
        return jsonify({
            "message": "Order created successfully",
            "order": {
                "id": new_order.id,
                "order_number": new_order.order_number,
                "description": new_order.description,
                "created_at": new_order.created_at.isoformat(),
                "created_by_user_id": new_order.created_by_user_id
            }
        }), 201 # Created
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating order '{order_number}' by '{current_user.username}': {e}")
        return jsonify({"message": "Failed to create order"}), 500


@main.route('/orders', methods=['GET'])
@login_required
def get_orders():
    """Retrieves a list of orders."""
    try:
        orders = db.session.scalars(db.select(Order).order_by(Order.created_at.desc())).all()

        orders_list = [{
            "id": order.id,
            "order_number": order.order_number,
            "description": order.description,
            "created_at": order.created_at.isoformat(),
            "created_by_user_id": order.created_by_user_id,
            "creator_username": order.creator.username if order.creator else "N/A"
        } for order in orders]

        return jsonify({"orders": orders_list}), 200
    except Exception as e:
        current_app.logger.error(f"Error retrieving orders: {e}")
        return jsonify({"message": "Failed to retrieve orders"}), 500


# --- Re-add DELETE /orders route ---
@main.route('/orders/<int:order_id>', methods=['DELETE'])
@login_required
@role_required(RoleType.ADMIN)
def delete_order(order_id):
    """Deletes an order (Admin only)."""
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"message": f"Order ID {order_id} not found"}), 404
    order_number = order.order_number
    try:
        # Assuming cascade delete is set up in models for scans/comments
        db.session.delete(order)
        db.session.commit()
        current_app.logger.warning(f"Order '{order_number}' (ID: {order_id}) deleted by admin '{current_user.username}'.")
        return jsonify({"message": f"Order '{order_number}' deleted"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting order {order_id}: {e}")
        return jsonify({"message": "Failed to delete order"}), 500


# --- Scan Routes ---
@main.route('/scans', methods=['POST'])
@login_required
def record_scan():
    """Records a new scan event."""
    data = request.get_json()
    required_fields = ['barcode', 'status', 'order_id']
    if not data or not all(field in data for field in required_fields):
        return jsonify({"message": f"Missing required fields: {required_fields}"}), 400

    barcode = data.get('barcode')
    status_str = data.get('status')
    order_id = data.get('order_id')
    notes = data.get('notes') # Optional

    # Validate status
    try:
        scan_status = ScanStatus(status_str) # Convert string ('Pass'/'Fail') to Enum
    except ValueError:
        valid_statuses = [s.value for s in ScanStatus]
        return jsonify({"message": f"Invalid status '{status_str}'. Must be one of: {valid_statuses}"}), 400

    # Validate order ID
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"message": f"Order with ID {order_id} not found"}), 404 # Not Found

    # --- Keep Duplicate Scan Check ---
    existing_scan = db.session.scalars(
        db.select(Scan).filter_by(barcode=barcode, order_id=order_id)
    ).first()
    if existing_scan:
        current_app.logger.warning(f"Duplicate scan attempt: Barcode '{barcode}' already exists for Order ID {order_id}.")
        return jsonify({"message": f"Barcode '{barcode}' has already been scanned for this order (Order ID: {order_id})"}), 409 # Conflict
    # ---

    # --- Re-add department logic ---
    user_department_id = current_user.department_id
    if not user_department_id:
        # Handle users without department (e.g., Admin)
        # For now, require a department for scanning.
        return jsonify({"message": "User must belong to a department to record scans"}), 400

    new_scan = Scan(
        barcode=barcode,
        status=scan_status,
        notes=notes,
        user_id=current_user.id,
        department_id=user_department_id,
        order_id=order_id
    )

    db.session.add(new_scan)
    try:
        db.session.commit()
        current_app.logger.info(f"Scan recorded: Barcode: '{barcode}', Order: {order.order_number}, Status: {scan_status.value}, User: '{current_user.username}', Dept: {user_department_id}.")
        # Return the created scan data (including department_id)
        return jsonify({
            "message": "Scan recorded successfully",
            "scan": {
                "id": new_scan.id,
                "barcode": new_scan.barcode,
                "timestamp": new_scan.timestamp.isoformat(),
                "status": new_scan.status.value,
                "notes": new_scan.notes,
                "user_id": new_scan.user_id,
                "department_id": new_scan.department_id,
                "order_id": new_scan.order_id
            }
        }), 201 # Created
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error recording scan for barcode '{barcode}': {e}")
        return jsonify({"message": "Failed to record scan"}), 500


@main.route('/scans', methods=['GET'])
@login_required
def get_scans():
    """Retrieves a list of scans, optionally filtered by order_id."""

    # --- Restore Filtering Logic ---
    query = db.select(Scan)

    # Filter by order_id
    order_id_filter = request.args.get('order_id', type=int)
    if order_id_filter:
        query = query.where(Scan.order_id == order_id_filter)

    # Filter by user_id
    user_id_filter = request.args.get('user_id', type=int)
    if user_id_filter:
        query = query.where(Scan.user_id == user_id_filter)

    # Filter by department_id
    department_id_filter = request.args.get('department_id', type=int)
    if department_id_filter:
        query = query.where(Scan.department_id == department_id_filter)

    # Ordering
    query = query.order_by(Scan.timestamp.desc())
    # --- End Filtering ---

    try:
        # Eager load related objects
        query = query.options(db.joinedload(Scan.user), db.joinedload(Scan.department))
        scans = db.session.scalars(query).all()

        scan_list = [{
            "id": scan.id,
            "barcode": scan.barcode,
            "timestamp": scan.timestamp.isoformat(),
            "status": scan.status.value,
            "notes": scan.notes,
            "user_id": scan.user_id,
            "department_id": scan.department_id,
            "order_id": scan.order_id,
            "username": scan.user.username if scan.user else "N/A",
            "department_name": scan.department.name if scan.department else "N/A"
        } for scan in scans]

        return jsonify({"scans": scan_list}), 200
    except Exception as e:
        current_app.logger.error(f"Error retrieving scans: {e}")
        return jsonify({"message": "Failed to retrieve scans"}), 500


# --- Add PUT /scans route (Edit) ---
@main.route('/scans/<int:scan_id>', methods=['PUT'])
@login_required
@roles_required(RoleType.ADMIN, RoleType.MANAGER)
def update_scan(scan_id):
    """Updates a scan's status or notes (Admin/Manager)."""
    scan = db.session.get(Scan, scan_id)
    if not scan:
        return jsonify({"message": f"Scan ID {scan_id} not found"}), 404

    # Optional: Manager check for own department?
    # if current_user.role.name == RoleType.MANAGER and scan.department_id != current_user.department_id:
    #     return jsonify({"message": "Managers can only edit scans from their own department"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"message": "No update data provided"}), 400

    changes_made = False
    log_changes = []
    if 'status' in data:
        try:
            new_status = ScanStatus(data['status'])
            if scan.status != new_status:
                log_changes.append(f"status to '{new_status.value}'")
                scan.status = new_status
                changes_made = True
        except ValueError:
            return jsonify({"message": f"Invalid status '{data['status']}'"}), 400
    if 'notes' in data:
        if scan.notes != data['notes']:
            log_changes.append("notes updated")
            scan.notes = data['notes']
            changes_made = True

    if not changes_made:
        return jsonify({"message": "No changes detected"}), 200

    try:
        db.session.commit()
        current_app.logger.info(f"Scan ID {scan_id} updated by user '{current_user.username}': {', '.join(log_changes)}.")
        # Return updated scan? Or just success?
        return jsonify({"message": "Scan updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating scan {scan_id}: {e}")
        return jsonify({"message": "Failed to update scan"}), 500


# --- Add DELETE /scans route ---
@main.route('/scans/<int:scan_id>', methods=['DELETE'])
@login_required
@roles_required(RoleType.ADMIN, RoleType.MANAGER)
def delete_scan(scan_id):
    """Deletes a scan (Admin/Manager)."""
    scan = db.session.get(Scan, scan_id)
    if not scan:
        return jsonify({"message": f"Scan ID {scan_id} not found"}), 404

    # Optional: Manager check for own department?
    # if current_user.role.name == RoleType.MANAGER and scan.department_id != current_user.department_id:
    #     return jsonify({"message": "Managers can only delete scans from their own department"}), 403

    scan_barcode = scan.barcode
    try:
        db.session.delete(scan)
        db.session.commit()
        current_app.logger.warning(f"Scan '{scan_barcode}' (ID: {scan_id}) deleted by user '{current_user.username}'.")
        return jsonify({"message": f"Scan '{scan_barcode}' deleted"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting scan {scan_id}: {e}")
        return jsonify({"message": "Failed to delete scan"}), 500


# --- Re-add Department Routes ---
@main.route('/departments', methods=['POST'])
@login_required
@role_required(RoleType.ADMIN)
def create_department():
    """Creates a new department."""
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"message": "Missing required field: name"}), 400
    name = data.get('name')
    if db.session.scalars(db.select(Department).filter_by(name=name)).first():
        return jsonify({"message": f"Department '{name}' already exists"}), 409
    new_dept = Department(name=name)
    db.session.add(new_dept)
    try:
        db.session.commit()
        current_app.logger.info(f"Department '{name}' created by user '{current_user.username}'.")
        return jsonify({"message": "Department created", "department": {"id": new_dept.id, "name": new_dept.name}}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating department '{name}': {e}")
        return jsonify({"message": "Failed to create department"}), 500

@main.route('/departments', methods=['GET'])
@login_required
def get_departments():
    """Retrieves a list of all departments."""
    try:
        departments = db.session.scalars(db.select(Department).order_by(Department.name)).all()
        return jsonify({"departments": [{"id": d.id, "name": d.name} for d in departments]}), 200
    except Exception as e:
        current_app.logger.error(f"Error retrieving departments: {e}")
        return jsonify({"message": "Failed to retrieve departments"}), 500

# --- Add DELETE /departments route ---
@main.route('/departments/<int:department_id>', methods=['DELETE'])
@login_required
@role_required(RoleType.ADMIN)
def delete_department(department_id):
    """Deletes a department (Admin only). Fails if users are assigned."""
    dept = db.session.get(Department, department_id)
    if not dept:
        return jsonify({"message": f"Department ID {department_id} not found"}), 404

    # Check if any users are assigned to this department
    user_count = db.session.scalar(db.select(db.func.count(User.id)).where(User.department_id == department_id))
    if user_count > 0:
        return jsonify({"message": f"Cannot delete department '{dept.name}' because {user_count} user(s) are assigned to it."}), 409 # Conflict
    
    # Check scans? (Maybe less critical, or handled differently)
    scan_count = db.session.scalar(db.select(db.func.count(Scan.id)).where(Scan.department_id == department_id))
    if scan_count > 0:
         return jsonify({"message": f"Cannot delete department '{dept.name}' because {scan_count} scan(s) are linked to it."}), 409 # Conflict

    dept_name = dept.name
    try:
        db.session.delete(dept)
        db.session.commit()
        current_app.logger.warning(f"Department '{dept_name}' (ID: {department_id}) deleted by admin '{current_user.username}'.")
        return jsonify({"message": f"Department '{dept_name}' deleted"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting department {department_id}: {e}")
        return jsonify({"message": "Failed to delete department"}), 500

# --- Re-add User Management Routes ---
@main.route('/users', methods=['POST'])
@login_required
@role_required(RoleType.ADMIN)
def create_user():
    """Creates a new user (Admin only)."""
    data = request.get_json()
    required = ['username', 'password', 'role_name']
    if not data or not all(f in data for f in required):
        return jsonify({"message": f"Missing required fields: {required}"}), 400

    username = data.get('username')
    password = data.get('password')
    role_name_str = data.get('role_name')
    department_id = data.get('department_id')

    if db.session.scalars(db.select(User).filter_by(username=username)).first():
        return jsonify({"message": f"Username '{username}' already exists"}), 409

    try:
        role_type = RoleType(role_name_str)
        role = db.session.scalars(db.select(Role).filter_by(name=role_type)).first()
        if not role:
            return jsonify({"message": f"Role '{role_name_str}' not found"}), 400
    except ValueError:
        return jsonify({"message": f"Invalid role_name '{role_name_str}'"}), 400

    department = None
    if department_id:
        department = db.session.get(Department, department_id)
        if not department:
            return jsonify({"message": f"Department ID {department_id} not found"}), 404

    new_user = User(username=username, role=role, department=department)
    new_user.set_password(password)
    db.session.add(new_user)
    try:
        db.session.commit()
        current_app.logger.info(f"User '{username}' created by admin '{current_user.username}'.")
        return jsonify({"message": "User created", "user": {"id": new_user.id, "username": new_user.username, "role": new_user.role.name.value, "department_id": new_user.department_id, "department_name": new_user.department.name if new_user.department else None}}), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating user '{username}': {e}")
        return jsonify({"message": "Failed to create user"}), 500

@main.route('/users', methods=['GET'])
@login_required
@role_required(RoleType.ADMIN)
def get_users():
    """Retrieves a list of all users (Admin only)."""
    try:
        users = db.session.scalars(db.select(User).order_by(User.username)).all()
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "role": user.role.name.value,
                "department_id": user.department_id,
                "department_name": user.department.name if user.department else None
            })
        return jsonify({"users": user_list}), 200
    except Exception as e:
        current_app.logger.error(f"Error retrieving users: {e}")
        return jsonify({"message": "Failed to retrieve users"}), 500

@main.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@role_required(RoleType.ADMIN)
def update_user(user_id):
    """Updates a user's role or department (Admin only)."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": f"User ID {user_id} not found"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"message": "No update data provided"}), 400

    current_app.logger.info(f"UPDATE_USER: ID {user_id} ('{user.username}'). Data: {data}")
    changes_made = False

    if 'role_name' in data:
        role_name_str = data['role_name']
        try:
            role_type = RoleType(role_name_str)
            role = db.session.scalars(db.select(Role).filter_by(name=role_type)).first()
            if role and user.role != role:
                user.role = role
                changes_made = True
                current_app.logger.info(f"UPDATE_USER: Set role to {role_name_str} for ID {user_id}.")
            elif not role:
                 current_app.logger.warning(f"UPDATE_USER: Role '{role_name_str}' not found.")
        except ValueError:
            current_app.logger.warning(f"UPDATE_USER: Invalid role_name '{role_name_str}'.")

    if 'department_id' in data:
        department_id = data['department_id']
        original_dept_id = user.department_id
        if department_id in [None, -1, "-1", "", "None"]:
            if original_dept_id is not None:
                user.department_id = None
                changes_made = True
                current_app.logger.info(f"UPDATE_USER: Set department to None for ID {user_id}.")
        else:
            try:
                dept_id_int = int(department_id)
                if dept_id_int != original_dept_id:
                    department = db.session.get(Department, dept_id_int)
                    if department:
                        user.department_id = dept_id_int
                        changes_made = True
                        current_app.logger.info(f"UPDATE_USER: Set department ID to {dept_id_int} for ID {user_id}.")
                    else:
                        current_app.logger.warning(f"UPDATE_USER: Department ID {dept_id_int} not found.")
            except (ValueError, TypeError):
                 current_app.logger.warning(f"UPDATE_USER: Invalid department ID format '{department_id}'.")

    if not changes_made:
        return jsonify({"message": "No changes applied"}), 200

    try:
        db.session.commit()
        current_app.logger.info(f"UPDATE_USER: Committed changes for ID {user_id}.")
        updated_user = {
             "id": user.id, "username": user.username, "role": user.role.name.value,
             "department_id": user.department_id, "department_name": user.department.name if user.department else None
        }
        return jsonify({"message": "User updated", "user": updated_user}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"UPDATE_USER: Error committing changes for ID {user_id}: {e}")
        return jsonify({"message": "Failed to update user"}), 500

# --- Re-add DELETE /users route ---
@main.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required(RoleType.ADMIN)
def delete_user(user_id):
    """Deletes a user (Admin only)."""
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": f"User ID {user_id} not found"}), 404

    if user.id == current_user.id:
        return jsonify({"message": "Cannot delete yourself"}), 400

    username = user.username
    try:
        # Consider implications for related scans/orders - need cascade or nullify in models?
        db.session.delete(user)
        db.session.commit()
        current_app.logger.warning(f"User '{username}' (ID: {user_id}) deleted by admin '{current_user.username}'.")
        return jsonify({"message": f"User '{username}' deleted"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user {user_id}: {e}")
        if "violates foreign key constraint" in str(e).lower():
            return jsonify({"message": f"Cannot delete user '{username}'. They likely have scans or orders associated."}), 409 # Conflict
        return jsonify({"message": "Failed to delete user"}), 500

# --- Authentication Routes (Keep, but simplify) ---
@main.route('/auth/login', methods=['POST'])
def login():
    """Authenticates a user and returns basic user data."""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"message": "Username and password required"}), 400

    username = data.get('username')
    password = data.get('password')

    # Find user (assuming User model still exists)
    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        login_user(user) # Use Flask-Login
        # Restore role/dept info in response
        user_data = {
            "id": user.id,
            "username": user.username,
            "role": user.role.name.value,
            "department_id": user.department_id,
            "department_name": user.department.name if user.department else ""
        }
        current_app.logger.info(f"LOGIN: Success for '{username}'. Role: {user_data['role']}, Dept: {user_data['department_name']}.")
        return jsonify({"message": "Login successful", "user": user_data}), 200
    else:
        current_app.logger.warning(f"LOGIN: Login failed for username: '{username}'.")
        return jsonify({"message": "Invalid username or password"}), 401 # Unauthorized

@main.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    """Logs the current user out."""
    username = current_user.username # Get username before logout
    logout_user()
    current_app.logger.info(f"User '{username}' logged out successfully.")
    return jsonify({"message": "Logout successful"}), 200

@main.route('/auth/me', methods=['GET'])
@login_required
def me():
    """Returns current logged-in user's basic information."""
    # Restore role/dept info in response
    user_data = {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role.name.value,
        "department_id": current_user.department_id,
        "department_name": current_user.department.name if current_user.department else ""
    }
    return jsonify({"user": user_data}), 200 
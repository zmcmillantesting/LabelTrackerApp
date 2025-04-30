# Database models 
import enum
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, login_manager # Import db and login_manager from api package
import os # Need os for environment variables

# Association table for many-to-many relationship between users and roles (if needed later)
# For now, assuming one role per user for simplicity
# roles_users = db.Table('roles_users',
#     db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
#     db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
# )

# --- Re-add RoleType Enum ---
class RoleType(enum.Enum):
    ADMIN = 'Admin'
    MANAGER = 'Manager'
    STANDARD = 'Standard'

# --- Re-add Role Model ---
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Enum(RoleType), unique=True, nullable=False)
    users = db.relationship('User', back_populates='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            RoleType.STANDARD: 'Standard User Role',
            RoleType.MANAGER: 'Manager Role',
            RoleType.ADMIN: 'Administrator Role'
        }
        for r_enum, desc in roles.items():
            role = db.session.scalars(db.select(Role).filter_by(name=r_enum)).first()
            if role is None:
                role = Role(name=r_enum)
                print(f'Creating role: {r_enum.value}')
                db.session.add(role)
        try:
            db.session.commit()
            print("Roles committed.")
        except Exception as e:
            db.session.rollback()
            print(f"Error committing roles: {e}")

    def __repr__(self):
        return f'<Role {self.name.value}>'

# --- Re-add Department Model ---
class Department(db.Model):
    __tablename__ = 'departments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    users = db.relationship('User', back_populates='department', lazy='dynamic')
    scans = db.relationship('Scan', back_populates='department', lazy='dynamic')

    def __repr__(self):
        return f'<Department {self.name}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    # --- Re-add role_id and department_id ---
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)

    # Relationships
    # --- Re-add role and department relationships ---
    role = db.relationship('Role', back_populates='users')
    department = db.relationship('Department', back_populates='users')
    scans = db.relationship('Scan', back_populates='user', lazy='dynamic', cascade="all, delete-orphan")
    orders_created = db.relationship('Order', back_populates='creator', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def create_admin():
        # --- Restore role logic in admin creation ---
        admin_role = db.session.scalars(db.select(Role).filter_by(name=RoleType.ADMIN)).first()
        if not admin_role:
            print("Admin role not found. Please run Role.insert_roles() first.")
            return

        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'password')

        admin_user = db.session.scalars(db.select(User).filter_by(username=admin_username)).first()

        password_changed = False
        if admin_user:
            print(f"Admin user '{admin_username}' already exists.")
            provided_password = os.environ.get('ADMIN_PASSWORD')
            if provided_password and not admin_user.check_password(provided_password):
                print(f"Updating password for admin user '{admin_username}'.")
                admin_user.set_password(provided_password)
                password_changed = True
            # Ensure the user has the admin role
            if admin_user.role != admin_role:
                print(f"Ensuring user '{admin_username}' has Admin role.")
                admin_user.role = admin_role
                db.session.add(admin_user)
        else:
            admin_user = User(username=admin_username, role=admin_role)
            admin_user.set_password(admin_password)
            print(f"Creating admin user: {admin_username}")
            db.session.add(admin_user)
            password_changed = True

        if db.session.dirty or db.session.new:
            try:
                db.session.commit()
                if password_changed:
                    print(f"Admin user '{admin_username}' created or password/role updated.")
                else:
                    print(f"Admin user '{admin_username}' checked, no changes needed.")
            except Exception as e:
                db.session.rollback()
                print(f"Error committing admin user changes: {e}")
        else:
            print(f"No changes detected for admin user '{admin_username}'.")

    # --- Re-add role checking properties ---
    @property
    def is_admin(self):
        return self.role and self.role.name == RoleType.ADMIN

    @property
    def is_manager(self):
        return self.role and self.role.name == RoleType.MANAGER

    def __repr__(self):
        return f'<User {self.username}>'

# User loader callback required by Flask-Login
@login_manager.user_loader
def load_user(user_id):
    # Uses the correct db.session.get
    return db.session.get(User, int(user_id))

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(128), unique=True, nullable=False, index=True)
    description = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    creator = db.relationship('User', back_populates='orders_created')
    scans = db.relationship('Scan', back_populates='order', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Order {self.order_number}>'

class ScanStatus(enum.Enum):
    PASS = 'Pass'
    FAIL = 'Fail'

class Scan(db.Model):
    __tablename__ = 'scans'
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(256), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    status = db.Column(db.Enum(ScanStatus), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # --- Re-add department_id ---
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='scans')
    # --- Re-add department relationship ---
    department = db.relationship('Department', back_populates='scans')
    order = db.relationship('Order', back_populates='scans')

    def __repr__(self):
        return f'<Scan {self.barcode} [{self.status.value}]>'

# --- Re-add Comment Model (Optional, but was there before) ---
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=True)

    user = db.relationship('User') # Simplified relationship for now
    order = db.relationship('Order')
    scan = db.relationship('Scan')

    # Add back_populates if needed later for bidirectional access

    def __repr__(self):
        link = f"Order {self.order_id}" if self.order_id else f"Scan {self.scan_id}"
        return f'<Comment by User {self.user_id} on {link}>' 
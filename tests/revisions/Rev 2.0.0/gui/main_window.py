# GUI main application window 
import sys
import os # Added for path joining
import datetime # Added for feedback timestamp
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QMessageBox, QTabWidget, QStatusBar, QLineEdit, QComboBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QDialogButtonBox,
    QFormLayout, QGroupBox, QTextEdit, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, pyqtSignal # Remove QFileSystemWatcher
from PyQt6.QtGui import QColor, QPalette, QPixmap, QFont # Added QFont
import logging

# Import the ApiClient (assuming it's in the same directory)
try:
    from .api_client import ApiClient
except ImportError:
    # Handle case where script is run directly for testing
    from api_client import ApiClient 

# Define placeholder barcode values (REPLACE WITH YOUR ACTUAL VALUES)
PASS_BARCODE_VALUE = "__PASS__"
FAIL_BARCODE_VALUE = "__FAIL__"

# --- Runtime Path Helper Function --- 
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # In development, use the directory of the current script (main_window.py)
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)
# ---

class MainWindow(QMainWindow):
    """Main application window displayed after login."""
    logged_out = pyqtSignal() # Signal emitted when logout is successful

    def __init__(self, user_data: dict, api_client: ApiClient, feedback_path_func):
        """
        Initializes the main window.

        Args:
            user_data (dict): Dictionary containing logged-in user information.
            api_client (ApiClient): The instance of the API client.
            feedback_path_func (callable): Function that returns the path for the feedback file.
        """
        super().__init__()
        self.user_data = user_data
        self.api_client = api_client
        self.feedback_path_func = feedback_path_func # Store the function
        self.orders = [] # Cache for orders dropdown
        self.departments = [] # Cache for departments dropdown
        self.users = [] # Cache for users list
        self.roles = ["Standard", "Manager", "Admin"] # Available roles
        
        # State for two-step scanning
        self.expecting_status_scan = False
        self.current_board_barcode = None
        self.current_scan_status = None # Stores "Pass" or "Fail"

        self.setWindowTitle("Label Tracker")
        self.setGeometry(100, 100, 900, 700) # Adjusted size

        # --- Remove log timer/watcher attributes ---

        # --- Remove user department logic if not needed elsewhere ---
        # self.user_department_name = user_data.get("department_name", "")
        # logging.info(f"User '{user_data.get('username')}' - Received department: '{self.user_department_name}'")

        self._init_ui()
        # --- Remove log monitoring start ---
        self._load_initial_data()

    def _init_ui(self):
        """Initialize the main window UI elements."""
        
        # --- Central Widget and Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Tab Widget for different sections ---
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # --- Create Tab Widget Instances (Remove log tabs) ---
        self.scan_tab = QWidget()
        self.view_data_tab = QWidget()
        self.feedback_tab = QWidget()
        # self.backend_log_tab = QWidget() # Remove
        # self.app_error_log_tab = QWidget() # Remove
        self.admin_tab_users = QWidget()
        self.admin_tab_depts = QWidget()
        self.admin_tab_orders = QWidget()

        # --- Populate Tab Widgets (Remove log tab creation calls) ---
        self._create_scan_tab()
        self._create_view_data_tab()
        self._create_feedback_tab()
        # self._create_backend_log_tab() # Remove
        # self._create_app_error_log_tab() # Remove
        self._create_admin_tab_users()
        self._create_admin_tab_depts()
        self._create_admin_tab_orders()

        # --- Add Always Visible Tabs --- 
        self.tab_widget.addTab(self.scan_tab, "Scan")
        self.tab_widget.addTab(self.view_data_tab, "View Data")
        self.tab_widget.addTab(self.feedback_tab, "Feedback / Report Issue")

        # --- Add logging to check role data ---
        logging.info(f"MainWindow _init_ui: Received user_data: {self.user_data}")
        # ---

        # --- Conditionally Add Admin Tabs --- 
        user_role = self.user_data.get("role")
        # --- Add logging for role value ---
        logging.info(f"MainWindow _init_ui: Checking user_role: '{user_role}' (Type: {type(user_role)})")
        # ---
        is_admin = (user_role == "Admin")
        is_manager = (user_role == "Manager")

        if is_admin:
            self.tab_widget.addTab(self.admin_tab_users, "Manage Users")
            self.tab_widget.addTab(self.admin_tab_depts, "Manage Depts")
            self.tab_widget.addTab(self.admin_tab_orders, "Manage Orders")
        elif is_manager:
             self.tab_widget.addTab(self.admin_tab_orders, "Manage Orders")
        
        # --- Status Bar, Menu Bar, Layout ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()
        self._create_menu_bar()
        central_widget.setLayout(main_layout)

    def _create_scan_tab(self):
        layout = QVBoxLayout(self.scan_tab)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(15)

        # --- Order Selection --- 
        order_group = QGroupBox("Select Order")
        order_layout = QHBoxLayout()
        self.scan_order_combo = QComboBox()
        order_layout.addWidget(QLabel("Order:"))
        order_layout.addWidget(self.scan_order_combo)
        refresh_orders_btn = QPushButton("Refresh Orders")
        refresh_orders_btn.clicked.connect(self._load_orders)
        order_layout.addWidget(refresh_orders_btn)
        order_group.setLayout(order_layout)
        layout.addWidget(order_group)

        # --- Barcode Input --- 
        barcode_group = QGroupBox("Scan Board Barcode")
        barcode_layout = QHBoxLayout()
        self.scan_barcode_input = QLineEdit()
        self.scan_barcode_input.setPlaceholderText("Scan Board Barcode -> Press Enter -> Scan Status Barcode -> Press Enter") 
        self.scan_barcode_input.textChanged.connect(lambda: self.scan_barcode_input.setStyleSheet(""))
        self.scan_barcode_input.returnPressed.connect(self._handle_barcode_input_enter)
        barcode_layout.addWidget(QLabel("Scan Input:"))
        barcode_layout.addWidget(self.scan_barcode_input)
        barcode_group.setLayout(barcode_layout)
        layout.addWidget(barcode_group)

        # --- Static Pass/Fail Barcode Images --- 
        status_display_group = QGroupBox("Scan Status Barcode")
        status_display_layout = QHBoxLayout()
        status_display_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Get base path using the helper function
        pass_img_path = resource_path(os.path.join("images", "pass_barcode.png"))
        fail_img_path = resource_path(os.path.join("images", "fail_barcode.png"))

        # Pass Image
        pass_layout = QVBoxLayout()
        pass_label = QLabel("Scan for PASS:")
        pass_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pass_image_label = QLabel()
        pass_pixmap = QPixmap(pass_img_path)
        if pass_pixmap.isNull():
            logging.warning(f"Could not load pass image: {pass_img_path}")
            self.pass_image_label.setText("[PASS IMAGE]")
        else:
             # Scale image if needed (adjust size)
            # pass_pixmap = pass_pixmap.scaled(150, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
             self.pass_image_label.setPixmap(pass_pixmap)
        self.pass_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pass_layout.addWidget(pass_label)
        pass_layout.addWidget(self.pass_image_label)
        status_display_layout.addLayout(pass_layout)

        status_display_layout.addSpacing(50)

        # Fail Image
        fail_layout = QVBoxLayout()
        fail_label = QLabel("Scan for FAIL:")
        fail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.fail_image_label = QLabel()
        fail_pixmap = QPixmap(fail_img_path)
        if fail_pixmap.isNull():
            logging.warning(f"Could not load fail image: {fail_img_path}")
            self.fail_image_label.setText("[FAIL IMAGE]")
        else:
             # fail_pixmap = fail_pixmap.scaled(150, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
             self.fail_image_label.setPixmap(fail_pixmap)
        self.fail_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fail_layout.addWidget(fail_label)
        fail_layout.addWidget(self.fail_image_label)
        status_display_layout.addLayout(fail_layout)
        
        status_display_group.setLayout(status_display_layout)
        layout.addWidget(status_display_group)
        
        # --- Notes --- 
        notes_group = QGroupBox("Notes (Optional)")
        notes_layout = QVBoxLayout()
        self.scan_notes_input = QTextEdit()
        self.scan_notes_input.setMaximumHeight(80)
        self.scan_notes_input.setPlaceholderText("Notes (Enter *after* board scan)")
        self.scan_notes_input.setEnabled(False)
        notes_layout.addWidget(self.scan_notes_input)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group)

        # --- Status Label --- 
        self.scan_status_label = QLabel("Scan Board Barcode and Press Enter")
        self.scan_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scan_status_label.setStyleSheet("QLabel { font-weight: bold; }")
        layout.addWidget(self.scan_status_label)

        layout.addStretch()
        
        # Focus on barcode input initially
        QTimer.singleShot(100, self.scan_barcode_input.setFocus)

    def _create_view_data_tab(self):
        layout = QVBoxLayout(self.view_data_tab)
        
        # --- Filters --- 
        filter_group = QGroupBox("Filter Scans")
        filter_layout = QHBoxLayout()
        self.view_order_filter_combo = QComboBox()
        self.view_order_filter_combo.addItem("All Orders", -1)
        filter_layout.addWidget(QLabel("Filter by Order:"))
        filter_layout.addWidget(self.view_order_filter_combo)
        refresh_view_btn = QPushButton("Refresh Scans")
        refresh_view_btn.clicked.connect(self._load_scans_for_view)
        filter_layout.addWidget(refresh_view_btn)
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # --- Scans Table --- 
        self.view_scans_table = QTableWidget()
        self.view_scans_table.setColumnCount(7) # ID, Barcode, Timestamp, Status, Notes, User, Dept
        self.view_scans_table.setHorizontalHeaderLabels(["ID", "Barcode", "Timestamp", "Status", "Notes", "User", "Department"])
        self.view_scans_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) # Read-only
        self.view_scans_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.view_scans_table.verticalHeader().setVisible(False) # Hide row numbers
        header = self.view_scans_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Barcode stretch
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Timestamp fit
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch) # Notes stretch
        layout.addWidget(self.view_scans_table)
        
        # --- Restore Scan Action Buttons (Edit/Delete - Admin/Manager) ---
        self.scan_actions_layout = QHBoxLayout()
        self.edit_scan_btn = QPushButton("Edit Selected Scan")
        self.delete_scan_btn = QPushButton("Delete Selected Scan")
        self.edit_scan_btn.clicked.connect(self._handle_edit_scan)
        self.delete_scan_btn.clicked.connect(self._handle_delete_scan)
        self.scan_actions_layout.addStretch()
        self.scan_actions_layout.addWidget(self.edit_scan_btn)
        self.scan_actions_layout.addWidget(self.delete_scan_btn)
        layout.addLayout(self.scan_actions_layout)
        
        # Hide buttons if user is Standard
        user_role = self.user_data.get("role")
        if user_role == "Standard":
             self.edit_scan_btn.setVisible(False)
             self.delete_scan_btn.setVisible(False)
             
        # --- Comments Section (Placeholder) --- 
        # Add QListWidget/QTextEdit for comments later
        # comments_group = QGroupBox("Comments for Selected Scan")
        # ...
        # layout.addWidget(comments_group)
        
    def _create_admin_tab_users(self):
        layout = QVBoxLayout(self.admin_tab_users)
        user_group = QGroupBox("Manage Users")
        user_layout = QVBoxLayout()

        # User Table
        self.admin_users_table = QTableWidget()
        self.admin_users_table.setColumnCount(4) # ID, Username, Role, Department
        self.admin_users_table.setHorizontalHeaderLabels(["ID", "Username", "Role", "Department"])
        self.admin_users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.admin_users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.admin_users_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        header = self.admin_users_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        user_layout.addWidget(self.admin_users_table)

        # Action Buttons
        button_layout = QHBoxLayout()
        add_user_btn = QPushButton("Add New User")
        edit_user_btn = QPushButton("Edit Selected User")
        # --- Restore Delete User Button ---
        delete_user_btn = QPushButton("Delete Selected User")
        delete_user_btn.setStyleSheet("QPushButton { color: red; }")
        refresh_users_btn = QPushButton("Refresh List")

        add_user_btn.clicked.connect(self._handle_add_user)
        edit_user_btn.clicked.connect(self._handle_edit_user)
        # --- Connect Delete User Button ---
        delete_user_btn.clicked.connect(self._handle_delete_user)
        refresh_users_btn.clicked.connect(self._load_users)

        button_layout.addWidget(add_user_btn)
        button_layout.addWidget(edit_user_btn)
        # --- Add Delete User Button to Layout ---
        button_layout.addWidget(delete_user_btn)
        button_layout.addStretch()
        button_layout.addWidget(refresh_users_btn)
        user_layout.addLayout(button_layout)

        user_group.setLayout(user_layout)
        layout.addWidget(user_group)
        self.admin_tab_users.setLayout(layout)

    def _create_admin_tab_depts(self):
        layout = QVBoxLayout(self.admin_tab_depts)
        dept_group = QGroupBox("Manage Departments")
        dept_layout = QVBoxLayout()

        # Department Table (Simple List for now)
        self.admin_depts_table = QTableWidget()
        self.admin_depts_table.setColumnCount(2) # ID, Name
        self.admin_depts_table.setHorizontalHeaderLabels(["ID", "Name"])
        self.admin_depts_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.admin_depts_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        dept_layout.addWidget(self.admin_depts_table)

        # Action Buttons
        button_layout = QHBoxLayout()
        add_dept_btn = QPushButton("Add New Department")
        # --- Add Delete Dept Button ---
        delete_dept_btn = QPushButton("Delete Selected Department")
        delete_dept_btn.setStyleSheet("QPushButton { color: red; }")
        refresh_depts_btn = QPushButton("Refresh List")

        add_dept_btn.clicked.connect(self._handle_add_dept)
        # --- Connect Delete Dept Button ---
        delete_dept_btn.clicked.connect(self._handle_delete_dept)
        refresh_depts_btn.clicked.connect(self._load_departments)

        button_layout.addWidget(add_dept_btn)
        # --- Add Delete Dept Button to Layout ---
        button_layout.addWidget(delete_dept_btn)
        button_layout.addStretch()
        button_layout.addWidget(refresh_depts_btn)
        dept_layout.addLayout(button_layout)

        dept_group.setLayout(dept_layout)
        layout.addWidget(dept_group)
        self.admin_tab_depts.setLayout(layout)

    def _create_admin_tab_orders(self):
        layout = QVBoxLayout(self.admin_tab_orders)
        order_group = QGroupBox("Create New Order")
        form_layout = QFormLayout()
        self.admin_order_number_input = QLineEdit()
        self.admin_order_desc_input = QLineEdit()
        create_order_btn = QPushButton("Create Order")
        self.admin_order_status_label = QLabel("")

        form_layout.addRow("Order Number:", self.admin_order_number_input)
        form_layout.addRow("Description (Optional):", self.admin_order_desc_input)
        form_layout.addRow(create_order_btn)
        form_layout.addRow(self.admin_order_status_label)
        order_group.setLayout(form_layout)
        layout.addWidget(order_group)

        # --- Restore Delete Order Section (Admin Only) --- 
        delete_order_group = QGroupBox("Delete Existing Order")
        delete_order_layout = QHBoxLayout()
        self.delete_order_combo = QComboBox() # Use cached orders
        delete_order_layout.addWidget(QLabel("Select Order to Delete:"))
        delete_order_layout.addWidget(self.delete_order_combo)
        delete_order_btn = QPushButton("Delete Selected Order")
        delete_order_btn.setStyleSheet("QPushButton { color: red; }")
        delete_order_btn.clicked.connect(self._handle_delete_order)
        delete_order_layout.addWidget(delete_order_btn)
        delete_order_group.setLayout(delete_order_layout)
        layout.addWidget(delete_order_group)

        layout.addStretch()
        self.admin_tab_orders.setLayout(layout)
        create_order_btn.clicked.connect(self._handle_create_order)
        # Populate the delete combo when orders are loaded (handled in _load_orders)

    def _create_feedback_tab(self):
        """Creates the UI elements for the feedback tab."""
        logging.info("-----> Starting _create_feedback_tab...") # Log start
        layout = QVBoxLayout(self.feedback_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_label = QLabel("Report an Issue or Provide Feedback")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        description_label = QLabel(
            "Describe the problem you encountered or suggest an improvement. "
            "Please be as detailed as possible. This will be saved to a file for the developers."
        )
        description_label.setWordWrap(True)
        layout.addWidget(description_label)

        self.feedback_text_edit = QTextEdit()
        self.feedback_text_edit.setPlaceholderText("Enter your feedback here...")
        layout.addWidget(self.feedback_text_edit)

        self.submit_feedback_button = QPushButton("Submit Feedback")
        self.submit_feedback_button.clicked.connect(self._handle_submit_feedback)
        layout.addWidget(self.submit_feedback_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.feedback_status_label = QLabel("")
        self.feedback_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.feedback_status_label)
        
        layout.addStretch()
        
        # --- Add Diagnostic Logging --- 
        logging.info(f"-----> Feedback tab object before setLayout: {self.feedback_tab}")
        logging.info(f"-----> Layout object before setLayout: {layout}")
        # Explicitly set the layout for the tab widget
        self.feedback_tab.setLayout(layout)
        logging.info(f"-----> Layout set on {self.feedback_tab}. Current layout: {self.feedback_tab.layout()}")
        # ---
        logging.info("-----> Finished _create_feedback_tab.") # Log end

    # --- Menu Bar and Status Bar ---
    def _create_menu_bar(self):
        """Creates the main menu bar."""
        menu_bar = self.menuBar()
        
        # File Menu
        file_menu = menu_bar.addMenu("&File")
        logout_action = file_menu.addAction("Logout")
        logout_action.triggered.connect(self._handle_logout)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close) # Close the main window

        # Help Menu (Optional)
        help_menu = menu_bar.addMenu("&Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._show_about_dialog)

    def update_status_bar(self):
        """Updates the status bar with user info (including role/dept)."""
        username = self.user_data.get("username", "N/A")
        role = self.user_data.get("role", "N/A")
        department = self.user_data.get("department_name", "N/A") # Use name
        status_text = f"Logged in as: {username} ({role}) | Department: {department}"
        self.status_bar.showMessage(status_text)

    # --- Data Loading Methods ---
    def _load_initial_data(self):
        """Load data needed for dropdowns etc. when window opens."""
        self._load_orders()
        self._load_scans_for_view() # Load initial scans
        
        # --- Load admin data ONLY if user is Admin --- 
        user_role = self.user_data.get("role")
        if user_role == "Admin":
             logging.info("User is Admin, loading users and departments.")
             # Check if the UI elements exist before loading (belt and suspenders)
             if hasattr(self, 'admin_users_table'):
                  self._load_users()
             if hasattr(self, 'admin_depts_table'):
                  self._load_departments()
        else:
             logging.info(f"User role is '{user_role}', skipping load of admin-only data.")

    @pyqtSlot()
    def _load_orders(self):
        logging.info("Loading orders for dropdowns...")
        result = self.api_client.get_orders()
        if result["success"]:
            self.orders = result["data"].get("orders", [])
            # Populate Scan Tab Combo Box
            self.scan_order_combo.clear()
            if not self.orders:
                 self.scan_order_combo.addItem("No orders found - Create one first!", -1)
            else:
                for order in self.orders:
                    self.scan_order_combo.addItem(f"{order['order_number']} - {order.get('description','')[:30]}...", order['id'])
            
            # Populate View Data Tab Combo Box
            self.view_order_filter_combo.clear()
            self.view_order_filter_combo.addItem("All Orders", -1)
            for order in self.orders:
                self.view_order_filter_combo.addItem(f"{order['order_number']} - {order.get('description','')[:30]}...", order['id'])
            
            # Populate Delete Order Combo (if it exists - Admin/Manager)
            if hasattr(self, 'delete_order_combo'):
                 self.delete_order_combo.clear()
                 if not self.orders:
                      self.delete_order_combo.addItem("No orders found", -1)
                 else:
                      for order in self.orders:
                           self.delete_order_combo.addItem(f"{order['order_number']}", order['id'])
            
            logging.info(f"Loaded {len(self.orders)} orders.")
        else:
            QMessageBox.warning(self, "Error Loading Orders", f"Could not fetch orders: {result.get('message')}")
            self.scan_order_combo.clear()
            self.scan_order_combo.addItem("Error loading orders", -1)
            self.view_order_filter_combo.clear()
            self.view_order_filter_combo.addItem("Error loading orders", -1)
            if hasattr(self, 'delete_order_combo'):
                 self.delete_order_combo.clear()
                 self.delete_order_combo.addItem("Error loading orders", -1)
            
    @pyqtSlot()
    def _load_scans_for_view(self):
        logging.info("-----> Attempting to load scans for view tab...")
        self.view_scans_table.setRowCount(0) # Clear table

        selected_order_id = self.view_order_filter_combo.currentData()
        if selected_order_id == -1: # "All Orders" selected
             selected_order_id = None

        # --- Add logging for filter ---
        logging.info(f"-----> Filtering scans for Order ID: {selected_order_id}")
        # ---
        result = self.api_client.get_scans(order_id=selected_order_id)

        if result["success"]:
            scans = result["data"].get("scans", [])
            self.view_scans_table.setRowCount(len(scans))
            for row, scan in enumerate(scans):
                # ID, Barcode, Timestamp, Status, Notes, User, Dept
                self.view_scans_table.setItem(row, 0, QTableWidgetItem(str(scan['id'])))
                self.view_scans_table.setItem(row, 1, QTableWidgetItem(scan['barcode']))
                # Format timestamp nicely (optional)
                try:
                    ts = scan['timestamp']
                    # Attempt to parse ISO format and display locally
                    from datetime import datetime
                    dt_obj = datetime.fromisoformat(ts.replace('Z', '+00:00')) # Handle Z timezone
                    local_ts = dt_obj.astimezone().strftime('%Y-%m-%d %H:%M:%S') # Convert to local timezone
                except Exception:
                    local_ts = ts # Fallback to original string
                self.view_scans_table.setItem(row, 2, QTableWidgetItem(local_ts))
                
                status_item = QTableWidgetItem(scan['status'])
                if scan['status'] == 'Fail':
                     status_item.setBackground(QColor('#FFCCCC')) # Light red background for Fail
                elif scan['status'] == 'Pass':
                     status_item.setBackground(QColor('#CCFFCC')) # Light green background for Pass
                self.view_scans_table.setItem(row, 3, status_item)
                
                self.view_scans_table.setItem(row, 4, QTableWidgetItem(scan.get('notes', '')))
                self.view_scans_table.setItem(row, 5, QTableWidgetItem(scan['username']))
                self.view_scans_table.setItem(row, 6, QTableWidgetItem(scan['department_name']))
            logging.info(f"-----> Displayed {len(scans)} scans in table.")
            # --- Force UI update ---
            QApplication.processEvents()
            self.view_scans_table.viewport().update() # Explicitly update viewport
            # ---
        else:
            QMessageBox.warning(self, "Error Loading Scans", f"Could not fetch scans: {result.get('message')}")
            logging.error("-----> Failed to load scans for view tab.")
            
    @pyqtSlot()
    def _load_users(self):
        logging.info("Loading users for admin tab...")
        if not hasattr(self, 'admin_users_table'): return
        self.admin_users_table.setRowCount(0)
        result = self.api_client.get_users()
        if result["success"]:
             self.users = result["data"].get("users", [])
             self.admin_users_table.setRowCount(len(self.users))
             for row, user in enumerate(self.users):
                  self.admin_users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
                  self.admin_users_table.setItem(row, 1, QTableWidgetItem(user['username']))
                  self.admin_users_table.setItem(row, 2, QTableWidgetItem(user['role']))
                  self.admin_users_table.setItem(row, 3, QTableWidgetItem(user.get('department_name', 'N/A')))
             logging.info(f"Displayed {len(self.users)} users.")
        else:
             QMessageBox.warning(self, "Error Loading Users", f"Could not fetch users: {result.get('message')}")
             
    @pyqtSlot()
    def _load_departments(self):
        logging.info("Loading departments for admin tab...")
        if not hasattr(self, 'admin_depts_table'): return
        self.admin_depts_table.setRowCount(0)
        result = self.api_client.get_departments()
        if result["success"]:
             self.departments = result["data"].get("departments", [])
             self.admin_depts_table.setRowCount(len(self.departments))
             for row, dept in enumerate(self.departments):
                  self.admin_depts_table.setItem(row, 0, QTableWidgetItem(str(dept['id'])))
                  self.admin_depts_table.setItem(row, 1, QTableWidgetItem(dept['name']))
             logging.info(f"Displayed {len(self.departments)} departments.")
             # Refresh user dialog dropdown if needed/open
        else:
             QMessageBox.warning(self, "Error Loading Depts", f"Could not fetch depts: {result.get('message')}")

    # --- Action Handlers ---
    @pyqtSlot()
    def _handle_barcode_input_enter(self):
        """Handles Enter key press in the barcode input field for both steps."""
        scanned_value = self.scan_barcode_input.text().strip()
        if not scanned_value:
            return 
            
        if not self.expecting_status_scan:
            # --- Step 1: Board Barcode Scanned --- 
            # --- Add Check: Ensure this isn't a status barcode --- 
            if scanned_value == PASS_BARCODE_VALUE or scanned_value == FAIL_BARCODE_VALUE:
                 logging.warning(f"Status barcode ({scanned_value}) scanned when expecting board barcode.")
                 self.show_scan_status_message("Error: Please scan the BOARD barcode first.", is_error=True)
                 self.scan_barcode_input.clear() # Clear the invalid input
                 self.scan_barcode_input.setFocus()
                 return # Do not proceed to step 2
            # ---
            
            self.current_board_barcode = scanned_value
            self.current_scan_status = None 
            self.expecting_status_scan = True
            self.scan_barcode_input.clear()
            self.scan_barcode_input.setPlaceholderText("NOW Scan PASS or FAIL Barcode then Press Enter...")
            self.show_scan_status_message(f"Board: {self.current_board_barcode}. Now scan PASS/FAIL.", is_error=False)
            logging.info(f"Board barcode captured: {self.current_board_barcode}")
            self.scan_barcode_input.setFocus()
            self.scan_notes_input.setEnabled(True)
            
        else:
            # --- Step 2: Status Barcode Scanned --- 
            status_barcode = scanned_value
            logging.info(f"Status barcode scanned: {status_barcode}")
            
            status_determined = None
            status_msg = ""
            status_color = "red" # Default to error color

            if status_barcode == PASS_BARCODE_VALUE:
                 status_determined = "Pass"
                 status_msg = f"Board: {self.current_board_barcode} -> Status: PASS Recorded. Submitting..."
                 status_color = "green"
                 logging.info("PASS status detected.")
            elif status_barcode == FAIL_BARCODE_VALUE:
                 status_determined = "Fail"
                 status_msg = f"Board: {self.current_board_barcode} -> Status: FAIL Recorded. Submitting..."
                 status_color = "orange"
                 logging.info("FAIL status detected.")
            else:
                 # Invalid Status Scan
                 status_msg = f"Unknown Status Barcode: {status_barcode[:20]}... Scan board again."
                 logging.warning(f"Unknown status barcode scanned: {status_barcode}")
                 self.show_scan_status_message(status_msg, is_error=True)
                 self._reset_scan_state() # Reset completely
                 return # Stop processing

            # Valid Status Scan - Proceed to Submit
            self.current_scan_status = status_determined 
            self.scan_status_label.setStyleSheet(f"QLabel {{ color: {status_color}; font-weight: bold; }}")
            self.scan_status_label.setText(status_msg)
            self.scan_barcode_input.clear()
            self.scan_barcode_input.setPlaceholderText("Submitting...")
            self.scan_barcode_input.setEnabled(False) # Disable input during submit
            self.scan_notes_input.setEnabled(False) # Disable notes during submit
            QApplication.processEvents() # Update UI before potential blocking API call

            # --- Directly Call Submit Logic --- 
            self._submit_scan_data_now()

    def _submit_scan_data_now(self):
        """Contains the logic to submit scan data (called after valid status scan)."""
        order_id = self.scan_order_combo.currentData()
        notes = self.scan_notes_input.toPlainText().strip()

        # Basic checks (should be valid if we reached here, but good practice)
        if order_id == -1 or not self.current_board_barcode or not self.current_scan_status:
             self.show_scan_status_message("Data inconsistency. Please start scan again.", is_error=True)
             self._reset_scan_state()
             return
             
        # Call the API
        result = self.api_client.record_scan(
            barcode=self.current_board_barcode,
            status=self.current_scan_status, 
            order_id=order_id, 
            notes=notes if notes else None
        )

        # Re-enable inputs after API call
        self.scan_barcode_input.setEnabled(True)
        self.scan_notes_input.setEnabled(True)
        
        if result["success"]:
            self.show_scan_status_message(f"OK: {self.current_board_barcode} -> {self.current_scan_status}. Ready for next board.", is_error=False)
            
            # --- Sync View Data Tab (Simplified) --- 
            # Always reload the data for the view tab in the background.
            # The table will be updated when the user switches to that tab.
            self._load_scans_for_view() 
            # ---
            
            self._reset_scan_state() # Reset for next scan
        else:
            self.show_scan_status_message(f"Submit Error: {result.get('message')}. Scan board again.", is_error=True)
            self._reset_scan_state()
            
    def _reset_scan_state(self):
        """Resets the scan tab state for the next board scan."""
        self.current_board_barcode = None
        self.current_scan_status = None
        self.expecting_status_scan = False
        self.scan_barcode_input.clear()
        self.scan_notes_input.clear()
        self.scan_status_label.setText("Scan Board Barcode and Press Enter") 
        self.scan_status_label.setStyleSheet("QLabel { font-weight: bold; }") 
        self.scan_barcode_input.setPlaceholderText("Scan Board Barcode -> Press Enter -> Scan Status Barcode -> Press Enter") 
        self.scan_barcode_input.setEnabled(True) 
        self.scan_notes_input.setEnabled(False) 
        self.scan_notes_input.setPlaceholderText("Notes (Enter *after* board scan)")
        self.scan_barcode_input.setFocus()

    def show_scan_status_message(self, message, is_error=True):
         if is_error:
              self.scan_status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
         else:
              self.scan_status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
         self.scan_status_label.setText(message)
         # Clear message after a few seconds if successful
         if not is_error and message: 
              QTimer.singleShot(3000, lambda: self.scan_status_label.setText(""))
              
    @pyqtSlot()
    def _handle_create_order(self):
         order_num = self.admin_order_number_input.text().strip()
         desc = self.admin_order_desc_input.text().strip()
         
         if not order_num:
              self.admin_order_status_label.setStyleSheet("color: red;")
              self.admin_order_status_label.setText("Order Number cannot be empty.")
              return
              
         self.admin_order_status_label.setText("Creating order...")
         result = self.api_client.create_order(order_num, desc if desc else None)
         
         if result["success"]:
              self.admin_order_status_label.setStyleSheet("color: green;")
              self.admin_order_status_label.setText("Order created successfully!")
              self.admin_order_number_input.clear()
              self.admin_order_desc_input.clear()
              self._load_orders() # Refresh dropdowns
              QTimer.singleShot(3000, lambda: self.admin_order_status_label.setText(""))
         else:
              self.admin_order_status_label.setStyleSheet("color: red;")
              self.admin_order_status_label.setText(f"Error: {result.get('message')}")

    @pyqtSlot()
    def _handle_add_dept(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Department")
        layout = QFormLayout(dialog)
        name_input = QLineEdit()
        layout.addRow("Department Name:", name_input)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec():
            name = name_input.text().strip()
            if name:
                 result = self.api_client.create_department(name)
                 if result["success"]:
                      QMessageBox.information(self, "Success", f"Department '{name}' created.")
                      self._load_departments() # Refresh list and potentially user add/edit dialogs
                 else:
                      QMessageBox.warning(self, "Error", f"Could not create department: {result.get('message')}")
            else:
                 QMessageBox.warning(self, "Input Error", "Department name cannot be empty.")
                 
    @pyqtSlot()
    def _handle_add_user(self):
        self._show_user_dialog()

    @pyqtSlot()
    def _handle_edit_user(self):
        selected_rows = self.admin_users_table.selectionModel().selectedRows()
        if not selected_rows:
             QMessageBox.warning(self, "Selection Error", "Please select a user to edit.")
             return
        if len(selected_rows) > 1:
             QMessageBox.warning(self, "Selection Error", "Please select only one user to edit.")
             return
             
        selected_row_index = selected_rows[0].row()
        user_id = int(self.admin_users_table.item(selected_row_index, 0).text())
        
        # Find the user data from our cached list
        user_to_edit = next((u for u in self.users if u['id'] == user_id), None)
        if not user_to_edit:
             QMessageBox.critical(self, "Error", "Could not find selected user data.")
             return
             
        # --- Call the dialog function, passing existing user data --- 
        self._show_user_dialog(existing_user=user_to_edit)
        # ---

    def _show_user_dialog(self, existing_user=None):
        """Shows a dialog to add or edit a user."""
        is_edit = existing_user is not None
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit User" if is_edit else "Add User")
        layout = QFormLayout(dialog)
        
        username_input = QLineEdit(existing_user['username'] if is_edit else "")
        password_input = QLineEdit()
        role_combo = QComboBox()
        dept_combo = QComboBox()
        
        role_combo.addItems(self.roles)
        dept_combo.addItem("None", None) # Option for no department
        for dept in self.departments:
             dept_combo.addItem(dept['name'], dept['id'])
             
        layout.addRow("Username:", username_input)
        if not is_edit:
             layout.addRow("Password:", password_input)
        else:
             # Don't allow password change here for simplicity
             username_input.setReadOnly(True) 
             pass_label = QLabel("<i>Password cannot be changed here</i>")
             layout.addRow("Password:", pass_label)
             
        layout.addRow("Role:", role_combo)
        layout.addRow("Department:", dept_combo)
        
        # Set current values for edit mode
        if is_edit:
             role_combo.setCurrentText(existing_user['role'])
             dept_id = existing_user.get('department_id')
             if dept_id:
                  index = dept_combo.findData(dept_id)
                  if index >= 0:
                       dept_combo.setCurrentIndex(index)
             else:
                  dept_combo.setCurrentIndex(0) # Select "None"
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec():
            username = username_input.text().strip()
            password = password_input.text() # Only relevant for add
            role_name = role_combo.currentText()
            dept_id = dept_combo.currentData() # Gets the data (ID or None)

            if not username:
                 QMessageBox.warning(self, "Input Error", "Username cannot be empty.")
                 return
            if not is_edit and not password:
                 QMessageBox.warning(self, "Input Error", "Password cannot be empty for new user.")
                 return
                 
            if is_edit:
                 # Call update API
                 result = self.api_client.update_user(existing_user['id'], role_name=role_name, department_id=dept_id)
                 if result["success"]:
                      QMessageBox.information(self, "Success", f"User '{username}' updated.")
                      self._load_users() # Refresh list
                 else:
                      QMessageBox.warning(self, "Error", f"Could not update user: {result.get('message')}")
            else:
                 # Call create API
                 result = self.api_client.create_user(username, password, role_name, department_id=dept_id)
                 if result["success"]:
                      QMessageBox.information(self, "Success", f"User '{username}' created.")
                      self._load_users() # Refresh list
                 else:
                      QMessageBox.warning(self, "Error", f"Could not create user: {result.get('message')}")
                      
    @pyqtSlot()
    def _handle_delete_user(self):
        selected_rows = self.admin_users_table.selectionModel().selectedRows()
        if not selected_rows:
             QMessageBox.warning(self, "Selection Error", "Please select a user to delete.")
             return
        if len(selected_rows) > 1:
             QMessageBox.warning(self, "Selection Error", "Please select only one user to delete.")
             return
             
        selected_row_index = selected_rows[0].row()
        user_id = int(self.admin_users_table.item(selected_row_index, 0).text())
        username = self.admin_users_table.item(selected_row_index, 1).text()
        
        if user_id == self.user_data.get('id'):
            QMessageBox.warning(self, "Error", "You cannot delete yourself.")
            return

        reply = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete user '{username}'?\nThis action cannot be undone.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            result = self.api_client.delete_user(user_id)
            if result["success"]:
                 QMessageBox.information(self, "Success", f"User '{username}' deleted.")
                 self._load_users() # Refresh list
            else:
                 QMessageBox.critical(self, "Error", f"Could not delete user: {result.get('message')}")

    @pyqtSlot()
    def _handle_delete_order(self):
         if not hasattr(self, 'delete_order_combo'): return # Should only be callable by Admin
         
         order_id = self.delete_order_combo.currentData()
         order_text = self.delete_order_combo.currentText()
         if order_id == -1:
              QMessageBox.warning(self, "Selection Error", "Please select a valid order to delete.")
              return
              
         reply = QMessageBox.question(self, "Confirm Delete Order", 
                                      f"Are you sure you want to DELETE order '{order_text}'?\nALL associated scans and comments will also be permanently deleted!",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                      QMessageBox.StandardButton.No)

         if reply == QMessageBox.StandardButton.Yes:
             result = self.api_client.delete_order(order_id)
             if result["success"]:
                  QMessageBox.information(self, "Success", f"Order '{order_text}' deleted.")
                  self._load_orders() # Refresh all order lists
                  self._load_scans_for_view() # Refresh scans view
             else:
                  QMessageBox.critical(self, "Error", f"Could not delete order: {result.get('message')}")

    @pyqtSlot()
    def _handle_edit_scan(self):
        selected_rows = self.view_scans_table.selectionModel().selectedRows()
        if not selected_rows:
             QMessageBox.warning(self, "Selection Error", "Please select a scan to edit.")
             return
        if len(selected_rows) > 1:
             QMessageBox.warning(self, "Selection Error", "Please select only one scan to edit.")
             return
             
        selected_row_index = selected_rows[0].row()
        scan_id = int(self.view_scans_table.item(selected_row_index, 0).text())
        current_status = self.view_scans_table.item(selected_row_index, 3).text()
        current_notes = self.view_scans_table.item(selected_row_index, 4).text()
        barcode = self.view_scans_table.item(selected_row_index, 1).text()
        
        # Show Edit Scan Dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Scan {scan_id} ({barcode})")
        layout = QFormLayout(dialog)
        
        status_combo = QComboBox()
        status_combo.addItems(["Pass", "Fail"])
        status_combo.setCurrentText(current_status)
        
        notes_edit = QTextEdit(current_notes)
        notes_edit.setMaximumHeight(100)
        
        layout.addRow("Status:", status_combo)
        layout.addRow("Notes:", notes_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec():
             new_status = status_combo.currentText()
             new_notes = notes_edit.toPlainText().strip()
             
             # Check if changes were made
             if new_status == current_status and new_notes == current_notes:
                  QMessageBox.information(self, "No Change", "Scan status and notes were not changed.")
                  return
                  
             result = self.api_client.update_scan(scan_id, status=new_status, notes=new_notes)
             if result["success"]:
                  QMessageBox.information(self, "Success", f"Scan {scan_id} updated.")
                  self._load_scans_for_view() # Refresh scan list
             else:
                  QMessageBox.warning(self, "Error", f"Could not update scan: {result.get('message')}")

    @pyqtSlot()
    def _handle_delete_scan(self):
        selected_rows = self.view_scans_table.selectionModel().selectedRows()
        if not selected_rows:
             QMessageBox.warning(self, "Selection Error", "Please select a scan to delete.")
             return
        if len(selected_rows) > 1:
             QMessageBox.warning(self, "Selection Error", "Please select only one scan to delete.")
             return
             
        selected_row_index = selected_rows[0].row()
        scan_id = int(self.view_scans_table.item(selected_row_index, 0).text())
        barcode = self.view_scans_table.item(selected_row_index, 1).text()

        reply = QMessageBox.question(self, "Confirm Delete Scan", 
                                     f"Are you sure you want to DELETE scan '{barcode}' (ID: {scan_id})?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            result = self.api_client.delete_scan(scan_id)
            if result["success"]:
                 QMessageBox.information(self, "Success", f"Scan '{barcode}' deleted.")
                 self._load_scans_for_view() # Refresh list
            else:
                 QMessageBox.critical(self, "Error", f"Could not delete scan: {result.get('message')}")

    @pyqtSlot()
    def _handle_submit_feedback(self):
        """Handles the submission of user feedback."""
        feedback_text = self.feedback_text_edit.toPlainText().strip()
        if not feedback_text:
            self.feedback_status_label.setText("<font color='red'>Feedback cannot be empty.</font>")
            QTimer.singleShot(3000, lambda: self.feedback_status_label.setText(""))
            return

        try:
            feedback_file = self.feedback_path_func() # Get path using the function
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            username = self.user_data.get("username", "UnknownUser")
            
            with open(feedback_file, 'a', encoding='utf-8') as f:
                f.write(f"--- Feedback Entry ---\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"User: {username}\n")
                f.write(f"Feedback:\n{feedback_text}\n")
                f.write(f"----------------------\n\n")
                
            logging.info(f"User feedback submitted by '{username}' to {feedback_file}")
            self.feedback_text_edit.clear()
            self.feedback_status_label.setText("<font color='green'>Feedback submitted successfully!</font>")
            QTimer.singleShot(3000, lambda: self.feedback_status_label.setText(""))

        except Exception as e:
            logging.error(f"Failed to write user feedback: {e}")
            self.feedback_status_label.setText(f"<font color='red'>Error submitting feedback: {e}</font>")
            # Keep the text in the box so the user doesn't lose it

    # --- Other Handlers ---
    @pyqtSlot()
    def _handle_logout(self):
        logout_result = self.api_client.logout()
        if logout_result["success"]:
             # Don't show message box here, controller will handle window switch
             # QMessageBox.information(self, "Logout", "You have been logged out.")
             logging.info("Logout successful, emitting signal.")
             self.logged_out.emit() # Emit the signal
             self.close() # Close this window
        else:
             QMessageBox.warning(self, "Logout Failed", f"Could not log out: {logout_result.get('message')}")
             
    @pyqtSlot()
    def _show_about_dialog(self):
         QMessageBox.about(self, "About Label Tracker", 
                           "Label Tracker Application\nVersion 1.0\n\nDeveloped for tracking label scans.")

    def closeEvent(self, event):
        """Stop timers/watchers when window closes, if they exist."""
        # --- Remove log timer/watcher stop logic ---
        super().closeEvent(event)

    @pyqtSlot()
    def _handle_delete_dept(self):
        """Handles deleting the selected department."""
        selected_rows = self.admin_depts_table.selectionModel().selectedRows()
        if not selected_rows:
            return QMessageBox.warning(self, "Selection Error", "Please select a department to delete.")
        
        row = selected_rows[0].row()
        try:
            dept_id = int(self.admin_depts_table.item(row, 0).text())
            dept_name = self.admin_depts_table.item(row, 1).text()
        except (AttributeError, ValueError, IndexError):
             QMessageBox.critical(self, "Error", "Could not get department details from selected row.")
             return

        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete the department '{dept_name}'?\n" +
                                   "This will fail if any users or scans are currently assigned to it.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            logging.info(f"Attempting to delete department ID: {dept_id} ('{dept_name}')")
            result = self.api_client.delete_department(dept_id)
            if result["success"]:
                 QMessageBox.information(self, "Success", f"Department '{dept_name}' deleted.")
                 self._load_departments() # Refresh department list
                 self._load_users()       # Refresh user list (might show N/A for deleted dept)
            else:
                 QMessageBox.critical(self, "Delete Failed", f"Could not delete department: {result.get('message')}")

# Example Usage (kept for testing, might need adjustments)
if __name__ == '__main__':
    # ... (Independent test code - needs updates if used, e.g., mocking new API calls)
    app = QApplication(sys.argv)
    dummy_client = ApiClient(base_url="http://dummyurl") 
    dummy_user_data_admin = {"id": 1, "username": "test_admin", "role": "Admin", "department": "IT"}
    # Mock API calls for testing UI
    dummy_client.get_orders = lambda: {"success": True, "data": {"orders": [
        {"id": 1, "order_number": "ORD-001", "description": "Desc 1", "creator_username": "admin"},
        {"id": 2, "order_number": "ORD-002", "description": "Desc 2", "creator_username": "admin"}
    ]}}
    dummy_client.get_scans = lambda order_id=None: {"success": True, "data": {"scans": [
        {"id": 101, "barcode": "BC1", "timestamp": "2023-01-01T10:00:00", "status": "Pass", "notes": "", "order_id": 1, "user_id": 1, "department_id": 1, "order_number": "ORD-001", "username": "admin", "department_name": "IT"} 
    ] if order_id == 1 else []}}
    dummy_client.get_departments = lambda: {"success": True, "data": {"departments": [
        {"id": 1, "name": "IT"}, {"id": 2, "name": "Assembly"}
    ]}}
    dummy_client.get_users = lambda: {"success": True, "data": {"users": [
        {"id": 1, "username": "test_admin", "role": "Admin", "department_id": 1, "department_name": "IT"},
        {"id": 2, "username": "test_user", "role": "Standard", "department_id": 2, "department_name": "Assembly"}
    ]}}
    
    main_win_admin = MainWindow(dummy_user_data_admin, dummy_client, lambda: "dummy_feedback_file.txt")
    main_win_admin.show()
    sys.exit(app.exec()) 
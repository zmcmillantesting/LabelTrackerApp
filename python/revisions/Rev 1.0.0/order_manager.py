from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QMessageBox,
                           QTabWidget, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
                           QTextEdit, QScrollArea, QGroupBox, QAbstractItemView, QSizePolicy, QDialog, QMenu)
from PyQt6.QtCore import QRegularExpression, QTimer, Qt
from PyQt6.QtGui import QRegularExpressionValidator, QPixmap
from data_manager import DataManager
# from comment_manager import CommentManager # Removed
import traceback # Added import
from datetime import datetime
import re
import os

class OrderManager(QWidget):
    def __init__(self, data_manager, username, on_logout=None):
        print(f"\nDEBUG: OrderManager.__init__ - START for '{username}'") # START __init__
        try:
            super().__init__()
            self.setMinimumSize(1200, 600)
            self.setMaximumSize(1400, 800)
            print(f"DEBUG: OrderManager.__init__ - Super init done")
            self.data_manager = data_manager
            self.username = username
            self.on_logout = on_logout if on_logout else self._dummy_logout
            print(f"DEBUG: OrderManager.__init__ - Basic attributes set")

            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(lambda: self.update_orders_table(force_refresh=False))
            self.refresh_timer.start(60000)
            print(f"DEBUG: OrderManager.__init__ - Refresh timer started")

            self.PASS_CODE = "__PASS__"
            self.FAIL_CODE = "__FAIL__"
            
            print(f"DEBUG: OrderManager.__init__ - Initializing UI elements to None...")
            self._init_ui_elements() # Initialize attributes to None
            print(f"DEBUG: OrderManager.__init__ - UI elements initialized to None")

            # 1. Initialize the UI structure
            print(f"DEBUG: OrderManager.__init__ - Calling init_ui()...")
            self.init_ui() # This now contains the main UI build logic
            print(f"DEBUG: OrderManager.__init__ - init_ui() finished")

            # 2. *After* UI is built, populate tables and selectors
            print("DEBUG: OrderManager.__init__ - Populating UI elements after init...")
            self.update_orders_table(force_refresh=True)
            self.update_all_order_selectors()
            print("DEBUG: OrderManager.__init__ - Populated tables and selectors")

            # 3. Set initial state for selections if possible
            print("DEBUG: OrderManager.__init__ - Setting initial selections...")
            self.force_barcode_selection_update(show_popup=False)
            self.update_board_selection(show_popup=False)
            print("DEBUG: OrderManager.__init__ - Initial selections set")

            print(f"DEBUG: OrderManager.__init__ - Initialized successfully for '{username}' - END") # END __init__

        except Exception as e:
            # This catches errors during super().__init__ or any part of the init process
            print(f"ERROR: OrderManager.__init__ - CRITICAL FAILURE for user '{username}': {e}")
            traceback.print_exc()
            # Attempt to set up a minimal error UI within the widget itself
            # This might fail if super().__init__() failed badly
            try:
                self._init_error_ui(e, on_logout)
            except Exception as error_ui_ex:
                 print(f"ERROR: OrderManager.__init__ - FAILED to even create error UI: {error_ui_ex}")
            # IMPORTANT: Re-raise the exception so MainWindow knows initialization failed
            raise e

    def _init_ui_elements(self):
        """Initializes all UI element attributes to None."""
        self.order_selector = None
        self.board_order_selector = None
        self.orders_table = None
        self.boards_table = None
        self.session_terminal = None
        self.barcode_entry = None
        self.board_entry = None
        self.board_desc_entry = None
        self.barcode_status_label = None
        self.board_stats_label = None
        self.board_debug_label = None
        self.barcode_order_debug_label = None
        self.board_order_display = None # Added missing init
        self.active_comments_dialog = None
        self.pending_barcode = None
        self.current_barcode_order = ""
        self.current_board_order = ""
        # Fields for Create Order tab (if manager)
        self.order_number_entry = None
        self.customer_entry = None
        self.board_name_entry = None
        self.quantity_entry = None
        self.comments_entry = None

    def _init_error_ui(self, error, on_logout):
        """Create minimal UI in case of initialization error"""
            layout = QVBoxLayout(self)
        error_label = QLabel(f"Error loading user interface: {str(error)}")
            layout.addWidget(error_label)
            if on_logout:
                logout_button = QPushButton("Return to Login")
                logout_button.clicked.connect(on_logout)
                layout.addWidget(logout_button)
    
    def _dummy_logout(self):
        print("Warning: No logout function provided")
        QMessageBox.warning(self, "Warning", "Logout function not available")
        
    def init_ui(self):
        print("DEBUG: OrderManager.init_ui - START")
        # Create the main layout for this OrderManager widget FIRST
        main_layout = QVBoxLayout(self) # Explicitly set layout on self
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        try: # Keep try-except for UI construction
            # --- Top Bar ---
            print("DEBUG: OrderManager.init_ui - Creating top bar...")
            top_bar_widget = QWidget()
            top_bar_layout = QHBoxLayout(top_bar_widget)
            top_bar_layout.setContentsMargins(5, 5, 5, 5)
            top_bar_layout.addStretch()
            logout_button = QPushButton("Logout")
            logout_button.setMinimumWidth(100)
            logout_button.setMinimumHeight(25)
            if callable(self.on_logout):
                logout_button.clicked.connect(self.on_logout)
            else:
                logout_button.setEnabled(False)
            top_bar_layout.addWidget(logout_button)
            main_layout.addWidget(top_bar_widget) # Add top bar to OrderManager's layout
            print("DEBUG: OrderManager.init_ui - Top bar created and added")

            # --- Tabs ---
            print("DEBUG: OrderManager.init_ui - Creating QTabWidget...")
        tabs = QTabWidget()
            tabs.setStyleSheet("QTabWidget::pane { border-top: 1px solid lightgray; margin: 0px; padding: 10px; } QTabBar::tab { min-width: 100px; }") # Stylesheet
            print("DEBUG: OrderManager.init_ui - QTabWidget created")
        
            # Check permissions
            print("DEBUG: OrderManager.init_ui - Checking permissions...")
        can_create_orders = self.data_manager.has_permission(self.username, "create_orders")
        can_scan_barcodes = self.data_manager.has_permission(self.username, "scan_barcodes")
        can_view_orders = self.data_manager.has_permission(self.username, "view_own_orders") or self.data_manager.has_permission(self.username, "view_all_orders")
            print(f"DEBUG: OrderManager.init_ui - Permissions: Create={can_create_orders}, Scan={can_scan_barcodes}, View={can_view_orders}")
        
            # Create and Add Tabs
            tab_widgets = [] # Keep track of created tabs for debugging
        if can_create_orders:
                print("DEBUG: OrderManager.init_ui - Creating 'Create Order' tab...")
                tab_widget = self._create_order_creation_tab()
                if tab_widget:
                    tabs.addTab(tab_widget, "Create Order")
                    tab_widgets.append("Create Order")
                    print("DEBUG: OrderManager.init_ui - 'Create Order' tab added")
                else:
                    print("ERROR: OrderManager.init_ui - _create_order_creation_tab returned None")

            if can_scan_barcodes:
                print("DEBUG: OrderManager.init_ui - Creating 'Board Management' tab...")
                tab_widget = self._create_board_management_tab()
                if tab_widget:
                    tabs.addTab(tab_widget, "Board Management")
                    tab_widgets.append("Board Management")
                    print("DEBUG: OrderManager.init_ui - 'Board Management' tab added")
                else:
                     print("ERROR: OrderManager.init_ui - _create_board_management_tab returned None")

                print("DEBUG: OrderManager.init_ui - Creating 'Scan Barcode' tab...")
                tab_widget = self._create_barcode_scanning_tab()
                if tab_widget:
                    tabs.addTab(tab_widget, "Scan Barcode")
                    tab_widgets.append("Scan Barcode")
                    print("DEBUG: OrderManager.init_ui - 'Scan Barcode' tab added")
                else:
                    print("ERROR: OrderManager.init_ui - _create_barcode_scanning_tab returned None")

            if can_view_orders:
                print("DEBUG: OrderManager.init_ui - Creating 'View Orders' tab...")
                tab_widget = self._create_view_orders_tab()
                if tab_widget:
                    tabs.addTab(tab_widget, "View Orders")
                    tab_widgets.append("View Orders")
                    print("DEBUG: OrderManager.init_ui - 'View Orders' tab added")
                else:
                    print("ERROR: OrderManager.init_ui - _create_view_orders_tab returned None")

            print(f"DEBUG: OrderManager.init_ui - Total tabs created and added: {tabs.count()} ({', '.join(tab_widgets)})")
            # *** Add the Tab Widget to the main layout ONLY if tabs were added ***
            if tabs.count() > 0:
                main_layout.addWidget(tabs)
                print("DEBUG: OrderManager.init_ui - Tabs widget added to main layout")
            else:
                 # Add a placeholder if no tabs are visible for this user
                 print("WARNING: OrderManager.init_ui - No tabs were added based on permissions! Adding placeholder.")
                 placeholder_label = QLabel("No functions available for this user.")
                 placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                 main_layout.addWidget(placeholder_label)
                 main_layout.addStretch() # Push placeholder up

        except Exception as ui_error:
             # Catch errors during UI construction *within* init_ui
             print(f"ERROR: OrderManager.init_ui - FAILED during UI construction: {ui_error}")
             traceback.print_exc()
             # Try to add an error label to the main layout if possible
             try:
                 error_label = QLabel(f"Failed to build Order Manager UI: {ui_error}")
                 main_layout.addWidget(error_label)
             except Exception as layout_error:
                  print(f"ERROR: Could not even add error label to layout: {layout_error}")
             # It's crucial to re-raise or handle this so __init__ knows it failed
             raise ui_error

        print("DEBUG: OrderManager.init_ui - END")

    def _create_order_creation_tab(self):
        print("DEBUG: OrderManager._create_order_creation_tab - START")
        try:
            order_tab = QWidget()
            order_layout = QVBoxLayout(order_tab)
            order_layout.setSpacing(15)
            is_manager_or_admin = self.data_manager.is_manager(self.username) or self.username == "admin"
            
            # Order number input
            order_number_layout = QHBoxLayout()
            order_number_label = QLabel("Order Number:")
            order_number_label.setMinimumWidth(100)
            self.order_number_entry = QLineEdit()
            self.order_number_entry.setMinimumWidth(250)
            order_number_layout.addWidget(order_number_label)
            order_number_layout.addWidget(self.order_number_entry)
            order_number_layout.addStretch()
            order_layout.addLayout(order_number_layout)
            
            # Enhanced order details for managers and admin
            if is_manager_or_admin:
                self._add_enhanced_order_fields(order_layout)

            # Create order button
            create_order_button = QPushButton("Create Order")
            create_order_button.setMinimumWidth(120)
            create_order_button.setMinimumHeight(30)
            create_order_button.clicked.connect(self.create_order)
            order_layout.addWidget(create_order_button)
            order_layout.addStretch()

            print("DEBUG: OrderManager._create_order_creation_tab - END")
            return order_tab
        except Exception as e:
            print(f"ERROR: Failed to create 'Create Order' tab: {e}")
            traceback.print_exc()
            return None # Return None on failure

    def _add_enhanced_order_fields(self, layout):
        """Adds enhanced fields for managers/admins to the create order tab."""
                # Customer name input
                customer_layout = QHBoxLayout()
                customer_label = QLabel("Customer:")
                customer_label.setMinimumWidth(100)
                self.customer_entry = QLineEdit()
                self.customer_entry.setMinimumWidth(250)
                self.customer_entry.setPlaceholderText("Enter customer name")
                customer_layout.addWidget(customer_label)
                customer_layout.addWidget(self.customer_entry)
                customer_layout.addStretch()
        layout.addLayout(customer_layout)
                
                # Board name input
                board_name_layout = QHBoxLayout()
                board_name_label = QLabel("Board Type:")
                board_name_label.setMinimumWidth(100)
                self.board_name_entry = QLineEdit()
                self.board_name_entry.setMinimumWidth(250)
                self.board_name_entry.setPlaceholderText("Enter board type/name")
                board_name_layout.addWidget(board_name_label)
                board_name_layout.addWidget(self.board_name_entry)
                board_name_layout.addStretch()
        layout.addLayout(board_name_layout)
                
                # Quantity input
                quantity_layout = QHBoxLayout()
                quantity_label = QLabel("Quantity:")
                quantity_label.setMinimumWidth(100)
                self.quantity_entry = QLineEdit()
                self.quantity_entry.setMinimumWidth(100)
                self.quantity_entry.setPlaceholderText("Total pieces")
                self.quantity_entry.setValidator(QRegularExpressionValidator(QRegularExpression("\\d+")))
                quantity_layout.addWidget(quantity_label)
                quantity_layout.addWidget(self.quantity_entry)
                quantity_layout.addStretch()
        layout.addLayout(quantity_layout)
                
                # Comments input
                comments_layout = QVBoxLayout()
                comments_label = QLabel("Initial Comments:")
                self.comments_entry = QTextEdit()
                self.comments_entry.setMaximumHeight(100)
                self.comments_entry.setPlaceholderText("Enter any initial comments for this order")
                comments_layout.addWidget(comments_label)
                comments_layout.addWidget(self.comments_entry)
        layout.addLayout(comments_layout)

    def _create_board_management_tab(self):
        print("DEBUG: OrderManager._create_board_management_tab - START")
        try:
            board_tab = QWidget()
            # Use a main vertical layout for the tab
            main_board_layout = QVBoxLayout(board_tab)
            main_board_layout.setSpacing(10) # Spacing between groups

            # Debug indicator (optional)
            # self.board_debug_label = QLabel("DEBUG: Initialized") ...

            # Order Selection Section
            main_board_layout.addWidget(self._create_board_order_selection_group())

            # Board Input Section
            main_board_layout.addWidget(self._create_board_input_group())

            # --- Boards Table Section (Modified Layout) ---
            table_group = QGroupBox("BOARDS IN SELECTED ORDER")
            table_group.setStyleSheet("QGroupBox { font-weight: bold; }") # Simpler style
            table_layout = QVBoxLayout(table_group) # Layout for inside the group

            # Row for controls (label, refresh, delete)
            controls_row = QHBoxLayout()
            table_label = QLabel("Current Boards:")
            table_label.setStyleSheet("font-weight: bold;")
            refresh_btn = QPushButton("🔄 Refresh Boards")
            refresh_btn.setStyleSheet("background-color: #6c757d; color: white;")
            refresh_btn.clicked.connect(self.manual_refresh_boards_table)
            controls_row.addWidget(table_label)
            controls_row.addStretch()
            controls_row.addWidget(refresh_btn)

            if self.data_manager.is_manager(self.username):
                delete_button = QPushButton("🗑️ Delete Selected Board")
                delete_button.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold;")
                delete_button.clicked.connect(self.delete_selected_board)
                controls_row.addWidget(delete_button)
            table_layout.addLayout(controls_row) # Add controls row to group layout

            # Create the boards table directly
            self.boards_table = QTableWidget()
            self.boards_table.setStyleSheet("font-size: 11pt;")
            self.boards_table.setColumnCount(3)
            self.boards_table.setHorizontalHeaderLabels(["Board ID", "Description", "Department"])
            self.boards_table.setColumnWidth(0, 150)
            self.boards_table.setColumnWidth(1, 250)
            self.boards_table.setAlternatingRowColors(True)
            self.boards_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.boards_table.setHorizontalHeader().setStretchLastSection(True)
            self.boards_table.verticalHeader().setVisible(False)
            # Enable vertical scrolling explicitly on the table
            self.boards_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            self.boards_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            # Set horizontal policy as needed
            self.boards_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

            if self.data_manager.is_manager(self.username):
                self.boards_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
                self.boards_table.customContextMenuRequested.connect(self.show_board_context_menu)

            table_layout.addWidget(self.boards_table) # Add table *directly* to the group layout

            # Board stats label
            self.board_stats_label = QLabel("No boards in this order")
            self.board_stats_label.setStyleSheet("color: #6c757d; padding-top: 5px;") # Add padding
            table_layout.addWidget(self.board_stats_label)

            # Add the table group to the main tab layout
            # Allow the table group to expand vertically
            main_board_layout.addWidget(table_group)
            main_board_layout.setStretchFactor(table_group, 1) # Make this group take available space

            # Initialize the order selector *after* the UI element is created
            self.update_order_selector_for_boards()

            print("DEBUG: OrderManager._create_board_management_tab - END")
            return board_tab
        except Exception as e:
            print(f"ERROR: Failed to create 'Board Management' tab: {e}")
            traceback.print_exc()
            return None

    def _create_board_order_selection_group(self):
        """Creates the 'ORDER SELECTION' group box."""
            selection_group = QGroupBox("ORDER SELECTION")
            selection_group.setStyleSheet("QGroupBox { font-weight: bold; background-color: #e6f2ff; border: 2px solid #004080; }")
            selection_layout = QVBoxLayout(selection_group)
            
            order_row = QHBoxLayout()
            order_label = QLabel("Active Order:")
            order_label.setStyleSheet("font-weight: bold;")
            order_label.setMinimumWidth(100)
            
            self.board_order_selector = QComboBox()
            self.board_order_selector.setStyleSheet("font-size: 12pt; padding: 5px;")
            self.board_order_selector.setMinimumWidth(250)
            
            self.board_order_display = QLabel("No order selected")
            self.board_order_display.setStyleSheet("color: blue; font-weight: bold; font-size: 12pt; padding: 5px; background-color: #e6e6e6;")
            
            order_row.addWidget(order_label)
            order_row.addWidget(self.board_order_selector)
            order_row.addWidget(self.board_order_display)
            selection_layout.addLayout(order_row)
            
            warning = QLabel("⚠️ After selecting an order, click UPDATE SELECTION button below")
            warning.setStyleSheet("color: red; font-weight: bold;")
            selection_layout.addWidget(warning)
            
            update_btn = QPushButton("✓ UPDATE SELECTION")
            update_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; font-size: 14px;")
            update_btn.setMinimumHeight(50)
            update_btn.clicked.connect(self.update_board_selection)
            selection_layout.addWidget(update_btn)
            
        return selection_group
            
    def _create_board_input_group(self):
        """Creates the 'ADD NEW BOARD' group box."""
            input_group = QGroupBox("ADD NEW BOARD")
            input_group.setStyleSheet("QGroupBox { font-weight: bold; background-color: #f0f7ff; }")
            input_layout = QVBoxLayout(input_group)
            
            id_row = QHBoxLayout()
            id_label = QLabel("Board ID:")
            id_label.setMinimumWidth(100)
            self.board_entry = QLineEdit()
            self.board_entry.setStyleSheet("font-size: 12pt; padding: 5px;")
            self.board_entry.setMinimumWidth(250)
            self.board_entry.setPlaceholderText("Enter unique board identifier")
            id_row.addWidget(id_label)
            id_row.addWidget(self.board_entry)
            input_layout.addLayout(id_row)
            
            desc_row = QHBoxLayout()
            desc_label = QLabel("Description:")
            desc_label.setMinimumWidth(100)
            self.board_desc_entry = QLineEdit()
            self.board_desc_entry.setStyleSheet("font-size: 12pt; padding: 5px;")
            self.board_desc_entry.setMinimumWidth(250)
            self.board_desc_entry.setPlaceholderText("Optional description of the board")
            desc_row.addWidget(desc_label)
            desc_row.addWidget(self.board_desc_entry)
            input_layout.addLayout(desc_row)
            
            add_board_button = QPushButton("+ ADD BOARD TO ORDER")
            add_board_button.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 10px; font-size: 12px;")
            add_board_button.setMinimumHeight(40)
            add_board_button.clicked.connect(self.add_board)
            input_layout.addWidget(add_board_button)
            
        return input_group

    def _create_barcode_scanning_tab(self):
        print("DEBUG: OrderManager._create_barcode_scanning_tab - START")
        try:
            barcode_tab = QWidget()
            barcode_layout = QVBoxLayout(barcode_tab)
            barcode_layout.setSpacing(10)

            # Add reference barcodes section
            reference_group = self._create_status_barcodes_reference_group()
            if reference_group: # Only add if images were found
                 barcode_layout.addWidget(reference_group)

            # Add order selection section
            barcode_layout.addWidget(self._create_barcode_order_selection_group())

            # Add barcode input section
                barcode_input_layout = QHBoxLayout()
                barcode_label = QLabel("Barcode:")
            barcode_label.setMinimumWidth(100)
                self.barcode_entry = QLineEdit()
            self.barcode_entry.setMinimumWidth(250)
                self.barcode_entry.returnPressed.connect(self.add_barcode)
            barcode_input_layout.addStretch()
                barcode_input_layout.addWidget(barcode_label)
                barcode_input_layout.addWidget(self.barcode_entry)
            barcode_input_layout.addStretch()
                barcode_layout.addLayout(barcode_input_layout)
            
            # Add status label
                self.barcode_status_label = QLabel("Scan Board Barcode")
            self._set_status_label_info("Scan Board Barcode") # Use helper
                self.barcode_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                barcode_layout.addWidget(self.barcode_status_label)
            
            barcode_layout.addStretch()

            # Load orders into selector
            self.update_order_selector()

            print("DEBUG: OrderManager._create_barcode_scanning_tab - END")
            return barcode_tab
        except Exception as e:
            print(f"ERROR: Failed to create 'Scan Barcode' tab: {e}")
            traceback.print_exc()
            return None

    def _create_status_barcodes_reference_group(self):
        """Creates the 'Status Barcodes Reference' group box."""
        reference_group = QGroupBox("Status Barcodes Reference")
        reference_group.setStyleSheet("QGroupBox { font-weight: bold; background-color: #e6ffe6; border: 1px solid #004d00; }")
        reference_layout = QVBoxLayout(reference_group)

        pass_image_path = os.path.join('barcodes', 'pass_barcode.png')
        fail_image_path = os.path.join('barcodes', 'fail_barcode.png')

        if os.path.exists(pass_image_path) and os.path.exists(fail_image_path):
            # Pass barcode
                pass_container = QWidget()
                pass_container.setStyleSheet("background-color: #e6ffe6; border: 3px solid #4CAF50; border-radius: 5px; padding: 5px;")
                pass_layout = QVBoxLayout(pass_container)
                pass_label = QLabel("✅ PASS Status Barcode")
                pass_label.setStyleSheet("color: #2E7D32; font-weight: bold; font-size: 14pt;")
                pass_pixmap = QPixmap(pass_image_path).scaledToWidth(300)
            pass_image_label = QLabel()
            pass_image_label.setPixmap(pass_pixmap)
            pass_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                pass_layout.addWidget(pass_label)
            pass_layout.addWidget(pass_image_label)
            reference_layout.addWidget(pass_container)
            reference_layout.addSpacing(5)
                
            # Fail barcode
                fail_container = QWidget()
                fail_container.setStyleSheet("background-color: #ffe6e6; border: 3px solid #f44336; border-radius: 5px; padding: 5px;")
                fail_layout = QVBoxLayout(fail_container)
                fail_label = QLabel("❌ FAIL Status Barcode")
                fail_label.setStyleSheet("color: #C62828; font-weight: bold; font-size: 14pt;")
                fail_pixmap = QPixmap(fail_image_path).scaledToWidth(300)
            fail_image_label = QLabel()
            fail_image_label.setPixmap(fail_pixmap)
            fail_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                fail_layout.addWidget(fail_label)
            fail_layout.addWidget(fail_image_label)
                reference_layout.addWidget(fail_container)
            reference_layout.addSpacing(5)
                
            # Instructions
                instructions = QLabel(
                    "📝 Instructions:\n"
                    "1. Scan the board's barcode\n"
                    "2. Then scan either PASS or FAIL barcode above to record the status"
                )
                instructions.setStyleSheet("""
                    font-size: 12pt; 
                    color: #333; 
                    margin-top: 5px;
                    padding: 5px;
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                """)
                instructions.setAlignment(Qt.AlignmentFlag.AlignLeft)
                reference_layout.addSpacing(5)
                reference_layout.addWidget(instructions)
            return reference_group
            else:
                error_label = QLabel("Status barcodes not found. Please run generate_barcodes.py first.")
                error_label.setStyleSheet("color: red; font-weight: bold;")
                reference_layout.addWidget(error_label)
            return reference_group # Return group even with error message

    def _create_barcode_order_selection_group(self):
        """Creates the order selection group box for the barcode tab."""
        barcode_order_section = QGroupBox("ORDER SELECTION - Important!")
        barcode_order_section.setStyleSheet("QGroupBox { font-weight: bold; color: #004080; }")
        barcode_order_section_layout = QVBoxLayout(barcode_order_section)

        order_selection_layout = QHBoxLayout()
        order_selection_label = QLabel("Select Order:")
        order_selection_label.setMinimumWidth(100)

        self.order_selector = QComboBox()
        self.order_selector.setObjectName("order_selector")
        self.order_selector.setMinimumWidth(250)

        self.barcode_order_debug_label = QLabel("")
        self.barcode_order_debug_label.setStyleSheet("font-weight: bold; color: blue; font-size: 12px;")

        order_selection_layout.addWidget(order_selection_label)
        order_selection_layout.addWidget(self.order_selector)
        order_selection_layout.addWidget(self.barcode_order_debug_label)
        order_selection_layout.addStretch()

        barcode_order_section_layout.addLayout(order_selection_layout)

        barcode_selection_note = QLabel("⚠️ IMPORTANT: After selecting an order, click UPDATE to confirm your selection")
        barcode_selection_note.setStyleSheet("color: red; font-weight: bold;")
        barcode_order_section_layout.addWidget(barcode_selection_note)

        confirm_barcode_selection_btn = QPushButton("UPDATE SELECTION")
        confirm_barcode_selection_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 6px;")
        confirm_barcode_selection_btn.setMinimumHeight(40)
        confirm_barcode_selection_btn.clicked.connect(self.force_barcode_selection_update)
        barcode_order_section_layout.addWidget(confirm_barcode_selection_btn)

        return barcode_order_section

    def _create_view_orders_tab(self):
        print("DEBUG: OrderManager._create_view_orders_tab - START")
        try:
            orders_tab = QWidget()
            orders_layout = QVBoxLayout(orders_tab)
            orders_layout.setSpacing(10)

            # Orders table group
            orders_group = QGroupBox("Orders")
            orders_group_layout = QVBoxLayout(orders_group)
            
            # Header with buttons
            header_layout = QHBoxLayout()
            header_label = QLabel("Active Orders List")
            header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            header_layout.addWidget(header_label)
            header_layout.addStretch()
            
            view_comments_button = QPushButton("View Comments")
            view_comments_button.setMinimumWidth(120)
            view_comments_button.setMinimumHeight(30)
            view_comments_button.clicked.connect(self.view_selected_order_comments)
            header_layout.addWidget(view_comments_button)
            
            refresh_button = QPushButton("Refresh")
            refresh_button.setMinimumWidth(100)
            refresh_button.setMinimumHeight(30)
            refresh_button.clicked.connect(lambda: self.update_orders_table(force_refresh=True))
            header_layout.addWidget(refresh_button)
            orders_group_layout.addLayout(header_layout)
            
            # Orders table
            self.orders_table = QTableWidget()
            self.orders_table.setColumnCount(5)
            self.orders_table.setHorizontalHeaderLabels(["Order Number", "Customer", "Quantity", "Boards", "Time Since Creation"])
            self.orders_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
            self.orders_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.orders_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            self.orders_table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            self.orders_table.setAlternatingRowColors(True)
            self.orders_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.orders_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self.orders_table.verticalHeader().setVisible(False)
            self.orders_table.setMinimumHeight(600)
            self.orders_table.setMaximumHeight(600)
            font = self.orders_table.font()
            font.setPointSize(9)
            self.orders_table.setFont(font)
            
            orders_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            orders_group_layout.addWidget(self.orders_table)
            
            orders_layout.addWidget(orders_group)
            orders_layout.setStretchFactor(orders_group, 1)
            
            print("DEBUG: OrderManager._create_view_orders_tab - END")
            return orders_tab
        except Exception as e:
            print(f"ERROR: Failed to create 'View Orders' tab: {e}")
            traceback.print_exc()
            return None
    
    def create_order(self):
        try:
            order_number = self.order_number_entry.text().strip()
            if not order_number:
                QMessageBox.warning(self, "Error", "Please enter an order number")
                return
            
            is_manager_or_admin = self.data_manager.is_manager(self.username) or self.username == "admin"
            quantity, customer_name, board_name, comments = None, None, None, None
            
            if is_manager_or_admin:
                quantity = self.quantity_entry.text().strip() or None
                customer_name = self.customer_entry.text().strip() or None
                board_name = self.board_name_entry.text().strip() or None
                comments = self.comments_entry.toPlainText().strip() or None

                success = self.data_manager.create_order(
                    order_number, 
                quantity=quantity,
                customer_name=customer_name,
                board_name=board_name,
                comments=comments,
                    created_by=self.username
                )
            
            if success:
                QMessageBox.information(self, "Success", f"Order {order_number} created successfully")
                self.order_number_entry.clear()
                if is_manager_or_admin:
                    self.quantity_entry.clear()
                    self.customer_entry.clear()
                    self.board_name_entry.clear()
                    self.comments_entry.clear()
                
                # Update selectors and tables
                self.update_all_order_selectors()
                self.update_orders_table(force_refresh=True)
            else:
                QMessageBox.warning(self, "Error", "Order number already exists")
        except Exception as e:
            print(f"Error creating order: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def _set_status_label_style(self, text, color, background_color, border_color):
        """Helper to set the style and text of the barcode status label."""
        if self.barcode_status_label:
            self.barcode_status_label.setText(text)
            self.barcode_status_label.setStyleSheet(
                f"font-weight: bold; color: {color}; background-color: {background_color}; "
                f"padding: 5px; border: 1px solid {border_color}; border-radius: 3px;"
            )

    def _set_status_label_success(self, text):
        self._set_status_label_style(text, "#4CAF50", "#e6ffe6", "#4CAF50")

    def _set_status_label_error(self, text):
        self._set_status_label_style(text, "#f44336", "#ffe6e6", "#f44336")

    def _set_status_label_warning(self, text):
        self._set_status_label_style(text, "#FFA000", "#fff3e0", "#FFA000")

    def _set_status_label_info(self, text):
         self._set_status_label_style(text, "#007bff", "#e7f3ff", "#b8daff")

    def add_barcode(self):
        """Add a barcode to the current order using the two-step process"""
        try:
            # Use current_barcode_order which is updated by force_barcode_selection_update
            order_number = self.current_barcode_order
            if not order_number:
                self._set_status_label_error("❌ Error: Please select an order first")
                return
            
            scanned_barcode = self.barcode_entry.text().strip()
            if not scanned_barcode:
                return # Ignore empty scans
                
            print(f"Processing barcode: {scanned_barcode} for order: {order_number}")
            
            # Handle status barcodes (PASS/FAIL)
            if scanned_barcode in [self.PASS_CODE, self.FAIL_CODE]:
                if self.pending_barcode is None:
                    self._set_status_label_error("❌ Error: Please scan a board barcode first")
                    self.barcode_entry.clear()
                    return

                # Finalize the scan
                status = "PASS" if scanned_barcode == self.PASS_CODE else "FAIL"
                print(f"Finalizing scan for '{self.pending_barcode}' with status: {status}")
                self.finalize_barcode_scan(self.pending_barcode, status)
                
                # Reset pending state
                self.pending_barcode = None
                # self._set_status_label_success("✅ Ready to scan next board") # Status set by finalize_barcode_scan
                self.barcode_entry.clear()

            # Handle regular board barcode scans
            else:
                if self.pending_barcode is not None:
                    self._set_status_label_error(f"❌ Error: Please scan PASS or FAIL for '{self.pending_barcode}' first")
                    self.barcode_entry.clear() # Clear the new scan, keep the pending one
                    return
                
                # Store as pending
                print(f"Storing '{scanned_barcode}' as pending. Waiting for PASS/FAIL scan.")
                self.pending_barcode = scanned_barcode
                self._set_status_label_warning(f"⏳ Pending: {self.pending_barcode} - Scan PASS or FAIL")
                self.barcode_entry.clear()
                self.barcode_entry.setFocus() # Keep focus for next scan

        except Exception as e:
            print(f"Error in add_barcode (two-step): {str(e)}")
            traceback.print_exc()
            self._set_status_label_error(f"❌ Error: {str(e)}")
            # Reset state on error
            self.pending_barcode = None
            self.barcode_entry.clear()

    def finalize_barcode_scan(self, barcode_to_add, status):
        """Adds the barcode to the order and adds the Pass/Fail comment."""
        try:
            order_number = self.current_barcode_order # Use the confirmed order
            if not order_number:
                print("Error: Order number lost during finalization")
                self._set_status_label_error("❌ Internal Error: Order selection lost")
                return

            print(f"Attempting to add barcode '{barcode_to_add}' to order '{order_number}'")
            # Step 1: Add the barcode (which also creates the board entry)
            add_result, add_message = self.data_manager.add_barcode(order_number, barcode_to_add, self.username)

            if not add_result:
                self._set_status_label_error(f"❌ Error: {add_message}")
                    self.log_to_terminal(f"Failed to add '{barcode_to_add}' to '{order_number}': {add_message}")
                return

            # Step 2: Add the Pass/Fail comment
            comment_text = f"STATUS: {status} - Board/barcode tested and {'passed' if status == 'PASS' else 'failed'}"
            print(f"Adding comment for '{barcode_to_add}': '{comment_text}'")
            comment_success = self.data_manager.add_board_comment(order_number, barcode_to_add, comment_text, self.username)

            if comment_success:
                self._set_status_label_success(f"✅ Added '{barcode_to_add}' with status: {status}")
                    self.log_to_terminal(f"Added '{barcode_to_add}' to '{order_number}' with status: {status}")
                # Synchronize all views
                self.sync_order_views(order_number)
            else:
                # Barcode was added, but comment failed
                self._set_status_label_warning(f"⚠️ Added '{barcode_to_add}' but failed to add {status} comment")
                    self.log_to_terminal(f"Added '{barcode_to_add}' to '{order_number}', but FAILED to add {status} comment.")
                # Still sync views as the barcode/board was added
                self.sync_order_views(order_number)

        except Exception as e:
            print(f"Error finalizing barcode scan: {str(e)}")
            traceback.print_exc()
            self._set_status_label_error(f"❌ Error: {str(e)}")

    def _create_comments_dialog_layout(self, dialog, order_number, order_data):
        """Creates the layout and content for the comments dialog."""
            layout = QVBoxLayout(dialog)
            
        # Order Info Section
            info_group = QGroupBox("Order Information")
            info_layout = QVBoxLayout(info_group)
            customer = order_data.get("customer_name", "N/A")
            quantity = order_data.get("quantity", "N/A")
            created_by = order_data.get("created_by", "N/A")
            created_at = order_data.get("created_at", "N/A")
        board_count = len(order_data.get("boards", {})) or len(order_data.get("barcodes", []))
                
            info_layout.addWidget(QLabel(f"Customer: {customer}"))
            info_layout.addWidget(QLabel(f"Quantity: {quantity}"))
            info_layout.addWidget(QLabel(f"Total Boards: {board_count}"))
            info_layout.addWidget(QLabel(f"Created by: {created_by}"))
            info_layout.addWidget(QLabel(f"Created at: {created_at}"))
            layout.addWidget(info_group)
            
        # Order Comments Section
            comments_group = QGroupBox("Order Comments")
            comments_layout = QVBoxLayout(comments_group)
            order_comments = order_data.get("comments", [])
            if order_comments:
                scroll_area = QScrollArea()
                scroll_area.setWidgetResizable(True)
                scroll_widget = QWidget()
                scroll_layout = QVBoxLayout(scroll_widget)
                for comment in order_comments:
                comment_label = QLabel(f"{comment.get('text', '')}")
                    comment_label.setWordWrap(True)
                    comment_label.setStyleSheet("font-size: 10pt;")
                    scroll_layout.addWidget(comment_label)
                meta_label = QLabel(f"By: {comment.get('user', 'Unknown')} at {comment.get('timestamp', 'Unknown')}")
                    meta_label.setStyleSheet("color: #666; font-size: 9pt;")
                    scroll_layout.addWidget(meta_label)
                scroll_layout.addWidget(QLabel("-------------------")) # Separator
                scroll_widget.setLayout(scroll_layout)
                scroll_area.setWidget(scroll_widget)
                comments_layout.addWidget(scroll_area)
            else:
                comments_layout.addWidget(QLabel("No comments for this order"))
            layout.addWidget(comments_group)
            
        # Board Comments Section
        layout.addWidget(self._create_board_comments_group(order_data))

        # Buttons
        button_layout = QHBoxLayout()
        refresh_button = QPushButton("Refresh Comments")
        # Use lambda to capture the current order_number for refresh
        refresh_button.clicked.connect(lambda: self.refresh_comments_dialog(order_number))
        close_button = QPushButton("Close")
        close_button.clicked.connect(lambda: self.close_comments_dialog(dialog))
        button_layout.addWidget(refresh_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        return layout

    def _create_board_comments_group(self, order_data):
        """Creates the group box displaying comments for each board."""
            board_comments_group = QGroupBox("Board Comments")
            board_comments_layout = QVBoxLayout(board_comments_group)
            
        all_boards = self._get_sorted_boards_with_comments(order_data)

        if all_boards:
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)

            for board_id, board_data, comments, _, _, has_comments in all_boards:
                board_group = self._create_single_board_comment_group(board_id, board_data, comments, has_comments)
                scroll_layout.addWidget(board_group)
                scroll_layout.addSpacing(10)

            scroll_widget.setLayout(scroll_layout)
            scroll_area.setWidget(scroll_widget)
            board_comments_layout.addWidget(scroll_area)
        else:
            board_comments_layout.addWidget(QLabel("No boards in this order"))

        return board_comments_group

    def _get_sorted_boards_with_comments(self, order_data):
        """Gets and sorts all boards, merging board data and comments."""
        all_boards = []
            board_comments_dict = order_data.get("board_comments", {})
        boards_dict = order_data.get("boards", {})
        barcodes_list = order_data.get("barcodes", [])

        processed_ids = set()

        # Process boards with explicit data
        for board_id, board_data in boards_dict.items():
            if board_id in processed_ids: continue
            comments = board_comments_dict.get(board_id, [])
            numeric_part, timestamp = self._extract_board_sort_keys(board_id, board_data)
            all_boards.append((board_id, board_data, comments, numeric_part, timestamp, bool(comments)))
            processed_ids.add(board_id)

        # Process boards only present in comments
        for board_id, comments in board_comments_dict.items():
             if board_id in processed_ids: continue
             board_data = {"description": "Comments only", "added_at": "N/A", "added_by": "N/A"} # Minimal data
             numeric_part, timestamp = self._extract_board_sort_keys(board_id, board_data)
                all_boards.append((board_id, board_data, comments, numeric_part, timestamp, True))
             processed_ids.add(board_id)

        # Process boards only present as barcodes
        for board_id in barcodes_list:
            if board_id in processed_ids: continue
            board_data = {"description": "Barcode only", "added_at": "N/A", "added_by": "N/A"} # Minimal data
            comments = []
            numeric_part, timestamp = self._extract_board_sort_keys(board_id, board_data)
            all_boards.append((board_id, board_data, comments, numeric_part, timestamp, False))
            processed_ids.add(board_id)

        # Sort by numeric part first, then by timestamp
        all_boards.sort(key=lambda x: (x[2], x[3]))
        return all_boards

    def _extract_board_sort_keys(self, board_id, board_data):
        """Extracts numeric part and timestamp for sorting boards."""
                    numeric_part = 0
                    try:
                        numeric_match = re.search(r'^\d+', board_id)
                        if numeric_match:
                            numeric_part = int(numeric_match.group())
        except: pass # Ignore errors
        timestamp = board_data.get("added_at", "") if isinstance(board_data, dict) else ""
        return numeric_part, timestamp

    def _create_single_board_comment_group(self, board_id, board_data, comments, has_comments):
         """Creates the group box for a single board's comments and info."""
                    board_group = QGroupBox(f"Board ID: {board_id}")
                    board_layout = QVBoxLayout(board_group)
                    
                    desc = board_data.get("description", "N/A")
                    department = board_data.get("department", "N/A")
                    added_by = board_data.get("added_by", "Unknown")
                    added_at = board_data.get("added_at", "Unknown")
                    
         # Determine latest status and style
                    latest_status = "Unknown"
                    status_style = ""
                    if comments:
                        for comment in reversed(comments):
                 text = comment.get("text", "")
                 if "STATUS:" in text:
                     if "PASS" in text:
                                    latest_status = "PASS"
                                    status_style = "background-color: #e6ffe6; border: 1px solid #4CAF50;"
                     elif "FAIL" in text:
                                    latest_status = "FAIL"
                                    status_style = "background-color: #ffe6e6; border: 1px solid #ff4444;"
                     break # Found latest status
                    
                    if status_style:
                        board_group.setStyleSheet(f"QGroupBox {{ {status_style} }}")
                    
         # Info Label
                    info_text = f"""
                    <p style='margin: 5px 0;'><b>Status:</b> {latest_status}</p>
                    <p style='margin: 5px 0;'><b>Description:</b> {desc}</p>
                    <p style='margin: 5px 0;'><b>Department:</b> {department}</p>
                    <p style='margin: 5px 0;'><b>Added by:</b> {added_by} at {added_at}</p>
                    """
                    info_label = QLabel(info_text)
                    info_label.setTextFormat(Qt.TextFormat.RichText)
                    board_layout.addWidget(info_label)
                    
         # Comments Label
                    if has_comments and comments:
             comments_html = "<p><b>Comments:</b></p>"
                        for comment in comments:
                            comment_text = comment.get("text", "")
                            comment_by = comment.get("user", "Unknown")
                            comment_time = comment.get("timestamp", "Unknown")
                 style = ""
                            if "STATUS:" in comment_text:
                     style = "color: green; font-weight: bold;" if "PASS" in comment_text else "color: red; font-weight: bold;"
                            else:
                                style = "color: #333;"
                            
                 comments_html += f"""
                 <p style='{style} margin: 5px 0;'>{comment_text}</p>
                            <p style='color: #666; font-size: 8pt; margin: 2px 0;'>By: {comment_by} at {comment_time}</p>
                            """
             comment_label = QLabel(comments_html)
                        comment_label.setTextFormat(Qt.TextFormat.RichText)
                        comment_label.setWordWrap(True)
                        board_layout.addWidget(comment_label)
                    
         return board_group

    def show_comments_dialog(self, order_number):
        """Show a dialog with all comments for the selected order"""
        try:
            print(f"\n---------- DEBUG: Opening comments dialog for order '{order_number}' ----------")
            orders = self.data_manager.load_orders(force_reload=True) # Force reload

            if order_number not in orders:
                QMessageBox.warning(self, "Error", f"Order {order_number} not found")
                return

            order_data = orders[order_number]

            # If a dialog is already open, close it first
            if self.active_comments_dialog:
                self.active_comments_dialog.close()
                self.active_comments_dialog = None

            # Create a new dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Comments for Order {order_number}")
            dialog.setMinimumWidth(800)
            dialog.setMinimumHeight(600)

            # Create layout and content
            layout = self._create_comments_dialog_layout(dialog, order_number, order_data)
            dialog.setLayout(layout)

            # Store reference and show
            self.active_comments_dialog = dialog
            dialog.show() # Use show() instead of exec() for non-blocking
            
        except Exception as e:
            print(f"Error showing comments dialog: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error showing comments: {str(e)}")
            self.active_comments_dialog = None # Clear reference on error

    def refresh_comments_dialog(self, order_number):
        """Refreshes the content of the currently open comments dialog"""
        if self.active_comments_dialog:
            print(f"Refreshing comments dialog for order: {order_number}")
            # Close the old one and open a new one with fresh data
            self.active_comments_dialog.close()
            self.active_comments_dialog = None
            self.show_comments_dialog(order_number)
        else:
            print("No active comments dialog to refresh.")
            
    def close_comments_dialog(self, dialog):
        """Properly close the comments dialog and clean up references"""
        if dialog == self.active_comments_dialog:
        self.active_comments_dialog = None
        dialog.close()
    
    def _calculate_time_since(self, timestamp_str):
        """Calculates human-readable time difference from a timestamp string."""
        if not timestamp_str:
            return ""
        try:
            created_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            delta = now - created_time

            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)

            if days > 0: return f"{days}d {hours}h {minutes}m"
            if hours > 0: return f"{hours}h {minutes}m"
            return f"{minutes}m"
                except Exception as e:
            # print(f"Error calculating time for '{timestamp_str}': {e}") # Reduce noise
            return timestamp_str # Return original string if parsing fails

    def _populate_order_table_row(self, row, order_number, order_data):
        """Fills a single row in the orders table."""
                self.orders_table.setItem(row, 0, QTableWidgetItem(order_number))
                
                customer = order_data.get("customer_name", "")
        self.orders_table.setItem(row, 1, QTableWidgetItem(str(customer)))
                
                quantity = order_data.get("quantity", "")
        self.orders_table.setItem(row, 2, QTableWidgetItem(str(quantity)))

        board_count = len(order_data.get("boards", {})) or len(order_data.get("barcodes", []))
                board_item = QTableWidgetItem(str(board_count))
                # Highlight the board count for better visibility
                if board_count > 0:
                    board_item.setBackground(Qt.GlobalColor.lightGray)
                    board_item.setForeground(Qt.GlobalColor.blue)
                    board_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.orders_table.setItem(row, 3, board_item)
                
        time_since = self._calculate_time_since(order_data.get("created_at", ""))
        self.orders_table.setItem(row, 4, QTableWidgetItem(time_since))

    def update_orders_table(self, force_refresh=False):
        """Update the orders table with current order data"""
        if not self.orders_table:
            print("DEBUG: update_orders_table called but self.orders_table is None.")
            return

        try:
            orders = self.data_manager.load_orders(force_reload=force_refresh)
            print(f"DEBUG: Updating orders table - Found {len(orders)} orders. Force refresh: {force_refresh}") # DEBUG Print

            current_selection = None
            selected_rows = self.orders_table.selectedItems()
            if selected_rows:
                current_row = selected_rows[0].row()
                current_item = self.orders_table.item(current_row, 0)
                if current_item:
                    current_selection = current_item.text()

            # Disable updates, clear, and repopulate
            self.orders_table.setUpdatesEnabled(False)
            self.orders_table.clearContents()
            self.orders_table.setRowCount(len(orders))

            row_to_select = -1
            if not orders:
                 print("DEBUG: No orders found to display.")
            else:
                for row, (order_number, order_data) in enumerate(orders.items()):
                    self._populate_order_table_row(row, order_number, order_data)
                    if current_selection and order_number == current_selection:
                        row_to_select = row

            # Disconnect/reconnect signal handler to avoid issues during update
            try: self.orders_table.itemSelectionChanged.disconnect()
            except: pass
            self.orders_table.itemSelectionChanged.connect(self.on_order_selection_changed)
            
            # Adjust column widths
            self.orders_table.setColumnWidth(0, 120)
            self.orders_table.setColumnWidth(1, 150)
            self.orders_table.setColumnWidth(2, 80)
            self.orders_table.setColumnWidth(3, 80)
            self.orders_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
            
            # Re-enable updates and repaint
            self.orders_table.setUpdatesEnabled(True)
            self.orders_table.repaint()
            
            # Restore selection
            if row_to_select >= 0:
                self.orders_table.selectRow(row_to_select)
            
        except Exception as e:
            print(f"Error updating orders table: {str(e)}")
            traceback.print_exc()
            if self.orders_table: self.orders_table.setUpdatesEnabled(True) # Ensure updates re-enabled

    def _populate_order_selector(self, selector, current_selection_var_name):
        """Helper to populate an order QComboBox."""
        if not selector:
            print(f"Warning: Attempted to populate a non-existent selector ({current_selection_var_name}).")
                return
                
        print(f"DEBUG: Populating selector '{selector.objectName()}'...") # DEBUG Print
        current_selection = getattr(self, current_selection_var_name, "")

        selector.blockSignals(True)
        selector.clear()
        orders = self.data_manager.load_orders(force_reload=True) # Force reload to ensure it has latest
        print(f"DEBUG: Found {len(orders)} orders for selector.") # DEBUG Print

            index_to_select = -1
        for i, order_number in enumerate(orders):
            selector.addItem(order_number)
            if current_selection and order_number == current_selection:
                index_to_select = i

        if index_to_select == -1 and selector.count() > 0:
                index_to_select = 0
            
        new_selection = ""
            if index_to_select >= 0:
            selector.setCurrentIndex(index_to_select)
            new_selection = selector.itemText(index_to_select)

        # Update the tracking variable AFTER setting index and getting text
        setattr(self, current_selection_var_name, new_selection)
        print(f"DEBUG: Selector '{selector.objectName()}' populated. Selected: '{new_selection}' (Index: {index_to_select})") # DEBUG Print

        # Update associated debug labels
        if selector == self.order_selector and self.barcode_order_debug_label:
             self.barcode_order_debug_label.setText(f"SELECTED: {new_selection}" if new_selection else "No Order Selected")
        elif selector == self.board_order_selector and self.board_order_display:
             self.board_order_display.setText(f"ORDER: {new_selection}" if new_selection else "No Order Selected")

        selector.blockSignals(False)

    def force_barcode_selection_update(self, show_popup=True):
        """Force update of the barcode order selection"""
        if not self.order_selector:
            print("DEBUG: Barcode order selector not ready for update.")
                return
        try:
            order_number = self.order_selector.currentText() # Get current text from UI
            print(f"DEBUG: Forcing barcode selection update. UI shows: '{order_number}'")

            # Update tracking variable
            self.current_barcode_order = order_number

            # Update the debug label for visibility
            if self.barcode_order_debug_label:
                self.barcode_order_debug_label.setText(f"SELECTED: {order_number}" if order_number else "No Order Selected")

            # Reset pending scan state
            self.pending_barcode = None
            self._set_status_label_info("Scan Board Barcode")
            if self.barcode_entry: self.barcode_entry.clear()

            if show_popup: # Only show popup if requested
                QMessageBox.information(self, "Selection Updated",
                                   f"Barcode Scanning tab\nOrder selection updated to:\n\n'{order_number}'\n\nScan Board Barcode to begin." if order_number else "No order selected.")
        except Exception as e:
            print(f"Error forcing barcode selection update: {str(e)}")
            traceback.print_exc()
    
    def update_board_selection(self, show_popup=True):
        """Update the selected order for board management with visual confirmation"""
        if not self.board_order_selector:
             print("DEBUG: Board order selector not ready for update.")
            return
        try:
            order_number = self.board_order_selector.currentText() # Get current text from UI
            print(f"DEBUG: Updating board selection. UI shows: '{order_number}'")
            
            # Update tracking variable
            self.current_board_order = order_number
            
            # Update visual indicators
            if self.board_order_display:
                self.board_order_display.setText(f"ORDER: {order_number}" if order_number else "No Order Selected")
            if self.board_debug_label:
            self.board_debug_label.setText(f"DEBUG: Order '{order_number}' selected at {datetime.now().strftime('%H:%M:%S')}")
            
            # Refresh the boards table for the new selection
            self.refresh_boards_display_now()
            
            if show_popup: # Only show popup if requested
            QMessageBox.information(self, "Order Selected", 
                                  f"Active order set to: {order_number}\n\nThe boards table now shows boards in this order." if order_number else "No order selected.")
        except Exception as e:
            print(f"Error updating board selection: {str(e)}")
            traceback.print_exc()
            if show_popup: QMessageBox.critical(self, "Error", f"Could not update selection: {str(e)}")
    
    def manual_refresh_boards_table(self):
        """Manually triggered refresh of the boards table with visual feedback"""
        try:
            self.refresh_boards_display_now() # Call the main refresh logic
            if self.board_debug_label: self.board_debug_label.setText(f"DEBUG: Table refreshed at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Error manually refreshing boards table: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Could not refresh boards table: {str(e)}")
    
    def _sort_boards(self, boards_dict):
        """Sorts a dictionary of boards by numeric ID then timestamp."""
        sorted_boards = []
        for board_id, board_data in boards_dict.items():
            numeric_part, timestamp = self._extract_board_sort_keys(board_id, board_data)
            sorted_boards.append((board_id, board_data, numeric_part, timestamp))
        sorted_boards.sort(key=lambda x: (x[2], x[3]))
        return sorted_boards

    def _populate_board_table_row(self, row, board_id, board_data):
        """Fills a single row in the boards table."""
        self.boards_table.setItem(row, 0, QTableWidgetItem(board_id))
        self.boards_table.setItem(row, 1, QTableWidgetItem(board_data.get("description", "")))
        self.boards_table.setItem(row, 2, QTableWidgetItem(board_data.get("department", "")))

    def refresh_boards_display_now(self):
        """Force immediate refresh of the boards display with hard reload of data"""
        if not self.boards_table:
             print("DEBUG: refresh_boards_display_now called but self.boards_table is None.")
             return

        try:
            order_number = self.current_board_order # Use the confirmed order
            print(f"DEBUG: Force refreshing boards table for confirmed order '{order_number}'")
            
            if not order_number:
                self.boards_table.clearContents()
                self.boards_table.setRowCount(0)
                if self.board_stats_label: self.board_stats_label.setText("No order selected")
                return
            
            # Force reload data and get boards
            boards = self.data_manager.get_boards_for_order(order_number, force_reload=True)
            board_count = len(boards)
            print(f"DEBUG: Found {board_count} boards for order {order_number}")
            
            # Update table
            self.boards_table.blockSignals(True)
            self.boards_table.clearContents()
            self.boards_table.setRowCount(0) # Clear rows
            
            if boards:
                sorted_boards = self._sort_boards(boards)
                self.boards_table.setRowCount(board_count) # Set correct count
                for row, (board_id, board_data, _, _) in enumerate(sorted_boards):
                    self._populate_board_table_row(row, board_id, board_data)
                if self.board_stats_label: self.board_stats_label.setText(f"{board_count} boards in order {order_number}")
            else:
                # Ensure row count is 0 if no boards
                self.boards_table.setRowCount(0)
                if self.board_stats_label: self.board_stats_label.setText(f"No boards found in order {order_number}")
            
            self.boards_table.blockSignals(False)
            self.boards_table.resizeRowsToContents() # Resize rows
            # Maybe resize columns too, or ensure initial widths are good
            # self.boards_table.resizeColumnsToContents()
            self.boards_table.repaint()
            
            # Scroll to bottom
            if board_count > 0:
                self.boards_table.scrollToBottom()
                
        except Exception as e:
            print(f"Error refreshing boards display: {str(e)}")
            traceback.print_exc()
        finally:
             # Ensure signals are unblocked even if error occurs
             if self.boards_table: self.boards_table.blockSignals(False)
    
    def view_selected_order_comments(self):
        """View comments for the currently selected order in the orders table"""
        if not self.orders_table:
            QMessageBox.warning(self, "Error", "Orders table is not available.")
            return
        try:
            selected_row = self.orders_table.currentRow()
            if selected_row < 0:
                QMessageBox.warning(self, "Warning", "Please select an order from the 'View Orders' table first")
                return
            
            order_item = self.orders_table.item(selected_row, 0)
            if order_item:
                order_number = order_item.text()
                self.show_comments_dialog(order_number) # Call the dialog display method
            else:
                 QMessageBox.warning(self, "Warning", "Could not identify the selected order.")
        except Exception as e:
            print(f"Error in view_selected_order_comments: {e}") # Log specific error location
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error viewing comments: {e}")
    
    def sync_order_views(self, order_number):
        """Synchronize all order views when an order is modified"""
        try:
            print(f"DEBUG: Syncing order views for '{order_number}'")
            
            # Force reload orders data
            orders = self.data_manager.load_orders(force_reload=True)
            
            # Update Board Management Tab if it's showing the affected order
            if self.current_board_order == order_number:
                self.refresh_boards_display_now()
                # print(f"Updated Board Management tab for order '{order_number}'") # Reduce noise

            # No specific update needed for Barcode Tab (selection is manual)

            # Always update the View Orders Tab
            self.update_orders_table(force_refresh=True) # Force refresh ensures it gets latest data
            # print(f"Updated View Orders tab") # Reduce noise

            # Select the updated order in the View Orders Tab for visibility
            self.select_order_in_view(order_number)
            
            # Update comments dialog if it's open and showing this order
            if self.active_comments_dialog:
                 dialog_title = self.active_comments_dialog.windowTitle()
                 if f"Order {order_number}" in dialog_title:
                     print(f"Refreshing open comments dialog for {order_number}")
                     self.refresh_comments_dialog(order_number)

            # Optional: Show a less intrusive notification? Maybe skip the popup.
            # board_count = len(orders.get(order_number, {}).get("boards", {})) or len(orders.get(order_number, {}).get("barcodes", []))
            # QMessageBox.information(self, "Order Updated", f"Order {order_number} updated (Boards: {board_count}). Views synchronized.")
            
            print(f"Order views synchronized for '{order_number}'")
        except Exception as e:
            print(f"Error syncing order views: {str(e)}")
            traceback.print_exc()
    
    def select_order_in_view(self, order_number):
        """Select the specified order in the View Orders tab table"""
        if not self.orders_table: return
        try:
            for row in range(self.orders_table.rowCount()):
                item = self.orders_table.item(row, 0)
                if item and item.text() == order_number:
                    # print(f"Selecting order {order_number} in View Orders tab (row {row})") # Reduce noise
                    self.orders_table.selectRow(row)
                    self.orders_table.scrollToItem(item, QAbstractItemView.ScrollHint.EnsureVisible)
                    break
        except Exception as e:
            print(f"Error selecting order in view: {str(e)}")
            traceback.print_exc()
    
    def show_board_context_menu(self, position):
        """Show context menu for board management (managers only)"""
        if not self.data_manager.is_manager(self.username):
            return
            
        try:
            selected_items = self.boards_table.selectedItems()
            if not selected_items: return

            menu = QMenu()
            delete_action = menu.addAction("Delete Board")
            action = menu.exec(self.boards_table.mapToGlobal(position))
            
            if action == delete_action:
                self.delete_selected_board()
                
        except Exception as e:
            print(f"Error showing context menu: {str(e)}")
            traceback.print_exc()
    
    def delete_selected_board(self):
        """Delete the selected board from the boards table (managers only)"""
        if not self.data_manager.is_manager(self.username):
            QMessageBox.warning(self, "Permission Denied", "Only managers can delete boards.")
            return
            
        try:
            selected_row = self.boards_table.currentRow()
            if selected_row < 0:
                QMessageBox.warning(self, "No Selection", "Please select a board to delete.")
                return
                
            board_id_item = self.boards_table.item(selected_row, 0)
            if not board_id_item: return # Should not happen
            board_id = board_id_item.text()
            order_number = self.current_board_order # Use confirmed order

            if not order_number:
                 QMessageBox.warning(self, "Error", "Cannot determine the current order.")
                 return

            reply = QMessageBox.question(
                self, "Confirm Deletion",
                f"Are you sure you want to delete board '{board_id}' from order '{order_number}'?\n\nThis action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                success, message = self.data_manager.delete_board(order_number, board_id, self.username)
                if success:
                    QMessageBox.information(self, "Board Deleted", message)
                    self.sync_order_views(order_number) # Refresh display
                else:
                    QMessageBox.warning(self, "Error", message)
                    
        except Exception as e:
            print(f"Error deleting board: {str(e)}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def clear_session_terminal(self):
        """Clear the session terminal log"""
        if self.session_terminal:
            self.session_terminal.clear()
            self.log_to_terminal("Terminal cleared")
    
    def log_to_terminal(self, message):
        """Add a timestamped log message to the session terminal"""
        if self.session_terminal:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.session_terminal.append(f"[{timestamp}] {message}")
            # Auto-scroll to the bottom
            cursor = self.session_terminal.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.session_terminal.setTextCursor(cursor) 

    # Added method to handle item selection changes in the orders table
    def on_order_selection_changed(self):
        """Handle selection changes in the main orders table."""
        # Currently, this might not need to do anything automatically,
        # actions like viewing comments are triggered by buttons.
        # We keep the connection in case future functionality needs it.
        selected_row = self.orders_table.currentRow()
        if selected_row >= 0:
            order_item = self.orders_table.item(selected_row, 0)
            if order_item:
                # print(f"DEBUG: Order '{order_item.text()}' selected in View Orders tab.") # Reduce noise
                pass
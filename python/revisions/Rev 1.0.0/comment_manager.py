from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from data_manager import DataManager
import traceback

class CommentManager(QWidget):
    """
    Simplified CommentManager that doesn't display any UI elements 
    but still provides necessary methods for backend functionality.
    """
    def __init__(self, data_manager, username):
        try:
            super().__init__()
            print(f"\n---------- DEBUG: Initializing simplified CommentManager for user '{username}' ----------")
            self.data_manager = data_manager
            self.username = username
            self.current_order = None
            
            # Create an empty layout with no visible elements
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            self.setLayout(layout)
            
            # Initialize attributes for compatibility
            self.order_entry = None
            self.board_entry = None
            self.search_button = None
            self.board_combo = None
            self.comment_entry = None
            self.add_comment_button = None
            self.comments_display = None
            
            print("Simplified CommentManager initialized successfully")
        except Exception as e:
            print(f"Error initializing CommentManager: {str(e)}")
            print("Traceback:")
            traceback.print_exc()
            # Create minimal UI in case of error
            layout = QVBoxLayout(self)
            error_label = QLabel(f"Error initializing: {str(e)}")
            layout.addWidget(error_label)
    
    # Stub methods for compatibility - they don't do anything visible
    def update_comments_display(self, order_number):
        self.current_order = order_number
    
    def update_board_combo(self):
        pass
    
    def get_current_board_id(self):
        return None
    
    def on_board_selection_changed(self, index):
        pass
    
    def update_board_comments(self, order_number, board_id):
        pass
    
    def search_board(self):
        pass 
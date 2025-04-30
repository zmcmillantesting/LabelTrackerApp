import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from main import MainWindow

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler to show error messages in GUI"""
    # Print the error and traceback
    print("\n***** CRITICAL ERROR *****")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    # Try to show error in GUI
    error_msg = f"{exc_type.__name__}: {exc_value}"
    try:
        app = QApplication.instance()
        if app:
            QMessageBox.critical(None, "Error", 
                              f"Critical error occurred:\n\n{error_msg}\n\n"
                              f"See console for details.")
    except Exception:
        pass  # Can't show GUI error, already printed to console
    
    # Don't exit immediately in case they want to see console
    print("\nPress Enter to exit...")
    input()
    sys.exit(1)

def main():
    # Set up global exception handler
    sys.excepthook = handle_exception
    
    print("Starting Order Management System...")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    print("\nApplication running. Close console to exit.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 
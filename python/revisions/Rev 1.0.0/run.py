import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from main import MainWindow

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler to show error messages in GUI and console."""
    # Print the error and traceback to console
    print("\n***** APPLICATION ERROR *****")
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    print("***************************\n")

    # Format a message for the GUI dialog
    error_msg = f"{exc_type.__name__}: {exc_value}"
    detailed_traceback = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    # Try to show error in GUI if possible
    try:
        # Check if QApplication instance exists, avoid creating a new one if not needed
        app_instance = QApplication.instance()
        if app_instance:
            # Use a QMessageBox to display the error
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Application Error")
            msg_box.setText(f"A critical error occurred:\n\n{error_msg}")
            # Add detailed traceback in the details section for technical users
            msg_box.setDetailedText(detailed_traceback)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()
        else:
             # If no app instance, GUI part failed or happened before app init
             print("GUI not available to display error message.")

    except Exception as gui_error:
        print(f"Could not display error in GUI: {gui_error}")
        # Fallback to console is already done

    # Important: Don't exit immediately here, let the application try to close gracefully
    # or allow user to see the console. The sys.exit in __main__ will handle exit code.
    # Returning True might suppress Python's default exit, depending on context.
    # Let Python handle the exit after the hook runs.

if __name__ == "__main__":
    # Set the custom exception handler
    sys.excepthook = handle_exception

    print("\n====== Order Management System ======")
    print("Starting application...")

    app = QApplication(sys.argv)
    try:
        window = MainWindow()
        window.show()

        print("\nAvailable user accounts (see users.json/reset_users.py for details):")
        print("  Admin: admin / password")
        # Add more examples if helpful
        print("\nApplication running. Close the window or console to exit.")

        # Start the Qt event loop
        exit_code = app.exec()
        sys.exit(exit_code)

    except Exception as startup_error:
         # Handle critical startup errors that occur after excepthook is set
         # but before the event loop starts or during MainWindow init
         print("\n***** CRITICAL STARTUP ERROR *****")
         traceback.print_exc()
         print("********************************\n")
         try:
              QMessageBox.critical(None, "Startup Error",
                                   f"Failed to start the application:\n\n{startup_error}\n\n"
                                   "See console for details.")
         except Exception as msgbox_error:
              print(f"Could not display startup error in GUI: {msgbox_error}")
         sys.exit(1) # Exit with error code if startup fails critically 
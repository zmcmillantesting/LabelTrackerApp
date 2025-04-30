# Label Tracker Application (Local Storage Version)

A desktop application for tracking scanned labels with local SQLite storage.

## Overview

This version of the Label Tracker application uses local SQLite databases instead of connecting to a remote API server. 
All data is stored in the `P:\Development_Testing` directory with the following structure:

- `data\`: Main data folder
  - `[department_name]\`: A folder for each department containing its database
- `cont\`: For relatively static data (users, departments)
  - `users.db`: Database storing users, roles, and departments
- `prev\`: Previous revisions and PyInstaller folders
- `dev\`: Development data like errors-feedback files

## Features

*   **User Authentication:** Secure login with username/password stored in SQLite.
*   **Role-Based Access Control:** Standard, Manager, and Admin roles with different permissions.
*   **Order Management:** Admins/Managers can create and delete orders.
*   **Scan Tracking:** Two-step process (scan board, then scan Pass/Fail status barcode).
*   **Department-Specific Data:** Each department has its own database for orders and scans.
*   **Data Viewing:** View scanned data, filterable by order.
*   **Data Editing (Manager/Admin):** Edit status (Pass/Fail) and notes for existing scans. Delete scans.
*   **User Management (Admin):** Add, edit (role/department), and delete users.
*   **Department Management (Admin):** Add departments.
*   **User Feedback:** A dedicated tab allows users to submit feedback or report issues.
*   **Standalone Executable:** Can be built into a single `.exe` file for easy distribution (using PyInstaller).

## Setup

1.  **Prerequisites:**
    *   Python 3.x
    *   `pip` (Python package installer)

2.  **Install Python Dependencies:**
    ```bash
    pip install PyQt6 bcrypt pyinstaller
    ```

3.  **Initialize the Application:**
    The application will automatically create necessary directories and database files on first run.

## Running the Application

Simply run the `run_local.py` script:

```bash
python run_local.py
```

The default admin credentials are:
- Username: `admin`
- Password: `1234`

## Building the Standalone Executable

1. Make sure PyInstaller is installed: `pip install pyinstaller`
2. Run PyInstaller with the spec file:
   ```bash
   pyinstaller application/LabelTrackerLocal.spec
   ```
3. The executable will be created in the `dist/LabelTrackerLocal` directory.

## Migrating from API Version

If you want to migrate from the API version of the application:

1. Run `copy_gui_files.py` to copy the necessary GUI files from the original project:
   ```bash
   python copy_gui_files.py <path_to_original_project> <path_to_this_project>
   ```

2. The script will copy:
   - `main_window.py` and `widgets.py` from the original project
   - All image files from the original project's `gui/images` folder

## File Structure

* `data_manager.py`: Core class for managing SQLite database operations
* `main_window_adapter.py`: Adapter to make the original MainWindow work with the data manager
* `run_local.py`: Application entry point
* `gui/login_window.py`: Custom login window for the local version
* `gui/main_window.py`: Original main window (used without modification)
* `gui/widgets.py`: Original widgets (used without modification) 
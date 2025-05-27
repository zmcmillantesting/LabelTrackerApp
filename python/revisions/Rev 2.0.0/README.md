# Label Tracker Application

A desktop application for tracking scanned labels with user roles and data storage. 

## Features

*   **User Authentication:** Secure login with username/password.
*   **Role-Based Access Control:** Standard, Manager, and Admin roles with different permissions.
*   **Order Management:** Admins/Managers can create and delete orders. 
*   **Scan Tracking:** Two-step process (scan board, then scan Pass/Fail status barcode).
    *   Scans are associated with a selected order.
    *   Prevents duplicate board barcode scans *within the same order*.
    *   Prevents accidental scanning of status barcodes when a board barcode is expected.
*   **Data Viewing:** View scanned data, filterable by order.
*   **Data Editing (Manager/Admin):** Edit status (Pass/Fail) and notes for existing scans. Delete scans.
*   **User Management (Admin):** Add, edit (role/department), and delete users.
*   **Department Management (Admin):** Add departments.
*   **Error Logging (Developer Use):** Automatically logs application errors (level ERROR and above) to `errors-feedback/error_log.txt`.
*   **User Feedback:** A dedicated tab allows users to submit feedback or report issues, which are appended to `errors-feedback/user_feedback.txt`.
*   **Standalone Executable:** Can be built into a single `.exe` file for easy distribution (using PyInstaller).

## Setup

1.  **Prerequisites:**
    *   Python 3.x
    *   Docker Desktop (for running the PostgreSQL database easily)
    *   `pip` (Python package installer)
2.  **Clone Repository:** Obtain the project code.
    ```bash
    # If using git
    git clone <repository_url>
    cd <project_directory>
    ```
3.  **Create Environment File:** Copy `.env.example` to `.env` in the project root.
    ```bash
    # Windows (Command Prompt)
    copy .env.example .env
    # Windows (PowerShell)
    Copy-Item .env.example .env
    # Linux/macOS
    cp .env.example .env
    ```
    *   Modify `.env` (Optional): Change `SECRET_KEY`. Set `ADMIN_USERNAME` and `ADMIN_PASSWORD` for the initial admin user (otherwise defaults to `admin`/`password`). Ensure `DATABASE_URL` matches the database settings (defaults match `docker-compose.yml`).
4.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Start Database:** Run the PostgreSQL database using Docker Compose.
    ```bash
    docker compose up -d db
    ```
    *   (Ensure Docker Desktop is running first).
6.  **Database Migrations:** Initialize the database schema.
    ```powershell
    # Windows PowerShell (adjust DB URL if changed from default)
    $env:DATABASE_URL='postgresql://label_user:changeme@localhost:5432/label_tracker'; flask --app run.py db init
    $env:DATABASE_URL='postgresql://label_user:changeme@localhost:5432/label_tracker'; flask --app run.py db migrate -m "Initial schema"
    $env:DATABASE_URL='postgresql://label_user:changeme@localhost:5432/label_tracker'; flask --app run.py db upgrade

    # Linux/macOS (adjust DB URL if changed from default)
    # export DATABASE_URL='postgresql://label_user:changeme@localhost:5432/label_tracker'
    # flask --app run.py db init
    # flask --app run.py db migrate -m "Initial schema"
    # flask --app run.py db upgrade
    ```
    *   (Note: `db init` only needed the very first time).
7.  **Seed Initial Data:** Create default roles and the admin user.
    ```powershell
    # Windows PowerShell (adjust DB URL; use --admin-pass if needed)
    $env:DATABASE_URL='postgresql://label_user:changeme@localhost:5432/label_tracker'; flask --app run.py seed

    # Linux/macOS (adjust DB URL; use --admin-pass if needed)
    # export DATABASE_URL='postgresql://label_user:changeme@localhost:5432/label_tracker'
    # flask --app run.py seed 
    ```

## Running the Application (Development)

1.  **Start Backend API Server:** (Requires Docker container `db` to be running)
    ```powershell
    # Windows PowerShell (adjust DB URL if needed)
    $env:DATABASE_URL='postgresql://label_user:changeme@localhost:5432/label_tracker'; python run.py

    # Linux/macOS (adjust DB URL if needed)
    # export DATABASE_URL='postgresql://label_user:changeme@localhost:5432/label_tracker'
    # python run.py 
    ```
    *   The API server will run on `http://localhost:5000`. Keep this terminal open.
2.  **Run Frontend GUI:** Open a *second* terminal in the project root.
    ```bash
    python run_gui.py
    ```
    *   The login window should appear. Log in using the admin credentials (default `admin`/`password` or those set in `.env`/`--admin-pass`).

## Building the Standalone GUI Executable (for Distribution)

1.  **Install PyInstaller:** Ensure it's installed in your development environment (`pip install -r requirements.txt` should have included it).
2.  **Build Command:** Run from the project root directory.
    ```bash
    pyinstaller --name="LabelTrackerApp" --windowed --onefile run_gui.py --add-data "gui/images;gui/images"
    ```
    *   `--name`: Sets the executable name.
    *   `--windowed`: Hides the console window.
    *   `--onefile`: Creates a single `.exe` file (omit for a folder build).
    *   `run_gui.py`: Your main script.
    *   `--add-data "gui/images;gui/images"`: Crucial for including the image files.
3.  **Output:** The standalone application (`LabelTrackerApp.exe` or folder) will be in the `dist` directory.
4.  **Configuration:** Before building, consider making the API `base_url` in `run_gui.py` (`ApiClient` initialization) configurable instead of hardcoding `http://localhost:5000`. It needs to point to the actual IP/hostname of the machine running the backend API on the target LAN.

## Running the Standalone GUI (End Users)

1.  **Backend Must Be Running:** Ensure the administrator has the PostgreSQL database (Docker container `db`) and the backend API server (`run.py`) running continuously on the central server machine.
2.  **Distribute:** Copy the built `LabelTrackerApp.exe` (or the `LabelTrackerApp` folder from `dist`) to the end-user's Windows machine.
3.  **Run:** The user simply double-clicks `LabelTrackerApp.exe` to start the application. No Python installation is needed on their machine.

## Logging and Feedback Files

When the GUI application (`run_gui.py` or the built executable) is run, it creates a directory named `errors-feedback` in the same location as the script/executable.

*   `errors-feedback/error_log.txt`: This file is intended for developers. It automatically logs any critical application errors or unhandled exceptions that occur. This helps diagnose crashes or unexpected problems.
*   `errors-feedback/user_feedback.txt`: This file collects feedback submitted by users through the "Feedback / Report Issue" tab in the application. It includes the user's comment, their username, and a timestamp.

## Updating the Application

Updates involve replacing the backend code/database on the server and/or distributing a new frontend executable.

**Backend Only Update:**
1.  Update code on the server.
2.  Install/update Python dependencies on the server (`pip install -r requirements.txt`).
3.  Run database migrations on the server if the schema changed (`flask db migrate`, `flask db upgrade`).
4.  Restart the backend API server process (`run.py`).

**Frontend Only Update:**
1.  Update code in the development environment.
2.  Install/update Python dependencies in the dev environment.
3.  Rebuild the executable using PyInstaller.
4.  Distribute the new `.exe` file to users, replacing the old one.

**Both Backend & Frontend Update:**
1.  Perform backend update steps on the server first.
2.  Perform frontend update steps in the development environment and distribute the new `.exe`.

**(Remember to back up the database before running migrations!)** 
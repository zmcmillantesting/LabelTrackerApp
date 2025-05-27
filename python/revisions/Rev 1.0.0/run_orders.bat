@echo off
echo ===================================================
echo        ORDER MANAGEMENT SYSTEM LAUNCHER
echo ===================================================
echo.

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in your PATH.
    echo Please install Python 3.6 or higher and try again.
    pause
    exit /b 1
)

:: Check if run.py exists
if not exist run.py (
    echo ERROR: run.py not found in the current directory.
    echo Make sure you're running this script from the project root folder.
    pause
    exit /b 1
)

:: Check for required files
if not exist data_manager.py (
    echo WARNING: data_manager.py not found. The application may not work correctly.
)

if not exist comment_manager.py (
    echo WARNING: comment_manager.py not found. The application may not work correctly.
)

if not exist order_manager.py (
    echo WARNING: order_manager.py not found. The application may not work correctly.
)

:: Check for PyQt6
python -c "import PyQt6" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo WARNING: PyQt6 is not installed. Attempting to install...
    pip install PyQt6
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to install PyQt6. Please install it manually with:
        echo pip install PyQt6
        pause
        exit /b 1
    )
)

echo Starting Order Management System...
echo.
echo Available user accounts:
echo   Admin: username='admin', password='password'
echo   Test: username='zmcmillan', password='1234'
echo   Quality: username='quality_user', password='password123'
echo   Production: username='production_user', password='password123'
echo.

python run.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo The application exited with an error (code %ERRORLEVEL%).
    echo Please check the output above for more details.
    pause
)

exit /b 0 
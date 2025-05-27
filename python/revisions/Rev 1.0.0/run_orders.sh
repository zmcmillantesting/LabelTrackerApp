#!/bin/bash

echo "==================================================="
echo "        ORDER MANAGEMENT SYSTEM LAUNCHER"
echo "==================================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python is not installed or not in your PATH."
    echo "Please install Python 3.6 or higher and try again."
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if run.py exists
if [ ! -f "run.py" ]; then
    echo "ERROR: run.py not found in the current directory."
    echo "Make sure you're running this script from the project root folder."
    read -p "Press Enter to exit..."
    exit 1
fi

# Check for required files
if [ ! -f "data_manager.py" ]; then
    echo "WARNING: data_manager.py not found. The application may not work correctly."
fi

if [ ! -f "comment_manager.py" ]; then
    echo "WARNING: comment_manager.py not found. The application may not work correctly."
fi

if [ ! -f "order_manager.py" ]; then
    echo "WARNING: order_manager.py not found. The application may not work correctly."
fi

# Check for PyQt6
if ! python3 -c "import PyQt6" &> /dev/null; then
    echo "WARNING: PyQt6 is not installed. Attempting to install..."
    pip3 install PyQt6
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install PyQt6. Please install it manually with:"
        echo "pip3 install PyQt6"
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

echo "Starting Order Management System..."
echo
echo "Available user accounts:"
echo "  Admin: username='admin', password='password'"
echo "  Test: username='zmcmillan', password='1234'"
echo "  Quality: username='quality_user', password='password123'"
echo "  Production: username='production_user', password='password123'"
echo

python3 run.py

if [ $? -ne 0 ]; then
    echo
    echo "The application exited with an error (code $?)."
    echo "Please check the output above for more details."
    read -p "Press Enter to continue..."
fi

exit 0 
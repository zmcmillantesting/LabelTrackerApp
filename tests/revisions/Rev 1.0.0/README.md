# Order Management System

A PyQt6-based application for tracking orders with barcode scanning, user access control, and department-specific permissions.

## Features

- **User Authentication**: Secure login with role-based access control
- **Department Structure**: Different departments with specific permissions
- **Manager Authority**: Users can be designated as managers with additional privileges
- **Order Tracking**: Create and track orders with barcodes
- **Board Management**: Create and track individual boards within orders
- **Board Comments**: Quality and Test departments can add board-specific comments
- **UI Improvements**: Clear interface with properly sized elements
- **Error Handling**: Comprehensive error detection and reporting

## Setup & Running

1. **Requirements**:
   - Python 3.6+
   - PyQt6

2. **Setting Up User Data**:
   ```
   python reset_users.py
   ```
   This creates sample users and orders for testing.

3. **Running the Application**:
   ```
   python run.py
   ```

## User Accounts

| Username | Password | Department | Role |
|----------|----------|------------|------|
| admin | password | Administration | Admin |
| manager1 | password123 | Production Control | Manager |
| quality_user | password123 | Quality | Standard |
| test_user | password123 | Test | Standard |
| smt_user | password123 | SMT/AOI | Standard |
| bench_user | password123 | Bench | Standard |
| through_hole_user | password123 | Through Hole | Standard |
| production_user | password123 | Production Control | Standard |
| shipping_user | password123 | Shipping | Standard |

## Department Permissions

- **Administration**: Full access to all features
- **Quality**: View all orders, scan barcodes, add comments
- **Test**: View own orders, scan barcodes, add comments
- **Production Control**: View all orders, scan barcodes
- **SMT/AOI, Bench, Through Hole**: View own orders, scan barcodes
- **Shipping**: View all orders, scan barcodes

## Manager Authority

Managers have additional permissions regardless of their department:
- Create new orders
- Manage orders (delete, etc.)
- View all orders

Only administrators can assign or revoke manager status.

## Comments System

Quality and Test departments can add board-specific comments:
1. Enter a board ID (barcode)
2. Add a comment
3. View comments by board ID
4. Select previously commented boards from dropdown

## Troubleshooting

If you encounter any issues:
1. Check the console for detailed error messages
2. Try resetting the user database: `python reset_users.py`
3. Ensure all files are in the same directory
4. Make sure PyQt6 is properly installed: `pip install PyQt6`

## Files

- `main.py`: Main application entry point
- `data_manager.py`: Handles user and order data
- `login_window.py`: Login screen
- `admin_panel.py`: Admin interface
- `order_manager.py`: Order tracking interface
- `comment_manager.py`: Comments functionality
- `reset_users.py`: Script to reset user/order data
- `run.py`: Script to run the application with error handling

## Board Management System

The application now includes a dedicated Board Management system:

1. **Adding Boards**: All departmental users can add boards to orders
   - Select an order
   - Enter a unique board ID
   - Add optional description
   - The system automatically records the department and user who added the board

2. **Viewing Boards**: Boards are displayed in a dedicated table with:
   - Board ID
   - Description
   - Department that added it

3. **Board-Specific Comments**: Quality and Test departments can add comments to specific boards
   - Comments are linked to individual boards
   - Comments include timestamp and user information
   - Board details (description, department, etc.) are displayed with comments

4. **Workflow Integration**: Each department sees the boards they're responsible for
   - Boards maintain their department association
   - Comments from Quality and Test can be tracked per-board
   - Board histories can be reviewed across departments 
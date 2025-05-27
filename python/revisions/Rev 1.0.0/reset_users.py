import json
import os

def reset_users():
    # Default users with correct format and all departments
    users = {
        "admin": {
            "password": "password",
            "department": "admin",
            "is_manager": True
        },
        "manager1": {
            "password": "password123",
            "department": "production_control",
            "is_manager": True
        },
        "smt_user": {
            "password": "password123",
            "department": "smt_aoi",
            "is_manager": False
        },
        "bench_user": {
            "password": "password123",
            "department": "bench",
            "is_manager": False
        },
        "through_hole_user": {
            "password": "password123",
            "department": "through_hole",
            "is_manager": False
        },
        "production_user": {
            "password": "password123",
            "department": "production_control",
            "is_manager": False
        },
        "quality_user": {
            "password": "password123",
            "department": "quality",
            "is_manager": False
        },
        "test_user": {
            "password": "password123",
            "department": "test",
            "is_manager": False
        },
        "shipping_user": {
            "password": "password123",
            "department": "shipping",
            "is_manager": False
        }
    }
    
    # Create sample orders
    orders = {
        "ORD001": {
            "barcodes": ["BC001", "BC002", "BC003"],
            "board_comments": {
                "BC001": [
                    {
                        "text": "Board passed initial inspection",
                        "user": "quality_user",
                        "timestamp": "2023-08-10 14:30:00"
                    }
                ],
                "BC002": [
                    {
                        "text": "Failed test #3, needs rework",
                        "user": "test_user",
                        "timestamp": "2023-08-10 15:45:00"
                    }
                ]
            },
            "boards": {
                "BC001": {
                    "description": "Main controller board",
                    "department": "production_control",
                    "added_by": "production_user",
                    "added_at": "2023-08-10 10:15:00"
                },
                "BC002": {
                    "description": "Power supply board",
                    "department": "smt_aoi",
                    "added_by": "smt_user",
                    "added_at": "2023-08-10 11:30:00"
                },
                "BC003": {
                    "description": "Interface board",
                    "department": "through_hole",
                    "added_by": "through_hole_user", 
                    "added_at": "2023-08-10 12:45:00"
                }
            },
            "comments": [
                {
                    "text": "Order started",
                    "user": "admin",
                    "timestamp": "2023-08-10 09:00:00"
                }
            ],
            "created_at": "2023-08-10 09:00:00"
        },
        "ORD002": {
            "barcodes": ["BC004", "BC005"],
            "board_comments": {},
            "boards": {
                "BC004": {
                    "description": "Sensor board",
                    "department": "bench",
                    "added_by": "bench_user",
                    "added_at": "2023-08-11 10:30:00"
                },
                "BC005": {
                    "description": "LED display board",
                    "department": "test",
                    "added_by": "test_user",
                    "added_at": "2023-08-11 11:15:00"
                }
            },
            "comments": [],
            "created_at": "2023-08-11 10:15:00"
        }
    }
    
    # Save to users.json
    with open("users.json", "w") as f:
        json.dump(users, f, indent=2)
    
    # Save to orders.json
    with open("orders.json", "w") as f:
        json.dump(orders, f, indent=2)
    
    print(f"Reset users.json with {len(users)} users and orders.json with {len(orders)} orders")
    print("\nAvailable users:")
    for username, data in users.items():
        print(f"  Username: {username}, Password: {data['password']}, Department: {data['department']}, Manager: {data['is_manager']}")
    
    print("\nSample orders created: ORD001, ORD002")
    print("Sample barcodes: BC001-BC005")

if __name__ == "__main__":
    reset_users() 
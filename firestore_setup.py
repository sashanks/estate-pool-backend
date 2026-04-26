"""
Firebase Firestore Setup Helper
Provides utilities to set up and test Firestore collections for the API.

Run: python firestore_setup.py
"""

import json
import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime
from typing import Dict, List, Any

# Initialize Firebase
def init_firebase():
    """Initialize Firebase app."""
    if not firebase_admin._apps:
        creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase_credentials.json")
        if not os.path.exists(creds_path):
            print(f"Error: Firebase credentials not found at {creds_path}")
            return None
        
        cred = credentials.Certificate(creds_path)
        firebase_admin.initialize_app(cred)
        print("✓ Firebase initialized")
    
    return firestore.client()


def create_sample_area_document(db, area_id: str, data: Dict[str, Any]):
    """Create a sample area document in Firestore."""
    try:
        db.collection("areas").document(area_id).set(data)
        print(f"✓ Created document: areas/{area_id}")
        return True
    except Exception as e:
        print(f"✗ Error creating document: {str(e)}")
        return False


def sample_area_data(area_name: str, pincode: str) -> Dict[str, Any]:
    """Generate sample area data structure."""
    return {
        "name": area_name,
        "pincode": pincode,
        "created_at": datetime.now().isoformat(),
        "education": [
            {
                "name": "St. Xavier School",
                "type": "Private School",
                "rating": 4.5,
                "distance_km": 0.5
            },
            {
                "name": "Delhi Public School",
                "type": "Private School",
                "rating": 4.7,
                "distance_km": 1.2
            },
            {
                "name": "Delhi University",
                "type": "College",
                "rating": 4.3,
                "distance_km": 3.5
            }
        ],
        "health": [
            {
                "name": "Apollo Hospital",
                "type": "Multi-specialty Hospital",
                "beds": 150,
                "rating": 4.6,
                "distance_km": 1.0
            },
            {
                "name": "Fortis Healthcare",
                "type": "Hospital",
                "beds": 200,
                "rating": 4.5,
                "distance_km": 1.5
            },
            {
                "name": "Local Clinic",
                "type": "Primary Health Center",
                "rating": 3.8,
                "distance_km": 0.3
            }
        ],
        "infrastructure": [
            {
                "name": "Delhi Metro - Blue Line",
                "type": "Metro Station",
                "distance_km": 0.8
            },
            {
                "name": "Central Bus Depot",
                "type": "Bus Station",
                "distance_km": 1.2
            },
            {
                "name": "City Water Supply",
                "type": "Utility",
                "status": "Operational"
            },
            {
                "name": "Electricity Grid",
                "type": "Utility",
                "status": "24/7 Supply"
            }
        ],
        "transport": [
            {
                "name": "Metro Line 1 (Blue)",
                "type": "Rapid Transit",
                "frequency_minutes": 3
            },
            {
                "name": "Bus Route 101",
                "type": "Public Bus",
                "frequency_minutes": 15
            },
            {
                "name": "Taxi Service",
                "type": "Ride-sharing",
                "availability": "24/7"
            },
            {
                "name": "Parking",
                "type": "Facility",
                "spots_available": 200
            }
        ],
        "greenery": [
            {
                "name": "Central Park",
                "type": "Public Park",
                "area_hectares": 50,
                "rating": 4.4,
                "distance_km": 0.5
            },
            {
                "name": "Green Belt",
                "type": "Nature Reserve",
                "area_hectares": 100,
                "distance_km": 2.0
            },
            {
                "name": "Street Trees",
                "type": "Urban Greening",
                "count": 500
            }
        ],
        "religious_establishment": [
            {
                "name": "Central Mosque",
                "type": "Mosque",
                "capacity": 500,
                "distance_km": 0.8
            },
            {
                "name": "Shri Ram Mandir",
                "type": "Hindu Temple",
                "capacity": 1000,
                "distance_km": 1.2
            },
            {
                "name": "St. John's Church",
                "type": "Church",
                "capacity": 300,
                "distance_km": 1.5
            },
            {
                "name": "Sikh Gurudwara",
                "type": "Sikh Temple",
                "capacity": 800,
                "distance_km": 0.9
            }
        ]
    }


def setup_sample_data():
    """Set up sample areas in Firestore."""
    db = init_firebase()
    if not db:
        return
    
    print("\n📍 Setting up sample area data...")
    
    sample_areas = [
        ("delhi-110001", "New Delhi", "110001"),
        ("delhi-110002", "Old Delhi", "110002"),
        ("delhi-110017", "Shahdara", "110017"),
    ]
    
    for area_id, area_name, pincode in sample_areas:
        data = sample_area_data(area_name, pincode)
        create_sample_area_document(db, area_id, data)
    
    print("\n✓ Sample data setup complete!")


def list_areas():
    """List all areas in Firestore."""
    db = init_firebase()
    if not db:
        return
    
    print("\n📋 Existing areas in Firestore:")
    
    try:
        docs = db.collection("areas").stream()
        count = 0
        for doc in docs:
            data = doc.to_dict()
            print(f"  - {doc.id}: {data.get('name')} ({data.get('pincode')})")
            count += 1
        
        if count == 0:
            print("  (No areas found)")
        else:
            print(f"\nTotal: {count} areas")
    except Exception as e:
        print(f"Error listing areas: {str(e)}")


def delete_area(area_id: str):
    """Delete an area document from Firestore."""
    db = init_firebase()
    if not db:
        return
    
    try:
        db.collection("areas").document(area_id).delete()
        print(f"✓ Deleted: areas/{area_id}")
    except Exception as e:
        print(f"✗ Error deleting document: {str(e)}")


def query_by_name(area_name: str):
    """Query areas by name."""
    db = init_firebase()
    if not db:
        return
    
    print(f"\n🔍 Searching for areas named: {area_name}")
    
    try:
        docs = db.collection("areas").where("name", "==", area_name).stream()
        count = 0
        for doc in docs:
            data = doc.to_dict()
            print(f"Found: {doc.id}")
            print(f"  Name: {data.get('name')}")
            print(f"  Pincode: {data.get('pincode')}")
            print(f"  Categories: {', '.join(data.keys())}")
            count += 1
        
        if count == 0:
            print("No areas found with this name")
    except Exception as e:
        print(f"Error querying areas: {str(e)}")


def main():
    """Main menu."""
    print("🏘️  Firestore Setup Helper")
    print("=" * 50)
    print("\nOptions:")
    print("1. Setup sample data")
    print("2. List all areas")
    print("3. Query area by name")
    print("4. Delete area")
    print("5. Exit")
    
    choice = input("\nSelect an option (1-5): ").strip()
    
    if choice == "1":
        setup_sample_data()
    elif choice == "2":
        list_areas()
    elif choice == "3":
        area_name = input("Enter area name: ").strip()
        query_by_name(area_name)
    elif choice == "4":
        area_id = input("Enter area ID: ").strip()
        confirm = input(f"Delete {area_id}? (y/n): ").strip().lower()
        if confirm == "y":
            delete_area(area_id)
    elif choice == "5":
        print("Goodbye!")
        return
    else:
        print("Invalid option")
    
    print("\n" + "=" * 50)
    again = input("\nRun another operation? (y/n): ").strip().lower()
    if again == "y":
        main()


if __name__ == "__main__":
    main()

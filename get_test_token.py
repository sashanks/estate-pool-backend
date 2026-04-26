#!/usr/bin/env python3
"""
Generate a Firebase ID token for API testing.
Usage: python get_test_token.py [email] [password]
"""

import sys
import json
import requests
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase
try:
    cred = credentials.Certificate('firebase_credentials.json')
    app = firebase_admin.initialize_app(cred)
except ValueError:
    # App already initialized
    app = firebase_admin.get_app()

# Get Firebase API key from credentials
with open('firebase_credentials.json') as f:
    firebase_config = json.load(f)
    project_id = firebase_config['project_id']

def get_test_token_via_rest(email: str = "test@example.com", password: str = "test123456") -> str:
    """Generate a Firebase ID token via REST API (mimics real user login)."""
    try:
        # Get the API key from the Firebase project
        # For testing, we'll use the sign-up endpoint which creates a user if not exists
        url = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
        
        # Note: You need to get your Firebase Web API key
        # Go to Firebase Console > Project Settings > Web API Key
        api_key = "AIzaSyDwyJaLpR3t2AH-8D-lhW9XWZY4HXe9KOI"  # Placeholder - update with your actual key
        
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        response = requests.post(f"{url}?key={api_key}", json=payload)
        data = response.json()
        
        if "error" in data:
            print(f"✗ Error: {data['error']['message']}")
            return None
        
        id_token = data.get('idToken')
        print(f"✓ Firebase ID Token Generated:")
        print(f"  Email: {email}")
        print(f"  Token: {id_token}\n")
        
        return id_token
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def get_test_token_custom(uid: str = "test-user-123") -> str:
    """Generate a custom Firebase token (for server-to-server auth, not for API testing)."""
    try:
        # Create a custom token (server-side only)
        custom_token = auth.create_custom_token(uid)
        token_str = custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token
        
        # Exchange custom token for ID token
        url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken"
        api_key = "AIzaSyDwyJaLpR3t2AH-8D-lhW9XWZY4HXe9KOI"  # Placeholder - update with your actual key
        
        payload = {"token": token_str, "returnSecureToken": True}
        response = requests.post(f"{url}?key={api_key}", json=payload)
        data = response.json()
        
        if "error" in data:
            print(f"✗ Error exchanging token: {data['error']['message']}")
            return None
        
        id_token = data.get('idToken')
        print(f"✓ ID Token Generated (from custom token):")
        print(f"  UID: {uid}")
        print(f"  Token: {id_token}\n")
        
        return id_token
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    print("=" * 70)
    print("Firebase ID Token Generator for API Testing")
    print("=" * 70)
    
    # Option 1: Try REST API method (requires Web API key)
    email = sys.argv[1] if len(sys.argv) > 1 else "test@example.com"
    password = sys.argv[2] if len(sys.argv) > 2 else "test123456"
    
    print(f"\nAttempting to generate token via Firebase REST API...")
    token = get_test_token_via_rest(email, password)
    
    if token:
        print("=" * 70)
        print("✓ SUCCESS! Use this token in APIDOG:")
        print("=" * 70)
        print(f"\nAuthorization Header:")
        print(f"  Bearer {token}\n")
        
        print("cURL Example:")
        print(f"""curl -X POST http://localhost:8000/api/v1/neighborhood/summary \\
  -H 'Authorization: Bearer {token}' \\
  -H 'Content-Type: application/json' \\
  -d '{{
    "latitude": 28.6139,
    "longitude": 77.2090,
    "area_name": "New Delhi",
    "pincode": "110001"
  }}'
""")
    else:
        print("\n" + "=" * 70)
        print("⚠️  REST API method failed. Trying custom token exchange...")
        print("=" * 70)
        token = get_test_token_custom()
        
        if token:
            print("=" * 70)
            print("✓ SUCCESS! Use this token in APIDOG:")
            print("=" * 70)
            print(f"\nAuthorization Header:")
            print(f"  Bearer {token}\n")
        else:
            print("\n" + "=" * 70)
            print("❌ Token generation failed!")
            print("=" * 70)
            print("""
SOLUTION: You need to get your Firebase Web API Key:
1. Go to Firebase Console: https://console.firebase.google.com/
2. Select project 'neighbourhood-4c5b6'
3. Click Project Settings (gear icon)
4. Go to "Your apps" tab
5. Find your Web app
6. Copy the API Key from the Firebase config
7. Update this script (line ~13) with your actual API key

Example:
  api_key = "AIzaSy..."  # Your actual Firebase Web API key
""")


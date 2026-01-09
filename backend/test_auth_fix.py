import requests
import json
import random

API_URL = "http://localhost:8000" # fallback if not set

def test_registration():
    email = f"testuser_{random.randint(1000, 9999)}@example.com"
    full_name = "Test User"
    password = "password123"
    
    print(f"Testing registration for: {email}")
    
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json={"email": email, "full_name": full_name, "password": password}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("--- Registration Successful! ---")
            return email, password
        else:
            print("--- Registration Failed! ---")
            return None, None
    except Exception as e:
        print(f"Connection failed: {e}")
        return None, None

def test_login(email, password):
    print(f"Testing login for: {email}")
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            data={"username": email, "password": password}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("--- Login Successful! ---")
        else:
            print("--- Login Failed! ---")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    email, password = test_registration()
    if email:
        test_login(email, password)

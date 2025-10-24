#!/usr/bin/env python3
"""Test script for the updated Flask API with new admin registration fields"""

import requests
import json
import time

def test_api_registration():
    """Test the API registration endpoint with new fields"""
    print("🧪 Testing API registration with new fields...")

    # Start the Flask server in background
    import subprocess
    import os

    # Start the server
    server_process = subprocess.Popen([
        'python', 'simple_api.py'
    ], cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for server to start
    time.sleep(2)

    try:
        # Test registration with all fields
        response = requests.post('http://localhost:8001/api/admin/register', json={
            'email': 'api_test@example.com',
            'password': 'testpass123',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1995-05-15',
            'phone_number': '+1987654321'
        })

        if response.status_code == 201:
            data = response.json()
            if data.get('success'):
                print("✅ API registration with all fields successful!")
            else:
                print(f"❌ API registration failed: {data.get('message')}")
                return False
        else:
            print(f"❌ API registration failed with status {response.status_code}")
            return False

        # Test registration with minimal fields
        response2 = requests.post('http://localhost:8001/api/admin/register', json={
            'email': 'api_minimal@example.com',
            'password': 'testpass123'
        })

        if response2.status_code == 201:
            data2 = response2.json()
            if data2.get('success'):
                print("✅ API registration with minimal fields successful!")
            else:
                print(f"❌ API minimal registration failed: {data2.get('message')}")
                return False
        else:
            print(f"❌ API minimal registration failed with status {response2.status_code}")
            return False

        # Test duplicate email
        response3 = requests.post('http://localhost:8001/api/admin/register', json={
            'email': 'api_test@example.com',
            'password': 'differentpass'
        })

        if response3.status_code == 400:
            data3 = response3.json()
            if not data3.get('success'):
                print("✅ API duplicate email properly rejected!")
            else:
                print("❌ API duplicate email was not rejected!")
                return False
        else:
            print(f"❌ API duplicate email test failed with status {response3.status_code}")
            return False

        print("🎉 All API registration tests passed!")
        return True

    finally:
        # Stop the server
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    print("🚀 Starting API tests...\n")

    try:
        if test_api_registration():
            print("\n🎊 All API tests passed! The Flask API is working correctly.")
        else:
            print("\n💥 Some API tests failed. Please check the implementation.")
    except Exception as e:
        print(f"\n💥 API test error: {e}")
        print("Make sure Flask and requests are installed: pip install flask requests")
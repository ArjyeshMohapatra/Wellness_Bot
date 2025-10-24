#!/usr/bin/env python3
"""Test script for the updated authentication system with new admin registration fields"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_auth import register_admin, login_admin

def test_new_registration():
    """Test registering an admin with the new fields"""
    print("🧪 Testing new admin registration with additional fields...")

    # Test registration with all fields
    success = register_admin(
        email="test@example.com",
        password="testpass123",
        first_name="John",
        last_name="Doe",
        date_of_birth="1990-01-01",
        phone_number="+1234567890"
    )

    if success:
        print("✅ Registration with all fields successful!")
    else:
        print("❌ Registration with all fields failed!")
        return False

    # Test registration with minimal fields (optional fields None)
    success2 = register_admin(
        email="minimal@example.com",
        password="testpass123"
    )

    if success2:
        print("✅ Registration with minimal fields successful!")
    else:
        print("❌ Registration with minimal fields failed!")
        return False

    # Test duplicate email
    success3 = register_admin(
        email="test@example.com",
        password="differentpass"
    )

    if not success3:
        print("✅ Duplicate email properly rejected!")
    else:
        print("❌ Duplicate email was not rejected!")
        return False

    print("🎉 All registration tests passed!")
    return True

def test_login():
    """Test login functionality"""
    print("\n🧪 Testing login functionality...")

    success = login_admin("test@example.com", "testpass123")
    if success:
        print("✅ Login successful!")
        return True
    else:
        print("❌ Login failed!")
        return False

if __name__ == "__main__":
    print("🚀 Starting authentication tests...\n")

    if test_new_registration() and test_login():
        print("\n🎊 All tests passed! The authentication system is working correctly.")
    else:
        print("\n💥 Some tests failed. Please check the implementation.")
        sys.exit(1)
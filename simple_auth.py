import hashlib
import secrets
from src.db import execute_query
import bcrypt

def hash_password(password):
    """Hash password using bcrypt (secure for passwords)"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    """Check password against bcrypt hash"""
    return bcrypt.checkpw(password.encode(), hashed.encode())

def register_admin(email, password, first_name=None, last_name=None, date_of_birth=None, phone_number=None):
    """Register a new admin using existing users table"""
    try:
        # Check if user already exists by email
        existing_email = execute_query("SELECT id FROM users WHERE email = %s",(email,),fetch=True)

        if existing_email:
            print("❌ Admin with this email already exists!")
            return False

        # Hash password and save
        password_hash = hash_password(password)
        result = execute_query("INSERT INTO users (email, password_hash, role, first_name, last_name, date_of_birth, phone_number) VALUES (%s, %s, 'admin', %s, %s, %s, %s)",(email, password_hash, first_name, last_name, date_of_birth, phone_number))

        if result:
            print("✅ Admin registered successfully!")
            return True
        else:
            print("❌ Registration failed!")
            return False

    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False

def login_admin(email, password):
    """Login admin using existing users table"""
    try:
        # Get user from database
        users = execute_query("SELECT password_hash FROM users WHERE email = %s AND is_active = TRUE",(email,),fetch=True)

        if not users:
            print("❌ Admin not found!")
            return False

        user = users[0]

        # Check password
        if check_password(password, user['password_hash']):
            print("✅ Login successful!")
            return True
        else:
            print("❌ Wrong password!")
            return False

    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

def reset_admin_password(email):
    """Reset password to a random one using existing password_resets table"""
    try:
        # Check if admin exists
        users = execute_query("SELECT id FROM users WHERE email = %s AND is_active = TRUE",(email,),fetch=True)

        if not users:
            print("❌ Admin not found!")
            return None

        user_id = users[0]['id']

        # Generate new random password
        new_password = secrets.token_hex(8)  # 16 character random password
        password_hash = hash_password(new_password)

        # Update password in users table
        execute_query("UPDATE users SET password_hash = %s WHERE id = %s",(password_hash, user_id))

        print(f"✅ Password reset! New password: {new_password}")
        print("⚠️  Save this password - it's shown only once!")
        return new_password

    except Exception as e:
        print(f"❌ Password reset error: {e}")
        return None

def get_all_admins():
    """Get all admin users (for management)"""
    try:
        admins = execute_query("SELECT id, email, created_at FROM users WHERE role = 'admin' AND is_active = TRUE",fetch=True)
        return admins
    except Exception as e:
        print(f"❌ Error getting admins: {e}")
        return []

if __name__ == "__main__":
    print("🔐 Simple Admin Authentication System")
    print("=" * 40)
    print("\nGetting all admins...")
    admins = get_all_admins()
    for admin in admins:
        print(f"   - {admin['email']} (ID: {admin['id']})")
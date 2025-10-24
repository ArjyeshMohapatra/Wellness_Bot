from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add src directory to path so we can import simple_auth and db
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from simple_auth import register_admin, login_admin, reset_admin_password, get_all_admins

# Simple Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:3000"])  # React dev servers

@app.route('/api/admin/register', methods=['POST'])
def api_register():
    """Register admin endpoint for React"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        date_of_birth = data.get('date_of_birth')
        phone_number = data.get('phone_number')

        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'}), 400

        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400

        success = register_admin(email, password, first_name, last_name, date_of_birth, phone_number)
        if success:
            return jsonify({'success': True, 'message': 'Admin registered successfully'}), 201
        else:
            return jsonify({'success': False, 'message': 'Registration failed'}), 400

    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/admin/login', methods=['POST'])
def api_login():
    """Login admin endpoint for React"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'}), 400

        success = login_admin(email, password)
        if success:
            return jsonify({'success': True, 'message': 'Login successful'}), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/admin/reset-password', methods=['POST'])
def api_reset_password():
    """Reset password endpoint for React"""
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'success': False, 'message': 'Email required'}), 400

        new_password = reset_admin_password(email)
        if new_password:
            return jsonify({
                'success': True,
                'message': 'Password reset successful',
                'new_password': new_password  # In real app, don't send this!
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Reset failed'}), 400

    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/admin/list', methods=['GET'])
def api_list_admins():
    """Get all admins endpoint for React"""
    try:
        admins = get_all_admins()
        return jsonify({'success': True, 'admins': admins}), 200

    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Simple API is running'}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)
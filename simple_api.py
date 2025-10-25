from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add src directory to path so we can import simple_auth and db
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from simple_auth import register_admin, login_admin, reset_admin_password, get_all_admins
from db import execute_query, init_db_pool

# Initialize database connection pool
init_db_pool()

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
            # Get user details after successful login
            user_query = "SELECT id, email, first_name, last_name, role FROM users WHERE email = %s AND is_active = TRUE"
            user_result = execute_query(user_query, (email,), fetch=True)
            if user_result:
                user = user_result[0]
                return jsonify({
                    'success': True, 
                    'message': 'Login successful',
                    'user': {
                        'id': user['id'],
                        'email': user['email'],
                        'first_name': user['first_name'],
                        'last_name': user['last_name'],
                        'role': user['role']
                    }
                }), 200
            else:
                return jsonify({'success': False, 'message': 'User data not found'}), 500
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

@app.route('/api/payment/transaction', methods=['POST'])
def api_save_transaction():
    """Save payment transaction endpoint"""
    try:
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        user_id = data.get('user_id')
        plan_name = data.get('plan_name')
        billing_type = data.get('billing_type')
        duration_months = data.get('duration_months')
        amount = data.get('amount')

        print(f"Payment attempt: transaction_id={transaction_id}, user_id={user_id}, plan_name={plan_name}")

        if not all([transaction_id, user_id, plan_name, billing_type, duration_months, amount]):
            missing = []
            if not transaction_id: missing.append('transaction_id')
            if not user_id: missing.append('user_id')
            if not plan_name: missing.append('plan_name')
            if not billing_type: missing.append('billing_type')
            if not duration_months: missing.append('duration_months')
            if not amount: missing.append('amount')
            print(f"Missing fields: {missing}")
            return jsonify({'success': False, 'message': f'Missing required fields: {", ".join(missing)}'}), 400

        # Check if user exists
        user_check = execute_query("SELECT id FROM users WHERE id = %s", (user_id,), fetch=True)
        if not user_check:
            print(f"User with id {user_id} does not exist")
            return jsonify({'success': False, 'message': 'User not found. Please login again.'}), 400

        query = """
            INSERT INTO payment_transactions 
            (transaction_id, user_id, plan_name, billing_type, duration_months, amount, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'completed')
        """
        params = (transaction_id, user_id, plan_name, billing_type, duration_months, amount)
        
        execute_query(query, params)
        print(f"Payment saved successfully for user {user_id}")
        return jsonify({'success': True, 'message': 'Transaction saved successfully'}), 201

    except Exception as e:
        print(f"API Error in payment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/payment/check-subscription', methods=['GET'])
def api_check_subscription():
    """Check if user has active subscription"""
    try:
        email = request.args.get('email')
        print(f"Checking subscription for email: {email}")

        if not email:
            return jsonify({'success': False, 'message': 'Email required'}), 400

        # First get user_id from email (assuming we have a users table with email)
        query = "SELECT id FROM users WHERE email = %s"
        result = execute_query(query, (email,), fetch=True)
        print(f"User lookup result: {result}")

        if not result:
            print(f"No user found for email: {email}")
            return jsonify({'hasActiveSubscription': False, 'message': 'User not found'}), 200

        user_id = result[0]['id']
        print(f"Found user_id: {user_id}")

        # Check for active subscription (assuming current date is within the subscription period)
        query = """
            SELECT plan_name, billing_type, duration_months, created_at, status
            FROM payment_transactions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 5
        """
        result = execute_query(query, (user_id,), fetch=True)
        print(f"Transaction lookup result: {result}")

        # Check for completed transactions
        completed_transactions = [t for t in result if t['status'] == 'completed']
        print(f"Completed transactions: {completed_transactions}")

        if completed_transactions:
            transaction = completed_transactions[0]
            # For now, assume subscription is active if there's any completed transaction
            # In a real app, you'd check if current date is within the subscription period
            return jsonify({
                'hasActiveSubscription': True,
                'planName': transaction['plan_name'],
                'billingType': transaction['billing_type'],
                'message': 'Active subscription found'
            }), 200
        else:
            return jsonify({'hasActiveSubscription': False, 'message': 'No active subscription'}), 200

    except Exception as e:
        print(f"API Error in check-subscription: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=False)
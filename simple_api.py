from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import sys
import os

# Add src directory to path so we can import simple_auth and db
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from simple_auth import register_admin, login_admin, reset_admin_password, get_all_admins
from services.database_service import save_admin_panel_config, get_admin_panel_config
from db import execute_query, init_db_pool

# Initialize database connection pool
init_db_pool()

# Simple Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:5173", "http://localhost:3000"], 
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
     supports_credentials=True)

@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', 'http://localhost:5173')
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

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

@app.route('/api/admin/panel/save', methods=['POST'])
def api_save_admin_panel():
    """Save admin panel configuration"""
    try:
        data = request.get_json()
        print(f"API: Received data for panel/save: {data}")
        admin_user_id = data.get('admin_user_id')
        group_id = data.get('group_id')
        config_data = data.get('config_data')
        print(f"API: admin_user_id: {admin_user_id}, config_data keys: {list(config_data.keys()) if config_data else None}")

        if not all([admin_user_id, config_data]):
            print(f"API: Missing fields - admin_user_id: {admin_user_id}, config_data: {config_data}")
            return jsonify({'success': False, 'message': 'Missing required fields: admin_user_id, config_data'}), 400

        # Generate a license key for this configuration
        from generate_license import generate_license_key
        license_key = generate_license_key()

        # Add license key to config data
        config_data['license_key'] = license_key

        # If group_id is not provided, save as admin template with group_id=None
        if not group_id:
            # Save configuration with NULL group_id using admin_user_id
            success = save_admin_panel_config(admin_user_id, None, config_data)
            if success:
                # Save license key to database
                execute_query(
                    "INSERT INTO licenses (license_key, is_active, assigned_group_id, assigned_admin_id, created_at) VALUES (%s, TRUE, %s, %s, NOW())",
                    (license_key, None, admin_user_id)
                )
                return jsonify({
                    'success': True,
                    'message': 'Configuration template saved successfully',
                    'license_key': license_key,
                    'bot_username': 'WellnessBot'
                }), 200
            else:
                return jsonify({'success': False, 'message': 'Failed to save configuration template'}), 500

        # Save configuration for specific group
        success = save_admin_panel_config(admin_user_id, int(group_id), config_data)
        if success:
            # Save license key to database
            execute_query(
                "INSERT INTO licenses (license_key, is_active, assigned_group_id, assigned_admin_id, created_at) VALUES (%s, TRUE, %s, %s, NOW())",
                (license_key, int(group_id), admin_user_id)
            )
            return jsonify({
                'success': True,
                'message': 'Configuration saved successfully',
                'license_key': license_key,
                'bot_username': 'WellnessBot'
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to save configuration'}), 500

    except Exception as e:
        print(f"API Error in save admin panel: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/panel/config', methods=['GET'])
def api_get_admin_panel_config():
    """Get admin panel configuration for a group"""
    try:
        group_id = request.args.get('group_id')

        if not group_id:
            return jsonify({'success': False, 'message': 'Group ID required'}), 400

        # Import here to avoid circular imports
        from services.database_service import get_admin_panel_config

        config = get_admin_panel_config(int(group_id))
        if config:
            return jsonify({'success': True, 'config': config}), 200
        else:
            return jsonify({'success': False, 'message': 'Configuration not found'}), 404

    except Exception as e:
        print(f"API Error in get admin panel config: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/generate-license', methods=['POST'])
def api_generate_license():
    """Generate and save a new license key for admin"""
    try:
        data = request.get_json()
        admin_user_id = data.get('admin_user_id')
        group_id = data.get('group_id')

        if not admin_user_id:
            return jsonify({'success': False, 'message': 'Admin user ID required'}), 400

        # Import the license generator
        from generate_license import generate_license_key

        # Generate new license key
        license_key = generate_license_key()

        # Save to database
        execute_query(
            "INSERT INTO licenses (license_key, is_active, assigned_group_id, assigned_admin_id, created_at) VALUES (%s, TRUE, %s, %s, NOW())",
            (license_key, group_id, admin_user_id)
        )

        return jsonify({
            'success': True,
            'license_key': license_key,
            'message': 'License key generated and saved successfully'
        }), 200

    except Exception as e:
        print(f"API Error in generate license: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/generate-unique-user-ids', methods=['POST'])
def api_generate_unique_user_ids():
    """Generate unique user IDs for a group"""
    try:
        data = request.get_json()
        admin_user_id = data.get('admin_user_id')
        group_id = data.get('group_id')
        count = data.get('count', 25)

        if not admin_user_id or not group_id:
            return jsonify({'success': False, 'message': 'Admin user ID and group ID required'}), 400

        # Verify that this admin owns this group (through license assignment)
        group_check = execute_query(
            """
            SELECT gc.group_id 
            FROM groups_config gc
            JOIN licenses l ON gc.license_key = l.license_key
            WHERE gc.group_id = %s AND l.assigned_admin_id = %s AND l.is_active = TRUE
            """,
            (group_id, admin_user_id),
            fetch=True
        )

        if not group_check:
            return jsonify({'success': False, 'message': 'Unauthorized: You do not own this group'}), 403

        # Generate unique user IDs
        from services.database_service import generate_unique_user_ids_for_group
        user_ids = generate_unique_user_ids_for_group(group_id, count)

        return jsonify({
            'success': True,
            'user_ids': user_ids,
            'count': len(user_ids),
            'message': f'Successfully generated {len(user_ids)} unique user IDs'
        }), 200

    except Exception as e:
        print(f"API Error in generate unique user IDs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/get-group-id', methods=['GET'])
def api_get_group_id():
    """Get group ID for an admin"""
    try:
        admin_user_id = request.args.get('admin_user_id')

        if not admin_user_id:
            return jsonify({'success': False, 'message': 'Admin user ID required'}), 400

        # Get group ID for this admin
        group_result = execute_query(
            """
            SELECT DISTINCT gc.group_id
            FROM groups_config gc
            JOIN licenses l ON gc.license_key = l.license_key
            WHERE l.assigned_admin_id = %s AND l.is_active = TRUE
            LIMIT 1
            """,
            (admin_user_id,),
            fetch=True
        )

        if not group_result:
            return jsonify({'success': False, 'message': 'No group found for this admin'}), 404

        group_id = group_result[0]['group_id']

        return jsonify({
            'success': True,
            'group_id': group_id
        }), 200

    except Exception as e:
        print(f"API Error in get group ID: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/get-available-user-ids', methods=['GET'])
def api_get_available_user_ids():
    """Get available (unused) user IDs for a group"""
    try:
        admin_user_id = request.args.get('admin_user_id')

        if not admin_user_id:
            return jsonify({'success': False, 'message': 'Admin user ID required'}), 400

        # Get group ID for this admin
        group_result = execute_query(
            """
            SELECT DISTINCT gc.group_id
            FROM groups_config gc
            JOIN licenses l ON gc.license_key = l.license_key
            WHERE l.assigned_admin_id = %s AND l.is_active = TRUE
            LIMIT 1
            """,
            (admin_user_id,),
            fetch=True
        )

        if not group_result:
            return jsonify({'success': False, 'message': 'No group found for this admin'}), 404

        group_id = group_result[0]['group_id']

        # Get available user IDs
        from services.database_service import get_available_unique_user_ids
        available_ids = get_available_unique_user_ids(group_id)

        return jsonify({
            'success': True,
            'user_ids': available_ids,
            'count': len(available_ids),
            'message': f'Found {len(available_ids)} available user IDs'
        }), 200

    except Exception as e:
        print(f"API Error in get available user IDs: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500


@app.route('/api/admin/dashboard/settings', methods=['GET'])
def api_get_admin_dashboard_settings():
    """Get admin dashboard settings"""
    try:
        admin_user_id = request.args.get('admin_user_id')
        print(f"API: Getting dashboard settings for admin_user_id: {admin_user_id}")

        if not admin_user_id:
            return jsonify({'success': False, 'message': 'Admin user ID required'}), 400

        from src.services.database_service import get_admin_dashboard_settings

        settings = get_admin_dashboard_settings(int(admin_user_id))
        print(f"API: Retrieved settings: {settings}")
        if settings:
            return jsonify({'success': True, 'settings': settings}), 200
        else:
            return jsonify({'success': True, 'settings': None}), 200  # No settings yet

    except Exception as e:
        print(f"API Error in get admin dashboard settings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/dashboard/settings', methods=['POST'])
def api_save_admin_dashboard_settings():
    """Save admin dashboard settings"""
    try:
        data = request.get_json()
        print(f"API: Saving dashboard settings for data: {data}")
        admin_user_id = data.get('admin_user_id')
        settings = data.get('settings', {})

        if not admin_user_id:
            print("API: No admin_user_id provided")
            return jsonify({'success': False, 'message': 'Admin user ID required'}), 400

        from src.services.database_service import save_admin_dashboard_settings

        success = save_admin_dashboard_settings(int(admin_user_id), settings)
        print(f"API: Save result: {success}")
        if success:
            return jsonify({'success': True, 'message': 'Settings saved successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'Failed to save settings'}), 500

    except Exception as e:
        print(f"API Error in save admin dashboard settings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=False)
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import sys
import os
import json

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

        # Update subscription limits based on the new payment
        update_limits_query = """
            INSERT INTO admin_subscription_limits (admin_user_id, max_members, current_total_members)
            VALUES (%s, get_max_members_for_admin(%s), 0)
            ON DUPLICATE KEY UPDATE
                max_members = get_max_members_for_admin(%s),
                updated_at = CURRENT_TIMESTAMP
        """
        execute_query(update_limits_query, (user_id, user_id, user_id))
        print(f"Subscription limits updated for user {user_id}")

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

        # Get telegram_id from database user id
        user_result = execute_query(
            "SELECT telegram_id FROM users WHERE id = %s AND is_active = TRUE",
            (admin_user_id,),
            fetch=True
        )

        if not user_result:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        telegram_id = user_result[0]['telegram_id']

        # Always create new event and license for each save
        # Add license_key to config_data (will be generated in save_admin_panel_config)
        config_data['license_key'] = ''  # Placeholder, will be set in function

        # Save configuration
        success, license_key, event_id = save_admin_panel_config(telegram_id, int(group_id) if group_id else None, config_data)

        if success:
            return jsonify({
                'success': True,
                'message': 'Configuration saved successfully',
                'license_key': license_key,
                'bot_username': 'WellnessBot',
                'event_id': event_id
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

        # Generate unique user ID (one per call)
        from services.database_service import generate_unique_user_ids_for_group
        user_ids = generate_unique_user_ids_for_group(group_id, 1)

        if user_ids:
            return jsonify({
                'success': True,
                'user_ids': user_ids,
                'message': 'Successfully generated unique user ID'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Could not generate user ID (subscription limit reached or error)'
            }), 400

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

        # Get telegram_id from database user id
        user_result = execute_query(
            "SELECT telegram_id FROM users WHERE id = %s AND is_active = TRUE",
            (admin_user_id,),
            fetch=True
        )

        if not user_result:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        telegram_id = user_result[0]['telegram_id']

        # Get group ID for this admin
        group_result = execute_query(
            """
            SELECT DISTINCT gc.group_id
            FROM groups_config gc
            JOIN events e ON gc.event_id = e.event_id
            JOIN licenses l ON e.license_key = l.license_key
            WHERE l.assigned_admin_id = %s AND l.is_active = TRUE AND gc.group_id != 0
            ORDER BY gc.group_id DESC
            LIMIT 1
            """,
            (telegram_id,),
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
    """Get admin dashboard settings - now returns all settings for all groups"""
    try:
        admin_user_id = request.args.get('admin_user_id')
        group_id = request.args.get('group_id')  # Optional: get settings for specific group
        print(f"API: Getting dashboard settings for admin_user_id: {admin_user_id}, group_id: {group_id}")

        if not admin_user_id:
            return jsonify({'success': False, 'message': 'Admin user ID required'}), 400

        from src.services.database_service import get_admin_bot_settings, get_bot_settings_for_group

        if group_id:
            # Get settings for specific group
            settings = get_bot_settings_for_group(int(admin_user_id), int(group_id))
            if settings:
                return jsonify({'success': True, 'settings': settings}), 200
            else:
                return jsonify({'success': True, 'settings': None}), 200  # No settings for this group yet
        else:
            # Get all settings for admin
            settings_list = get_admin_bot_settings(int(admin_user_id))
            print(f"API: Retrieved {len(settings_list)} settings")
            return jsonify({'success': True, 'settings': settings_list}), 200

    except Exception as e:
        print(f"API Error in get admin dashboard settings: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/admin/dashboard/settings', methods=['POST'])
def api_save_admin_dashboard_settings():
    """Save admin dashboard settings for a specific group"""
    try:
        data = request.get_json()
        print(f"API: Saving dashboard settings for data: {data}")
        admin_user_id = data.get('admin_user_id')
        group_id = data.get('group_id', 0)  # Default to 0 if not provided (for backward compatibility)
        settings = data.get('settings', {})

        if not admin_user_id:
            print("API: No admin_user_id provided")
            return jsonify({'success': False, 'message': 'Admin user ID required'}), 400

        from src.services.database_service import save_bot_settings_for_group

        success = save_bot_settings_for_group(int(admin_user_id), int(group_id), settings)
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

@app.route('/api/admin/events', methods=['GET'])
def api_get_events():
    """Get events for admin with associated groups"""
    try:
        admin_user_id = request.args.get('admin_user_id')
        if not admin_user_id:
            return jsonify({'success': False, 'message': 'admin_user_id required'}), 400

        # Get events with associated groups
        query = """
            SELECT 
                e.*,
                GROUP_CONCAT(
                    JSON_OBJECT(
                        'group_id', gc.group_id,
                        'group_name', gc.group_name,
                        'is_active', gc.is_active
                    )
                ) as groups_json
            FROM events e
            LEFT JOIN groups_config gc ON e.event_id = gc.event_id
            WHERE e.admin_user_id = %s
            GROUP BY e.event_id
            ORDER BY e.created_at DESC
        """
        events = execute_query(query, (admin_user_id,), fetch=True)
        
        # Parse the groups JSON for each event
        for event in events:
            if event['groups_json']:
                try:
                    # Parse the concatenated JSON objects
                    groups_str = event['groups_json']
                    # Split by comma and parse each JSON object
                    group_objects = []
                    for group_json in groups_str.split(',{'):
                        if not group_json.startswith('{'):
                            group_json = '{' + group_json
                        try:
                            group_objects.append(json.loads(group_json))
                        except json.JSONDecodeError:
                            continue
                    event['groups'] = group_objects
                except Exception as e:
                    print(f"Error parsing groups for event {event['event_id']}: {e}")
                    event['groups'] = []
            else:
                event['groups'] = []
            # Remove the raw JSON string
            del event['groups_json']
        
        return jsonify({'success': True, 'events': events}), 200
    except Exception as e:
        print(f"Error getting events: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/events', methods=['POST'])
def api_create_event():
    """Create a new event"""
    try:
        data = request.get_json()
        admin_user_id = data.get('admin_user_id')
        event_name = data.get('event_name')

        if not admin_user_id or not event_name:
            return jsonify({'success': False, 'message': 'admin_user_id and event_name required'}), 400

        # Check if user exists
        user_check = execute_query("SELECT id FROM users WHERE id = %s", (admin_user_id,), fetch=True)
        if not user_check:
            return jsonify({'success': False, 'message': 'User not found. Please login again.'}), 400

        # Create event with default values
        from generate_license import generate_license_key
        license_key = generate_license_key()

        query = """
            INSERT INTO events (admin_user_id, event_name, license_key, event_type, event_days, slots_per_day, start_date, end_date, min_pass_points, is_active)
            VALUES (%s, %s, %s, 'normal', 7, 2, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 3650 DAY), 250, TRUE)
        """
        event_id = execute_query(query, (admin_user_id, event_name, license_key))
        if not event_id:
            raise Exception("Failed to insert event")

        # Insert license into licenses table
        license_query = """
            INSERT INTO licenses (license_key, event_id, is_active, assigned_admin_id)
            VALUES (%s, %s, TRUE, %s)
        """
        execute_query(license_query, (license_key, event_id, admin_user_id))

        # Create default bot settings for the event
        bot_settings_query = """
            INSERT INTO bot_settings (event_id, bot_username, has_admin_permissions, event_type, event_name, event_days, pass_points, slots_per_day, welcome_message, kick_response, undesignated_slot_response, leaderboard_time, is_active)
            VALUES (%s, 'WellnessBot', FALSE, 'normal', %s, 7, 250, 2, 'Welcome to our wellness program!', 'You have been removed for not following the rules.', 'Please respond to your assigned slot.', '11:00', TRUE)
        """
        execute_query(bot_settings_query, (event_id, event_name))

        return jsonify({'success': True, 'event_id': event_id, 'license_key': license_key}), 200
    except Exception as e:
        print(f"Error creating event: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/bot/settings', methods=['GET'])
def api_get_bot_settings():
    """Get bot settings for event"""
    try:
        event_id = request.args.get('event_id')
        if not event_id:
            return jsonify({'success': False, 'message': 'event_id required'}), 400

        query = "SELECT * FROM bot_settings WHERE event_id = %s"
        settings = execute_query(query, (event_id,), fetch=True)
        if settings:
            setting = settings[0]
            # Convert banned_words from JSON to comma-separated string
            if 'banned_words' in setting and setting['banned_words']:
                try:
                    banned_words_list = json.loads(setting['banned_words'])
                    setting['banned_words'] = ', '.join(banned_words_list)
                except (json.JSONDecodeError, TypeError):
                    setting['banned_words'] = ''
            # Convert loaded_slots from JSON to list
            if 'loaded_slots' in setting and setting['loaded_slots']:
                try:
                    setting['loaded_slots'] = json.loads(setting['loaded_slots'])
                except (json.JSONDecodeError, TypeError):
                    setting['loaded_slots'] = []
            return jsonify({'success': True, 'settings': setting}), 200
        else:
            return jsonify({'success': False, 'message': 'Settings not found'}), 404
    except Exception as e:
        print(f"Error getting bot settings: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/bot/settings/save', methods=['POST'])
def api_save_bot_settings():
    """Save bot settings for an event"""
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        config_data = data.get('config_data')

        if not event_id or not config_data:
            return jsonify({'success': False, 'message': 'event_id and config_data required'}), 400

        # Update bot_settings for the event
        query = """
            INSERT INTO bot_settings (event_id, bot_username, has_admin_permissions, event_type, event_name,
                                     event_days, pass_points, slots_per_day, welcome_message, kick_response,
                                     undesignated_slot_response, leaderboard_time, banned_words, loaded_slots)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            bot_username = VALUES(bot_username),
            has_admin_permissions = VALUES(has_admin_permissions),
            event_type = VALUES(event_type),
            event_name = VALUES(event_name),
            event_days = VALUES(event_days),
            pass_points = VALUES(pass_points),
            slots_per_day = VALUES(slots_per_day),
            welcome_message = VALUES(welcome_message),
            kick_response = VALUES(kick_response),
            undesignated_slot_response = VALUES(undesignated_slot_response),
            leaderboard_time = VALUES(leaderboard_time),
            banned_words = VALUES(banned_words),
            loaded_slots = VALUES(loaded_slots)
        """
        # Handle banned_words - convert to JSON array
        banned_words = config_data.get('banned_words', '')
        if isinstance(banned_words, str) and banned_words.strip():
            # Split by comma and strip whitespace
            banned_words_list = [word.strip() for word in banned_words.split(',') if word.strip()]
            banned_words_json = json.dumps(banned_words_list)
        elif isinstance(banned_words, list):
            banned_words_json = json.dumps(banned_words)
        else:
            banned_words_json = json.dumps([])

        params = (
            event_id,
            config_data.get('bot_username', 'WellnessBot'),
            config_data.get('has_admin_permissions', False),
            config_data.get('event_type', 'normal'),
            config_data.get('event_name', ''),
            config_data.get('event_days', 7),
            config_data.get('pass_points', 250),
            config_data.get('slots_per_day', 2),
            config_data.get('welcome_message', ''),
            config_data.get('kick_response', ''),
            config_data.get('undesignated_slot_response', ''),
            config_data.get('leaderboard_time', '11:00'),
            banned_words_json,
            json.dumps(config_data.get('loaded_slots', []))
        )
        execute_query(query, params)

        # Save slots for the event
        slots_data = config_data.get('slots', [])
        if slots_data:
            # First, delete existing slots for this event
            execute_query("DELETE FROM event_slots WHERE event_id = %s", (event_id,))
            # Then insert new slots
            for slot in slots_data:
                slot_query = """
                    INSERT INTO event_slots (event_id, slot_name, start_time, end_time, initial_message,
                                           response_positive, response_clarify, image_file_path, slot_type,
                                           slot_points, is_mandatory, button_count, button_names, button_values)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                slot_params = (
                    event_id,
                    slot.get('name', ''),
                    slot.get('startTime', ''),
                    slot.get('endTime', ''),
                    slot.get('botResponse', ''),
                    slot.get('postResponse', ''),
                    '',  # response_clarify
                    slot.get('image', ''),
                    'button' if slot.get('type') == 'button' else 'default',
                    slot.get('points', 10),
                    slot.get('compulsory', False),
                    slot.get('buttonCount', 0),
                    json.dumps(slot.get('buttonNames', [])),
                    json.dumps(slot.get('buttonValues', []))
                )
                execute_query(slot_query, slot_params)

        # Get the license key for this event
        license_query = "SELECT license_key FROM events WHERE event_id = %s"
        license_result = execute_query(license_query, (event_id,), fetch=True)
        license_key = license_result[0]['license_key'] if license_result else None

        return jsonify({
            'success': True, 
            'message': 'Bot settings saved successfully',
            'license_key': license_key,
            'bot_username': config_data.get('bot_username', 'WellnessBot')
        }), 200
    except Exception as e:
        print(f"Error saving bot settings: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/sync-notification', methods=['POST'])
def api_sync_notification():
    """Receive notifications when admin panel settings are changed"""
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        change_type = data.get('change_type')  # 'settings_updated', 'event_updated', etc.
        admin_user_id = data.get('admin_user_id')

        if not event_id or not change_type:
            return jsonify({'success': False, 'message': 'event_id and change_type required'}), 400

        # Log the notification
        print(f"Sync notification received: event_id={event_id}, change_type={change_type}, admin_user_id={admin_user_id}")

        # Store notification in database for bot to process
        insert_query = """
            INSERT INTO sync_notifications (event_id, change_type, admin_user_id)
            VALUES (%s, %s, %s)
        """
        execute_query(insert_query, (event_id, change_type, admin_user_id))

        # Find all groups using this event_id and queue notifications
        groups_query = "SELECT group_id FROM groups_config WHERE event_id = %s AND is_active = TRUE"
        groups = execute_query(groups_query, (event_id,), fetch=True)

        if groups:
            print(f"Found {len(groups)} groups using event {event_id}, queuing notifications...")

            # Queue individual notifications for each group
            for group in groups:
                group_notification_query = """
                    INSERT INTO sync_notifications (event_id, change_type, admin_user_id)
                    VALUES (%s, %s, %s)
                """
                # Add group_id to change_type for group-specific processing
                group_change_type = f"{change_type}_group_{group['group_id']}"
                execute_query(group_notification_query, (event_id, group_change_type, admin_user_id))

        # Immediate database updates (synchronous operations)
        if change_type == 'settings_updated':
            # Refresh cached settings immediately in database
            print(f"Immediate database sync for event {event_id}")

        return jsonify({
            'success': True,
            'message': f'Sync notification processed for {change_type}',
            'event_id': event_id,
            'groups_notified': len(groups) if 'groups' in locals() else 0
        }), 200
    except Exception as e:
        print(f"Error processing sync notification: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=False)
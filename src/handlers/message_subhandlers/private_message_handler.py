from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from datetime import datetime
import re
from ...services import database_service as db
from ...db import execute_query
from ...bot_utils import safe_send_message
from .utils import extract_license_key

logger = logging.getLogger(__name__)

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle private messages for user validation and KYC process."""
    try:
        message = update.message
        user_id = message.from_user.id
        text = message.text or ""

        logger.info(f"Received private message from user {user_id}: '{text}'")

        # Check if this user is already in a validation process
        user_state = context.user_data.get('kyc_state', {})

        if not user_state:
            # First message from user, ask if they have a unique user ID
            logger.info(f"New user {user_id} - sending welcome message")
            await safe_send_message(
                context=context,
                chat_id=user_id,
                text="👋 **Welcome to the Wellness Bot!**\n\n"
                     "To join a wellness group, you need a unique user ID provided by the group admin.\n\n"
                     "❓ **Do you have a unique user ID?**\n\n"
                     "• If **YES**, please reply with your 6-digit user ID\n"
                     "• If **NO**, please contact your group admin to get one\n\n"
                     "💡 Example: `123456`",
                parse_mode="Markdown"
            )
            context.user_data['kyc_state'] = {'step': 'awaiting_user_id'}
            return

        # Handle different KYC steps
        current_step = user_state.get('step')
        logger.info(f"User {user_id} in step: {current_step}")

        if current_step == 'awaiting_user_id':
            # Validate the user ID
            if not text.strip().isdigit() or len(text.strip()) != 6:
                logger.warning(f"User {user_id} provided invalid user ID format: '{text}'")
                await safe_send_message(
                    context=context,
                    chat_id=user_id,
                    text="❌ **Invalid User ID Format**\n\n"
                         "Please provide a valid 6-digit user ID.\n"
                         "Example: `123456`\n\n"
                         "If you don't have a user ID, please contact your group admin.",
                    parse_mode="Markdown"
                )
                return

            user_id_input = text.strip()

            # Validate user ID exists and get group info
            from ..services.database_service import validate_unique_user_id
            validation = validate_unique_user_id(user_id_input)

            if not validation['valid']:
                await safe_send_message(
                    context=context,
                    chat_id=user_id,
                    text="❌ **Invalid User ID**\n\n"
                         "The user ID you provided is not valid or doesn't exist.\n\n"
                         "Please check with your group admin and try again.",
                    parse_mode="Markdown"
                )
                return

            if validation['used']:
                await safe_send_message(
                    context=context,
                    chat_id=user_id,
                    text="❌ **User ID Already Used**\n\n"
                         "This user ID has already been used by another member.\n\n"
                         "Please contact your group admin for a new user ID.",
                    parse_mode="Markdown"
                )
                return

            # User ID is valid, start KYC collection
            context.user_data['kyc_state'] = {
                'step': 'collecting_kyc',
                'user_id': user_id_input,
                'group_id': validation['group_id'],
                'kyc_data': {}
            }

            await safe_send_message(
                context=context,
                chat_id=user_id,
                text="✅ **User ID Validated!**\n\n"
                     "Now I need to collect some information for KYC verification.\n\n"
                     "📝 **Please provide your full name:**\n"
                     "(Example: John Doe)",
                parse_mode="Markdown"
            )
            context.user_data['kyc_state']['kyc_data']['telegram_user_id'] = user_id
            return

        elif current_step == 'collecting_kyc':
            kyc_data = user_state.get('kyc_data', {})

            # Step 1: Full Name
            if 'full_name' not in kyc_data:
                if not text.strip():
                    await safe_send_message(
                        context=context,
                        chat_id=user_id,
                        text="❌ **Invalid Name**\n\nPlease provide your full name.",
                        parse_mode="Markdown"
                    )
                    return

                kyc_data['full_name'] = text.strip()
                context.user_data['kyc_state']['kyc_data'] = kyc_data

                await safe_send_message(
                    context=context,
                    chat_id=user_id,
                    text="📅 **Please provide your date of birth:**\n"
                         "(Format: DD/MM/YYYY)\n"
                         "Example: `15/10/1990`",
                    parse_mode="Markdown"
                )
                return

            # Step 2: Date of Birth
            elif 'date_of_birth' not in kyc_data:
                text = text.strip()

                # Check basic format - accept DD/MM/YYYY, DD-MM-YYYY, DD/MM/YY, DD-MM-YY
                date_pattern = r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$'
                if not re.match(date_pattern, text):
                    await safe_send_message(
                        context=context,
                        chat_id=user_id,
                        text="❌ **Invalid Date Format**\n\n"
                             "Please use DD/MM/YYYY or DD-MM-YYYY format.\n"
                             "Examples: `15/10/1990` or `15-10-1990`",
                        parse_mode="Markdown"
                    )
                    return

                # Parse the date
                try:
                    parts = re.split(r'[-/]', text)
                    if len(parts) != 3:
                        raise ValueError("Invalid format")

                    day, month, year = map(int, parts)

                    # Handle 2-digit years
                    if year < 100:
                        if year > 25:  # Assume 19xx
                            year += 1900
                        else:  # Assume 20xx
                            year += 2000

                    # Validate ranges
                    if not (1 <= day <= 31):
                        raise ValueError("Invalid day")
                    if not (1 <= month <= 12):
                        raise ValueError("Invalid month")
                    if not (1900 <= year <= 2010):  # Reasonable age range
                        raise ValueError("Invalid year")

                    # Validate day for month
                    days_in_month = [31, 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
                    if day > days_in_month[month - 1]:
                        raise ValueError("Invalid day for month")

                    # Additional validation: user should be at least 13 years old
                    today = datetime.now()
                    birth_date = datetime(year, month, day)
                    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

                    if age < 13:
                        await safe_send_message(
                            context=context,
                            chat_id=user_id,
                            text="❌ **Invalid Age**\n\n"
                                 "You must be at least 13 years old to use this service.",
                            parse_mode="Markdown"
                        )
                        return

                    # Store in DD/MM/YYYY format
                    formatted_date = f"{day:02d}/{month:02d}/{year}"
                    kyc_data['date_of_birth'] = formatted_date
                    context.user_data['kyc_state']['kyc_data'] = kyc_data

                    await safe_send_message(
                        context=context,
                        chat_id=user_id,
                        text="📱 **Please provide your phone number:**\n"
                             "(Include country code)\n"
                             "Example: `+91 9876543210`",
                        parse_mode="Markdown"
                    )
                    return

                except ValueError as e:
                    await safe_send_message(
                        context=context,
                        chat_id=user_id,
                        text="❌ **Invalid Date**\n\n"
                             "Please provide a valid date.\n"
                             "Examples: `15/10/1990` or `15-10-1990`",
                        parse_mode="Markdown"
                    )
                    return

            # Step 3: Phone Number
            elif 'phone_number' not in kyc_data:
                if not text.strip():
                    await safe_send_message(
                        context=context,
                        chat_id=user_id,
                        text="❌ **Invalid Phone Number**\n\nPlease provide your phone number.",
                        parse_mode="Markdown"
                    )
                    return

                kyc_data['phone_number'] = text.strip()
                context.user_data['kyc_state']['kyc_data'] = kyc_data

                await safe_send_message(
                    context=context,
                    chat_id=user_id,
                    text="🖼️ **Please send your profile picture:**\n\n"
                         "Upload a clear photo of yourself.",
                    parse_mode="Markdown"
                )
                return

            # Step 4: Profile Picture
            elif 'profile_picture_file_id' not in kyc_data:
                if not message.photo:
                    await safe_send_message(
                        context=context,
                        chat_id=user_id,
                        text="❌ **Profile Picture Required**\n\n"
                             "Please send a photo of yourself.",
                        parse_mode="Markdown"
                    )
                    return

                # Get the highest quality photo
                photo = message.photo[-1]
                file_id = photo.file_id
                kyc_data['profile_picture_file_id'] = file_id
                context.user_data['kyc_state']['kyc_data'] = kyc_data

                await safe_send_message(
                    context=context,
                    chat_id=user_id,
                    text="🎂 **Please provide your age:**\n"
                         "(Just the number)\n"
                         "Example: `25`",
                    parse_mode="Markdown"
                )
                return

            # Step 5: Age
            elif 'age' not in kyc_data:
                if not text.strip().isdigit():
                    await safe_send_message(
                        context=context,
                        chat_id=user_id,
                        text="❌ **Invalid Age**\n\nPlease provide a valid number for your age.",
                        parse_mode="Markdown"
                    )
                    return

                kyc_data['age'] = int(text.strip())
                context.user_data['kyc_state']['kyc_data'] = kyc_data

                keyboard = [
                    ["Male", "Female"],
                    ["Other", "Prefer not to say"]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

                await safe_send_message(
                    context=context,
                    chat_id=user_id,
                    text="🚹🚺 **Please select your gender:**",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
                return

            # Step 6: Gender
            elif 'gender' not in kyc_data:
                valid_genders = ["Male", "Female", "Other", "Prefer not to say"]
                if text.strip() not in valid_genders:
                    await safe_send_message(
                        context=context,
                        chat_id=user_id,
                        text="❌ **Invalid Gender Selection**\n\nPlease select from the options provided.",
                        parse_mode="Markdown"
                    )
                    return

                kyc_data['gender'] = text.strip()
                context.user_data['kyc_state']['kyc_data'] = kyc_data

                await complete_kyc_process(update, context)
                return

        # Fallback for unexpected inputs
        await safe_send_message(
            context=context,
            chat_id=user_id,
            text="🤔 **I'm not sure what you mean.**\n\n"
                 "If you have a unique user ID, please provide it.\n"
                 "Otherwise, contact your group admin.",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error in handle_private_message: {e}", exc_info=True)
        try:
            await safe_send_message(
                context=context,
                chat_id=user_id,
                text="❌ **Internal Error**\n\nThere was an error processing your request. Please try again later.",
                parse_mode="Markdown"
            )
        except Exception:
            logger.exception("Failed to notify user about internal error")


async def complete_kyc_process(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Complete the KYC process and provide group invitation link."""
    user_id = update.message.from_user.id
    user_state = context.user_data.get('kyc_state', {})
    kyc_data = user_state.get('kyc_data', {})
    group_id = user_state.get('group_id')
    unique_user_id = user_state.get('user_id')

    try:
        # Assign the unique user ID to this member
        from ..services.database_service import assign_unique_user_id_to_member
        success = assign_unique_user_id_to_member(group_id, user_id, unique_user_id)

        if not success:
            await safe_send_message(
                context=context,
                chat_id=user_id,
                text="❌ **Error Completing Registration**\n\n"
                "There was an issue with your registration. Please contact support.",
                parse_mode="Markdown"
            )
            return

        # Store KYC data in database
        try:
            # Convert date from DD/MM/YYYY to YYYY-MM-DD
            date_str = kyc_data['date_of_birth']
            day, month, year = map(int, date_str.split('/'))
            mysql_date = f"{year:04d}-{month:02d}-{day:02d}"

            kyc_query = """
                INSERT INTO kyc_data
                (user_id, group_id, unique_user_id, full_name, date_of_birth, phone_number, profile_picture_file_id, age, gender)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            execute_query(kyc_query, (
                user_id,
                group_id,
                unique_user_id,
                kyc_data['full_name'],
                mysql_date,  # Use converted date format
                kyc_data['phone_number'],
                kyc_data.get('profile_picture_file_id'),
                kyc_data['age'],
                kyc_data['gender']
            ))
        except Exception as kyc_error:
            logger.error(f"Error storing KYC data: {kyc_error}")
            # Don't fail the entire process for KYC storage error

        # Get group invite link
        try:
            chat = await context.bot.get_chat(group_id)
            if chat.invite_link:
                invite_link = chat.invite_link
            else:
                # Create a new invite link
                invite_link_obj = await context.bot.create_chat_invite_link(
                    chat_id=group_id,
                    name=f"Welcome - {kyc_data.get('full_name', 'New Member')}",
                    creates_join_request=False
                )
                invite_link = invite_link_obj.invite_link
        except Exception as e:
            logger.error(f"Error getting/creating invite link: {e}")
            await safe_send_message(
                context=context,
                chat_id=user_id,
                text="❌ **Error Getting Group Link**\n\n"
                "There was an issue generating your group invitation link. Please contact the group admin.",
                parse_mode="Markdown"
            )
            return

        # Send success message with group link
        success_message = (
            "🎉 <b>KYC Verification Complete!</b>\n\n"
            f"✅ <b>Welcome {kyc_data.get('full_name', 'New Member')}!</b>\n\n"
            "Your registration has been completed successfully.\n\n"
            "🔗 <b>Click below to join your wellness group:</b>\n\n"
            f"{invite_link}\n\n"
            "📋 <b>Your Details:</b>\n"
            f"• Name: {kyc_data.get('full_name')}\n"
            f"• Age: {kyc_data.get('age')}\n"
            f"• User ID: {unique_user_id}\n\n"
            "💪 <b>Get ready for an amazing wellness journey!</b>"
        )

        await safe_send_message(
            context=context,
            chat_id=user_id,
            text=success_message,
            parse_mode="HTML"
        )

        # Clear user state
        context.user_data.clear()

        logger.info(f"User {user_id} completed KYC and was assigned user ID {unique_user_id} for group {group_id}")

    except Exception as e:
        logger.error(f"Error completing KYC process: {e}")
        await safe_send_message(
            context=context,
            chat_id=user_id,
            text="❌ **Error Completing Registration**\n\n"
            "There was an issue with your registration. Please try again or contact support.",
            parse_mode="Markdown"
        )


async def handle_license_key(message, context, license_key):
    """Handle license key activation"""
    try:
        # Check if license is being sent in a group/supergroup
        if message.chat.type not in ["group", "supergroup"]:
            await safe_send_message(
                context=context,
                chat_id=message.chat.id,
                text="❌ **Invalid Chat Type**\n\nLicense keys must be sent in the group chat where the bot is installed, not in private messages.\n\nPlease send the license key in your group chat.",
                parse_mode="Markdown"
            )
            return

        # Check if license key exists and is available
        license_query = "SELECT license_key, assigned_group_id, is_active FROM licenses WHERE license_key = %s"
        license_result = execute_query(license_query, (license_key,), fetch=True)

        if not license_result:
            await safe_send_message(
                context=context,
                chat_id=message.chat.id,
                text=f"❌ **Invalid License Key**\n\nThe license key `{license_key}` is not valid.\n\nPlease check the key from your admin panel and try again.",
                parse_mode="Markdown"
            )
            return

        license_data = license_result[0]

        if license_data['assigned_group_id'] is not None and license_data['assigned_group_id'] != 0:
            await safe_send_message(
                context=context,
                chat_id=message.chat.id,
                text=f"❌ **License Key Already Used**\n\nThe license key `{license_key}` has already been assigned to another group.\n\nPlease get a new license key from your admin panel.",
                parse_mode="Markdown"
            )
            return

        if not license_data['is_active']:
            await safe_send_message(
                context=context,
                chat_id=message.chat.id,
                text=f"❌ **License Key Inactive**\n\nThe license key `{license_key}` is inactive.\n\nPlease contact support or get a new license key.",
                parse_mode="Markdown"
            )
            return

        # License is valid, assign it to the current group
        actual_group_id = message.chat.id  # Actual Telegram group ID for API calls
        db_group_id = actual_group_id  # Use the actual group ID for database operations

        # Get admin_user_id from groups_config
        admin_query = "SELECT admin_user_id FROM groups_config WHERE group_id = %s"
        admin_result = execute_query(admin_query, (db_group_id,), fetch=True)
        admin_user_id = admin_result[0]['admin_user_id'] if admin_result else None

        # Update the license with group and admin assignment
        update_query = "UPDATE licenses SET assigned_group_id = %s, assigned_admin_id = %s WHERE license_key = %s"
        execute_query(update_query, (db_group_id, admin_user_id, license_key))

        # Update group config with license key
        config_query = "UPDATE groups_config SET license_key = %s WHERE group_id = %s"
        execute_query(config_query, (license_key, db_group_id))

        # Check if bot has admin permissions in this group
        has_admin_permissions = False
        try:
            bot_member = await context.bot.get_chat_member(actual_group_id, context.bot.id)
            has_admin_permissions = bot_member.status in ["administrator", "creator"]

            # Update admin permissions status in database
            admin_update_query = "UPDATE groups_config SET has_admin_permissions = %s WHERE group_id = %s"
            execute_query(admin_update_query, (has_admin_permissions, db_group_id))

            logger.info(f"Bot admin permissions verified for group {actual_group_id}: {has_admin_permissions}")
        except Exception as e:
            logger.warning(f"Could not verify bot admin permissions for group {actual_group_id}: {e}")
            # Don't fail the activation if we can't check permissions

        logger.info(f"License key {license_key} assigned to group {db_group_id} (Telegram ID: {actual_group_id})")

        # Send success message
        admin_status_text = "✅ Admin permissions verified!" if has_admin_permissions else "⚠️ Please ensure I have admin permissions for full functionality."

        await safe_send_message(
            context=context,
            chat_id=message.chat.id,
            text=f"🎉 **License Activated Successfully!**\n\n"
            f"✅ License Key: `{license_key}`\n"
            f"{admin_status_text}\n\n"
            f"Your wellness bot is now activated!\n\n"
            f"🚀 **Features Now Available:**\n"
            f"• Automatic point tracking\n"
            f"• Time slot management\n"
            f"• Leaderboard system\n"
            f"• Content moderation\n"
            f"• Member management\n\n"
            f"💡 **Next Steps:**\n"
            f"• Set up your wellness slots in the admin panel\n"
            f"• Configure banned words and bot responses\n"
            f"• Generate unique user IDs for your members\n"
            f"• Share the bot link and user IDs with potential members",
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error handling license key {license_key}: {e}", exc_info=True)
        await safe_send_message(
            context=context,
            chat_id=message.chat.id,
            text="❌ **Error Activating License**\n\nThere was an error activating your license. Please try again or contact support.",
            parse_mode="Markdown"
        )
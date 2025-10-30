from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions, ReplyKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes
import logging
from datetime import datetime, timedelta
import re
from pytz import timezone, utc
from ..services import database_service as db
from ..services.file_storage import FileStorage
from .. import config
from .start_handler import points, schedule
from ..db import execute_query
from ..bot_utils import safe_send_message

logger = logging.getLogger(__name__)
storage = FileStorage(config.STORAGE_PATH)
ist=timezone("Asia/Kolkata")

def sanitize_text(text):
    """Remove HTML tags and URLs from text."""
    if not text: return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Remove URLs
    text = re.sub(r"http[s]?://\S+", "", text)
    return text.strip()


def extract_license_key(text):
    """Extract license key from message text. Format: WLB-xxxx-xxxx-xxxx-xxxx"""
    if not text:
        return None
    
    # Look for WLB-xxxx-xxxx-xxxx-xxxx pattern
    pattern = r'WLB-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}'
    match = re.search(pattern, text.upper())
    return match.group(0) if match else None


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
                import re
                from datetime import datetime

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

        if license_data['assigned_group_id'] is not None:
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
        group_id = message.chat.id

        # Update the license with group assignment
        update_query = "UPDATE licenses SET assigned_group_id = %s WHERE license_key = %s"
        execute_query(update_query, (group_id, license_key))

        # Update group config with license key
        config_query = "UPDATE groups_config SET license_key = %s WHERE group_id = %s"
        execute_query(config_query, (license_key, group_id))

        # Check if bot has admin permissions in this group
        has_admin_permissions = False
        try:
            bot_member = await context.bot.get_chat_member(group_id, context.bot.id)
            has_admin_permissions = bot_member.status in ["administrator", "creator"]
            
            # Update admin permissions status in database
            admin_update_query = "UPDATE groups_config SET has_admin_permissions = %s WHERE group_id = %s"
            execute_query(admin_update_query, (has_admin_permissions, group_id))
            
            logger.info(f"Bot admin permissions verified for group {group_id}: {has_admin_permissions}")
        except Exception as e:
            logger.warning(f"Could not verify bot admin permissions for group {group_id}: {e}")
            # Don't fail the activation if we can't check permissions

        logger.info(f"License key {license_key} assigned to group {group_id}")

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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages in groups and private chats."""
    message = update.message

    # Handle private messages for user validation/KYC process
    if message.chat.type == "private":
        await handle_private_message(update, context)
        return

    # Check if bot was added to a group
    if message.new_chat_members:
        for member in message.new_chat_members:
            if member.id == context.bot.id:
                # Bot was added to this group
                logger.info(f"Bot added to group {message.chat.id} via message handler")
                from .join_handler import handle_bot_added_to_group
                await handle_bot_added_to_group(update, context)
                return

    # Check for license key in any chat (private or group)
    if message.text:
        license_key = extract_license_key(message.text)
        if license_key:
            await handle_license_key(message, context, license_key)
            return

    # Only handle group messages for the rest
    if message.chat.type not in ["group", "supergroup"]:
        return

    group_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    if message.text and message.text in ["My Score 💯", "Time Sheet 📅"]:
        if message.text == "My Score 💯": await points(update, context)
        elif message.text == "Time Sheet 📅": await schedule(update, context)
        return

    # Check if group is configured
    group_config = db.get_group_config(group_id)
    if not group_config:
        logger.warning(f"Group {group_id} not configured yet")
        return

    # Ensure member exists in database
    member, is_new = db.add_member(group_id, user_id, username, first_name, restrict_new=False)

    # Update member activity
    db.update_member_activity(group_id, user_id)

    # Check if user is admin first - admins are NEVER restricted and EXEMPT from all penalties
    member = db.get_member(group_id, user_id)
    
    if member and member.get("is_restricted") and member.get("restriction_until"):
        restriction_until_utc = member.get("restriction_until")  # Fetch raw datetime from DB (likely naive UTC)

        # Ensure it's a datetime object (if stored as string somehow, convert)
        if isinstance(restriction_until_utc, str):
            try:
                # Assuming the string format from DB is standard UTC
                restriction_until_utc = datetime.strptime(restriction_until_utc, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logger.error(f"Could not parse restriction_until string: {restriction_until_utc}")
                # Handle error appropriately, maybe skip restriction check
                restriction_until_utc = None

        if restriction_until_utc:
            # 1. Make the naive UTC datetime timezone-aware
            restriction_until_utc_aware = utc.localize(restriction_until_utc)

            # 2. Convert aware UTC time to aware IST time
            restriction_until_ist_aware = restriction_until_utc_aware.astimezone(ist)

            # 3. Get current time in IST (already aware)
            now_ist_aware = datetime.now(ist)

            # 4. Compare aware datetimes
            if now_ist_aware > restriction_until_ist_aware:
                start_date = now_ist_aware.date()  # Use the current IST date
                end_date = start_date + timedelta(days=7)
                # Restriction has expired, update the database
                query = "UPDATE group_members SET is_restricted = 0, restriction_until = NULL, cycle_start_date = %s, cycle_end_date = %s WHERE group_id = %s AND user_id = %s"
                execute_query(query, (start_date, end_date, group_id, user_id))
                # Refresh member data
                member = db.get_member(group_id, user_id)
                logger.info(f"Lifted expired restriction for user {user_id} in group {group_id}.")
            else:
                logger.info(f"User {user_id} was manually unrestricted by an admin. Syncing database.")
                start_date = now_ist_aware.date()
                end_date = start_date + timedelta(days=7)
                query = "UPDATE group_members SET is_restricted = 0, restriction_until = NULL, cycle_start_date = %s, cycle_end_date = %s WHERE group_id = %s AND user_id = %s"
                execute_query(query, (start_date, end_date, group_id, user_id))
                # Refresh member data so the rest of the function works
                member = db.get_member(group_id, user_id)

    # Also check if user is currently a Telegram admin/creator
    is_telegram_admin = member and member.get("is_admin", 0) == 1

    # Send welcome if new member
    if is_new:
        welcome_message = group_config.get("welcome_message", "Welcome!")
        welcome_text = f"Hi {first_name}, {welcome_message}"

        restriction_until_str = member.get("restriction_until")
        if (member.get("is_restricted") and restriction_until_str and not is_telegram_admin):
            if isinstance(restriction_until_str, str):
                restriction_until_dt = datetime.strptime(restriction_until_str, "%Y-%m-%d %H:%M:%S")
            else:
                restriction_until_dt = restriction_until_str

        if is_telegram_admin:
            welcome_text += "\n\nAs an admin, you have full access immediately! 💼"

        await safe_send_message(context=context, chat_id=group_id, text=welcome_text)

    # Check database admin
    is_db_admin = group_config and group_config.get("admin_user_id") == user_id

    # User is admin if they're either Telegram admin OR database admin
    is_admin = is_telegram_admin or is_db_admin

    # If user is admin but was restricted, unrestrict them immediately
    if is_admin and member and member.get("is_restricted", 0) == 1:
        try:
            chat_member = await context.bot.get_chat_member(group_id, user_id)
        
            # Only try to change admin permissions if the user is not the creator
            if chat_member.status != 'creator':
                await context.bot.restrict_chat_member(
                    chat_id=group_id,
                    user_id=user_id,
                    permissions=ChatPermissions(can_send_messages=True, can_send_other_messages=True)
                )

            # Update database
            query = "UPDATE group_members SET is_restricted = 0, restriction_until = NULL WHERE group_id = %s AND user_id = %s"
            execute_query(query, (group_id, user_id))

            logger.info(f"Admin {user_id} was restricted but has now been unrestricted in group {group_id}")
        except Exception as e:
            logger.error(f"Error unrestricting admin: {e}",exc_info=True)

    # Check for banned words FIRST - ALWAYS ban on 2 warnings regardless of points (EXCEPT ADMINS)
    if message.text and not is_admin:
        custom_banned = db.get_banned_words(group_id)

        if not custom_banned: logger.warning(f"No banned words found for group {group_id}. Check database!")

        message_text_lower = message.text.lower()

        # Check if ANY banned word appears in the message with word boundaries
        matched_word = None
        for banned_word in custom_banned:
            # Use word boundaries for single words, substring for phrases
            if " " in banned_word:
                # Multi-word phrases: substring match
                if banned_word.lower() in message_text_lower:
                    matched_word = banned_word
                    logger.warning(f"BANNED PHRASE MATCH: '{banned_word}' found in '{message.text[:50]}'")
                    break
            else:
                pattern = r"\b" + re.escape(banned_word.lower()) + r"\b"
                if re.search(pattern, message_text_lower):
                    matched_word = banned_word
                    logger.warning(f"BANNED WORD MATCH: '{banned_word}' found in '{message.text[:50]}'")
                    break

        if matched_word:
            try:
                await message.delete()
                db.add_banned_words_warning(group_id, user_id)

                # Deduct 10 knockout points for banned word
                db.deduct_knockout_points(group_id, user_id, 10)

                member = db.get_member(group_id, user_id)
                warnings = member["banned_word_count"] if member else 1
                total_points = member["total_points"] if member else 0

                warning_msg = await safe_send_message(
                    context=context, 
                    chat_id=group_id,
                    text=f"⚠️ {first_name}, please avoid using inappropriate language!\n"
                    f"Warning {warnings}/2. Using banned word: '{matched_word}'\n",
                )

                context.job_queue.run_once(lambda _: warning_msg.delete(), when=5)

                if warnings >= 2:
                    try:
                        until_date = datetime.now(ist) + timedelta(minutes=1)

                        await context.bot.ban_chat_member(group_id, user_id, until_date=until_date)

                        db.remove_member(group_id, user_id, "kicked")
                        logger.warning(f"User {user_id} record has been DELETED from the database.")
                        
                        await context.bot.unban_chat_member(group_id, user_id)

                        if total_points >= 100:
                            kick_msg = (
                                f"👋 {first_name} earned {total_points} points but has been REMOVED from the group.\n"
                                f"Reason: 2 warnings for using banned words.\n"
                            )
                        else:
                            kick_msg = (
                                f"🚫 {first_name} has been REMOVED from the group.\n"
                                f"Reason: 2 warnings for using banned words.\n"
                            )

                        await safe_send_message(context=context, chat_id=group_id, text=kick_msg)
                        logger.warning(f"User {user_id} ({first_name}) kicked for 2 banned word violations")

                    except Exception as ban_error:
                        logger.error(f"Failed to apply 24-hour ban for user {user_id}: {ban_error}")
                        await safe_send_message(
                            context=context, 
                            chat_id=group_id,
                            text=f"⚠️ Could not ban {first_name}. Please check my admin permissions.",
                        )

                logger.warning(f"Banned word detected from user {user_id}: {matched_word}")
                return

            except Exception as e:
                logger.error(f"Error handling banned word: {e}",exc_info=True)

    # Get active slot
    active_slot = db.get_active_slot(group_id)

    if not active_slot:
        # No active slot - delete message, warn, and deduct knockout points
        try:
            await message.delete()
            db.add_general_warning(group_id, user_id)

            # Deduct 5 knockout points for posting outside slot
            db.deduct_knockout_points(group_id, user_id, 5)

            warning_msg = await safe_send_message(
                context=context, 
                chat_id=group_id,
                text=f"⏰ {first_name}, no active slot right now!\n"
                f"Please only post during designated time slots.\n",
            )

            # Delete warning after 10 seconds
            context.job_queue.run_once(lambda _: warning_msg.delete(), when=10)
            logger.info(f"Message outside slot from user {user_id} - knockout points deducted")
            return

        except Exception as e:
            logger.error(f"Error deleting message: {e}",exc_info=True)
            return

    # Handle message based on slot type and content
    slot_id = active_slot["slot_id"]
    slot_name = active_slot["slot_name"]
    slot_type = active_slot["slot_type"]

    # Get active event
    event = db.get_active_event(group_id)
    event_id = event["event_id"] if event else None

    # Check if already completed today
    if event_id and db.check_slot_completed_today(event_id, slot_id, user_id):
        try:
            # If it's a duplicate, delete the message and inform the user.
            await message.delete()
            info_msg = await safe_send_message(
                context=context,
                chat_id=group_id,
                text=f"✅ {first_name}, you've already completed this slot today!",
            )
            
            async def delete_info_msg(context):
                if info_msg:
                    await info_msg.delete()
            context.job_queue.run_once(delete_info_msg,when=5)
            return
        except Exception as e:
            logger.error(f"Error handling duplicate submission: {e}", exc_info=True)
            return
        
    if slot_type == "button":
        try:
            await message.delete()
            warning_msg = await safe_send_message(
                context=context,
                chat_id=group_id,
                text=f"⏰ {first_name}, please use the buttons for the {slot_name} slot!\n"
                     f"Messages are not accepted right now.",
            )
            # Delete warning after 10 seconds
            context.job_queue.run_once(lambda _: warning_msg.delete(), when=10)
            logger.info(f"Deleted invalid message from user {user_id} during button slot {slot_name}")
            return  # Stop all further processing
        except Exception as e:
            logger.error(f"Error deleting message during button slot: {e}", exc_info=True)
            return
        
    # Accept ANY media type for regular slots except button typed
    if message.photo:
        await handle_photo_response(update, context, active_slot, event_id)

    elif message.text:
        await handle_text_response(update, context, active_slot, event_id)

    elif (message.video or message.document or message.sticker or message.animation or message.voice or message.video_note):
        # Other media types - ask for confirmation
        await handle_other_media_response(update, context, active_slot, event_id)

    else:
        # Unknown content type
        logger.warning(f"Unknown message type from user {user_id} in group {group_id}")


async def handle_text_response(update: Update, context: ContextTypes.DEFAULT_TYPE, slot: dict, event_id: int):
    """Handle text message for a slot."""
    message = update.message
    group_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    username = message.from_user.username or ""
    last_name = message.from_user.last_name or ""
    text = sanitize_text(message.text)
    display_name=username or first_name or "You"

    slot_id = slot["slot_id"]
    slot_name = slot["slot_name"]

    keywords = db.get_slot_keywords(slot_id)
    text_lower = text.lower()
    keyword_match = any(keyword.lower() in text_lower for keyword in keywords)

    if keyword_match:
        points = slot["slot_points"]
        
        db.add_points(group_id, user_id, points, event_id)
        db.log_activity(group_id=group_id, user_id=user_id, activity_type="text", slot_name=slot_name,
                        username=username, first_name=first_name, last_name=last_name, message_content=text,
                        points_earned=points)

        await message.reply_text(f'✅ {display_name} scored {points} points!')
        logger.info(f"User {user_id} completed slot {slot_name} with text")

    else:
        keyboard = [
            [InlineKeyboardButton("✅ Yes", callback_data=f"confirm_yes_{slot_id}_{user_id}_{message.message_id}"),
             InlineKeyboardButton("❌ No", callback_data=f"confirm_no_{slot_id}_{user_id}_{message.message_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        confirmation_msg = await message.reply_text(slot["response_clarify"], reply_markup=reply_markup)

        if "pending_confirmations" not in context.bot_data:
            context.bot_data["pending_confirmations"] = {}

        context.bot_data["pending_confirmations"][confirmation_msg.message_id] = {
            "user_id": user_id, "username": username, "first_name": first_name, "last_name": last_name,
            "slot_id": slot_id, "slot_name": slot_name, "event_id": event_id, "group_id": group_id,
            "original_message_id": message.message_id, "text": text, "points": slot["slot_points"], "type": "text"
        }

        context.job_queue.run_once(
            auto_reject_confirmation,
            when=config.CONFIRMATION_TIMEOUT,
            data={"confirmation_msg_id": confirmation_msg.message_id},
        )

async def handle_photo_response(update: Update, context: ContextTypes.DEFAULT_TYPE, slot: dict, event_id: int):
    """Handle photo message for a slot."""
    message = update.message
    group_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    username = message.from_user.username or ""
    last_name=message.from_user.last_name or ""
    display_name= username or first_name or "You"

    slot_id = slot["slot_id"]
    slot_name = slot["slot_name"]

    # Get the largest photo
    photo = message.photo[-1]
    file_id = photo.file_id

    # Check if photo has a caption with keyword match
    caption = message.caption if message.caption else ""
    keywords = db.get_slot_keywords(slot_id)

    caption_lower = caption.lower()
    keyword_match = (
        any(keyword.lower() in caption_lower for keyword in keywords)
        if keywords and caption
        else False
    )

    if keyword_match or not keywords:
        # Direct match OR no keywords defined (all photos accepted) - award points
        try:
            # Download and save photo
            file = await context.bot.get_file(file_id)

            # Create formatted filename: {username}_{slotname}_{YYYY_MM_DD_HH_MM_SS_am/pm}.jpg
            timestamp = datetime.now(ist).strftime("%Y_%m_%d_%I_%M_%S_%p").lower()
            filename = f"{username}_{slot_name}_{timestamp}.jpg"

            # Save file with new structure
            local_path = await storage.save_photo(group_id, user_id, username, slot_name, file, filename)

            # Award points
            points = slot["slot_points"]
            db.add_points(group_id=group_id, user_id=user_id, points=points, event_id=event_id)
            db.log_activity(group_id=group_id, user_id=user_id, slot_name=slot_name, username=username,
                            first_name=first_name, last_name=last_name, activity_type="photo", 
                            telegram_file_id=file_id, local_file_path=local_path, points_earned=points,
                            )

            if event_id:
                db.mark_slot_completed(group_id=group_id, event_id=event_id, slot_id=slot_id, user_id=user_id, status="completed", points=points)

            await message.reply_text(f'✅ {display_name} scored {points} points!')
            logger.info(f"User {user_id} completed slot {slot_name} with photo")

        except Exception as e:
            logger.error(f"Error handling photo: {e}",exc_info=True)
            await message.reply_text("Sorry, there was an error processing your photo. Please try again.")

    else:
        # Keywords exist but no match - ask for confirmation
        keyboard = [
            [InlineKeyboardButton("✅ Yes", callback_data=f"confirm_yes_{slot_id}_{user_id}_{message.message_id}"),
             InlineKeyboardButton("❌ No", callback_data=f"confirm_no_{slot_id}_{user_id}_{message.message_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        confirmation_msg = await message.reply_text(slot["response_clarify"], reply_markup=reply_markup)

        # Store confirmation data in context
        if "pending_confirmations" not in context.bot_data:
            context.bot_data["pending_confirmations"] = {}

        context.bot_data["pending_confirmations"][confirmation_msg.message_id] = {
            "user_id": user_id, "first_name": first_name, "last_name": last_name, "slot_id": slot_id,
            "slot_name": slot_name, "event_id": event_id, "group_id": group_id, "original_message_id": message.message_id,
            "photo_file_id": file_id, "username": username, "caption": caption, "points": slot["slot_points"],
            "type": "photo",
        }

        # Auto-select "No" after timeout
        context.job_queue.run_once(
            auto_reject_confirmation,
            when=config.CONFIRMATION_TIMEOUT,
            data={"confirmation_msg_id": confirmation_msg.message_id},
        )


async def handle_other_media_response(
    update: Update, context: ContextTypes.DEFAULT_TYPE, slot: dict, event_id: int
):
    """Handle other media types (video, sticker, document, etc.) for a photo slot."""
    message = update.message
    group_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name or ""
    username = message.from_user.username or ""
    last_name=message.from_user.last_name or ""

    slot_id = slot["slot_id"]
    slot_name = slot["slot_name"]

    # Determine media type and file extension
    media_type = None
    file_id = None
    file_ext = None

    if message.video:
        media_type = "video"
        file_id = message.video.file_id
        file_ext = "mp4"
    elif message.document:
        media_type = "document"
        file_id = message.document.file_id
        # Get original filename extension if available
        if message.document.file_name:
            file_ext = (message.document.file_name.split(".")[-1] if "." in message.document.file_name else "file")
        else:
            file_ext = "file"
    elif message.sticker:
        media_type = "sticker"
        file_id = message.sticker.file_id
        file_ext = "webp"
    elif message.animation:
        media_type = "animation"
        file_id = message.animation.file_id
        file_ext = "gif"
    elif message.voice:
        media_type = "voice"
        file_id = message.voice.file_id
        file_ext = "ogg"
    elif message.video_note:
        media_type = "video_note"
        file_id = message.video_note.file_id
        file_ext = "mp4"

    # Determine points based on media type
    if media_type in ["video", "document", "voice", "video_note", "sticker", "animation"]: points = slot["slot_points"]
    else: points = slot["slot_points"]

    keyboard = [
        [InlineKeyboardButton("✅ Yes", callback_data=f"confirm_yes_{slot_id}_{user_id}_{message.message_id}"),
         InlineKeyboardButton("❌ No", callback_data=f"confirm_no_{slot_id}_{user_id}_{message.message_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # points_msg = f" ({points} points)" if points > 0 else " (no points)"
    confirmation_msg = await message.reply_text(f"{first_name}, Is this your {slot_name} ?", reply_markup=reply_markup)

    # Store confirmation data in context
    if "pending_confirmations" not in context.bot_data:
        context.bot_data["pending_confirmations"] = {}

    context.bot_data["pending_confirmations"][confirmation_msg.message_id] = {
        "user_id": user_id, "first_name": first_name, "last_name": last_name, "slot_id": slot_id,
        "slot_name": slot_name, "event_id": event_id, "group_id": group_id, "original_message_id": message.message_id,
        "file_id": file_id, "username": username, "caption": message.caption if message.caption else "",
        "points": points, "type": "media", "media_type": media_type, "file_ext": file_ext,
    }

    # Auto-select "No" after timeout
    context.job_queue.run_once(
        auto_reject_confirmation,
        when=config.CONFIRMATION_TIMEOUT,
        data={"confirmation_msg_id": confirmation_msg.message_id},
    )


async def auto_reject_confirmation(context: ContextTypes.DEFAULT_TYPE):
    """Auto-rejects confirmation for a user after timeout."""
    job = context.job
    confirmation_msg_id = job.data["confirmation_msg_id"]

    if "pending_confirmations" in context.bot_data:
        if confirmation_msg_id in context.bot_data["pending_confirmations"]:
            data = context.bot_data["pending_confirmations"][confirmation_msg_id]

            if data:
                try:
                    # Deletes the user's original message that was rejected
                    original_message_id = data.get("original_message_id")
                    if original_message_id:
                        await context.bot.delete_message(chat_id=data["group_id"], message_id=original_message_id)
                        logger.info(f"Deleted timed-out message {original_message_id}")

                    await context.bot.edit_message_text(
                        chat_id=data["group_id"],
                        message_id=confirmation_msg_id,
                        text="⏱️ Timeout didn't get a confirmation!",
                    )

                    # Deletes the "Timeout" message itself after 3 seconds
                    context.job_queue.run_once(
                        lambda ctx: context.bot.delete_message(data["group_id"], confirmation_msg_id),when=5)

                    # Logs that the activity was invalid
                    db.log_activity(group_id=data["group_id"], user_id=data["user_id"], username=data["username"],
                                    first_name=data["first_name"], last_name=data["last_name"], 
                                    slot_name=data["slot_name"], activity_type=data.get("type", "text"),
                                    message_content=data.get("text", ""), points_earned=0, is_valid=False)

                except Exception as e:
                    logger.error(f"Error in auto-reject: {e}",exc_info=True)


# Create message handlers
text_message_handler = MessageHandler((filters.TEXT & ~filters.COMMAND) | filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_message)
photo_message_handler = MessageHandler(filters.PHOTO, handle_message)
video_message_handler = MessageHandler(filters.VIDEO, handle_message)
document_message_handler = MessageHandler(filters.Document.ALL, handle_message)
sticker_message_handler = MessageHandler(filters.Sticker.ALL, handle_message)
animation_message_handler = MessageHandler(filters.ANIMATION, handle_message)
voice_message_handler = MessageHandler(filters.VOICE, handle_message)
video_note_message_handler = MessageHandler(filters.VIDEO_NOTE, handle_message)
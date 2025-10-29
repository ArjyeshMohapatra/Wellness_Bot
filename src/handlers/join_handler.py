from telegram import Update, ReplyKeyboardMarkup, ChatPermissions
from telegram.ext import ChatMemberHandler, ContextTypes
import logging
import time
from datetime import datetime, timedelta
from pytz import timezone
from ..bot_utils import safe_send_message
from ..config import NEW_MEMBER_RESTRICTION_MINUTES
from ..services import database_service as db
from ..db import execute_query

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


async def track_chats(update, context):
    """Handles the bot being added to or removed from a group."""
    was_member, is_member = extract_status_change(update.chat_member)
    chat = update.effective_chat
    group_id = chat.id

    # Get old and new status
    old_status = update.chat_member.old_chat_member.status
    new_status = update.chat_member.new_chat_member.status

    logger.info(f"Bot status change in group {group_id}: {old_status} -> {new_status}")
    logger.info(f"Chat member update received: was_member={was_member}, is_member={is_member}")

    if not was_member and is_member:
        # Bot was added to group
        logger.info(f"Bot added to group {group_id} ({chat.title})")
        await handle_bot_added_to_group(update, context)

    elif was_member and is_member:
        # Bot was already in group, but status changed (e.g., promoted to admin)
        logger.info(f"Bot status changed in group {group_id}: checking for promotion")
        if (old_status not in ["administrator", "creator"] and 
            new_status in ["administrator", "creator"]):
            # Bot was promoted to admin
            logger.info(f"Bot promoted to admin in group {group_id} - calling handler")
            await handle_bot_promoted_to_admin(update, context)
        else:
            logger.info(f"Bot status changed but not a promotion: {old_status} -> {new_status}")

    elif was_member and not is_member:
        # Bot was removed from group
        logger.info(f"Bot removed from group {group_id}")


async def handle_bot_added_to_group(update, context):
    """Handle when bot is added to a group"""
    chat = update.effective_chat
    group_id = chat.id

    try:
        admins = await context.bot.get_chat_administrators(group_id)
        owner = next((admin for admin in admins if admin.status == "creator"), None)
        admin_user_id = (owner.user.id if owner else admins[0].user.id if admins else None)

        if admin_user_id:
            bot_member = await context.bot.get_chat_member(group_id, context.bot.id)

            # Always create a pending config when bot is added, regardless of admin status
            group_config = db.get_group_config(group_id)
            
            if not group_config:
                # Create pending config (no license yet)
                success = db.create_pending_group_config(group_id, admin_user_id)
                if success:
                    logger.info(f"Created pending config for group {group_id}")
                else:
                    logger.error(f"Failed to create pending config for group {group_id}")

            if bot_member.status in ["administrator", "creator"]:
                # Bot is already admin, check if we need to request license
                if group_config and not group_config.get('license_key'):
                    # Ask for license key
                    logger.info(f"Group {group_id} has config but no license - requesting license key")
                    await safe_send_message(
                        context=context,
                        chat_id=group_id,
                        text="🎉 **Admin Rights Granted!**\n\n"
                        "I'm now an administrator in this group!\n\n"
                        "🔑 **License Key Required**\n\n"
                        "To activate the full wellness tracking features, please provide a license key.\n\n"
                        "📋 **Please provide the license key:**\n"
                        "Send me the license key that you received from the admin panel.\n\n"
                        "💡 **Format:** WLB-xxxx-xxxx-xxxx-xxxx\n\n"
                        "Once you send the license key, I'll be fully activated!",
                        parse_mode="Markdown"
                    )
                elif not group_config:
                    # Config was just created, ask for license
                    logger.info(f"Created config for group {group_id}, now requesting license key")
                    await safe_send_message(
                        context=context,
                        chat_id=group_id,
                        text="🎉 **Welcome! I'm now managing this group!**\n\n"
                        "🔑 **License Key Required**\n\n"
                        "To activate the full wellness tracking features, please provide a license key.\n\n"
                        "📋 **Please provide the license key:**\n"
                        "Send me the license key that you received from the admin panel.\n\n"
                        "💡 **Format:** WLB-xxxx-xxxx-xxxx-xxxx\n\n"
                        "Once you send the license key, I'll be fully activated!",
                        parse_mode="Markdown"
                    )
                else:
                    # Group already has license
                    await safe_send_message(
                        context=context,
                        chat_id=group_id,
                        text="🎉 **Welcome back!**\n\n"
                        "I'm now active in this group again!\n"
                        "All wellness tracking features are available.",
                        parse_mode="Markdown"
                    )
            else:
                await safe_send_message(
                    context=context, 
                    chat_id=group_id,
                    text="⚠️ I need admin rights to function properly!\n"
                    "Please make me an admin first.",
                )
                logger.warning(f"Bot is not admin in group {group_id}", exc_info=True)

    except Exception as e:
        logger.error(f"Error setting up group {group_id}: {e}", exc_info=True)


async def handle_bot_promoted_to_admin(update, context):
    """Handle when bot is promoted to admin in a group"""
    chat = update.effective_chat
    group_id = chat.id

    logger.info(f"handle_bot_promoted_to_admin called for group {group_id}")

    try:
        # Check if group already has config
        group_config = db.get_group_config(group_id)
        logger.info(f"Group config for {group_id}: {group_config}")
        
        if group_config:
            # Group has config, ask for license key to allow admin to provide their own
            logger.info(f"Group {group_id} promoted to admin - requesting license key")
            
            await safe_send_message(
                context=context,
                chat_id=group_id,
                text="🎉 **Admin Rights Granted!**\n\n"
                "I'm now an administrator in this group!\n\n"
                "🔑 **License Key Required**\n\n"
                "To activate the full wellness tracking features, please provide a license key.\n\n"
                "📋 **Please provide the license key:**\n"
                "Send me the license key that you received from the admin panel.\n\n"
                "💡 **Format:** WLB-xxxx-xxxx-xxxx-xxxx\n\n"
                "Once you send the license key, I'll be fully activated!",
                parse_mode="Markdown"
            )
        else:
            # No config exists, create it and ask for license
            logger.warning(f"No config found for group {group_id} during promotion, creating config")
            success = db.create_group_config(group_id, update.effective_user.id if update.effective_user else None)
            logger.info(f"Config creation result: {success}")
            
            if success:
                await safe_send_message(
                    context=context,
                    chat_id=group_id,
                    text="🎉 **Admin Rights Granted!**\n\n"
                    "I'm now an administrator in this group!\n\n"
                    "🔑 **License Key Required**\n\n"
                    "To activate the full wellness tracking features, please provide a license key.\n\n"
                    "📋 **Please provide the license key:**\n"
                    "Send me the license key that you received from the admin panel.\n\n"
                    "💡 **Format:** WLB-xxxx-xxxx-xxxx-xxxx\n\n"
                    "Once you send the license key, I'll be fully activated!",
                    parse_mode="Markdown"
                )
            else:
                logger.error(f"Failed to create config for group {group_id} during promotion")

    except Exception as e:
        logger.error(f"Error handling bot promotion in group {group_id}: {e}", exc_info=True)


def extract_status_change(chat_member_update):
    """
    Treats creator/administrator/member as in-chat.
    Treats restricted as in-chat only if its is_member flag is True.
    Treats left/kicked as out-of-chat.
    """
    old = chat_member_update.old_chat_member
    new = chat_member_update.new_chat_member

    def in_chat(cm):
        st = cm.status  # 'creator','administrator','member','restricted','left','kicked'
        if st in ("creator", "administrator", "member"): return True
        if st == "restricted": return bool(getattr(cm, "is_member", False))
        return False  # left or kicked

    return in_chat(old), in_chat(new)


async def track_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles a real member join:
    - Ignores bots
    - Skips admins/creators for restriction
    - Adds/updates DB member record
    - Sends welcome
    - Applies temporary restriction until the stored restriction_until (IST) if required
    """
    was_member, is_member = extract_status_change(update.chat_member)
    
    user = update.chat_member.new_chat_member.user
    if user.is_bot: return
    
    chat = update.effective_chat
    group_id = chat.id
    user_id = user.id
    first_name = user.first_name or ""
    username = user.username or ""
    last_name= user.last_name or ""
    
    # if an existing member leaves or gets kicked
    if was_member and not is_member:
        action = update.chat_member.new_chat_member.status
        if action not in ['left', 'kicked', 'banned']: action = 'left' 

        logger.info(f"👤 Member {action}: {user_id} ({first_name} @{username}) from group {group_id}")

        db.remove_member(group_id, user_id, action)
        logger.info(f"Archived '{action}' member {user_id} in member_history.")
        return

    # if a new member joins so lets continue with rest of the function
    elif not was_member and is_member:
        # Check if user has a valid unique user ID before allowing them to join
        from ..services.database_service import get_member
        existing_member = get_member(group_id, user_id)

        # If user is not in database or doesn't have a unique_user_id assigned, kick them
        if not existing_member or not existing_member.get('unique_user_id') or existing_member.get('user_id') == 0:
            try:
                # Kick the user immediately
                await context.bot.ban_chat_member(
                    chat_id=group_id,
                    user_id=user_id,
                    revoke_messages=False
                )

                # Send message explaining why they were kicked
                await safe_send_message(
                    context=context,
                    chat_id=group_id,
                    text=f"🚫 **Access Denied**\n\n"
                    f"@{username or user_id} was removed from the group.\n\n"
                    f"**Reason:** You haven't completed the necessary KYC verification.\n\n"
                    f"**To join this group:**\n"
                    f"1. Contact the group admin to get a unique user ID\n"
                    f"2. Start a private chat with this bot: @{context.bot.username or 'WellnessBot'}\n"
                    f"3. Provide your user ID and complete KYC verification\n"
                    f"4. You'll receive a group invitation link\n\n"
                    f"💡 **Need help?** Contact the group administrator.",
                    parse_mode="Markdown"
                )

                logger.info(f"🚫 Kicked user {user_id} ({first_name} @{username}) from group {group_id} - no valid user ID")
                return

            except Exception as kick_error:
                logger.error(f"Failed to kick user {user_id} without valid user ID: {kick_error}")
                # Continue with normal flow if kicking fails

    # if any other case rather than if and elif
    else:
        return

    group_config = db.get_group_config(group_id)
    if not group_config:
        logger.warning(f"Group {group_id} not configured - skipping member {user_id}", exc_info=True)
        return

    try:
        # determines if user is Telegram admin/owner; admins should not be restricted
        chat_member = await context.bot.get_chat_member(chat_id=group_id, user_id=user_id)
        is_admin = chat_member.status in ["administrator", "creator"]

        member, is_new = db.add_member(group_id=group_id, user_id=user_id, username=username, first_name=first_name, last_name=last_name, is_admin=is_admin)
        if not member:
            logger.error(f"CRITICAL: Failed to add/update member {user_id} in DB. Aborting join flow.",exc_info=True)
            return

        welcome_message = group_config.get("welcome_message", "Welcome!")
        welcome_text = f"Hi {first_name}, {welcome_message}"
        if is_admin: welcome_text += "\n\nAs an admin, you have full access immediately! 💼"
        
        reply_markup=ReplyKeyboardMarkup(
            [["My Score 💯", "Time Sheet 📅"]],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        await safe_send_message(context=context, chat_id=group_id, text=welcome_text, reply_markup=reply_markup)
        logger.info(f"✅ Welcome message sent to {user_id} in group {group_id}", exc_info=True)

        restriction_until_value = member.get("restriction_until")
        needs_restrict = (member.get("is_restricted") and restriction_until_value and not is_admin)

        if needs_restrict:
            # Parses restriction_until (stored as naive IST datetime or string "%Y-%m-%d %H:%M:%S")
            if isinstance(restriction_until_value, str):
                restriction_until_dt_ist = datetime.strptime(restriction_until_value, "%Y-%m-%d %H:%M:%S")
            else:
                restriction_until_dt_ist = restriction_until_value

            # Converts IST (UTC+5:30) naive to UTC naive for Telegram until_date
            utc_restriction = restriction_until_dt_ist - timedelta(hours=5, minutes=30)

            logger.debug(f"[DEBUG] Restricting user {user_id} in group {group_id} until {utc_restriction} UTC",exc_info=True)
            try:
                await context.bot.restrict_chat_member(
                    chat_id=group_id,
                    user_id=user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=utc_restriction,
                )
                logger.info(f"🔒 Applied restriction for {user_id} until {utc_restriction} UTC", exc_info=True)
            except Exception as restrict_e:
                logger.warning(f"⚠️ Could not restrict {user_id}. Check bot admin permissions. Error: {restrict_e}",exc_info=True)

    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR in track_members for {user_id}: {e}",exc_info=True)


# Handler definitions
bot_join_handler = ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER)
member_join_handler = ChatMemberHandler(track_members, ChatMemberHandler.CHAT_MEMBER)

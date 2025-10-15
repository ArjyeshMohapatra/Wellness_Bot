from telegram import Update, ReplyKeyboardMarkup, ChatPermissions
from telegram.ext import ChatMemberHandler, ContextTypes
import logging
import time
from datetime import datetime, timedelta
from pytz import timezone

from config import NEW_MEMBER_RESTRICTION_MINUTES
from services import database_service as db
from db import execute_query

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


async def track_chats(update, context):
    """Handles the bot being added to or removed from a group."""
    result = extract_status_change(update.my_chat_member)
    if result is None:
        return

    was_member, is_member = result
    chat = update.effective_chat
    group_id = chat.id

    if not was_member and is_member:
        logger.info(f"Bot added to group {group_id} ({chat.title})")

        try:
            admins = await context.bot.get_chat_administrators(group_id)
            owner = next((admin for admin in admins if admin.status == "creator"), None)
            admin_user_id = (
                owner.user.id if owner else admins[0].user.id if admins else None
            )

            if admin_user_id:
                bot_member = await context.bot.get_chat_member(group_id, context.bot.id)

                if bot_member.status in ["administrator", "creator"]:
                    success = db.create_group_config(group_id, admin_user_id)

                    if success:
                        welcome_msg = await context.bot.send_message(
                            chat_id=group_id,
                            text=f"👋 Hello! I'm now managing this group!\n\n"
                            f"✅ **Auto-Setup Complete!**\n\n"
                            f"I've automatically configured:\n"
                            f"• 9 daily time slots\n"
                            f"• Points tracking system\n"
                            f"• Content moderation\n"
                            f"• Auto member management\n\n"
                            f"📋 **Commands:**\n"
                            f"/start - Bot status\n"
                            f"/schedule - View all time slots\n"
                            f"/points - Check your points\n"
                            f"/leaderboard - Top members\n\n"
                            f"🎯 **Ready to use!** Post messages during time slots to earn points!",
                            parse_mode="Markdown",
                        )

                        try:
                            await context.bot.pin_chat_message(
                                group_id, welcome_msg.message_id
                            )
                        except Exception as pin_error:
                            logger.warning(f"Could not pin message: {pin_error}")

                        logger.info(f"Group {group_id} fully auto-configured")
                    else:
                        logger.error(f"Failed to create config for group {group_id}")

                else:
                    await context.bot.send_message(
                        chat_id=group_id,
                        text="⚠️ I need admin rights to function properly!\n"
                        "Please make me an admin first.",
                    )
                    logger.warning(f"Bot is not admin in group {group_id}")

        except Exception as e:
            logger.error(f"Error setting up group {group_id}: {e}")

    elif was_member and not is_member:
        logger.info(f"Bot removed from group {group_id}")


# In telegram-bot/src/handlers/join_handler.py


async def track_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles new members joining or leaving the group."""
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    chat = update.effective_chat
    user = update.chat_member.new_chat_member.user

    if user.is_bot or not (not was_member and is_member):
        return  # Ignore bots or members who were already in the group

    group_id = chat.id
    user_id = user.id
    first_name = user.first_name
    username = user.username

    logger.info(
        f"👤 New member joining: {user_id} ({first_name} @{username}) in group {group_id}"
    )
    logger.debug(
        f"[DEBUG] Attempting DB add_member for user {user_id} in group {group_id}"
    )

    group_config = db.get_group_config(group_id)
    if not group_config:
        logger.warning(f"Group {group_id} not configured - skipping member {user_id}")
        return

    try:
        # Step 1: Check if Telegram admin/owner (always unrestricted)
        chat_member = await context.bot.get_chat_member(
            chat_id=group_id, user_id=user_id
        )
        is_telegram_admin = chat_member.status in ["administrator", "creator"]

        # Step 2: Add to DB (this now returns the member dict or None)
        member, is_new = db.add_member(
            group_id, user_id, username, first_name, is_telegram_admin
        )
        logger.debug(f"[DEBUG] DB add_member result: {member}, is_new: {is_new}")
        if not member:
            logger.error(
                f"CRITICAL: Failed to add/update member {user_id} in DB. Aborting join flow."
            )
            return

        # Step 3: Send welcome message IMMEDIATELY
        welcome_message = group_config.get("welcome_message", "Welcome!")
        welcome_text = f"Hi {first_name}, {welcome_message}"

        restriction_until_str = member.get("restriction_until")
        if (
            member.get("is_restricted")
            and restriction_until_str
            and not is_telegram_admin
        ):
            # Parse the restriction time (stored as IST naive datetime or string)
            if isinstance(restriction_until_str, str):
                restriction_until_dt = datetime.strptime(
                    restriction_until_str, "%Y-%m-%d %H:%M:%S"
                )
            else:
                restriction_until_dt = restriction_until_str
            # Format the restriction time for the user's local timezone (IST)
            restriction_local_time = restriction_until_dt.strftime("%I:%M %p on %b %d")
            welcome_text += f"\n\nJust a heads-up, new members are restricted from messaging until **{restriction_local_time} (IST)**."

        if is_telegram_admin:
            welcome_text += "\n\nAs an admin, you have full access immediately! 💼"

        logger.debug(
            f"[DEBUG] Sending welcome message to {user_id} in group {group_id}: {welcome_text}"
        )
        await context.bot.send_message(chat_id=group_id, text=welcome_text)
        logger.info(f"✅ Welcome message sent to {user_id} in group {group_id}")

        # Step 4: Apply Telegram restriction ONLY if needed, with robust error handling
        if (
            member.get("is_restricted")
            and restriction_until_str
            and not is_telegram_admin
        ):
            # Parse to datetime, convert to UTC naive for Telegram
            if isinstance(restriction_until_str, str):
                restriction_until_dt = datetime.strptime(
                    restriction_until_str, "%Y-%m-%d %H:%M:%S"
                )
            else:
                restriction_until_dt = restriction_until_str
            # IST is UTC+5:30, so subtract to get UTC
            utc_restriction = restriction_until_dt - timedelta(hours=5, minutes=30)
            logger.debug(
                f"[DEBUG] Attempting to restrict user {user_id} in group {group_id} until {utc_restriction}"
            )
            try:
                await context.bot.restrict_chat_member(
                    chat_id=group_id,
                    user_id=user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=utc_restriction,
                )
                logger.info(
                    f"🔒 Successfully applied Telegram restriction for {user_id} until {utc_restriction} UTC."
                )
            except Exception as restrict_e:
                logger.warning(
                    f"⚠️ Could not apply Telegram restriction for {user_id}. PLEASE CHECK BOT PERMISSIONS. Error: {restrict_e}"
                )
            logger.debug(f"[DEBUG] Restriction attempt finished for user {user_id}")

    except Exception as e:
        logger.error(
            f"❌ CRITICAL ERROR in track_members for {user_id}: {e}", exc_info=True
        )


def extract_status_change(chat_member_update):
    """Extracts old and new member status from a chat_member update."""
    was_member = chat_member_update.old_chat_member.is_member
    is_member = chat_member_update.new_chat_member.is_member

    # If there's no change in membership status, return None
    if was_member == is_member:
        return None

    return was_member, is_member


# Handler definitions
bot_join_handler = ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER)
member_join_handler = ChatMemberHandler(track_members, ChatMemberHandler.CHAT_MEMBER)

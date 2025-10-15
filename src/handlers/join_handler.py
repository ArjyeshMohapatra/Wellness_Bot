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


async def track_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles new members joining or leaving the group."""
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    chat = update.effective_chat
    group_id = chat.id
    user = update.chat_member.new_chat_member.user
    user_id = user.id
    first_name = user.first_name

    if user.is_bot:
        return

    group_config = db.get_group_config(group_id)
    if not group_config:
        return

    if not was_member and is_member:
        try:
            # Determines if the new member is a Telegram admin
            chat_member = await context.bot.get_chat_member(
                chat_id=group_id, user_id=user_id
            )
            is_telegram_admin = chat_member.status in ["administrator", "creator"]

            # Adds member to the DB. The service now handles the logic.
            db.add_member(
                group_id, user_id, user.username, user.first_name, is_telegram_admin
            )

            # Fetches the newly created member record to see if a restriction was set
            member = db.get_member(group_id, user_id)
            if not member:
                logger.error(
                    f"Failed to retrieve member record for user {user_id}. Aborting."
                )
                return

            # Apply's Telegram restriction if the DB record says they are restricted
            if member.get("is_restricted") and member.get("restriction_until"):
                restriction_until_dt = member["restriction_until"]

                await context.bot.restrict_chat_member(
                    chat_id=group_id,
                    user_id=user_id,
                    permissions=ChatPermissions(
                        can_send_messages=False,
                        can_send_other_messages=False,
                        can_invite_users=False,
                    ),
                    until_date=restriction_until_dt,
                )
                # Welcome the new user
                welcome_message = group_config.get("welcome_message", "Welcome!")
                await context.bot.send_message(
                    chat_id=group_id, text=f"Hi {first_name}, {welcome_message}."
                )

                logger.info(
                    f"✅ User {user_id} joined and has been MUTED until {restriction_until_dt}."
                )

            # 5. If they are an admin, they won't be restricted, so send the admin welcome
            elif is_telegram_admin:
                welcome_msg_text = f"Welcome, {first_name}! As an admin, you have full access immediately."
                logger.info(
                    f"Admin {user_id} joined group {group_id} - no restrictions applied."
                )
                reply_markup = ReplyKeyboardMarkup(
                    [["My Score 💯", "Time Sheet 📅"]],
                    resize_keyboard=True,
                    one_time_keyboard=False,
                )
                await context.bot.send_message(
                    chat_id=group_id, text=welcome_msg_text, reply_markup=reply_markup
                )

        except Exception as e:
            logger.error(
                f"❌ CRITICAL ERROR restricting new member {user_id}: {e}",
                exc_info=True,
            )

    elif was_member and not is_member:
        db.remove_member(group_id, user_id, "left")
        logger.info(f"User {user_id} left group {group_id}")


def extract_status_change(chat_member_update):
    """Extracts old and new member status from a chat_member update."""
    old_status = chat_member_update.old_chat_member.status
    new_status = chat_member_update.new_chat_member.status

    MEMBER_STATUSES = ["member", "administrator", "creator", "restricted"]

    was_member = old_status in MEMBER_STATUSES
    is_member = new_status in MEMBER_STATUSES

    # If there's no change in membership status, return None
    if was_member == is_member:
        return None

    return was_member, is_member


# Handler definitions
bot_join_handler = ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER)
member_join_handler = ChatMemberHandler(track_members, ChatMemberHandler.CHAT_MEMBER)

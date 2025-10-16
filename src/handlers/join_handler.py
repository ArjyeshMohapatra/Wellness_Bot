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
    was_member, is_member = extract_status_change(update.chat_member)
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


def extract_status_change(chat_member_update):
    """
    Treats creator/administrator/member as in-chat.
    Treats restricted as in-chat only if its is_member flag is True.
    Treats left/kicked as out-of-chat.
    """
    old = chat_member_update.old_chat_member
    new = chat_member_update.new_chat_member

    def in_chat(cm):
        st = (
            cm.status
        )  # 'creator','administrator','member','restricted','left','kicked'
        if st in ("creator", "administrator", "member"):
            return True
        if st == "restricted":
            return bool(getattr(cm, "is_member", False))
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
    # 1) Classify the transition
    was_member, is_member = extract_status_change(update.chat_member)

    # 2) Only act on human users
    user = update.chat_member.new_chat_member.user
    if user.is_bot:
        return

    # 3) Only proceed for real joins (previously out, now in)
    if not (not was_member and is_member):
        return

    chat = update.effective_chat
    group_id = chat.id
    user_id = user.id
    first_name = user.first_name or ""
    username = user.username

    logger.info(
        f"👤 New member joining: {user_id} ({first_name} @{username}) in group {group_id}"
    )

    # 4) Load group config; if not configured, stop
    group_config = db.get_group_config(group_id)
    if not group_config:
        logger.warning(f"Group {group_id} not configured - skipping member {user_id}")
        return

    try:
        # 5) Determine if user is Telegram admin/owner; admins should not be restricted
        chat_member = await context.bot.get_chat_member(
            chat_id=group_id, user_id=user_id
        )
        is_admin = chat_member.status in ["administrator", "creator"]

        # 6) Add/update DB member record; your db.add_member returns (member_dict, is_new)
        member, is_new = db.add_member(
            group_id=group_id,
            user_id=user_id,
            username=username,
            first_name=first_name,
            is_admin=is_admin,
        )
        if not member:
            logger.error(
                f"CRITICAL: Failed to add/update member {user_id} in DB. Aborting join flow."
            )
            return

        # 7) Prepare welcome message
        welcome_message = group_config.get("welcome_message", "Welcome!")
        welcome_text = f"Hi {first_name}, {welcome_message}"
        if is_admin:
            welcome_text += "\n\nAs an admin, you have full access immediately! 💼"

        await context.bot.send_message(chat_id=group_id, text=welcome_text)
        logger.info(f"✅ Welcome message sent to {user_id} in group {group_id}")

        # 8) Apply temporary restriction only if:
        #    - DB says member.is_restricted
        #    - restriction_until present
        #    - user is NOT a Telegram admin/creator
        restriction_until_value = member.get("restriction_until")
        needs_restrict = (
            member.get("is_restricted") and restriction_until_value and not is_admin
        )

        if needs_restrict:
            # Parse restriction_until (stored as naive IST datetime or string "%Y-%m-%d %H:%M:%S")
            if isinstance(restriction_until_value, str):
                restriction_until_dt_ist = datetime.strptime(
                    restriction_until_value, "%Y-%m-%d %H:%M:%S"
                )
            else:
                restriction_until_dt_ist = restriction_until_value

            # Convert IST (UTC+5:30) naive to UTC naive for Telegram until_date
            utc_restriction = restriction_until_dt_ist - timedelta(hours=5, minutes=30)

            logger.debug(
                f"[DEBUG] Restricting user {user_id} in group {group_id} until {utc_restriction} UTC"
            )
            try:
                await context.bot.restrict_chat_member(
                    chat_id=group_id,
                    user_id=user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=utc_restriction,
                )
                logger.info(
                    f"🔒 Applied restriction for {user_id} until {utc_restriction} UTC"
                )
            except Exception as restrict_e:
                logger.warning(
                    f"⚠️ Could not restrict {user_id}. Check bot admin permissions. Error: {restrict_e}"
                )

    except Exception as e:
        logger.error(
            f"❌ CRITICAL ERROR in track_members for {user_id}: {e}", exc_info=True
        )


# Handler definitions
bot_join_handler = ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER)
member_join_handler = ChatMemberHandler(track_members, ChatMemberHandler.CHAT_MEMBER)

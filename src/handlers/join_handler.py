from telegram import Update, ReplyKeyboardMarkup, ChatPermissions
from telegram.ext import ChatMemberHandler, ContextTypes
import logging
import time
from datetime import datetime, timedelta, timezone

# You can use the built-in zoneinfo if your Python is 3.9+
# from zoneinfo import ZoneInfo 

from config import NEW_MEMBER_RESTRICTION_MINUTES
from services import database_service as db
from db import execute_query

logger = logging.getLogger(__name__)

async def unrestrict_member(context: ContextTypes.DEFAULT_TYPE):
    """Unrestricts a member after the set restriction time."""
    job_data = context.job.data
    group_id = job_data['group_id']
    user_id = job_data['user_id']
    first_name = job_data['first_name']
    welcome_message = job_data['welcome_message']

    try:
        # Unrestrict the user by setting default permissions
        await context.bot.restrict_chat_member(
            chat_id=group_id,
            user_id=user_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True
            ),
            until_date=0  # until_date=0 or not specified means forever, but setting all permissions to True effectively unrestricts
        )
        
        welcome_msg_text = (f"Hi {first_name}, {welcome_message}")
        
        reply_markup = ReplyKeyboardMarkup(
            [['My Score 💯', 'Time Sheet 📅']],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        logger.info(f"✅ User {user_id} ({first_name}) has been UNMUTED in group {group_id}.")
        await context.bot.send_message(
            chat_id=group_id,
            text={welcome_msg_text},
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"❌ ERROR unrestricting user {user_id} ({first_name}) in group {group_id}: {e}", exc_info=True)

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
            owner = next((admin for admin in admins if admin.status == 'creator'), None)
            admin_user_id = owner.user.id if owner else admins[0].user.id if admins else None
            
            if admin_user_id:
                bot_member = await context.bot.get_chat_member(group_id, context.bot.id)
                
                if bot_member.status in ['administrator', 'creator']:
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
                            parse_mode='Markdown'
                        )
                        
                        try:
                            await context.bot.pin_chat_message(group_id, welcome_msg.message_id)
                        except Exception as pin_error:
                            logger.warning(f"Could not pin message: {pin_error}")
                        
                        logger.info(f"Group {group_id} fully auto-configured")
                    else:
                        logger.error(f"Failed to create config for group {group_id}")
                
                else:
                    await context.bot.send_message(
                        chat_id=group_id,
                        text="⚠️ I need admin rights to function properly!\n"
                             "Please make me an admin first."
                    )
                    logger.warning(f"Bot is not admin in group {group_id}")
            
        except Exception as e:
            logger.error(f"Error setting up group {group_id}: {e}")
    
    elif was_member and not is_member:
        logger.info(f"Bot removed from group {group_id}")

async def track_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"track_members called for chat_member update: {update.chat_member}")
    """Handles new members joining or leaving the group."""
    result = extract_status_change(update.chat_member)
    if result is None:
        logger.info("track_members: extract_status_change returned None, returning.")
        return

    was_member, is_member = result
    chat = update.effective_chat
    group_id = chat.id
    user = update.chat_member.new_chat_member.user
    user_id = user.id

    if user.is_bot:
        logger.info(f"track_members: User {user_id} is a bot, returning.")
        return

    group_config = db.get_group_config(group_id)
    if not group_config:
        logger.info(f"track_members: No group config found for {group_id}, returning.")
        return

    if not was_member and is_member:
        logger.info(f"track_members: New member {user_id} joining group {group_id}. Proceeding with restriction logic.")
        try:
            chat_member = await context.bot.get_chat_member(chat_id=group_id, user_id=user_id)
            is_telegram_admin = chat_member.status in ['administrator', 'creator']
            
            db.add_member(group_id, user_id, user.username, user.first_name)

            if not is_telegram_admin:
                
                until_date_timestamp = int(time.time()) + (NEW_MEMBER_RESTRICTION_MINUTES * 60)
                logger.info(f"Calculated until_date_timestamp: {until_date_timestamp}")

                await context.bot.restrict_chat_member(
                    chat_id=group_id,
                    user_id=user_id,
                    permissions=ChatPermissions(
                        can_send_messages=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False,
                        can_change_info=False,
                        can_invite_users=False,
                        can_pin_messages=False
                    )
                )
                
                welcome_message = group_config.get('welcome_message', 'Welcome! 🌟')
                # Schedule the unrestrict job
                context.job_queue.run_once(
                    unrestrict_member,
                    NEW_MEMBER_RESTRICTION_MINUTES * 60,  # Convert minutes to seconds
                    data={'group_id': group_id, 'user_id': user_id, 'first_name': user.first_name, 'welcome_message': welcome_message},
                    name=f"unrestrict_{user_id}_{group_id}"
                )
                
                logger.info(f"✅ User {user_id} joined and has been MUTED for {NEW_MEMBER_RESTRICTION_MINUTES} minute(s). Unrestriction scheduled.")
            
            else:
                welcome_msg_text = f"Welcome, {user.first_name}! As an admin, you have full access immediately."
                logger.info(f"Admin {user_id} joined group {group_id} - no restrictions applied.")

        except Exception as e:
            logger.error(f"❌ CRITICAL ERROR restricting new member {user_id}: {e}", exc_info=True)
            welcome_msg_text = f"Welcome, {user.first_name}!"

        await context.bot.send_message(
            chat_id=group_id,
            text=welcome_msg_text,
            reply_markup=reply_markup
        )

    elif was_member and not is_member:
        db.remove_member(group_id, user_id, 'left')
        logger.info(f"User {user_id} left group {group_id}")

def extract_status_change(chat_member_update):
    """Extracts old and new member status from a chat_member update."""
    old_member = chat_member_update.old_chat_member
    new_member = chat_member_update.new_chat_member

    # Determine if the user was a member and is now a member
    was_member = old_member.status in ["member", "administrator", "creator"] or old_member.is_member is True
    is_member = new_member.status in ["member", "administrator", "creator"] or new_member.is_member is True

    # If there's no change in membership status, return None
    if was_member == is_member:
        return None

    return was_member, is_member

# Handler definitions
bot_join_handler = ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER)
member_join_handler = ChatMemberHandler(track_members, ChatMemberHandler.CHAT_MEMBER)
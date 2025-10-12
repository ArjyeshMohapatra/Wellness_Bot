from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ChatMemberHandler, ContextTypes
import logging

from services import database_service as db

logger = logging.getLogger(__name__)

async def track_chats(update, context):
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

async def track_members(update, context):
    result = extract_status_change(update.chat_member)
    if result is None:
        return
    
    was_member, is_member = result
    chat = update.effective_chat
    group_id = chat.id
    user = update.chat_member.new_chat_member.user
    user_id = user.id
    
    if user.is_bot:
        return
    
    group_config = db.get_group_config(group_id)
    if not group_config:
        return
    
    if not was_member and is_member:
        db.add_member(group_id, user_id, user.username, user.first_name)
        
        reply_markup = ReplyKeyboardMarkup(
            [['My Score 💯', 'Time Sheet 📅']],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        welcome_msg = group_config.get('welcome_message', 'Welcome! 🌟')
        await context.bot.send_message(
            chat_id=group_id,
            text=f"{user.first_name}, {welcome_msg}\n\nUse the keyboard below for quick access:",
            reply_markup=reply_markup
        )
        logger.info(f"User {user_id} joined group {group_id}")
    
    elif was_member and not is_member:
        db.remove_member(group_id, user_id, 'left')
        logger.info(f"User {user_id} left group {group_id}")

def extract_status_change(chat_member_update):
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))
    
    if status_change is None:
        return None
    
    old_status, new_status = status_change
    was_member = old_status in ["member", "administrator", "creator"] or (old_is_member is True)
    is_member = new_status in ["member", "administrator", "creator"] or (new_is_member is True)
    
    return was_member, is_member

# Handler definitions
bot_join_handler = ChatMemberHandler(track_chats, ChatMemberHandler.MY_CHAT_MEMBER)
member_join_handler = ChatMemberHandler(track_members, ChatMemberHandler.CHAT_MEMBER)


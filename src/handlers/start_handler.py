from telegram import Update,ReplyKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes
import logging
from datetime import datetime
from services import database_service as db

logger = logging.getLogger(__name__)

async def start(update, context):
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_html(
            f"Hi {user.mention_html()}! 👋\n\n"
            f"I'm a Wellness Group Manager Bot.\n\n"
            f"Add me to a group and make me an admin to start managing:\n"
            f"• Time slot enforcement\n"
            f"• Points tracking\n"
            f"• Inactive user monitoring\n"
            f"• Content moderation\n\n"
            f"Use /help for more commands."
        )
    else:
        # In group chat - check if user is admin
        try:
            chat_member = await context.bot.get_chat_member(chat.id, user.id)
            is_admin = chat_member.status in ['creator', 'administrator']
        except Exception as e:
            logger.warning(f"Could not check admin status: {e}")
            is_admin = False
        
        # Only allow admins to use /start in groups
        if not is_admin:
            logger.info(f"Non-admin user {user.id} tried to use /start in group {chat.id}")
            return  # Silently ignore
        
        # Admin-only code below:
        reply_markup = ReplyKeyboardMarkup(
            [['My Score 💯', 'Time Sheet 📅']],
            resize_keyboard=True,
            one_time_keyboard=False
        )
        
        group_config = db.get_group_config(chat.id)
        
        if group_config:
            await update.message.reply_text(
                f"✅ Group is configured and active!\n\n"
                f"Available commands:\n"
                f"/points - Check your points\n"
                f"/schedule - View today's slots\n"
                f"/help - Show help\n\n"
                f"💡 Use the keyboard buttons below for quick access!",
                reply_markup=reply_markup
            )
        else:
            group_id = chat.id

            # Try to auto-configure if the bot has admin rights
            try:
                admins = await context.bot.get_chat_administrators(group_id)
                owner = next((admin for admin in admins if admin.status == 'creator'), None)
                admin_user_id = owner.user.id if owner else (admins[0].user.id if admins else update.effective_user.id)
            except Exception as e:
                logger.warning(f"Could not fetch chat administrators: {e}")
                admins = None
                admin_user_id = update.effective_user.id

            try:
                bot_member = await context.bot.get_chat_member(group_id, context.bot.id)
            except Exception as e:
                logger.warning(f"Could not fetch bot membership status: {e}")
                bot_member = None

            if bot_member and bot_member.status in ['administrator', 'creator']:
                success = db.create_group_config(group_id, admin_user_id)

                if success:
                    welcome_text = (
                        f"👋 Hello! I'm now managing this group!\n\n"
                        f"✅ *Auto-Setup Complete!*\n\n"
                        f"I've automatically configured:\n"
                        f"• 8 daily time slots\n"
                        f"• Points tracking system\n"
                        f"• Content moderation\n"
                        f"• Auto member management\n\n"
                        f"📋 *Commands:*\n"
                        f"/schedule - View all time slots\n"
                        f"/points - Check your points\n"
                        f"/leaderboard - Top members\n\n"
                        f"🎯 *Ready to use!* Post messages during time slots to earn points!"
                    )

                    try:
                        welcome_msg = await context.bot.send_message(chat_id=group_id, text=welcome_text, parse_mode='Markdown')
                        try:
                            await context.bot.pin_chat_message(group_id, welcome_msg.message_id)
                        except Exception as pin_error:
                            logger.warning(f"Could not pin message: {pin_error}")
                    except Exception as send_error:
                        logger.error(f"Failed to send welcome message: {send_error}")

                    await update.message.reply_text("✅ Group auto-configured. Check the pinned welcome message for details.")
                else:
                    await update.message.reply_text("❌ Failed to auto-configure the group. Please check bot permissions.")
            else:
                await update.message.reply_text(
                    f"⚠️ Group not configured yet! I can auto-configure if I'm an admin.\n\n"
                    f"Please make me an admin and run /start again."
                )

async def points(update, context):
    user = update.effective_user
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("Use this command in a group!")
        return
    
    group_id = chat.id
    user_id = user.id
    
    # Ensure member exists
    db.add_member(group_id, user_id, user.username, user.first_name)
    
    member = db.get_member(group_id, user_id)
    
    if member:
        earned_points = member.get('current_points', 0)  # Points earned
        knockout = member.get('knockout_points', 0)      # Points lost
        total_points = earned_points - knockout           # Net points
        day_num = member.get('user_day_number', 1)
        
        message = f"🎯 {user.first_name}, your stats:\n\n"
        message += f"✅ Earned Points: {earned_points}\n"
        message += f"❌ Knockout Points: {knockout}\n"
        message += f"━━━━━━━━━━━━━━━━\n"
        message += f"💰 **Total Points: {total_points}**\n"
        message += f"📅 Day: {day_num}/7\n"
        
        if knockout > 0:
            message += f"\n⚠️ You lost {knockout} points due to violations!"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text(
            f"{user.first_name}, you're not registered yet. Send any message to register!"
        )

async def schedule(update, context):
    chat = update.effective_chat
    
    if chat.type == 'private':
        await update.message.reply_text("Use this command in a group!")
        return
    
    group_id = chat.id
    all_slots = db.get_all_slots(group_id)
    
    if all_slots:
        message = "📅 **Today's Schedule**\n\n"
        
        for slot in all_slots:
            start = slot['start_time']
            end = slot['end_time']
            name = slot['slot_name']
            points_text = slot['points_for_text']
            points_photo = slot['points_for_photo']
            
            # Convert timedelta to time string if needed
            if hasattr(start, 'total_seconds'):
                start = (datetime.min + start).time()
            if hasattr(end, 'total_seconds'):
                end = (datetime.min + end).time()
            
            message += f"⏰ {start.strftime('%H:%M')} - {end.strftime('%H:%M')}\n"
            message += f"   {name}\n"
            message += f"   📝 Text: {points_text}pts | 📸 Photo: {points_photo}pts\n\n"
        
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("No slots configured yet!")

async def help_command(update, context):
    await update.message.reply_text(
        "🤖 **Bot Commands**\n\n"
        "/points - Check your points\n"
        "/schedule - View today's schedule\n"
        "/help - Show this help\n\n"
        "**How it works:**\n"
        "• Post messages/photos only during active slots\n"
        "• Earn points for participation\n"
        "• Stay active to avoid being kicked\n"
        "• Avoid banned words\n"
        "• Reach minimum points to stay in the group\n"
        "• Leaderboard posted automatically at 10:15 PM daily 🏆\n\n"
        "💡 Keyboard buttons appear automatically for easy access!"
    )

async def test_leaderboard(update, context):
    """Manual leaderboard trigger for testing (admin only)."""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == 'private':
        await update.message.reply_text("Use this command in a group!")
        return
    
    # Check if user is admin
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status not in ['creator', 'administrator']:
            await update.message.reply_text("❌ Only admins can use this command!")
            return
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return
    
    group_id = chat.id
    
    # Get active event
    event = db.get_active_event(group_id)
    if not event:
        await update.message.reply_text("❌ No active event found!")
        return
    
    # Get leaderboard
    top_members = db.get_leaderboard(group_id, 10)
    
    if top_members:
        message = "🏆 **End of Day Leaderboard - Top 10**\n\n"
        
        for i, member in enumerate(top_members, 1):
            name = member.get('first_name', member.get('username', 'Unknown'))
            earned = member.get('current_points', 0)
            knockout = member.get('knockout_points', 0)
            total = earned - knockout
            
            medal = ""
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            
            message += f"{medal} {i}. {name}: {total} pts"
            if knockout > 0:
                message += f" ({earned} earned - {knockout} lost)"
            message += "\n"
        
        message += "\n📅 Great job everyone! See you tomorrow! 🌟"
        
        await update.message.reply_text(message)
        logger.info(f"Manual leaderboard posted by admin {user.id} in group {group_id}")
    else:
        await update.message.reply_text("📊 No participants yet!")

start_handler = CommandHandler("start", start)
points_handler = CommandHandler("points", points)
schedule_handler = CommandHandler("schedule", schedule)
help_handler = CommandHandler("help", help_command)
test_leaderboard_handler = CommandHandler("testleaderboard", test_leaderboard)
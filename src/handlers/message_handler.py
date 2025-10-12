from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters, ContextTypes
import logging
from datetime import datetime, timedelta
import re

from services import database_service as db
from services.file_storage import FileStorage
import config
from handlers.start_handler import points, schedule

logger = logging.getLogger(__name__)
storage = FileStorage(config.STORAGE_PATH)

def sanitize_text(text):
    """Remove HTML tags and URLs from text."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    return text.strip()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages in groups."""
    message = update.message
    
    # Only handle group messages
    if message.chat.type not in ['group', 'supergroup']:
        return
    
    group_id = message.chat.id
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    if message.text and message.text in ['My Score 💯', "Time Sheet 📅"]:
        if message.text == 'My Score 💯':
            await points(update, context)
        elif message.text == "Time Sheet 📅":
            await schedule(update, context)
        return
    
    # Check if group is configured
    group_config = db.get_group_config(group_id)
    if not group_config:
        logger.warning(f"Group {group_id} not configured yet")
        return
    
    # Ensure member exists in database
    db.add_member(group_id, user_id, username, first_name)
    
    # Update member activity
    db.update_member_activity(group_id, user_id)
    
    # Check if user is restricted (joined mid-day)
    member = db.get_member(group_id, user_id)
    if member and member.get('is_restricted', 0) == 1:
        # User is restricted - delete message and notify
        try:
            await message.delete()
            
            # Get actual first slot time dynamically
            all_slots = db.get_all_slots(group_id)
            if all_slots and len(all_slots) > 0:
                first_slot = all_slots[0]
                first_slot_time = first_slot['start_time']
                if hasattr(first_slot_time, 'total_seconds'):
                    first_slot_time = (datetime.min + first_slot_time).time()
                time_str = first_slot_time.strftime("%H:%M")
                slot_name = first_slot['slot_name']
                restriction_text = f"You are restricted from posting until tomorrow's first slot ({slot_name} - {time_str}).\n\n"
            else:
                restriction_text = f"You are restricted from posting until tomorrow's first slot.\n\n"
            
            restriction_msg = await context.bot.send_message(
                chat_id=group_id,
                text=f"👋 {first_name}, welcome to the group!\n\n"
                     f"⚠️ You joined during an active slot time.\n"
                     f"{restriction_text}"
                     f"Your Day 1 will start tomorrow! 📅"
            )
            
            # Delete notification after 15 seconds
            context.job_queue.run_once(
                lambda ctx: restriction_msg.delete(),
                when=15
            )
            
            logger.info(f"Restricted user {user_id} tried to post")
            return
            
        except Exception as e:
            logger.error(f"Error handling restricted user: {e}")
            return
    
    # Check for banned words FIRST - ALWAYS ban on 2 warnings regardless of points
    if message.text:
        custom_banned = db.get_banned_words(group_id)
        
        if not custom_banned:
            logger.warning(f"No banned words found for group {group_id}. Check database!")
        
        message_text_lower = message.text.lower()
        
        # Check if ANY banned word appears in the message with word boundaries
        matched_word = None
        for banned_word in custom_banned:
            # Use word boundaries for single words, substring for phrases
            if ' ' in banned_word:
                # Multi-word phrases: substring match
                if banned_word.lower() in message_text_lower:
                    matched_word = banned_word
                    logger.warning(f"BANNED PHRASE MATCH: '{banned_word}' found in '{message.text[:50]}'")
                    break
            else:
                pattern = r'\b' + re.escape(banned_word.lower()) + r'\b'
                if re.search(pattern, message_text_lower):
                    matched_word = banned_word
                    logger.warning(f"BANNED WORD MATCH: '{banned_word}' found in '{message.text[:50]}'")
                    break
        
        if matched_word:
            try:
                await message.delete()
                db.add_warning(group_id, user_id)
                
                # Deduct 10 knockout points for banned word
                db.deduct_knockout_points(group_id, user_id, 10)
                
                member = db.get_member(group_id, user_id)
                warnings = member['banned_word_count'] if member else 1
                current_points = member['current_points'] if member else 0
                
                warning_msg = await context.bot.send_message(
                    chat_id=group_id,
                    text=f"⚠️ {first_name}, please avoid using inappropriate language!\n"
                         f"Warning {warnings}/2. Using banned word: '{matched_word}'\n"
                         f"⚠️ -10 knockout points deducted!"
                )
                
                context.job_queue.run_once(
                    lambda ctx: warning_msg.delete(),
                    when=5
                )
                
                # Ban for 1 day if 2 warnings
                if warnings >= 2:
                    
                    # Ban for 1 day (until_date requires Unix timestamp)
                    ban_until = datetime.now() + timedelta(days=1)
                    await context.bot.ban_chat_member(group_id, user_id, until_date=ban_until)
                    db.remove_member(group_id, user_id, 'banned')
                    
                    # Congratulate them if they had good points but still ban for violations
                    if current_points >= 100:
                        kick_msg = (f"👋 Congratulations {first_name}! You earned {current_points} points.\n"
                                   f"However, you've been BANNED due to repeated use of inappropriate language.\n"
                                   f"Reason: 2 warnings for banned words\n")
                    else:
                        kick_msg = (f"🚫 {first_name} has been BANNED.\n"
                                   f"Reason: 2 warnings for banned words\n")
                    
                    await context.bot.send_message(chat_id=group_id, text=kick_msg)
                
                logger.warning(f"Banned word detected from user {user_id}: {matched_word}")
                return
                
            except Exception as e:
                logger.error(f"Error handling banned word: {e}")
    
    # Get active slot
    active_slot = db.get_active_slot(group_id)
    
    if not active_slot:
        # No active slot - delete message, warn, and deduct knockout points
        try:
            await message.delete()
            db.add_warning(group_id, user_id)
            
            # Deduct 5 knockout points for posting outside slot
            db.deduct_knockout_points(group_id, user_id, 5)
            
            warning_msg = await context.bot.send_message(
                chat_id=group_id,
                text=f"⏰ {first_name}, no active slot right now!\n"
                     f"Please only post during designated time slots.\n"
                     f"⚠️ -5 knockout points deducted!"
            )
            
            # Delete warning after 10 seconds
            context.job_queue.run_once(
                lambda ctx: warning_msg.delete(),
                when=10
            )
            
            logger.info(f"Message outside slot from user {user_id} - knockout points deducted")
            return
            
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return
    
    # Handle message based on slot type and content
    slot_id = active_slot['slot_id']
    slot_name = active_slot['slot_name']
    slot_type = active_slot['slot_type']
    
    # Get active event
    event = db.get_active_event(group_id)
    event_id = event['event_id'] if event else None
    
    # Check if already completed today
    if event_id and db.check_slot_completed_today(event_id, slot_id, user_id):
        try:
            await message.delete()
            info_msg = await context.bot.send_message(
                chat_id=group_id,
                text=f"✅ {first_name}, you've already completed this slot today!"
            )
            context.job_queue.run_once(lambda ctx: info_msg.delete(), when=5)
            return
        except Exception as e:
            logger.error(f"Error handling duplicate submission: {e}")
            return
    
    if slot_type == 'button':
        try:
            await message.delete()
            hint_msg = await context.bot.send_message(
                chat_id=group_id,
                text=f"💧 {first_name}, please use the water intake buttons for this slot!"
            )
            context.job_queue.run_once(lambda ctx: hint_msg.delete(), when=5)
        except Exception as e:
            logger.error(f"Error sending button hint: {e}")
        return
    
    # Accept ANY media type for regular slots
    if message.photo:
        await handle_photo_response(update, context, active_slot, event_id)
    
    elif message.text:
        await handle_text_response(update, context, active_slot, event_id)
    
    elif message.video or message.document or message.sticker or message.animation or message.voice or message.video_note:
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
    first_name = message.from_user.first_name
    text = sanitize_text(message.text)
    
    slot_id = slot['slot_id']
    slot_name = slot['slot_name']
    
    # Get slot keywords
    keywords = db.get_slot_keywords(slot_id)
    
    # Check if text matches keywords
    text_lower = text.lower()
    keyword_match = any(keyword.lower() in text_lower for keyword in keywords)
    
    if keyword_match:
        # Direct match - award points
        points = slot['points_for_text']
        db.add_points(group_id, user_id, points, event_id)
        db.log_activity(group_id, user_id, slot_name, 'text', text, points_earned=points)
        
        if event_id:
            db.mark_slot_completed(event_id, slot_id, user_id, 'completed')
        
        await message.reply_text(slot['response_positive'] + f"\n+{points} points!")
        logger.info(f"User {user_id} completed slot {slot_name} with text")
    
    else:
        # No keyword match - ask for confirmation
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes", callback_data=f"confirm_yes_{slot_id}_{user_id}_{message.message_id}"),
                InlineKeyboardButton("❌ No", callback_data=f"confirm_no_{slot_id}_{user_id}_{message.message_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        confirmation_msg = await message.reply_text(
            slot['response_clarify'],
            reply_markup=reply_markup
        )
        
        # Store confirmation data in context
        if 'pending_confirmations' not in context.bot_data:
            context.bot_data['pending_confirmations'] = {}
        
        context.bot_data['pending_confirmations'][confirmation_msg.message_id] = {
            'user_id': user_id,
            'slot_id': slot_id,
            'slot_name': slot_name,
            'event_id': event_id,
            'group_id': group_id,
            'original_message_id': message.message_id,
            'text': text,
            'points': slot['points_for_text']
        }
        
        # Auto-select "No" after timeout
        context.job_queue.run_once(
            auto_reject_confirmation,
            when=config.CONFIRMATION_TIMEOUT,
            data={'confirmation_msg_id': confirmation_msg.message_id}
        )

async def handle_photo_response(update: Update, context: ContextTypes.DEFAULT_TYPE, slot: dict, event_id: int):
    """Handle photo message for a slot."""
    message = update.message
    group_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username or f"user{user_id}"
    
    slot_id = slot['slot_id']
    slot_name = slot['slot_name']
    
    # Get the largest photo
    photo = message.photo[-1]
    file_id = photo.file_id
    
    # Check if photo has a caption with keyword match
    caption = message.caption if message.caption else ""
    keywords = db.get_slot_keywords(slot_id)
    
    caption_lower = caption.lower()
    keyword_match = any(keyword.lower() in caption_lower for keyword in keywords) if keywords and caption else False
    
    if keyword_match or not keywords:
        # Direct match OR no keywords defined (all photos accepted) - award points
        try:
            # Download and save photo
            file = await context.bot.get_file(file_id)
            
            # Create formatted filename: {username}_{slotname}_{YYYY_MM_DD_HH_MM_SS_am/pm}.jpg
            timestamp = datetime.now().strftime("%Y_%m_%d_%I_%M_%S_%p").lower()
            filename = f"{username}_{slot_name}_{timestamp}.jpg"
            
            # Save file with new structure
            local_path = await storage.save_photo(group_id, user_id, username, slot_name, file, filename)
            
            # Award points
            points = slot['points_for_photo']
            db.add_points(group_id, user_id, points, event_id)
            db.log_activity(group_id, user_id, slot_name, 'photo', 
                           telegram_file_id=file_id, local_file_path=local_path, points_earned=points)
            
            if event_id:
                db.mark_slot_completed(event_id, slot_id, user_id, 'completed')
            
            await message.reply_text(slot['response_positive'] + f"\n+{points} points!")
            logger.info(f"User {user_id} completed slot {slot_name} with photo")
            
        except Exception as e:
            logger.error(f"Error handling photo: {e}")
            await message.reply_text("Sorry, there was an error processing your photo. Please try again.")
    
    else:
        # Keywords exist but no match - ask for confirmation
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes", callback_data=f"confirm_yes_{slot_id}_{user_id}_{message.message_id}"),
                InlineKeyboardButton("❌ No", callback_data=f"confirm_no_{slot_id}_{user_id}_{message.message_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        confirmation_msg = await message.reply_text(
            slot['response_clarify'],
            reply_markup=reply_markup
        )
        
        # Store confirmation data in context
        if 'pending_confirmations' not in context.bot_data:
            context.bot_data['pending_confirmations'] = {}
        
        context.bot_data['pending_confirmations'][confirmation_msg.message_id] = {
            'user_id': user_id,
            'slot_id': slot_id,
            'slot_name': slot_name,
            'event_id': event_id,
            'group_id': group_id,
            'original_message_id': message.message_id,
            'photo_file_id': file_id,
            'username': username,
            'caption': caption,
            'points': slot['points_for_photo'],
            'type': 'photo'
        }
        
        # Auto-select "No" after timeout
        context.job_queue.run_once(
            auto_reject_confirmation,
            when=config.CONFIRMATION_TIMEOUT,
            data={'confirmation_msg_id': confirmation_msg.message_id}
        )

async def handle_other_media_response(update: Update, context: ContextTypes.DEFAULT_TYPE, slot: dict, event_id: int):
    """Handle other media types (video, sticker, document, etc.) for a photo slot."""
    message = update.message
    group_id = message.chat.id
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username or f"user{user_id}"
    
    slot_id = slot['slot_id']
    slot_name = slot['slot_name']
    
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
            file_ext = message.document.file_name.split('.')[-1] if '.' in message.document.file_name else "file"
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
    if media_type in ['video', 'document']:
        points = slot['points_for_photo']  # 10 points - same effort as photo
    elif media_type in ['voice', 'video_note']:
        points = slot['points_for_text']  # 5 points - like text message
    elif media_type in ['sticker', 'animation']:
        points = 0  # No points - entertainment only
    else:
        points = slot['points_for_photo']  # Default
    
    # Always ask for confirmation for non-photo media
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"confirm_yes_{slot_id}_{user_id}_{message.message_id}"),
            InlineKeyboardButton("❌ No", callback_data=f"confirm_no_{slot_id}_{user_id}_{message.message_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    points_msg = f" (+{points} points)" if points > 0 else " (no points)"
    confirmation_msg = await message.reply_text(
        f"Is this {media_type} for the {slot_name} slot?{points_msg}",
        reply_markup=reply_markup
    )
    
    # Store confirmation data in context
    if 'pending_confirmations' not in context.bot_data:
        context.bot_data['pending_confirmations'] = {}
    
    context.bot_data['pending_confirmations'][confirmation_msg.message_id] = {
        'user_id': user_id,
        'slot_id': slot_id,
        'slot_name': slot_name,
        'event_id': event_id,
        'group_id': group_id,
        'original_message_id': message.message_id,
        'file_id': file_id,
        'username': username,
        'caption': message.caption if message.caption else '',
        'points': points,
        'type': 'media',  # Mark as media (not photo)
        'media_type': media_type,
        'file_ext': file_ext
    }
    
    # Auto-select "No" after timeout
    context.job_queue.run_once(
        auto_reject_confirmation,
        when=config.CONFIRMATION_TIMEOUT,
        data={'confirmation_msg_id': confirmation_msg.message_id}
    )

async def auto_reject_confirmation(context: ContextTypes.DEFAULT_TYPE):
    """Auto-reject confirmation after timeout."""
    job = context.job
    confirmation_msg_id = job.data['confirmation_msg_id']
    
    if 'pending_confirmations' in context.bot_data:
        if confirmation_msg_id in context.bot_data['pending_confirmations']:
            data = context.bot_data['pending_confirmations'][confirmation_msg_id]
            
            try:
                # Edit message to show timeout
                await context.bot.edit_message_text(
                    chat_id=data['group_id'],
                    message_id=confirmation_msg_id,
                    text="⏱️ Timeout - marked as No"
                )
                
                # Delete after 3 seconds
                context.job_queue.run_once(
                    lambda ctx: context.bot.delete_message(data['group_id'], confirmation_msg_id),
                    when=3
                )
                
                # Log as invalid activity
                db.log_activity(data['group_id'], data['user_id'], data['slot_name'], 
                              'text', data['text'], points_earned=0, is_valid=False)
                
            except Exception as e:
                logger.error(f"Error in auto-reject: {e}")
            
            # Remove from pending (use pop to prevent KeyError)
            context.bot_data['pending_confirmations'].pop(confirmation_msg_id, None)

# Create message handlers
text_message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
photo_message_handler = MessageHandler(filters.PHOTO, handle_message)
video_message_handler = MessageHandler(filters.VIDEO, handle_message)
document_message_handler = MessageHandler(filters.Document.ALL, handle_message)
sticker_message_handler = MessageHandler(filters.Sticker.ALL, handle_message)
animation_message_handler = MessageHandler(filters.ANIMATION, handle_message)
voice_message_handler = MessageHandler(filters.VOICE, handle_message)
video_note_message_handler = MessageHandler(filters.VIDEO_NOTE, handle_message)

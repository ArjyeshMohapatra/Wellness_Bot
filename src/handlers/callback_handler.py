from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
import logging
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import DatabaseService

logger = logging.getLogger(__name__)
db = DatabaseService()

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    
    await query.answer()
    
    data = query.data
    
    # Handle confirmation responses (Yes/No for keyword mismatch)
    if data.startswith('confirm_'):
        await handle_confirmation(update, context)
    
    # Handle water consumption buttons
    elif data.startswith('water_'):
        await handle_water_button(update, context)
    
    else:
        logger.warning(f"Unhandled callback data: {data}")

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Yes/No confirmation for slot responses."""
    query = update.callback_query
    data = query.data
    message = query.message
    
    # Parse callback data: confirm_yes/no_<slot_id>_<user_id>_<original_msg_id>
    parts = data.split('_')
    if len(parts) < 4:
        await query.edit_message_text("❌ Invalid confirmation.")
        return
    
    response = parts[1]  # 'yes' or 'no'
    slot_id = int(parts[2])
    expected_user_id = int(parts[3])
    
    # Verify it's the right user
    if query.from_user.id != expected_user_id:
        await query.answer("This confirmation is not for you!", show_alert=True)
        return
    
    # Get pending confirmation data
    pending_confirmations = context.bot_data.get('pending_confirmations', {})
    confirmation_data = pending_confirmations.get(message.message_id)
    
    if not confirmation_data:
        await query.edit_message_text("⏱️ This confirmation has expired.")
        return
    
    group_id = confirmation_data['group_id']
    slot_name = confirmation_data['slot_name']
    event_id = confirmation_data['event_id']
    points = confirmation_data['points']
    content_type = confirmation_data.get('type', 'text')
    
    if response == 'yes':
        # Handle based on content type
        if content_type == 'photo':
            # Import storage here to avoid circular imports
            from services.file_storage import FileStorage
            from config import Config
            
            photo_file_id = confirmation_data['photo_file_id']
            username = confirmation_data['username']
            caption = confirmation_data.get('caption', '')
            
            try:
                # Download and save photo
                file = await context.bot.get_file(photo_file_id)
                
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y_%m_%d_%I_%M_%S_%p").lower()
                filename = f"{username}_{slot_name}_{timestamp}.jpg"
                
                config = Config()
                storage = FileStorage(config.STORAGE_PATH)
                local_path = await storage.save_photo(group_id, expected_user_id, username, slot_name, file, filename)
                
                # Award points
                db.add_points(group_id, expected_user_id, points, event_id)
                db.log_activity(group_id, expected_user_id, slot_name, 'photo', 
                               telegram_file_id=photo_file_id, local_file_path=local_path, points_earned=points, is_valid=True)
                
                if event_id:
                    db.mark_slot_completed(event_id, slot_id, expected_user_id, 'completed')
                
                await query.edit_message_text(f"✅ Photo confirmed! +{points} points!")
                logger.info(f"User {expected_user_id} confirmed photo for slot {slot_name}")
            
            except Exception as e:
                logger.error(f"Error saving confirmed photo: {e}")
                await query.edit_message_text("❌ Error saving photo. Please try again.")
                
        else:
            # Text confirmation
            text = confirmation_data.get('text', '')
            db.add_points(group_id, expected_user_id, points, event_id)
            db.log_activity(group_id, expected_user_id, slot_name, 'text', text, points_earned=points, is_valid=True)
            
            if event_id:
                db.mark_slot_completed(event_id, slot_id, expected_user_id, 'completed')
            
            await query.edit_message_text(f"✅ Confirmed! +{points} points!")
            logger.info(f"User {expected_user_id} confirmed slot {slot_name}")
    
    else:
        # Log as invalid based on type
        if content_type == 'photo':
            db.log_activity(group_id, expected_user_id, slot_name, 'photo', points_earned=0, is_valid=False)
        else:
            text = confirmation_data.get('text', '')
            db.log_activity(group_id, expected_user_id, slot_name, 'text', text, points_earned=0, is_valid=False)
        
        await query.edit_message_text("❌ Cancelled. No points awarded.")
        logger.info(f"User {expected_user_id} rejected confirmation for slot {slot_name}")
        
        # Delete the original message that was rejected
        try:
            original_message_id = confirmation_data.get('original_message_id')
            if original_message_id:
                await context.bot.delete_message(chat_id=group_id, message_id=original_message_id)
                logger.info(f"Deleted rejected message {original_message_id}")
        except Exception as e:
            logger.warning(f"Could not delete original message: {e}")
    
    # Remove from pending
    del pending_confirmations[message.message_id]
    
    # Delete confirmation message after 3 seconds
    context.job_queue.run_once(
        lambda ctx: message.delete(),
        when=3
    )

async def handle_water_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle water consumption button clicks (1L to 5L)."""
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    first_name = query.from_user.first_name
    group_id = query.message.chat.id
    
    # Parse: water_<liters>_<slot_id>
    parts = data.split('_')
    if len(parts) < 3:
        await query.answer("Invalid water selection", show_alert=True)
        return
    
    liters = int(parts[1])
    slot_id = int(parts[2])
    
    # Get slot info
    active_slot = db.get_active_slot(group_id)
    
    if not active_slot or active_slot['slot_id'] != slot_id:
        await query.answer("This water slot is no longer active!", show_alert=True)
        return
    
    # Get event
    event = db.get_active_event(group_id)
    event_id = event['event_id'] if event else None
    
    # Check if already completed today
    if event_id and db.check_slot_completed_today(event_id, slot_id, user_id):
        await query.answer("Already completed!", show_alert=True)
        # Send visible message in chat
        slot_name = active_slot['slot_name']
        response_msg = await context.bot.send_message(
            chat_id=group_id,
            text=f"⚠️ {first_name}, you have already completed {slot_name} slot for today!",
            reply_to_message_id=query.message.message_id
        )
        # Auto-delete after 5 seconds
        context.job_queue.run_once(
            lambda ctx: response_msg.delete(),
            when=5
        )
        return
    
    # Calculate points (e.g., 2 points per liter)
    points = liters * 2
    slot_name = active_slot['slot_name']
    
    # Award points
    db.add_points(group_id, user_id, points, event_id)
    db.log_activity(group_id, user_id, slot_name, 'button', f"{liters}L water", points_earned=points)
    
    if event_id:
        db.mark_slot_completed(event_id, slot_id, user_id, 'completed')
    
    # Send confirmation as popup notification (doesn't replace message)
    await query.answer(f"✅ {liters}L logged! +{points} points!", show_alert=True)
    
    # Send a separate message to show who completed (doesn't replace buttons)
    response_msg = await context.bot.send_message(
        chat_id=group_id,
        text=f"💧 {first_name} drank {liters}L of water! +{points} points!"
    )
    
    ''' # Delete the response message after 5 seconds to keep chat clean
    context.job_queue.run_once(
        lambda ctx: response_msg.delete(),
        when=5
    ) '''
    
    logger.info(f"User {user_id} logged {liters}L water for slot {slot_name}")

callback_handler = CallbackQueryHandler(handle_callback)
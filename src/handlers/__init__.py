from .start_handler import (
    start_handler,
    points_handler,
    schedule_handler,
    help_handler,
    test_leaderboard_handler,
)
from .join_handler import bot_join_handler, member_join_handler
from .message_handler import (
    text_message_handler,
    photo_message_handler,
    video_message_handler,
    document_message_handler,
    sticker_message_handler,
    animation_message_handler,
    voice_message_handler,
    video_note_message_handler,
)
from .callback_handler import callback_handler
from .jobs import setup_jobs


def setup_handlers(application):
    """Setup all handlers for the bot."""
    # Command handlers
    application.add_handler(start_handler)
    application.add_handler(points_handler)
    # leaderboard_handler removed - now posts automatically at 10 PM daily
    application.add_handler(schedule_handler)
    application.add_handler(help_handler)
    application.add_handler(test_leaderboard_handler)  # Admin-only test command
    # keyboard_handler removed - keyboard now appears automatically

    # Chat member handlers (for tracking joins/leaves)
    application.add_handler(bot_join_handler)
    application.add_handler(member_join_handler)

    # Message handlers (order matters - more specific first)
    application.add_handler(photo_message_handler)
    application.add_handler(video_message_handler)
    application.add_handler(document_message_handler)
    application.add_handler(sticker_message_handler)
    application.add_handler(animation_message_handler)
    application.add_handler(voice_message_handler)
    application.add_handler(video_note_message_handler)
    application.add_handler(text_message_handler)

    # Callback handler (for buttons)
    application.add_handler(callback_handler)

    # Setup periodic jobs
    setup_jobs(application)

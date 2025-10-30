from .utils import logger


def save_banned_words(cursor, group_id, banned_words):
    """Save banned words to the banned_words table"""
    try:
        # For now, banned words are global (group_id = NULL)

        # Process the banned words array
        if banned_words and isinstance(banned_words, list) and len(banned_words) > 0:
            # Filter out empty strings and strip whitespace
            words = [word.strip() for word in banned_words if word.strip()]

            # Remove duplicates
            words = list(set(words))

            # Insert each word with group_id = NULL
            for word in words:
                try:
                    cursor.execute(
                        "INSERT INTO banned_words (group_id, word) VALUES (NULL, %s)",
                        (word,)
                    )
                except Exception as e:
                    logger.error(f"Failed executing save_banned_words. Query: INSERT INTO banned_words (group_id, word) VALUES (NULL, %s) | Params: {(word,)} | Error: {e}", exc_info=True)
                    raise

        logger.info(f"Saved {len(words) if 'words' in locals() else 0} global banned words")

    except Exception as e:
        logger.error(f"Error saving banned words: {e}")
        raise
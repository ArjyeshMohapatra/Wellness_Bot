import mysql.connector
from mysql.connector import pooling
import logging
import config
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# MySQL Connection Pool
connection_pool = None


def init_db_pool():
    """Initialize MySQL connection pool."""
    global connection_pool

    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="telegram_bot_pool", 
            pool_size=5,
            pool_reset_session=True, 
            host=config.DB_HOST, 
            port=config.DB_PORT, 
            user=config.DB_USER,
            password=config.DB_PASSWORD, 
            database=config.DB_NAME,
            charset="utf8mb4", 
            collation="utf8mb4_unicode_520_ci",
            use_unicode=True, 
            autocommit=False,
            client_flags=[mysql.connector.constants.ClientFlag.SSL]
            )
        logger.info("Database connection pool initialized successfully")
    except mysql.connector.Error as e:
        logger.error(f"Error initializing database pool: {e}",exc_info=True)
        raise


def get_db_connection(retries=3, delay=1):
    """Get database connection from pool (simple version)."""
    global connection_pool

    if connection_pool is None:
        init_db_pool()

    last_exception = None
    for attempt in range(retries):
        try:
            connection = connection_pool.get_connection()
            
            # Handle any unread results that might be left from previous uses
            try:
                cursor = connection.cursor()
                while cursor.nextset():
                    pass
                cursor.close()
            except:
                pass
            
            connection.set_charset_collation("utf8mb4", "utf8mb4_unicode_520_ci")
            cursor = connection.cursor()
            cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_520_ci;")
            cursor.close()
            return connection
        except mysql.connector.Error as e:
            last_exception = e
            logger.warning("Database connection failed (attempt %s/%s). Retrying in %s s...", attempt + 1, retries, delay)
            time.sleep(delay)

    if last_exception:
        raise last_exception


def execute_query(query, params=None, fetch=False):
    """Execute a query and optionally fetch results."""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())

        if fetch:
            result = cursor.fetchall()
            # Consume any remaining result sets
            while cursor.nextset():
                pass
            # Don't commit for read operations
            return result
        else:
            result = cursor.lastrowid or None
            # Consume any remaining result sets
            while cursor.nextset():
                pass
            # Only commit for write operations (INSERT, UPDATE, DELETE)
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                conn.commit()
            return result

    except mysql.connector.Error as e:
        if conn:
            conn.rollback()
        logger.error(f"Error executing query: {query} | Params: {params} | Error: {e}", exc_info=True)
        raise
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

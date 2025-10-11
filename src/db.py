import mysql.connector
from mysql.connector import pooling
from contextlib import contextmanager
import logging
import config

logger = logging.getLogger(__name__)

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
            autocommit=False
        )
        logger.info("Database connection pool initialized successfully")
    except mysql.connector.Error as e:
        logger.error(f"Error initializing database pool: {e}")
        raise

@contextmanager
def get_db_connection():
    """Get database connection from pool."""
    global connection_pool
    
    if connection_pool is None:
        init_db_pool()
    
    connection = None
    try:
        connection = connection_pool.get_connection()
        yield connection
        connection.commit()
    except mysql.connector.Error as e:
        if connection:
            connection.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()

def execute_query(query, params=None, fetch=False):
    """Execute a query and optionally fetch results."""
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            
            if fetch:
                if 'SELECT' in query.upper():
                    results = cursor.fetchall()
                    return results
                else:
                    return cursor.lastrowid
            else:
                conn.commit()
                return cursor.lastrowid if cursor.lastrowid else True
        finally:
            cursor.close()
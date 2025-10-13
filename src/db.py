import mysql.connector
from mysql.connector import pooling
from contextlib import contextmanager
import logging
import config

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
            charset='utf8mb4',
            collation='utf8mb4_unicode_520_ci',
            use_unicode=True,
            autocommit=False,
            client_flags=[mysql.connector.constants.ClientFlag.SSL]
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
        connection.set_charset_collation('utf8mb4', 'utf8mb4_unicode_520_ci')
        cursor = connection.cursor()
        cursor.execute("SET NAMES utf8mb4 COLLATE utf8mb4_unicode_520_ci;")
        cursor.close() 
        yield connection
        connection.commit() # commits only if everything succeeds
    except mysql.connector.Error as e:
        if connection:
            connection.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            connection.close() # returns connection back to the pool

def execute_query(query, params=None, fetch=False):
    """Execute a query and optionally fetch results."""
    with get_db_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:  # cursor auto-closed
            try:
                cursor.execute(query, params or ())
                if fetch:
                    return cursor.fetchall()  # return rows for SELECT
                return cursor.lastrowid or None
            except mysql.connector.Error as e:
                logger.error(f"Error executing query: {query} | Params: {params} | Error: {e}")
                raise
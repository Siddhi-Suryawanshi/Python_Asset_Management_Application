# models/db_manager.py
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG
from utils.logger import get_logger

log = get_logger(__name__)

class DatabaseManager:
    """OOP Encapsulation: Manages DB connections securely."""
    
    def __init__(self):
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            if self.connection.is_connected():
                log.info("Database connection established.")
        except Error as e:
            log.error(f"Database connection failed: {e}")
            raise Exception("Could not connect to the database. Check logs.")

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            log.info("Database connection closed.")

    def execute_query(self, query, params=None):
        """Executes INSERT, UPDATE, DELETE queries."""
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.lastrowid
        except Error as e:
            log.error(f"Query execution failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            self.disconnect()

    def fetch_one(self, query, params=None):
        """Fetches a single record."""
        try:
            self.connect()
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params)
            return cursor.fetchone()
        except Error as e:
            log.error(f"Fetch failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            self.disconnect()
import aiosqlite
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path("vinbot.db")

class Database:
    def __init__(self):
        self.connection = None

    async def connect(self):
        """Task 1.2: Connect to SQLite and initialize tables."""
        if self.connection is None:
            self.connection = await aiosqlite.connect(DB_PATH)
            self.connection.row_factory = aiosqlite.Row
            await self._init_tables()
            logger.info(f"Database connected at {DB_PATH}")

    async def disconnect(self):
        """Safely close the connection."""
        if self.connection:
            await self.connection.close()
            self.connection = None
            logger.info("Database disconnected")

    async def _init_tables(self):
        """Task 1.3: Initialize tables bot_state and orders."""
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS bot_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                symbol TEXT,
                side TEXT,
                price REAL,
                quantity REAL,
                rsi REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.connection.commit()

# Global database instance
db = Database()

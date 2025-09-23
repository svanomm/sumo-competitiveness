"""
Database module for storing scraped sumo data.
"""

import asyncio
import aiosqlite
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from config.settings import Config

logger = logging.getLogger(__name__)

class SumoDatabase:
    """Database manager for sumo competitiveness data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection."""
        self.db_path = db_path or Config.DATABASE_PATH
        self.db_path = Path(self.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def init_database(self) -> None:
        """Initialize database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            # Create wrestlers table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS wrestlers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    rank TEXT,
                    stable TEXT,
                    weight REAL,
                    height REAL,
                    birthplace TEXT,
                    debut_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create tournaments table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tournaments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    location TEXT,
                    start_date DATE,
                    end_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, year, month)
                )
            """)
            
            # Create matches table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tournament_id INTEGER,
                    day INTEGER,
                    wrestler1_id INTEGER,
                    wrestler2_id INTEGER,
                    winner_id INTEGER,
                    kimarite TEXT,
                    match_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tournament_id) REFERENCES tournaments (id),
                    FOREIGN KEY (wrestler1_id) REFERENCES wrestlers (id),
                    FOREIGN KEY (wrestler2_id) REFERENCES wrestlers (id),
                    FOREIGN KEY (winner_id) REFERENCES wrestlers (id)
                )
            """)
            
            # Create indexes for better performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_wrestlers_name ON wrestlers(name)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tournaments_date ON tournaments(year, month)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_matches_tournament ON matches(tournament_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_matches_wrestlers ON matches(wrestler1_id, wrestler2_id)")
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    async def insert_wrestler(self, wrestler_data: Dict[str, Any]) -> int:
        """Insert a wrestler into the database."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT OR REPLACE INTO wrestlers 
                (name, rank, stable, weight, height, birthplace, debut_date, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                wrestler_data.get('name'),
                wrestler_data.get('rank'),
                wrestler_data.get('stable'),
                wrestler_data.get('weight'),
                wrestler_data.get('height'),
                wrestler_data.get('birthplace'),
                wrestler_data.get('debut_date')
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def insert_tournament(self, tournament_data: Dict[str, Any]) -> int:
        """Insert a tournament into the database."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT OR REPLACE INTO tournaments 
                (name, year, month, location, start_date, end_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tournament_data.get('name'),
                tournament_data.get('year'),
                tournament_data.get('month'),
                tournament_data.get('location'),
                tournament_data.get('start_date'),
                tournament_data.get('end_date')
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def insert_match(self, match_data: Dict[str, Any]) -> int:
        """Insert a match into the database."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO matches 
                (tournament_id, day, wrestler1_id, wrestler2_id, winner_id, kimarite, match_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                match_data.get('tournament_id'),
                match_data.get('day'),
                match_data.get('wrestler1_id'),
                match_data.get('wrestler2_id'),
                match_data.get('winner_id'),
                match_data.get('kimarite'),
                match_data.get('match_time')
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def get_wrestler_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get wrestler by name."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM wrestlers WHERE name = ?", (name,))
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_tournament_by_details(self, name: str, year: int, month: int) -> Optional[Dict[str, Any]]:
        """Get tournament by name, year, and month."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM tournaments WHERE name = ? AND year = ? AND month = ?", 
                (name, year, month)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def close(self) -> None:
        """Close database connection."""
        # aiosqlite handles connection closing automatically
        pass
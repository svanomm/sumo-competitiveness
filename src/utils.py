"""
Utility functions for data processing and analysis.
"""

import pandas as pd
from typing import List, Dict, Any, Optional
import aiosqlite
from pathlib import Path

from config.settings import Config

class DataAnalyzer:
    """Class for analyzing scraped sumo data."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the data analyzer."""
        self.db_path = db_path or Config.DATABASE_PATH
    
    async def get_wrestler_stats(self) -> pd.DataFrame:
        """Get basic wrestler statistics."""
        async with aiosqlite.connect(self.db_path) as db:
            query = """
                SELECT 
                    name, rank, stable, weight, height, birthplace,
                    COUNT(m1.id) + COUNT(m2.id) as total_matches,
                    COUNT(CASE WHEN m1.winner_id = w.id THEN 1 END) + 
                    COUNT(CASE WHEN m2.winner_id = w.id THEN 1 END) as wins
                FROM wrestlers w
                LEFT JOIN matches m1 ON w.id = m1.wrestler1_id
                LEFT JOIN matches m2 ON w.id = m2.wrestler2_id
                GROUP BY w.id, w.name
                ORDER BY total_matches DESC
            """
            df = pd.read_sql_query(query, db)
            
            # Calculate win percentage
            df['win_percentage'] = (df['wins'] / df['total_matches'] * 100).round(2)
            df['win_percentage'] = df['win_percentage'].fillna(0)
            
            return df
    
    async def get_tournament_summary(self) -> pd.DataFrame:
        """Get tournament summary statistics."""
        async with aiosqlite.connect(self.db_path) as db:
            query = """
                SELECT 
                    t.name, t.year, t.month, t.location,
                    COUNT(m.id) as total_matches
                FROM tournaments t
                LEFT JOIN matches m ON t.id = m.tournament_id
                GROUP BY t.id
                ORDER BY t.year DESC, t.month DESC
            """
            return pd.read_sql_query(query, db)
    
    async def export_to_csv(self, output_dir: str = "data/exports"):
        """Export data to CSV files for further analysis."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export wrestler stats
        wrestler_stats = await self.get_wrestler_stats()
        wrestler_stats.to_csv(output_path / "wrestler_stats.csv", index=False)
        
        # Export tournament summary
        tournament_summary = await self.get_tournament_summary()
        tournament_summary.to_csv(output_path / "tournament_summary.csv", index=False)
        
        print(f"Data exported to {output_path}")

def clean_text(text: str) -> str:
    """Clean and normalize text data."""
    if not isinstance(text, str):
        return text
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters if needed
    # text = re.sub(r'[^\w\s-]', '', text)
    
    return text.strip()

def normalize_rank(rank: str) -> str:
    """Normalize sumo rank names."""
    if not isinstance(rank, str):
        return rank
    
    rank_mapping = {
        # Add rank normalizations here
        # Example: 'Yokozuna' -> 'Yokozuna'
        # 'Ozeki' -> 'Ozeki'
        # etc.
    }
    
    return rank_mapping.get(rank, rank)

def parse_japanese_date(date_str: str) -> str:
    """Parse Japanese date formats to ISO format."""
    # TODO: Implement Japanese date parsing
    # This would handle formats like "令和3年1月" -> "2021-01"
    return date_str
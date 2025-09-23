"""
SumoDB scraper for collecting bout-level sumo match data.
"""

import asyncio
import aiohttp
import pandas as pd
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import math

from .base_scraper import BaseScraper
from config.settings import Config

logger = logging.getLogger(__name__)

class SumoDBScraper(BaseScraper):
    """Specialized scraper for SumoDB (sumodb.sumogames.de) bout data."""
    
    def __init__(self, **kwargs):
        """Initialize SumoDB scraper."""
        super().__init__(**kwargs)
        self.base_url = "https://sumodb.sumogames.de/Query_bout.aspx"
        self.params = {
            'show_form': '0',
            'year': '2000-2025',
            'm': 'on',
            'j': 'on', 
            'rowcount': '5',
            'onlyw1': 'on'
        }
        self.rows_per_page = 1000
        self.total_rows = 76068
        self.total_pages = math.ceil(self.total_rows / self.rows_per_page)
    
    async def scrape_all_bouts(self, start_offset: int = 0, max_pages: Optional[int] = None) -> pd.DataFrame:
        """
        Scrape all bout data from SumoDB.
        
        Args:
            start_offset: Starting offset (default: 0)
            max_pages: Maximum number of pages to scrape (default: all)
        
        Returns:
            DataFrame with all bout data
        """
        logger.info(f"Starting to scrape SumoDB bout data...")
        logger.info(f"Total rows: {self.total_rows}, Pages: {self.total_pages}")
        
        if max_pages:
            pages_to_scrape = min(max_pages, self.total_pages)
        else:
            pages_to_scrape = self.total_pages
        
        all_dataframes = []
        start_page = start_offset // self.rows_per_page
        
        for page in range(start_page, start_page + pages_to_scrape):
            offset = page * self.rows_per_page
            
            logger.info(f"Scraping page {page + 1}/{self.total_pages} (offset: {offset})")
            
            # Build URL for this page
            url = self._build_url(offset)
            
            # Fetch and parse page
            html = await self.fetch_page(url)
            if html:
                try:
                    df = self._parse_bout_page(html, offset)
                    if not df.empty:
                        all_dataframes.append(df)
                        logger.info(f"Page {page + 1}: Found {len(df)} bouts")
                    else:
                        logger.warning(f"Page {page + 1}: No data found")
                except Exception as e:
                    logger.error(f"Error parsing page {page + 1}: {str(e)}")
            else:
                logger.error(f"Failed to fetch page {page + 1}")
            
            # Add delay between requests
            await asyncio.sleep(3)
        
        # Combine all dataframes
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            logger.info(f"Total bouts scraped: {len(combined_df)}")
            return combined_df
        else:
            logger.warning("No data was scraped")
            return pd.DataFrame()
    
    def _build_url(self, offset: int) -> str:
        """Build URL with the specified offset."""
        params = self.params.copy()
        params['offset'] = str(offset)
        
        # Build query string
        query_parts = []
        for key, value in params.items():
            query_parts.append(f"{key}={value}")
        
        return f"{self.base_url}?{'&'.join(query_parts)}"
    
    def _parse_bout_page(self, html: str, offset: int) -> pd.DataFrame:
        """Parse a single page of bout data from SumoDB."""
        soup = BeautifulSoup(html, 'lxml')
        
        # Find the data table - SumoDB has only one main table
        tables = soup.find_all('table')
        
        if not tables:
            logger.warning(f"No tables found in page with offset {offset}")
            return pd.DataFrame()
        
        # Use the first (and likely only) table
        table = tables[0]
        rows = table.find_all('tr')
        
        if len(rows) < 3:  # Need at least header + subheader + 1 data row
            logger.warning(f"Table too small: {len(rows)} rows")
            return pd.DataFrame()
        
        data_rows = []
        
        # Skip the first two rows (headers) and process data rows
        # Row 0: ['Basho', 'Day', 'Rikishi 1', '', 'Kimarite', '', 'Rikishi 2']
        # Row 1: ['Rank', 'Shikona', 'Result', 'Rank', 'Shikona', 'Result']
        # Row 2+: Actual bout data
        
        for row_idx, row in enumerate(rows[2:], start=2):  # Start from row 2
            cells = row.find_all(['td', 'th'])
            
            if len(cells) < 7:  # Need at least 7 columns for complete data
                continue
            
            try:
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                # Parse based on the known structure:
                # [Basho, Day, Rank1, Shikona1, Result1, Kimarite, Rank2, Shikona2, Result2]
                # Example: ['2000.01', '1', 'J13w', 'Aminishiki', '1-0 (8-7)', '', 'yorikiri', '', 'J13e', 'Wakakosho', '0-1 (8-7)']
                
                if len(cell_texts) >= 9:
                    basho = cell_texts[0]
                    day = cell_texts[1]
                    rank1 = cell_texts[2]
                    wrestler1 = cell_texts[3]
                    result1 = cell_texts[4]
                    # cell_texts[5] is empty
                    kimarite = cell_texts[6]
                    # cell_texts[7] is empty
                    rank2 = cell_texts[8]
                    wrestler2 = cell_texts[9] if len(cell_texts) > 9 else ''
                    result2 = cell_texts[10] if len(cell_texts) > 10 else ''
                    
                    row_data = {
                        'basho': basho,
                        'day': day,
                        'wrestler1': wrestler1,
                        'wrestler1_rank': rank1,
                        'wrestler1_result': result1,
                        'wrestler2': wrestler2,
                        'wrestler2_rank': rank2,
                        'wrestler2_result': result2,
                        'kimarite': kimarite,
                        'scraped_at': datetime.now().isoformat(),
                        'source_offset': offset
                    }
                    
                    data_rows.append(row_data)
            
            except Exception as e:
                logger.debug(f"Error parsing row {row_idx}: {str(e)}")
                continue
        
        # Convert to DataFrame
        if data_rows:
            df = pd.DataFrame(data_rows)
            logger.debug(f"Parsed {len(df)} rows from offset {offset}")
            return df
        else:
            logger.warning(f"No data rows found in page with offset {offset}")
            return pd.DataFrame()
    
    async def scrape(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """Override base scrape method to use scrape_all_bouts."""
        df = await self.scrape_all_bouts(**kwargs)
        return df.to_dict('records') if not df.empty else []
    
    def parse_page(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Parse page - implemented via _parse_bout_page."""
        offset = 0
        # Extract offset from URL if possible
        if 'offset=' in url:
            try:
                offset = int(url.split('offset=')[1].split('&')[0])
            except:
                pass
        
        df = self._parse_bout_page(html, offset)
        return df.to_dict('records') if not df.empty else []
    
    async def save_to_csv(self, filename: str = None, **scrape_kwargs) -> str:
        """Scrape all data and save to CSV file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/sumodb_bouts_{timestamp}.csv"
        
        logger.info(f"Starting full scrape and save to {filename}")
        
        df = await self.scrape_all_bouts(**scrape_kwargs)
        
        if not df.empty:
            # Ensure data directory exists
            import os
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            df.to_csv(filename, index=False)
            logger.info(f"Saved {len(df)} bouts to {filename}")
            return filename
        else:
            logger.error("No data to save")
            return None
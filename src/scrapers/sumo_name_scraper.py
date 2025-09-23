"""
SumoDB Name scraper for collecting wrestler profile data.
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

class SumoNameScraper(BaseScraper):
    """Specialized scraper for SumoDB wrestler profile data."""
    
    def __init__(self, **kwargs):
        """Initialize SumoDB name scraper."""
        super().__init__(**kwargs)
        self.base_url = "https://sumodb.sumogames.de/Query.aspx"
        self.params = {
            'show_form': '0',
            'columns': '1',
            'n_basho': '-1',
            'rowcount': '5',
            'show_total': 'on',
            'showheya': 'on',
            'showshusshin': 'on',
            'showbirthdate': 'on',
            'showhatsu': 'on',
            'showintai': 'on',
            'showheight': 'on',
            'showweight': 'on',
            'showhighest': 'on',
            'showcareerhigh': 'on',
            'showage': 'on',
            'sort_by': 'birthdate'
        }
        self.rows_per_page = 1000
        self.start_offset = 200000
        self.end_offset = 348000
        self.total_pages = (self.end_offset - self.start_offset) // self.rows_per_page + 1
    
    async def scrape_all_names(self, start_offset: int = None, max_pages: Optional[int] = None) -> pd.DataFrame:
        """
        Scrape all wrestler profile data from SumoDB.
        
        Args:
            start_offset: Starting offset (default: 200000)
            max_pages: Maximum number of pages to scrape (default: all)
        
        Returns:
            DataFrame with all wrestler profile data
        """
        if start_offset is None:
            start_offset = self.start_offset
            
        logger.info(f"Starting to scrape SumoDB wrestler profile data...")
        logger.info(f"Offset range: {start_offset} to {self.end_offset}")
        logger.info(f"Total pages: {self.total_pages}")
        
        if max_pages:
            pages_to_scrape = min(max_pages, self.total_pages)
        else:
            pages_to_scrape = self.total_pages
        
        all_dataframes = []
        current_offset = start_offset
        
        for page in range(pages_to_scrape):
            logger.info(f"Scraping page {page + 1}/{pages_to_scrape} (offset: {current_offset})")
            
            # Build URL for this page
            url = self._build_url(current_offset)
            
            # Fetch and parse page
            html = await self.fetch_page(url)
            if html:
                try:
                    df = self._parse_name_page(html, current_offset)
                    if not df.empty:
                        all_dataframes.append(df)
                        logger.info(f"Page {page + 1}: Found {len(df)} wrestler records")
                    else:
                        logger.warning(f"Page {page + 1}: No data found")
                except Exception as e:
                    logger.error(f"Error parsing page {page + 1}: {str(e)}")
            else:
                logger.error(f"Failed to fetch page {page + 1}")
            
            # Move to next offset
            current_offset += self.rows_per_page
            
            # Stop if we've reached the end offset
            if current_offset > self.end_offset:
                break
            
            # Add delay between requests
            if self.delay > 0:
                await asyncio.sleep(self.delay)
        
        # Combine all dataframes
        if all_dataframes:
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            logger.info(f"Total wrestler records scraped: {len(combined_df)}")
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
    
    def _parse_name_page(self, html: str, offset: int) -> pd.DataFrame:
        """Parse a single page of wrestler profile data from SumoDB."""
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
        # Row 0: ['Rikishi', 'Heya', 'Shusshin', 'Birth Date', 'Hatsu', 'Intai', 'Height', 'Weight', 'Highest Rank', 'Career High', '1>', 'Sum(total)']
        # Row 1: ['Date', 'Rank', 'Age', 'Record']
        # Row 2+: Actual wrestler data
        
        for row_idx, row in enumerate(rows[2:], start=2):  # Start from row 2
            cells = row.find_all(['td', 'th'])
            
            if len(cells) < 8:  # Need at least 8 columns for basic data
                continue
            
            try:
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                # Parse based on the known structure:
                # ['Yamanakayama', 'Magaki', 'Tochigi', '17.09.1970', '1986.03', '1997.03', '', '', 'Sd90', 'J13', '1987.09', 'Jd26e', '16.11', '6-1', '6']
                
                if len(cell_texts) >= 10:
                    rikishi = cell_texts[0]
                    heya = cell_texts[1] 
                    shusshin = cell_texts[2]
                    birth_date = cell_texts[3]
                    hatsu = cell_texts[4]  # Debut
                    intai = cell_texts[5]  # Retirement
                    height = cell_texts[6] if cell_texts[6] else None
                    weight = cell_texts[7] if cell_texts[7] else None
                    highest_rank = cell_texts[8] if cell_texts[8] else None
                    career_high = cell_texts[9] if cell_texts[9] else None
                    
                    # Additional data if available
                    date_info = cell_texts[10] if len(cell_texts) > 10 else None
                    rank_info = cell_texts[11] if len(cell_texts) > 11 else None
                    age_info = cell_texts[12] if len(cell_texts) > 12 else None
                    record_info = cell_texts[13] if len(cell_texts) > 13 else None
                    
                    row_data = {
                        'rikishi': rikishi,
                        'heya': heya,
                        'shusshin': shusshin,
                        'birth_date': birth_date,
                        'hatsu': hatsu,
                        'intai': intai,
                        'height': height,
                        'weight': weight,
                        'highest_rank': highest_rank,
                        'career_high': career_high,
                        'date_info': date_info,
                        'rank_info': rank_info,
                        'age_info': age_info,
                        'record_info': record_info,
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
        """Override base scrape method to use scrape_all_names."""
        df = await self.scrape_all_names(**kwargs)
        return df.to_dict('records') if not df.empty else []
    
    def parse_page(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Parse page - implemented via _parse_name_page."""
        offset = 200000
        # Extract offset from URL if possible
        if 'offset=' in url:
            try:
                offset = int(url.split('offset=')[1].split('&')[0])
            except:
                pass
        
        df = self._parse_name_page(html, offset)
        return df.to_dict('records') if not df.empty else []
    
    async def save_to_csv(self, filename: str = None, **scrape_kwargs) -> str:
        """Scrape all data and save to CSV file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/sumodb_wrestlers_{timestamp}.csv"
        
        logger.info(f"Starting full scrape and save to {filename}")
        
        df = await self.scrape_all_names(**scrape_kwargs)
        
        if not df.empty:
            # Ensure data directory exists
            import os
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            df.to_csv(filename, index=False)
            logger.info(f"Saved {len(df)} wrestler records to {filename}")
            return filename
        else:
            logger.error("No data to save")
            return None
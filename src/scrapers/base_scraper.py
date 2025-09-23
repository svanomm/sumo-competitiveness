"""
Base scraper class for asynchronous web scraping.
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Callable
from bs4 import BeautifulSoup
import logging
from abc import ABC, abstractmethod

from config.settings import Config

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all scrapers."""
    
    def __init__(self, max_concurrent: int = None, delay: float = None):
        """Initialize the scraper."""
        self.max_concurrent = max_concurrent or Config.MAX_CONCURRENT_REQUESTS
        self.delay = delay or Config.REQUEST_DELAY
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_session()
    
    async def start_session(self) -> None:
        """Start the aiohttp session."""
        timeout = aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT)
        self.session = aiohttp.ClientSession(
            headers=Config.get_headers(),
            timeout=timeout
        )
    
    async def close_session(self) -> None:
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str, **kwargs) -> Optional[str]:
        """Fetch a single page."""
        async with self.semaphore:
            try:
                if self.delay > 0:
                    await asyncio.sleep(self.delay)
                
                async with self.session.get(url, **kwargs) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.debug(f"Successfully fetched: {url}")
                        return content
                    else:
                        logger.warning(f"HTTP {response.status} for URL: {url}")
                        return None
            
            except asyncio.TimeoutError:
                logger.error(f"Timeout while fetching: {url}")
                return None
            except Exception as e:
                logger.error(f"Error fetching {url}: {str(e)}")
                return None
    
    async def fetch_pages(self, urls: List[str], **kwargs) -> List[Optional[str]]:
        """Fetch multiple pages concurrently."""
        tasks = [self.fetch_page(url, **kwargs) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    def parse_html(self, html: str, parser: str = "lxml") -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup."""
        return BeautifulSoup(html, parser)
    
    @abstractmethod
    async def scrape(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """Abstract method for scraping implementation."""
        pass
    
    @abstractmethod
    def parse_page(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Abstract method for parsing page content."""
        pass

class SumoScraper(BaseScraper):
    """Template scraper for sumo-related websites."""
    
    def __init__(self, base_urls: List[str], **kwargs):
        """Initialize with base URLs to scrape."""
        super().__init__(**kwargs)
        self.base_urls = base_urls
    
    async def scrape(self, url_generator: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """
        Main scraping method.
        
        Args:
            url_generator: Optional function to generate URLs dynamically
        
        Returns:
            List of scraped data dictionaries
        """
        all_data = []
        
        # Use provided URLs or generate them
        urls_to_scrape = self.base_urls
        if url_generator:
            urls_to_scrape.extend(url_generator())
        
        logger.info(f"Starting to scrape {len(urls_to_scrape)} URLs")
        
        # Fetch all pages
        html_contents = await self.fetch_pages(urls_to_scrape)
        
        # Parse each page
        for url, html in zip(urls_to_scrape, html_contents):
            if html:
                try:
                    page_data = self.parse_page(html, url)
                    all_data.extend(page_data)
                    logger.info(f"Parsed {len(page_data)} items from {url}")
                except Exception as e:
                    logger.error(f"Error parsing {url}: {str(e)}")
        
        logger.info(f"Total scraped items: {len(all_data)}")
        return all_data
    
    def parse_page(self, html: str, url: str) -> List[Dict[str, Any]]:
        """
        Parse a single page - IMPLEMENT THIS METHOD.
        
        Args:
            html: Raw HTML content
            url: Source URL
        
        Returns:
            List of parsed data dictionaries
        """
        # TODO: Implement specific parsing logic
        soup = self.parse_html(html)
        
        # Example structure - modify according to actual website structure
        data = []
        
        # Example: Parse wrestler information
        # wrestlers = soup.find_all('div', class_='wrestler-card')
        # for wrestler in wrestlers:
        #     data.append({
        #         'name': wrestler.find('h3').text.strip(),
        #         'rank': wrestler.find('.rank').text.strip() if wrestler.find('.rank') else None,
        #         'stable': wrestler.find('.stable').text.strip() if wrestler.find('.stable') else None,
        #         'source_url': url
        #     })
        
        return data
    
    def generate_tournament_urls(self, base_url: str, years: List[int], months: List[int]) -> List[str]:
        """
        Generate URLs for different tournaments.
        
        Args:
            base_url: Base URL pattern (should contain placeholders like {year}, {month})
            years: List of years to scrape
            months: List of months to scrape
        
        Returns:
            List of generated URLs
        """
        urls = []
        for year in years:
            for month in months:
                url = base_url.format(year=year, month=month)
                urls.append(url)
        return urls
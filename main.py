"""
Main application for running the SumoDB sumo bout scraper.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from config.settings import Config
from src.database.models import SumoDatabase
from src.scrapers.sumodb_scraper import SumoDBScraper

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SumoScrapingPipeline:
    """Main pipeline for scraping and storing SumoDB bout data."""
    
    def __init__(self):
        """Initialize the scraping pipeline."""
        self.database = SumoDatabase()
    
    async def run_scraping_pipeline(self, max_pages: int = None):
        """Run the complete scraping and data storage pipeline."""
        try:
            logger.info("Starting SumoDB scraping pipeline...")
            
            # Initialize database
            await self.database.init_database()
            logger.info("Database initialized")
            
            # Initialize scraper
            async with SumoDBScraper(delay=1.5) as scraper:
                logger.info("SumoDB scraper initialized")
                
                # Scrape data
                scraped_df = await scraper.scrape_all_bouts(max_pages=max_pages)
                logger.info(f"Scraped {len(scraped_df)} bouts")
                
                # Save to CSV
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_filename = f"data/sumodb_bouts_{timestamp}.csv"
                scraped_df.to_csv(csv_filename, index=False)
                logger.info(f"Data saved to {csv_filename}")
                
                # Optionally process and store in database
                # await self.process_scraped_data(scraped_df.to_dict('records'))
                
            logger.info("Scraping pipeline completed successfully")
            
        except Exception as e:
            logger.error(f"Error in scraping pipeline: {str(e)}")
            raise

async def main():
    """Main function to run the scraping pipeline."""
    print("SumoDB Scraper")
    print("=" * 40)
    print("This will scrape bout data from SumoDB (sumodb.sumogames.de)")
    print()
    
    # Ask user for scraping options
    choice = input("Enter 'test' for 3 pages, 'full' for all data, or number of pages: ").strip().lower()
    
    max_pages = None
    if choice == 'test':
        max_pages = 3
        print("Running test scrape (3 pages)")
    elif choice == 'full':
        print("Running full scrape (all ~77 pages)")
        print("This will take 2-3 hours with delays")
        confirm = input("Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Scraping cancelled")
            return
    else:
        try:
            max_pages = int(choice)
            print(f"Scraping {max_pages} pages")
        except ValueError:
            print("Invalid input. Running test scrape instead.")
            max_pages = 3
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    pipeline = SumoScrapingPipeline()
    await pipeline.run_scraping_pipeline(max_pages=max_pages)

if __name__ == "__main__":
    # Run the scraping pipeline
    asyncio.run(main())

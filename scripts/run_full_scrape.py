"""
Full SumoDB scraper - scrapes all bout data from 2000-2025.
"""

import asyncio
import logging
from datetime import datetime
from src.scrapers.sumodb_scraper import SumoDBScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'sumodb_scrape_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

async def run_full_sumodb_scrape():
    """Run the complete scrape of all SumoDB bout data."""
    print("SumoDB Full Scrape")
    print("=" * 50)
    print("This will scrape approximately 76,068 bout records")
    print("Estimated time: 2-3 hours with 1.5 second delays")
    print("Data will be saved to CSV file")
    print("=" * 50)
    
    confirm = input("Are you ready to start the full scrape? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Scraping cancelled.")
        return
    
    # Configure scraper with appropriate delays
    delay = 1.5  # 1.5 seconds between requests to be respectful
    
    print(f"Starting scrape with {delay} second delays between requests...")
    print("You can monitor progress in the log file and console output.")
    
    start_time = datetime.now()
    
    try:
        async with SumoDBScraper(delay=delay) as scraper:
            # Save directly to CSV with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/sumodb_all_bouts_{timestamp}.csv"
            
            print(f"Scraping all data and saving to: {filename}")
            
            saved_file = await scraper.save_to_csv(filename)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            if saved_file:
                print("\n" + "=" * 50)
                print("SCRAPING COMPLETED SUCCESSFULLY!")
                print(f"File saved: {saved_file}")
                print(f"Total time: {duration}")
                print("=" * 50)
            else:
                print("Scraping failed - check the logs for details")
    
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        print("Partial data may have been saved")
    except Exception as e:
        print(f"\nError during scraping: {str(e)}")
        print("Check the log file for detailed error information")

async def resume_scrape_from_offset(start_offset: int):
    """Resume scraping from a specific offset (useful if scraping was interrupted)."""
    print(f"Resuming scrape from offset: {start_offset}")
    
    # Calculate remaining pages
    total_rows = 76068
    rows_per_page = 1000
    remaining_rows = total_rows - start_offset
    
    if remaining_rows <= 0:
        print("No remaining data to scrape")
        return
    
    print(f"Approximately {remaining_rows} rows remaining")
    
    async with SumoDBScraper(delay=1.5) as scraper:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/sumodb_bouts_resume_{start_offset}_{timestamp}.csv"
        
        # Scrape remaining data
        df = await scraper.scrape_all_bouts(start_offset=start_offset)
        
        if not df.empty:
            df.to_csv(filename, index=False)
            print(f"Resume scraping completed. Saved {len(df)} bouts to {filename}")
        else:
            print("No data scraped during resume")

if __name__ == "__main__":
    print("SumoDB Complete Scraper")
    print("Options:")
    print("1. Full scrape from beginning")
    print("2. Resume from specific offset")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        asyncio.run(run_full_sumodb_scrape())
    elif choice == "2":
        try:
            offset = int(input("Enter offset to resume from: "))
            asyncio.run(resume_scrape_from_offset(offset))
        except ValueError:
            print("Invalid offset number")
    else:
        print("Invalid choice")
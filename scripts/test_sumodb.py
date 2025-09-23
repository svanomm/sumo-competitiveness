"""
Test script for SumoDB scraper - starts with a small sample.
"""

import asyncio
import logging
from src.scrapers.sumodb_scraper import SumoDBScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_sumodb_scraper():
    """Test the SumoDB scraper with a small sample."""
    
    # First, let's test with just 2 pages to verify the scraper works
    async with SumoDBScraper(delay=2.0) as scraper:  # 2 second delay between requests
        print("Testing SumoDB scraper with 2 pages...")
        
        # Test with just 2 pages first
        df = await scraper.scrape_all_bouts(start_offset=0, max_pages=2)
        
        if not df.empty:
            print(f"\nSuccessfully scraped {len(df)} bouts")
            print("\nFirst few rows:")
            print(df.head())
            print("\nColumn names:")
            print(df.columns.tolist())
            print(f"\nDataFrame shape: {df.shape}")
            
            # Save test results
            test_filename = "data/sumodb_test_sample.csv"
            df.to_csv(test_filename, index=False)
            print(f"\nTest data saved to {test_filename}")
        else:
            print("No data was scraped - check the parser logic")

async def run_full_scrape():
    """Run the full scrape of all bout data."""
    print("WARNING: This will scrape all 76+ pages and may take 2+ hours with delays!")
    confirm = input("Are you sure you want to proceed? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Scraping cancelled.")
        return
    
    async with SumoDBScraper(delay=1.5) as scraper:  # 1.5 second delay
        print("Starting full scrape of SumoDB bout data...")
        
        # Use the save_to_csv method for convenience
        filename = await scraper.save_to_csv()
        
        if filename:
            print(f"Full scrape completed and saved to {filename}")
        else:
            print("Scraping failed or no data found")

if __name__ == "__main__":
    print("SumoDB Scraper Test")
    print("=" * 30)
    
    # First run the test
    asyncio.run(test_sumodb_scraper())
    
    print("\n" + "=" * 50)
    print("Test completed. Check the results above.")
    print("If the test looks good, you can run the full scrape.")
    print("=" * 50)
    
    # Optionally run full scrape
    # asyncio.run(run_full_scrape())
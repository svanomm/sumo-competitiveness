"""
Test script for SumoDB scraper - scrapes first 3 pages and saves to CSV.
"""

import asyncio
import logging
from src.scrapers.sumodb_scraper import SumoDBScraper
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_3_pages_to_csv():
    """Test the SumoDB scraper with 3 pages and save to CSV."""
    
    print("Testing SumoDB scraper with 3 pages...")
    print("=" * 50)
    
    # Create timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/sumodb_3pages_test_{timestamp}.csv"
    
    async with SumoDBScraper(delay=2.0) as scraper:  # 2 second delay between requests
        print("Scraping first 3 pages (3000 bouts)...")
        
        # Test with 3 pages
        df = await scraper.scrape_all_bouts(start_offset=0, max_pages=3)
        
        if not df.empty:
            print(f"\nSuccessfully scraped {len(df)} bouts")
            print(f"Expected: ~3000 bouts")
            
            # Save to CSV
            import os
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            df.to_csv(filename, index=False)
            
            print(f"\nData saved to: {filename}")
            print(f"File size: {os.path.getsize(filename):,} bytes")
            
            print("\nDataFrame Info:")
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            print("\nFirst 5 rows:")
            print(df.head())
            
            print("\nLast 5 rows:")
            print(df.tail())
            
            print("\nData types:")
            print(df.dtypes)
            
            print("\nBasic statistics:")
            print(f"Unique basho (tournaments): {df['basho'].nunique()}")
            print(f"Unique wrestlers: {df['wrestler1'].nunique() + df['wrestler2'].nunique()}")
            print(f"Date range: {df['basho'].min()} to {df['basho'].max()}")
            
            # Check for any missing data
            print("\nMissing data check:")
            missing_data = df.isnull().sum()
            if missing_data.any():
                print(missing_data[missing_data > 0])
            else:
                print("No missing data found!")
            
            print(f"\n✅ Test completed successfully!")
            print(f"📁 File saved: {filename}")
            
        else:
            print("❌ No data was scraped - check the parser logic")

if __name__ == "__main__":
    asyncio.run(test_3_pages_to_csv())
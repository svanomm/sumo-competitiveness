"""
Test script for SumoDB Name scraper - tests first few pages.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.scrapers.sumo_name_scraper import SumoNameScraper
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_name_scraper():
    """Test the SumoDB name scraper with a small sample."""
    
    print("Testing SumoDB Name Scraper")
    print("=" * 50)
    print("Testing with first 2 pages from offset 200000...")
    
    # Create timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"data/sumodb_names_test_{timestamp}.csv"
    
    async with SumoNameScraper(delay=2.0) as scraper:  # 2 second delay between requests
        print("Scraping first 2 pages...")
        
        # Test with just 2 pages
        df = await scraper.scrape_all_names(start_offset=200000, max_pages=2)
        
        if not df.empty:
            print(f"\nSuccessfully scraped {len(df)} wrestler records")
            print(f"Expected: ~2000 records")
            
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
            print(f"Unique wrestlers: {df['rikishi'].nunique()}")
            print(f"Unique heya (stables): {df['heya'].nunique()}")
            print(f"Unique birthplaces: {df['shusshin'].nunique()}")
            
            # Check for any missing data
            print("\nMissing data check:")
            missing_data = df.isnull().sum()
            if missing_data.any():
                print(missing_data[missing_data > 0])
            else:
                print("No missing data found!")
            
            # Sample data analysis
            print("\nSample Data Analysis:")
            print("Birth date range:")
            print(f"  Earliest: {df['birth_date'].min()}")
            print(f"  Latest: {df['birth_date'].max()}")
            
            print("\nHeight/Weight info:")
            height_count = df['height'].notna().sum()
            weight_count = df['weight'].notna().sum()
            print(f"  Records with height: {height_count} ({height_count/len(df)*100:.1f}%)")
            print(f"  Records with weight: {weight_count} ({weight_count/len(df)*100:.1f}%)")
            
            print(f"\n✅ Test completed successfully!")
            print(f"📁 File saved: {filename}")
            
        else:
            print("❌ No data was scraped - check the parser logic")

async def estimate_full_scrape():
    """Estimate the scope of the full scrape."""
    print("\nFull Scrape Estimation:")
    print("=" * 30)
    
    start_offset = 200000
    end_offset = 348000
    rows_per_page = 1000
    
    total_pages = (end_offset - start_offset) // rows_per_page + 1
    estimated_records = total_pages * 1000
    
    print(f"Offset range: {start_offset:,} to {end_offset:,}")
    print(f"Total pages: {total_pages}")
    print(f"Estimated records: {estimated_records:,}")
    print(f"Estimated time (2s delay): {total_pages * 2 / 60:.1f} minutes")

if __name__ == "__main__":
    asyncio.run(test_name_scraper())
    asyncio.run(estimate_full_scrape())
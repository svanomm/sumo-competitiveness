"""
Full SumoDB Name scraper - scrapes all wrestler profile data.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path so we can import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.scrapers.sumo_name_scraper import SumoNameScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/sumodb_names_scrape_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

async def run_full_name_scrape():
    """Run the complete scrape of all SumoDB wrestler profile data."""
    print("SumoDB Wrestler Profile Scraper")
    print("=" * 50)
    print("This will scrape wrestler profile data from offset 200,000 to 348,000")
    print("Estimated records: ~149,000 wrestler career entries")
    print("Estimated time: ~5 minutes with 2 second delays")
    print("Data includes: names, heya, birthplace, debut/retirement dates, physical stats")
    print("=" * 50)
    
    confirm = input("Are you ready to start the full scrape? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Scraping cancelled.")
        return
    
    # Configure scraper with appropriate delays
    delay = 2.0  # 2 seconds between requests
    
    print(f"Starting scrape with {delay} second delays between requests...")
    print("You can monitor progress in the log file and console output.")
    
    start_time = datetime.now()
    
    try:
        async with SumoNameScraper(delay=delay) as scraper:
            # Save directly to CSV with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/sumodb_wrestlers_complete_{timestamp}.csv"
            
            print(f"Scraping all data and saving to: {filename}")
            
            saved_file = await scraper.save_to_csv(filename)
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            if saved_file:
                print("\n" + "=" * 50)
                print("SCRAPING COMPLETED SUCCESSFULLY!")
                print(f"File saved: {saved_file}")
                print(f"Total time: {duration}")
                
                # Load and show summary statistics
                import pandas as pd
                df = pd.read_csv(saved_file)
                print(f"Total records: {len(df):,}")
                print(f"Unique wrestlers: {df['rikishi'].nunique():,}")
                print(f"Unique heya (stables): {df['heya'].nunique()}")
                print(f"Records with height/weight: {df['height'].notna().sum():,}")
                print("=" * 50)
            else:
                print("Scraping failed - check the logs for details")
    
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        print("Partial data may have been saved")
    except Exception as e:
        print(f"\nError during scraping: {str(e)}")
        print("Check the log file for detailed error information")

async def run_batch_name_scrape(batch_size: int = 10):
    """Run the scrape in batches for better progress tracking."""
    print("SumoDB Wrestler Profile Batch Scraper")
    print("=" * 50)
    print(f"Scraping in batches of {batch_size} pages")
    print("Progress will be saved after each batch")
    print("=" * 50)
    
    start_offset = 200000
    end_offset = 348000
    rows_per_page = 1000
    total_pages = (end_offset - start_offset) // rows_per_page + 1
    
    print(f"Total pages to scrape: {total_pages}")
    print(f"Estimated total time: {(total_pages * 2) / 60:.1f} minutes")
    
    confirm = input("Start batch scraping? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Scraping cancelled.")
        return
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"data/sumodb_names_batch_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Track progress
    progress_file = output_dir / "progress.txt"
    final_file = output_dir / "sumodb_wrestlers_final.csv"
    
    all_dataframes = []
    
    try:
        async with SumoNameScraper(delay=2.0) as scraper:
            for batch_num in range(0, total_pages, batch_size):
                batch_start = batch_num
                batch_end = min(batch_num + batch_size, total_pages)
                
                print(f"\nBatch {batch_num//batch_size + 1}: Pages {batch_start+1}-{batch_end}")
                
                # Calculate offset for this batch
                start_batch_offset = start_offset + (batch_start * rows_per_page)
                pages_in_batch = batch_end - batch_start
                
                batch_df = await scraper.scrape_all_names(
                    start_offset=start_batch_offset, 
                    max_pages=pages_in_batch
                )
                
                if not batch_df.empty:
                    # Save batch file
                    batch_file = output_dir / f"batch_{batch_num//batch_size + 1:03d}.csv"
                    batch_df.to_csv(batch_file, index=False)
                    
                    # Add to collection
                    all_dataframes.append(batch_df)
                    
                    # Update progress
                    with open(progress_file, 'w') as f:
                        f.write(f"Completed batches: {batch_num//batch_size + 1}\n")
                        f.write(f"Last offset: {start_batch_offset + len(batch_df)}\n")
                        f.write(f"Total rows scraped: {sum(len(df) for df in all_dataframes)}\n")
                        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    
                    print(f"Batch saved: {len(batch_df)} rows -> {batch_file}")
                    print(f"Total scraped so far: {sum(len(df) for df in all_dataframes)} rows")
                else:
                    print(f"Warning: Batch {batch_num//batch_size + 1} returned no data")
        
        # Combine all batches into final file
        if all_dataframes:
            print("\nCombining all batches into final file...")
            import pandas as pd
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            combined_df.to_csv(final_file, index=False)
            
            print(f"\nBATCH SCRAPING COMPLETED!")
            print(f"Total wrestler records scraped: {len(combined_df):,}")
            print(f"Unique wrestlers: {combined_df['rikishi'].nunique():,}")
            print(f"Final file: {final_file}")
            print(f"Batch files saved in: {output_dir}")
        else:
            print("No data was scraped")
    
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        print(f"Partial data saved in: {output_dir}")
    except Exception as e:
        print(f"\nError during scraping: {str(e)}")
        print(f"Partial data saved in: {output_dir}")

if __name__ == "__main__":
    print("SumoDB Wrestler Profile Scraper")
    print("Options:")
    print("1. Full scrape (single file)")
    print("2. Batch scrape (progress tracking)")
    
    choice = input("Enter choice (1 or 2): ")
    
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    if choice == "1":
        asyncio.run(run_full_name_scrape())
    elif choice == "2":
        try:
            batch_size = int(input("Enter batch size (pages per batch, default 10): ") or "10")
            asyncio.run(run_batch_name_scrape(batch_size))
        except ValueError:
            print("Invalid batch size")
    else:
        print("Invalid choice")
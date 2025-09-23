"""
Batch SumoDB scraper - scrapes data in chunks and saves progressively.
"""

import asyncio
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from src.scrapers.sumodb_scraper import SumoDBScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'sumodb_batch_scrape_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

async def run_batch_scrape(batch_size: int = 10, delay: float = 1.5):
    """
    Run SumoDB scrape in batches, saving progress after each batch.
    
    Args:
        batch_size: Number of pages to scrape per batch
        delay: Delay between requests in seconds
    """
    print("SumoDB Batch Scraper")
    print("=" * 50)
    print(f"Scraping in batches of {batch_size} pages")
    print(f"Delay between requests: {delay} seconds")
    print("Progress will be saved after each batch")
    print("=" * 50)
    
    total_rows = 76068
    rows_per_page = 1000
    total_pages = (total_rows // rows_per_page) + 1
    
    print(f"Total pages to scrape: {total_pages}")
    print(f"Estimated total time: {(total_pages * delay) / 3600:.1f} hours")
    
    confirm = input("Start batch scraping? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Scraping cancelled.")
        return
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"data/sumodb_batch_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Track progress
    progress_file = output_dir / "progress.txt"
    final_file = output_dir / "sumodb_all_bouts_final.csv"
    
    all_dataframes = []
    
    try:
        async with SumoDBScraper(delay=delay) as scraper:
            for batch_num in range(0, total_pages, batch_size):
                batch_start = batch_num
                batch_end = min(batch_num + batch_size, total_pages)
                
                print(f"\nBatch {batch_num//batch_size + 1}: Pages {batch_start+1}-{batch_end}")
                
                # Scrape this batch
                start_offset = batch_start * rows_per_page
                pages_in_batch = batch_end - batch_start
                
                batch_df = await scraper.scrape_all_bouts(
                    start_offset=start_offset, 
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
                        f.write(f"Last offset: {start_offset + len(batch_df)}\n")
                        f.write(f"Total rows scraped: {sum(len(df) for df in all_dataframes)}\n")
                        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                    
                    print(f"Batch saved: {len(batch_df)} rows -> {batch_file}")
                    print(f"Total scraped so far: {sum(len(df) for df in all_dataframes)} rows")
                else:
                    print(f"Warning: Batch {batch_num//batch_size + 1} returned no data")
        
        # Combine all batches into final file
        if all_dataframes:
            print("\nCombining all batches into final file...")
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            combined_df.to_csv(final_file, index=False)
            
            print(f"\nBATCH SCRAPING COMPLETED!")
            print(f"Total bouts scraped: {len(combined_df)}")
            print(f"Final file: {final_file}")
            print(f"Batch files saved in: {output_dir}")
        else:
            print("No data was scraped")
    
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        print(f"Partial data saved in: {output_dir}")
        print("You can resume by checking the progress.txt file")
    except Exception as e:
        print(f"\nError during scraping: {str(e)}")
        print(f"Partial data saved in: {output_dir}")

async def resume_batch_scrape(batch_dir: str, batch_size: int = 10, delay: float = 1.5):
    """Resume a batch scrape from where it left off."""
    batch_path = Path(batch_dir)
    progress_file = batch_path / "progress.txt"
    
    if not progress_file.exists():
        print("No progress file found - cannot resume")
        return
    
    # Read progress
    with open(progress_file, 'r') as f:
        progress_lines = f.readlines()
    
    completed_batches = 0
    last_offset = 0
    
    for line in progress_lines:
        if line.startswith("Completed batches:"):
            completed_batches = int(line.split(":")[1].strip())
        elif line.startswith("Last offset:"):
            last_offset = int(line.split(":")[1].strip())
    
    print(f"Resuming from batch {completed_batches + 1}, offset {last_offset}")
    
    # Continue scraping
    total_pages = 77  # Known total
    remaining_batches = range(completed_batches, total_pages, batch_size)
    
    # Load existing data
    existing_files = list(batch_path.glob("batch_*.csv"))
    all_dataframes = []
    
    for file in sorted(existing_files):
        df = pd.read_csv(file)
        all_dataframes.append(df)
    
    print(f"Loaded {len(all_dataframes)} existing batches with {sum(len(df) for df in all_dataframes)} rows")
    
    # Continue scraping...
    # (Similar logic to run_batch_scrape but starting from the resume point)

if __name__ == "__main__":
    print("SumoDB Batch Scraper")
    print("Options:")
    print("1. Start new batch scrape")
    print("2. Resume batch scrape")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        try:
            batch_size = int(input("Enter batch size (pages per batch, default 10): ") or "10")
            delay = float(input("Enter delay between requests (seconds, default 1.5): ") or "1.5")
            asyncio.run(run_batch_scrape(batch_size, delay))
        except ValueError:
            print("Invalid input")
    elif choice == "2":
        batch_dir = input("Enter batch directory path: ")
        asyncio.run(resume_batch_scrape(batch_dir))
    else:
        print("Invalid choice")
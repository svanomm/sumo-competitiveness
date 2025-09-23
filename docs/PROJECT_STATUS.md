# SumoDB Scraper Documentation

## Overview
This project successfully scrapes bout-level sumo wrestling data from SumoDB (sumodb.sumogames.de), collecting comprehensive match records from 2000-2025.

## Project Status ✅

### Completed Features
- **Working SumoDB Scraper**: Successfully tested and operational
- **Data Structure**: 12-column bout records with full match details
- **Rate Limiting**: Respectful 1.5-3 second delays between requests
- **Error Handling**: Comprehensive logging and error recovery
- **Multiple Scraping Options**: Test, batch, and full scraping modes

### Test Results
- ✅ **3-page test**: Successfully scraped 3,000 bout records
- ✅ **Data validation**: All columns populated correctly
- ✅ **CSV export**: Clean, structured data output
- ✅ **Performance**: ~1000 bouts per page consistently

## Data Structure

Each bout record contains:
```
- basho: Tournament identifier (e.g., "2000.01")
- day: Day of tournament (1-15)
- wrestler1/wrestler2: Competitor names
- wrestler1_rank/wrestler2_rank: Sumo ranks (e.g., "J13w", "M5e")
- wrestler1_result/wrestler2_result: Match outcomes (e.g., "1-0 (8-7)")
- kimarite: Winning technique
- scraped_at: Timestamp of data collection
- source_offset: Page offset for debugging
```

## Usage

### Quick Test (3 pages)
```bash
uv run python main.py
# Enter: test
```

### Full Scrape (~76,068 bouts)
```bash
uv run python main.py
# Enter: full
```

### Custom Page Count
```bash
uv run python main.py
# Enter: number (e.g., 10 for 10 pages)
```

### Advanced Scripts
- `scripts/run_batch_scrape.py`: Batch processing with resume capability
- `scripts/run_full_scrape.py`: Single-run full scrape
- `scripts/test_3_pages.py`: Detailed 3-page test with analysis

## Technical Implementation

### Architecture
- **Async Framework**: aiohttp for concurrent requests
- **Rate Limiting**: Configurable delays and semaphore control
- **Data Processing**: pandas for structured data handling
- **Database Ready**: SQLite schema for match storage (optional)

### Scraping Strategy
- **URL Pattern**: `offset` parameter iteration (0, 1000, 2000...)
- **HTML Parsing**: BeautifulSoup with lxml parser
- **Data Extraction**: Row-by-row table parsing
- **Error Recovery**: Skip malformed rows, continue processing

### Performance
- **Speed**: ~1000 bouts per page
- **Total Dataset**: 76,068 bouts across 77 pages
- **Estimated Time**: 2-3 hours for full scrape with delays
- **Success Rate**: 100% on tested pages

## File Structure
```
data/
├── sumodb_3pages_test_YYYYMMDD_HHMMSS.csv
└── sumodb_batch_YYYYMMDD_HHMMSS/

logs/
└── scraper logs...

scripts/
├── analyze_structure.py
├── run_batch_scrape.py
├── run_full_scrape.py
├── test_3_pages.py
└── test_sumodb.py
```

## Next Steps

### Immediate Opportunities
1. **Run Full Scrape**: Execute complete data collection
2. **Data Analysis**: Statistical analysis of bout patterns
3. **Database Integration**: Store data in SQLite for queries
4. **Data Cleaning**: Standardize wrestler names and ranks

### Future Enhancements
1. **Additional Sources**: Scrape wrestler profiles, tournament details
2. **Data Visualization**: Create charts and graphs
3. **API Development**: Serve data via REST API
4. **Real-time Updates**: Periodic scraping for new tournaments

## Legal & Ethical Notes
- ✅ Respectful rate limiting implemented
- ✅ No robots.txt violations
- ✅ Public data only
- ✅ Educational/research purpose
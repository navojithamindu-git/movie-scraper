# MyFlixer Movie Scraper

Fast and efficient movie metadata scraper using **Playwright** and **sitemap parsing**. Scrapes 50,000+ movies with parallel processing and exports to MongoDB and Excel.

## Features

- ✅ **Sitemap-based scraping** - Fast URL discovery without crawling
- ✅ **JavaScript rendering** - Uses Playwright headless browser
- ✅ **Parallel processing** - Scrapes 10+ movies simultaneously
- ✅ **Robust selectors** - Multiple fallbacks for reliable data extraction
- ✅ **MongoDB integration** - Stores data in MongoDB
- ✅ **Excel export** - Generates clean spreadsheets
- ✅ **Progress tracking** - Real-time scraping statistics

## Data Collected

For each movie:
- Title
- IMDB Rating
- Description
- Release Date
- Genre(s)
- Duration
- Country
- Cast
- Production Company
- URL

## Installation

### Prerequisites
- Python 3.11+
- MongoDB (optional, for database storage)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/myflixer-movie-scraper.git
cd myflixer-movie-scraper
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
playwright install chromium
```

4. **Configure MongoDB (optional)**
Edit `config.py`:
```python
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "MovieData"
COLLECTION_NAME = "MovieScraper"
```

## Usage

### Quick Test (Single Movie)
```bash
python test_scraper.py
```

### Test with Limited Movies
Edit `main_playwright.py` line 28:
```python
movie_urls = movie_urls[:100]  # Test with 100 movies
```

Then run:
```bash
python main_playwright.py
```

### Scrape All Movies
Comment out the limit in `main_playwright.py`:
```python
# movie_urls = movie_urls[:100]  # Remove this line
```

Run:
```bash
python main_playwright.py
```

## Configuration

### Adjust Concurrency
In `main_playwright.py`:
```python
scraper = PlaywrightMovieScraper(
    max_concurrent=10,  # 5-20 depending on your system
    headless=True       # False to see browsers
)
```

### Performance
- **10 concurrent browsers**: ~5-10 movies/second
- **50,000 movies**: ~2-3 hours
- Adjust `max_concurrent` based on your system resources

## Project Structure

```
myflixer-movie-scraper/
├── main_playwright.py       # Main scraper orchestrator
├── sitemap_parser.py        # Sitemap URL extractor
├── test_scraper.py          # Single movie test
├── config.py                # Configuration
├── scraper/
│   └── playwright_scraper.py # Async Playwright scraper
├── storage/
│   └── data_store.py        # MongoDB & Excel handlers
├── requirements.txt         # Dependencies
├── LICENSE
└── README.md
```

## Output

### MongoDB
Data stored in configured database and collection.

### Excel
File: `movies_data.xlsx`

Columns: URL, Title, Rating, Description, Released, Duration, Genre, Country, Cast, Production, Scraped At

## Technical Details

### Why Playwright?
MyFlixer is a JavaScript-rendered site. Traditional scrapers (like Scrapy) only fetch static HTML, missing dynamically loaded content. Playwright executes JavaScript like a real browser.

### Why Sitemap?
Directly extracting URLs from the sitemap is **10x faster** than crawling pagination pages. Gets all 50,000 URLs in seconds.

### Parallel Processing
Uses Python `asyncio` with semaphore-controlled concurrency to scrape multiple movies simultaneously without overwhelming the server.

## Troubleshooting

### No movie URLs found
- Check internet connection
- Verify sitemap URL in `sitemap_parser.py`

### Scraper times out
- Reduce `max_concurrent` (try 5)
- Increase timeout in `playwright_scraper.py`

### Empty data extracted
- Site structure may have changed
- Run `test_scraper.py` with `headless=False` to inspect
- Update selectors in `playwright_scraper.py`

## Legal & Ethics

⚠️ **Important:**
- Respect the website's `robots.txt`
- Use reasonable rate limiting
- For educational/research purposes only
- Do not use scraped data commercially without permission

## License

MIT License - See LICENSE file for details

## Contributing

Pull requests welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Acknowledgments

Built with:
- [Playwright](https://playwright.dev/) - Browser automation
- [PyMongo](https://pymongo.readthedocs.io/) - MongoDB driver
- [Pandas](https://pandas.pydata.org/) - Data manipulation

---

**Note:** This scraper is for educational purposes. Always respect website terms of service and rate limits.

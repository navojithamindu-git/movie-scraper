"""
Quick test script to verify the scraper works before running on all movies
"""

import asyncio
from scraper.playwright_scraper import PlaywrightMovieScraper


async def test_single_movie():
    """Test scraping a single movie"""

    test_url = "https://myflixerz.to/movie/the-way-to-you-144003"

    print(f"Testing scraper with URL: {test_url}\n")

    scraper = PlaywrightMovieScraper(max_concurrent=1, headless=False)
    results = await scraper.scrape_all([test_url])

    if results:
        movie = results[0]
        print("\n" + "="*70)
        print("SCRAPED DATA:")
        print("="*70)
        for key, value in movie.items():
            print(f"{key:15} : {value}")
        print("="*70)
        print("\n[SUCCESS] Test successful! The scraper is working correctly.")
        print("  You can now run main_playwright.py to scrape all movies.")
    else:
        print("\n[FAILED] Test failed. No data was scraped.")
        print("  Please check the selectors or URL.")


if __name__ == "__main__":
    asyncio.run(test_single_movie())

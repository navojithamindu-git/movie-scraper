"""
Quick test script to verify the scraper works before running on all movies
"""

import asyncio
from scraper.playwright_scraper import PlaywrightMovieScraper
from storage.data_store import DataStore


async def test_single_movie():
    """Test scraping a single movie and ingesting into RecoMo"""

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

        # Send to RecoMo API
        print("\n[INGEST] Sending to RecoMo API...")
        store = DataStore(api_url="http://localhost:8000")
        try:
            result = store.insert_movie(movie)
            print(f"[INGEST] Result: {result}")
            print("\n[SUCCESS] Movie scraped + ingested + embedded!")
        except Exception as e:
            print(f"[INGEST] Failed: {e}")
            print("  Make sure RecoMo backend is running (uvicorn app.main:app --reload)")
    else:
        print("\n[FAILED] Test failed. No data was scraped.")
        print("  Please check the selectors or URL.")


if __name__ == "__main__":
    asyncio.run(test_single_movie())

"""
Phase 1: Scrape all movie data from sitemap and save to scraped_movies.json
Resumable — skips already-scraped URLs on restart.

Usage: python main_playwright.py
"""

import asyncio
import json
import os
import time

from sitemap_parser import SitemapParser
from scraper.playwright_scraper import PlaywrightMovieScraper

SCRAPED_FILE = "scraped_movies.json"
URL_CACHE_FILE = "movie_urls_cache.json"
BATCH_SIZE = 500


def load_scraped():
    if os.path.exists(SCRAPED_FILE):
        with open(SCRAPED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_scraped(movies):
    with open(SCRAPED_FILE, "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=2)


def get_all_urls():
    """Load URLs from cache if available, otherwise fetch from sitemap."""
    if os.path.exists(URL_CACHE_FILE):
        with open(URL_CACHE_FILE, "r", encoding="utf-8") as f:
            urls = json.load(f)
        print(f"Loaded {len(urls)} URLs from cache ({URL_CACHE_FILE})")
        return urls

    print("Fetching movie URLs from sitemap...")
    parser = SitemapParser(base_url="https://myflixerz.to")
    urls = parser.get_all_movie_urls()

    if urls:
        with open(URL_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(urls, f)
        print(f"Cached {len(urls)} URLs to {URL_CACHE_FILE}")

    return urls


async def main():
    print("=" * 70)
    print("PHASE 1: SCRAPE MOVIE DATA")
    print("=" * 70)
    print(f"Output: {SCRAPED_FILE}")
    print(f"Batch size: {BATCH_SIZE}")
    print("Stop anytime with Ctrl+C — progress is saved.\n")

    all_urls = get_all_urls()

    if not all_urls:
        print("No movie URLs found. Check your connection and try again.")
        return

    print(f"Found {len(all_urls)} movie URLs")

    # Find remaining URLs
    existing = load_scraped()
    scraped_urls = {m["url"] for m in existing}
    remaining_urls = [u for u in all_urls if u not in scraped_urls]

    if not remaining_urls:
        print(f"\nAll {len(all_urls)} movies already scraped!")
        print(f"Run 'python ingest.py' to send them to the API.")
        return

    print(f"Already scraped: {len(existing)}")
    print(f"Remaining: {len(remaining_urls)}")

    scraper = PlaywrightMovieScraper(max_concurrent=3, headless=True)

    for batch_start in range(0, len(remaining_urls), BATCH_SIZE):
        batch_urls = remaining_urls[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (len(remaining_urls) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"\n--- Batch {batch_num}/{total_batches} ({len(batch_urls)} URLs) ---")

        results = await scraper.scrape_all(batch_urls)

        # Find failed URLs and retry once with lower concurrency
        succeeded_urls = {m["url"] for m in results}
        failed_urls = [u for u in batch_urls if u not in succeeded_urls]

        if failed_urls:
            print(f"\nRetrying {len(failed_urls)} failed URLs (concurrency=3)...")
            retry_scraper = PlaywrightMovieScraper(max_concurrent=3, headless=True)
            retry_results = await retry_scraper.scrape_all(failed_urls)
            results.extend(retry_results)
            still_failed = len(failed_urls) - len(retry_results)
            if still_failed:
                print(f"  {still_failed} URLs failed after retry (skipped)")

        existing.extend(results)
        save_scraped(existing)
        print(f"Checkpoint: {len(existing)} total movies saved to {SCRAPED_FILE}")

    print(f"\nScraping complete: {len(existing)} movies in {SCRAPED_FILE}")
    print(f"Next step: python ingest.py")


if __name__ == "__main__":
    start_time = time.time()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nStopped. Progress saved — run again to resume.")

    elapsed = time.time() - start_time
    print(f"\nTime: {elapsed/60:.1f} minutes")
u
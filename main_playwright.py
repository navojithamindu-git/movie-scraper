import asyncio
from sitemap_parser import SitemapParser
from scraper.playwright_scraper import PlaywrightMovieScraper
from storage.data_store import DataStore
from config import MONGO_URI, DB_NAME, COLLECTION_NAME
import time


async def main():
    """Main function to orchestrate sitemap parsing and movie scraping"""

    print("="*70)
    print("MYFLIXER MOVIE SCRAPER - PLAYWRIGHT VERSION")
    print("="*70)

    # Step 1: Get all movie URLs from sitemap
    print("\n[1/4] Fetching movie URLs from sitemap...")
    parser = SitemapParser(base_url="https://myflixerz.to")
    movie_urls = parser.get_all_movie_urls()

    if not movie_urls:
        print("❌ No movie URLs found in sitemap. Exiting.")
        return

    print(f"✓ Found {len(movie_urls)} movie URLs")

    # Optional: Limit for testing (uncomment and adjust as needed)
    # movie_urls = movie_urls[:100]  # Test with first 100 movies
    # print(f"  → Limited to {len(movie_urls)} movies for testing")

    # Step 2: Scrape all movies with Playwright
    print(f"\n[2/4] Scraping movie details with Playwright...")
    scraper = PlaywrightMovieScraper(
        max_concurrent=10,  # Adjust based on your system (5-15 is good)
        headless=True       # Set to False to see browsers in action
    )

    movies_data = await scraper.scrape_all(movie_urls)

    if not movies_data:
        print("❌ No movies scraped successfully. Exiting.")
        return

    print(f"✓ Successfully scraped {len(movies_data)} movies")

    # Step 3: Save to MongoDB
    print(f"\n[3/4] Saving to MongoDB...")
    store = DataStore(MONGO_URI, DB_NAME, COLLECTION_NAME)

    saved_count = 0
    for movie in movies_data:
        try:
            store.insert_movie(movie)
            saved_count += 1
        except Exception as e:
            print(f"  ✗ Error saving movie '{movie.get('title', 'Unknown')}': {e}")

    print(f"✓ Saved {saved_count} movies to MongoDB")

    # Step 4: Export to Excel
    print(f"\n[4/4] Exporting to Excel...")
    try:
        excel_file = store.export_to_excel(movies_data)
        print(f"✓ Exported to {excel_file}")
    except Exception as e:
        print(f"✗ Error exporting to Excel: {e}")

    # Summary
    print("\n" + "="*70)
    print("SCRAPING COMPLETED!")
    print("="*70)
    print(f"Total URLs found:     {len(movie_urls)}")
    print(f"Successfully scraped: {len(movies_data)}")
    print(f"Saved to MongoDB:     {saved_count}")
    print(f"Excel export:         ✓")
    print("="*70)


if __name__ == "__main__":
    start_time = time.time()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Scraping interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

    elapsed = time.time() - start_time
    print(f"\nTotal execution time: {elapsed/60:.2f} minutes ({elapsed:.1f} seconds)")

import asyncio
import random
from playwright.async_api import async_playwright, Browser, Page
from typing import List, Dict, Optional
import time
from datetime import datetime


class PlaywrightMovieScraper:
    def __init__(self, max_concurrent: int = 10, headless: bool = True):
        """
        Initialize the scraper

        Args:
            max_concurrent: Number of concurrent browser contexts (default: 10)
            headless: Run browser in headless mode (default: True)
        """
        self.max_concurrent = max_concurrent
        self.headless = headless
        self.scraped_count = 0
        self.failed_count = 0
        self.start_time = None

    async def scrape_movie_details(self, page: Page, url: str) -> Optional[Dict]:
        """Scrape details from a single movie page"""
        try:
            # Navigate to the page
            await page.goto(url, timeout=60000, wait_until='domcontentloaded')

            # Wait for main content to load
            await page.wait_for_selector('.heading-name, .description', timeout=10000)

            # Determine type from URL
            content_type = 'TV Series' if '/tv/' in url else 'Movie'

            # Extract movie details
            movie_data = {
                'url': url,
                'type': content_type,
                'scraped_at': datetime.now().isoformat()
            }

            # Title
            try:
                title = await page.text_content('.heading-name', timeout=3000)
                if title:
                    movie_data['title'] = title.strip()
            except:
                pass

            # Poster image
            try:
                poster = await page.wait_for_selector('img.film-poster-img', timeout=5000)
                if poster:
                    # Try src first, then data-src (lazy-loaded images)
                    src = await poster.get_attribute('src')
                    if not src or src.startswith('data:'):
                        src = await poster.get_attribute('data-src')
                    if src:
                        movie_data['image_url'] = src
            except:
                pass

            # IMDB Rating
            try:
                rating = await page.text_content('.btn-imdb', timeout=3000)
                if rating:
                    movie_data['rating'] = rating.strip()
            except:
                pass

            # Description
            try:
                description = await page.text_content('.description', timeout=3000)
                if description:
                    # Clean up extra whitespace and newlines
                    description_clean = ' '.join(description.split())
                    movie_data['description'] = description_clean
            except:
                pass

            # Parse all row-line elements for metadata
            try:
                row_lines = await page.query_selector_all('.row-line')
                for row in row_lines:
                    row_text = await row.text_content()
                    if not row_text:
                        continue

                    row_text = row_text.strip()

                    # Released date
                    if 'Released:' in row_text:
                        released = row_text.replace('Released:', '').strip()
                        movie_data['released'] = released

                    # Duration
                    elif 'Duration:' in row_text:
                        duration = row_text.replace('Duration:', '').strip()
                        # Clean up whitespace and newlines
                        duration_clean = ' '.join(duration.split())
                        movie_data['duration'] = duration_clean

                    # Genre
                    elif 'Genre:' in row_text:
                        # Get genre links
                        genre_links = await row.query_selector_all('a')
                        genres = []
                        for link in genre_links:
                            genre_text = await link.text_content()
                            if genre_text:
                                genres.append(genre_text.strip())
                        if genres:
                            # Convert list to comma-separated string
                            movie_data['genre'] = ', '.join(genres)
                        else:
                            # Fallback to text content
                            genre = row_text.replace('Genre:', '').strip()
                            movie_data['genre'] = genre

                    # Country
                    elif 'Country:' in row_text:
                        # Get country links
                        country_links = await row.query_selector_all('a')
                        countries = []
                        for link in country_links:
                            country_text = await link.text_content()
                            if country_text:
                                countries.append(country_text.strip())
                        if countries:
                            movie_data['country'] = ', '.join(countries)
                        else:
                            # Fallback to text content
                            country = row_text.replace('Country:', '').strip()
                            movie_data['country'] = country

                    # Cast
                    elif 'Casts:' in row_text:
                        cast = row_text.replace('Casts:', '').strip()
                        if cast and cast != 'N/A':
                            # Clean up whitespace and newlines
                            cast_clean = ' '.join(cast.split())
                            movie_data['cast'] = cast_clean

                    # Production
                    elif 'Production:' in row_text:
                        # Get production links
                        prod_links = await row.query_selector_all('a')
                        productions = []
                        for link in prod_links:
                            prod_text = await link.text_content()
                            if prod_text:
                                productions.append(prod_text.strip())
                        if productions:
                            movie_data['production'] = ', '.join(productions)
                        else:
                            # Fallback to text content
                            production = row_text.replace('Production:', '').strip()
                            movie_data['production'] = production
            except Exception as e:
                print(f"  Warning: Error parsing row-lines: {str(e)[:50]}")

            self.scraped_count += 1

            # Print progress
            if self.scraped_count % 10 == 0:
                elapsed = time.time() - self.start_time
                rate = self.scraped_count / elapsed
                print(f"[Progress] Scraped {self.scraped_count} movies | Rate: {rate:.1f} movies/sec | Failed: {self.failed_count}")

            return movie_data

        except Exception as e:
            self.failed_count += 1
            print(f"[Error] Failed to scrape {url}: {str(e)[:100]}")
            return None

    async def scrape_single(self, browser: Browser, url: str, semaphore: asyncio.Semaphore) -> Optional[Dict]:
        """Scrape a single movie URL with semaphore control"""
        async with semaphore:
            # Random delay to avoid triggering rate limits
            await asyncio.sleep(random.uniform(1.5, 4.0))
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()

            try:
                result = await self.scrape_movie_details(page, url)
                return result
            finally:
                await context.close()

    async def scrape_all(self, movie_urls: List[str]) -> List[Dict]:
        """Scrape all movies with parallel processing"""
        print(f"\n{'='*70}")
        print(f"Starting Playwright scraper")
        print(f"Total URLs: {len(movie_urls)}")
        print(f"Concurrent browsers: {self.max_concurrent}")
        print(f"Headless mode: {self.headless}")
        print(f"{'='*70}\n")

        self.start_time = time.time()
        self.scraped_count = 0
        self.failed_count = 0

        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=self.headless)

            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(self.max_concurrent)

            # Create tasks for all URLs
            tasks = [
                self.scrape_single(browser, url, semaphore)
                for url in movie_urls
            ]

            # Execute all tasks
            results = await asyncio.gather(*tasks, return_exceptions=True)

            await browser.close()

        # Filter out None and exceptions
        valid_results = [r for r in results if r and isinstance(r, dict)]

        elapsed = time.time() - self.start_time
        print(f"\n{'='*70}")
        print(f"Scraping completed!")
        print(f"Total time: {elapsed:.2f} seconds")
        print(f"Successfully scraped: {len(valid_results)}")
        print(f"Failed: {self.failed_count}")
        print(f"Average rate: {len(valid_results)/elapsed:.2f} movies/sec")
        print(f"{'='*70}\n")

        return valid_results


async def main():
    """Test the scraper with sample URLs"""
    # Test URLs - replace with actual URLs from sitemap
    test_urls = [
        "https://myflixerz.to/movie/the-way-to-you-144003",
    ]

    scraper = PlaywrightMovieScraper(max_concurrent=5, headless=False)
    results = await scraper.scrape_all(test_urls)

    print("\nSample results:")
    for movie in results[:3]:
        print(f"\nTitle: {movie.get('title', 'N/A')}")
        print(f"Rating: {movie.get('rating', 'N/A')}")
        print(f"Genre: {movie.get('genre', 'N/A')}")
        print(f"URL: {movie.get('url', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())

"""
Phase 2: Ingest scraped movies from scraped_movies.json into RecoMo API.
Resumable — already-ingested URLs are pre-filtered locally (fast).

Usage: python ingest.py
       python ingest.py --limit 5000
       python ingest.py --api http://localhost:8000

Requires: RecoMo backend running (uvicorn app.main:app --reload)
"""

import argparse
import json
import os
import sys
import time

import requests

from storage.data_store import DataStore

SCRAPED_FILE = "scraped_movies.json"


def fetch_existing_urls(api_url):
    """Fetch all URLs already in the DB — one fast query to avoid slow per-movie skips."""
    print("Fetching already-ingested URLs from DB...")
    try:
        resp = requests.get(f"{api_url}/api/movies/urls", timeout=30)
        resp.raise_for_status()
        urls = set(resp.json())
        print(f"  {len(urls)} movies already in DB — skipping them.\n")
        return urls
    except Exception as e:
        print(f"  Warning: could not fetch existing URLs ({e}). Proceeding without pre-filter.\n")
        return set()


def main():
    parser = argparse.ArgumentParser(description="Ingest scraped movies to RecoMo API")
    parser.add_argument("--api", default=os.environ.get("RECOMO_API_URL", "http://localhost:8000"), help="RecoMo API URL")
    parser.add_argument("--limit", type=int, default=None, help="Max number of NEW movies to ingest (default: all)")
    args = parser.parse_args()

    print("=" * 70)
    print("PHASE 2: INGEST TO RECOMO API")
    print("=" * 70)
    print(f"Source: {SCRAPED_FILE}")
    print(f"API: {args.api}")
    if args.limit:
        print(f"Limit: {args.limit} new movies")
    print("Stop anytime with Ctrl+C — run again to resume.\n")

    if not os.path.exists(SCRAPED_FILE):
        print(f"No {SCRAPED_FILE} found. Run 'python main_playwright.py' first.")
        return

    with open(SCRAPED_FILE, "r", encoding="utf-8") as f:
        all_movies = json.load(f)

    # Pre-filter: skip movies already in DB (one fast local check)
    existing_urls = fetch_existing_urls(args.api)
    movies = [m for m in all_movies if m.get("url") not in existing_urls]

    print(f"Total scraped:  {len(all_movies)}")
    print(f"Already in DB:  {len(all_movies) - len(movies)}")
    print(f"New to ingest:  {len(movies)}")

    if args.limit:
        movies = movies[:args.limit]
        print(f"Ingesting:      {len(movies)} (limited to {args.limit})")

    print()

    if not movies:
        print("Nothing new to ingest. All done!")
        return

    total = len(movies)
    store = DataStore(api_url=args.api)
    saved = 0
    failed = 0

    for i, movie in enumerate(movies, 1):
        try:
            result = store.insert_movie(movie)
            if result and result.get("status") == "ingested":
                saved += 1
            else:
                failed += 1
                print(f"  Unexpected skip: '{movie.get('title', '?')}'")
        except Exception as e:
            failed += 1
            print(f"  Error: '{movie.get('title', '?')}': {e}")

        if i % 50 == 0 or i == total:
            print(f"  Progress: {i}/{total} | Ingested: {saved} | Failed: {failed}")

    print(f"\nDone: {saved} ingested, {failed} failed")

    # Exit with error if everything failed (e.g. backend unreachable)
    if total > 0 and saved == 0:
        print(f"\nERROR: 0 out of {total} movies ingested — backend may be unreachable.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    start_time = time.time()

    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped. Run again to resume.")

    elapsed = time.time() - start_time
    print(f"\nTime: {elapsed/60:.1f} minutes")

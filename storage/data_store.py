import re
import time

import requests
import pandas as pd


def parse_rating(raw):
    """Extract numeric rating from strings like 'IMDB: 7.4' or '7.4'."""
    if not raw:
        return None
    match = re.search(r"(\d+\.?\d*)", str(raw))
    return float(match.group(1)) if match else None


class DataStore:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url

    def insert_movie(self, movie, max_retries=3):
        """Send a single movie to RecoMo API with retry logic."""
        payload = {
            "title": movie.get("title", ""),
            "description": movie.get("description"),
            "genre": movie.get("genre"),
            "rating": parse_rating(movie.get("rating")),
            "type": movie.get("type"),
            "released": movie.get("released"),
            "duration": movie.get("duration"),
            "country": movie.get("country"),
            "cast": movie.get("cast"),
            "production": movie.get("production"),
            "url": movie.get("url"),
            "image_url": movie.get("image_url"),
        }

        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    f"{self.api_url}/api/movies/ingest",
                    json=payload,
                    timeout=90,
                )
                resp.raise_for_status()
                return resp.json()
            except (requests.ConnectionError, requests.Timeout) as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    print(f"    Retry {attempt + 1}/{max_retries} for '{movie.get('title')}' (waiting {wait}s)")
                    time.sleep(wait)
                else:
                    raise
            except requests.HTTPError as e:
                if e.response.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    print(f"    Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                elif attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    raise

    def export_to_excel(self, movies, filename="scraped_movies.xlsx"):
        df = pd.DataFrame(movies)
        df.to_excel(filename, index=False)

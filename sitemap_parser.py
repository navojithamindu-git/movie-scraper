import requests
import xml.etree.ElementTree as ET
from typing import List
import re

class SitemapParser:
    def __init__(self, base_url: str = "https://myflixerz.to"):
        self.base_url = base_url
        self.headers = {'User-Agent': 'Mozilla/5.0'}

    def fetch_sitemap(self, sitemap_url: str) -> str:
        """Fetch sitemap XML content"""
        try:
            response = requests.get(sitemap_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching sitemap {sitemap_url}: {e}")
            return ""

    def parse_sitemap_index(self, xml_content: str) -> List[str]:
        """Parse sitemap index and return list of sitemap URLs"""
        sitemap_urls = []
        try:
            root = ET.fromstring(xml_content)
            # Handle namespace
            ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            for sitemap in root.findall('.//ns:sitemap', ns):
                loc = sitemap.find('ns:loc', ns)
                if loc is not None and loc.text:
                    sitemap_urls.append(loc.text)

            # If no namespace found, try without
            if not sitemap_urls:
                for sitemap in root.findall('.//sitemap'):
                    loc = sitemap.find('loc')
                    if loc is not None and loc.text:
                        sitemap_urls.append(loc.text)
        except Exception as e:
            print(f"Error parsing sitemap index: {e}")

        return sitemap_urls

    def parse_sitemap(self, xml_content: str) -> List[str]:
        """Parse sitemap and return list of URLs"""
        urls = []
        try:
            root = ET.fromstring(xml_content)
            # Handle namespace
            ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            for url in root.findall('.//ns:url', ns):
                loc = url.find('ns:loc', ns)
                if loc is not None and loc.text:
                    urls.append(loc.text)

            # If no namespace found, try without
            if not urls:
                for url in root.findall('.//url'):
                    loc = url.find('loc')
                    if loc is not None and loc.text:
                        urls.append(loc.text)
        except Exception as e:
            print(f"Error parsing sitemap: {e}")

        return urls

    def filter_content_urls(self, urls: List[str]) -> List[str]:
        """Filter movie and TV series URLs"""
        content_urls = []
        content_pattern = re.compile(r'/(movie|tv)/[^/]+$')

        for url in urls:
            if content_pattern.search(url):
                content_urls.append(url)

        return content_urls

    def get_all_movie_urls(self) -> List[str]:
        """Main method to get all movie and TV series URLs from sitemap"""
        print("Fetching sitemap...")

        # Try different sitemap URLs
        sitemap_urls_to_try = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap_index.xml",
            f"{self.base_url}/post-sitemap.xml",
            f"{self.base_url}/movie-sitemap.xml",
        ]

        all_movie_urls = []

        for sitemap_url in sitemap_urls_to_try:
            print(f"Trying: {sitemap_url}")
            xml_content = self.fetch_sitemap(sitemap_url)

            if not xml_content:
                continue

            # Check if it's a sitemap index
            if '<sitemapindex' in xml_content or 'sitemap' in xml_content.lower()[:200]:
                print(f"  → Found sitemap index")
                child_sitemaps = self.parse_sitemap_index(xml_content)
                print(f"  → Found {len(child_sitemaps)} child sitemaps")

                for child_sitemap in child_sitemaps:
                    print(f"  → Fetching: {child_sitemap}")
                    child_xml = self.fetch_sitemap(child_sitemap)
                    if child_xml:
                        urls = self.parse_sitemap(child_xml)
                        movie_urls = self.filter_content_urls(urls)
                        print(f"     Found {len(movie_urls)} movie URLs")
                        all_movie_urls.extend(movie_urls)
            else:
                # Direct sitemap
                print(f"  → Found direct sitemap")
                urls = self.parse_sitemap(xml_content)
                movie_urls = self.filter_content_urls(urls)
                print(f"  → Found {len(movie_urls)} movie URLs")
                all_movie_urls.extend(movie_urls)

            if all_movie_urls:
                break  # Found movies, no need to try other URLs

        # Remove duplicates
        all_movie_urls = list(set(all_movie_urls))
        print(f"\nTotal unique movie URLs: {len(all_movie_urls)}")

        return all_movie_urls


if __name__ == "__main__":
    parser = SitemapParser()
    movie_urls = parser.get_all_movie_urls()

    if movie_urls:
        print(f"\nFirst 5 movie URLs:")
        for url in movie_urls[:5]:
            print(f"  - {url}")

        # Save to file
        with open('movie_urls.txt', 'w', encoding='utf-8') as f:
            for url in movie_urls:
                f.write(f"{url}\n")
        print(f"\nAll URLs saved to movie_urls.txt")
    else:
        print("\nNo movie URLs found!")

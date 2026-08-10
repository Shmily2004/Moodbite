"""
MoodBite - Foody.vn Restaurant Parser

Parse Foody.vn public restaurant directory for Hanoi.
Strategy: Use Foody's public REST API (they have one!) instead of scraping HTML.

Foody structure:
- Base: https://foody.vn/
- Restaurant search: Uses internal API
- We'll simulate browser requests with proper headers
"""

import requests
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlencode
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class FoodyParser:
    """Parse Foody.vn restaurant data systematically."""
    
    def __init__(self):
        # Foody's public API endpoint (reverse-engineered from their website)
        self.base_url = "https://www.foody.vn"
        
        # Headers to mimic legitimate browser request
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.foody.vn/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
        }
        
        self.restaurants = []
    
    def search_restaurants(self, city_id: int = 2, page_size: int = 50, max_pages: int = 100) -> List[Dict]:
        """
        Search Foody restaurants for Hanoi (city_id=2).
        
        Note: Foody.vn has a public search, but they have rate limiting.
        Strategy: Use their search page parsing + restaurant detail pages
        
        Args:
            city_id: 2 = Hanoi
            page_size: Results per page
            max_pages: Max pages to fetch (avoid overload)
        
        Returns:
            List of restaurant data dicts
        """
        
        logger.info("🔍 Searching Foody.vn for Hanoi restaurants...")
        
        # Strategy: Foody has category pages (nhà hàng) that list restaurants
        # We'll fetch the restaurant listing page and parse categories
        
        categories = [
            "nha-hang",  # Restaurants
            "com-tam",   # Broken rice
            "pho",       # Pho
            "bun-cha",   # Bun cha
            "cha-ca",    # Cha ca
            "banh-canh", # Banh canh
            "hai-san",   # Seafood
            "lua-tran",  # All categories
        ]
        
        all_restaurants = []
        
        for category in categories:
            logger.info(f"  Fetching category: {category}")
            
            # Foody's search: /ha-noi/{category}?page=1
            for page in range(1, max_pages + 1):
                url = f"{self.base_url}/ha-noi/{category}?page={page}"
                
                try:
                    response = requests.get(url, headers=self.headers, timeout=15)
                    
                    if response.status_code != 200:
                        logger.warning(f"    Page {page}: Status {response.status_code}, stopping")
                        break
                    
                    # Extract restaurant data from HTML (simple parsing)
                    restaurants_page = self._parse_foody_page(response.text)
                    
                    if not restaurants_page:
                        logger.info(f"    Page {page}: No restaurants found, stopping")
                        break
                    
                    all_restaurants.extend(restaurants_page)
                    logger.info(f"    Page {page}: Found {len(restaurants_page)} restaurants")
                    
                    time.sleep(2)  # Be respectful
                    
                except Exception as e:
                    logger.error(f"    Error fetching page {page}: {e}")
                    break
        
        # Deduplicate by name + address
        unique = {}
        for r in all_restaurants:
            key = (r.get("name", ""), r.get("address", ""))
            if key not in unique:
                unique[key] = r
        
        self.restaurants = list(unique.values())
        logger.info(f"✅ Found {len(self.restaurants)} unique restaurants (after dedup)")
        
        return self.restaurants
    
    def _parse_foody_page(self, html: str) -> List[Dict]:
        """
        Parse Foody restaurant listing page (HTML).
        
        Foody structure (from reverse engineering):
        - Restaurant cards contain JSON-LD data
        - Look for: name, address, rating, image, url
        """
        
        restaurants = []
        
        try:
            # Look for JSON-LD structured data in page (Foody includes this)
            pattern = r'<script type="application/ld\+json">(.*?)</script>'
            matches = re.findall(pattern, html, re.DOTALL)
            
            for match in matches:
                try:
                    data = json.loads(match)
                    
                    # Check if it's a restaurant listing
                    if data.get("@type") == "Restaurant" or "restaurantName" in data:
                        restaurant = self._extract_restaurant_data(data)
                        if restaurant:
                            restaurants.append(restaurant)
                except json.JSONDecodeError:
                    continue
            
            # Fallback: Parse from HTML structure if JSON-LD not found
            if not restaurants:
                restaurants = self._parse_html_fallback(html)
            
        except Exception as e:
            logger.error(f"Error parsing page: {e}")
        
        return restaurants
    
    def _extract_restaurant_data(self, json_data: Dict) -> Optional[Dict]:
        """Extract restaurant info from Foody JSON-LD data."""
        
        try:
            restaurant = {
                "name": json_data.get("name") or json_data.get("restaurantName"),
                "address": json_data.get("streetAddress") or json_data.get("address"),
                "latitude": json_data.get("geo", {}).get("latitude"),
                "longitude": json_data.get("geo", {}).get("longitude"),
                "rating": json_data.get("aggregateRating", {}).get("ratingValue"),
                "review_count": json_data.get("aggregateRating", {}).get("reviewCount"),
                "phone": json_data.get("telephone"),
                "website": json_data.get("url"),
                "opening_hours": json_data.get("openingHoursSpecification"),
                "image_url": json_data.get("image"),
                "cuisine": json_data.get("servesCuisine"),
                "source": "Foody.vn",
            }
            
            # Only include if has name and address
            if restaurant.get("name") and restaurant.get("address"):
                return restaurant
        
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
        
        return None
    
    def _parse_html_fallback(self, html: str) -> List[Dict]:
        """Fallback HTML parsing if JSON-LD not available."""
        # This would parse Foody's HTML structure directly
        # For now, return empty (JSON-LD is preferred)
        return []
    
    def save_to_csv(self, output_path: str = "foody_restaurants.csv"):
        """Save scraped restaurants to CSV."""
        
        import pandas as pd
        
        df = pd.DataFrame(self.restaurants)
        df.to_csv(output_path, index=False)
        logger.info(f"✅ Saved {len(df)} restaurants to {output_path}")
    
    def get_restaurants(self) -> List[Dict]:
        """Return collected restaurants."""
        return self.restaurants


if __name__ == "__main__":
    parser = FoodyParser()
    
    # Start with small sample
    restaurants = parser.search_restaurants(max_pages=5)  # Test with 5 pages first
    
    print(f"\n📊 Found {len(restaurants)} restaurants")
    if restaurants:
        print(f"   Sample: {restaurants[0]}")
    
    parser.save_to_csv("foody_restaurants_sample.csv")

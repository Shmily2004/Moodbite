"""
MoodBite - Tôi Đi Đâu Restaurant Parser

Parse https://toididau.net/ restaurant listings.
Much simpler than Foody - they have a clean directory structure.

Approach: Parse their restaurant category pages + individual listings
"""

import requests
import json
import time
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class ToiDiDauParser:
    """Parse ToiDiDau restaurant data."""
    
    def __init__(self):
        self.base_url = "https://toididau.net"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://toididau.net/",
        }
        self.restaurants = []
    
    def search_restaurants(self, max_restaurants: int = 1000) -> List[Dict]:
        """
        Search Tôi Đi Đâu for Hanoi restaurants.
        
        They have: /nha-hang/ha-noi?page=1&per_page=50
        """
        
        logger.info("🔍 Searching Tôi Đi Đâu for Hanoi restaurants...")
        
        page = 1
        all_restaurants = []
        consecutive_empty = 0
        
        while len(all_restaurants) < max_restaurants and consecutive_empty < 3:
            url = f"{self.base_url}/nha-hang/ha-noi?page={page}&per_page=50"
            
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                response.encoding = 'utf-8'
                
                if response.status_code != 200:
                    logger.warning(f"  Page {page}: Status {response.status_code}")
                    break
                
                # Parse page
                restaurants_page = self._parse_restaurant_page(response.text)
                
                if not restaurants_page:
                    consecutive_empty += 1
                    logger.info(f"  Page {page}: No restaurants (empty count: {consecutive_empty})")
                else:
                    consecutive_empty = 0
                    all_restaurants.extend(restaurants_page)
                    logger.info(f"  Page {page}: Found {len(restaurants_page)} restaurants (total: {len(all_restaurants)})")
                
                page += 1
                time.sleep(1)  # Respectful crawling
                
            except Exception as e:
                logger.error(f"  Page {page}: Error - {e}")
                break
        
        # Deduplicate
        unique = {}
        for r in all_restaurants:
            key = (r.get("name", ""), r.get("address", ""))
            if key not in unique:
                unique[key] = r
        
        self.restaurants = list(unique.values())
        logger.info(f"✅ Found {len(self.restaurants)} unique restaurants")
        
        return self.restaurants
    
    def _parse_restaurant_page(self, html: str) -> List[Dict]:
        """Parse restaurant listing page HTML."""
        
        restaurants = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Tôi Đi Đâu structure: restaurant cards in grid
            # Look for restaurant links
            restaurant_links = soup.find_all('a', class_=re.compile(r'restaurant|place'))
            
            for link in restaurant_links[:50]:  # Limit per page
                try:
                    # Extract URL
                    href = link.get('href', '')
                    if not href or '/place/' not in href:
                        continue
                    
                    # Restaurant name
                    name = link.get_text(strip=True)
                    if not name:
                        continue
                    
                    # Fetch full restaurant details
                    restaurant = self._fetch_restaurant_details(href, name)
                    if restaurant:
                        restaurants.append(restaurant)
                
                except Exception as e:
                    logger.debug(f"  Error parsing restaurant: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing page: {e}")
        
        return restaurants
    
    def _fetch_restaurant_details(self, url: str, name: str) -> Optional[Dict]:
        """Fetch full restaurant details from individual page."""
        
        try:
            full_url = f"{self.base_url}{url}" if not url.startswith('http') else url
            response = requests.get(full_url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract data from detail page
            restaurant = {
                "name": name,
                "url": full_url,
                "source": "ToiDiDau",
            }
            
            # Address - look for location info
            address_elem = soup.find(class_=re.compile(r'address|location'))
            if address_elem:
                restaurant["address"] = address_elem.get_text(strip=True)
            
            # Rating - find rating element
            rating_elem = soup.find(class_=re.compile(r'rating|score'))
            if rating_elem:
                try:
                    rating_text = rating_elem.get_text()
                    # Extract number from rating text
                    rating = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating:
                        restaurant["rating"] = float(rating.group(1))
                except:
                    pass
            
            # Review count
            review_elem = soup.find(class_=re.compile(r'review|comment'))
            if review_elem:
                try:
                    review_text = review_elem.get_text()
                    count = re.search(r'(\d+)', review_text)
                    if count:
                        restaurant["review_count"] = int(count.group(1))
                except:
                    pass
            
            # Images
            images = []
            img_links = soup.find_all('img', class_=re.compile(r'restaurant|place|image'))
            for img in img_links[:5]:  # Get first 5 images
                src = img.get('src') or img.get('data-src')
                if src and 'toididau' in src:
                    images.append(src)
            
            if images:
                restaurant["image_urls"] = images
            
            # Phone - look for phone number
            phone_pattern = r'\+?84\s?\d{1,3}\s?\d{3,4}\s?\d{3,4}'
            phone_match = re.search(phone_pattern, response.text)
            if phone_match:
                restaurant["phone"] = phone_match.group()
            
            # Only return if has essential fields
            if restaurant.get("name") and (restaurant.get("address") or restaurant.get("rating")):
                return restaurant
        
        except Exception as e:
            logger.debug(f"Error fetching details: {e}")
        
        return None
    
    def save_to_csv(self, output_path: str = "toididau_restaurants.csv"):
        """Save to CSV."""
        
        import pandas as pd
        
        df = pd.DataFrame(self.restaurants)
        df.to_csv(output_path, index=False)
        logger.info(f"✅ Saved {len(df)} restaurants to {output_path}")


if __name__ == "__main__":
    parser = ToiDiDauParser()
    restaurants = parser.search_restaurants(max_restaurants=100)
    
    print(f"\n📊 Found {len(restaurants)} restaurants")
    if restaurants:
        print(f"   Sample: {restaurants[0]}")
    
    parser.save_to_csv("toididau_restaurants_sample.csv")

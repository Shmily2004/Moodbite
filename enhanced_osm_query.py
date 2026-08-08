"""
MoodBite - Enhanced OSM Query with Cuisine Filters

Instead of a generic restaurant query, search by specific cuisine types.
This finds restaurants that might be missed by simple queries.

Example: Query for "pho", "banh mi", "cha ca", "seafood", etc separately.
"""

import overpy
import json
import logging
import time
import urllib.request
from pathlib import Path
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# overpy uses urllib.request under the hood with the default
# "Python-urllib/x.y" User-Agent. overpass-api.de's Cloudflare-style bot
# protection rejects that with HTTP 406, even though the query itself is
# valid. Installing a browser-like User-Agent globally fixes it.
_opener = urllib.request.build_opener()
_opener.addheaders = [
    ("User-Agent", "Mozilla/5.0 (compatible; MoodBiteOSMBot/1.0; +https://github.com/)")
]
urllib.request.install_opener(_opener)


class EnhancedOSMQuery:
    """Query OSM with multiple cuisine filters for comprehensive restaurant coverage."""

    def __init__(self, sleep_between_queries: float = 1.5, max_retries: int = 2):
        # Overpass mirrors, tried in order if one is down/blocking.
        self.mirrors = [
            "https://overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
        ]
        # overpass-api.de is unreachable on this network (connection times
        # out at the TCP level, before any HTTP request). Default to the
        # kumi.systems mirror instead, which is reachable.
        self.api = overpy.Overpass(url=self.mirrors[1])
        self.max_retries = max_retries
        self.all_restaurants = {}  # key = (name, address, rounded_lat, rounded_lng)
        self.sleep_between_queries = sleep_between_queries

        # Cuisine VALUES to search for (Vietnamese + popular cuisines in Hanoi).
        # OSM's "cuisine" tag is often multi-valued (e.g. "vietnamese;asian"),
        # so we match with a regex (~) rather than an exact (=) comparison.
        self.cuisine_filters = [
            "vietnamese",
            "pho",
            "banh_mi",
            "cha_ca",
            "seafood",
            "chinese",
            "thai",
            "japanese",
            "korean",
            "pizza",
            "burger",
            "coffee",
            "cake",
        ]

        # Hanoi bounding box: (south, west, north, east)
        self.bbox = (20.5, 105.7, 21.1, 106.0)

    def query_by_cuisine(self) -> List[Dict]:
        """Query OSM by specific cuisine types."""

        logger.info("Querying OSM with cuisine filters...")
        logger.info(f"   Bounding box: {self.bbox}")

        for i, cuisine in enumerate(self.cuisine_filters, 1):
            logger.info(f"\n  [{i}/{len(self.cuisine_filters)}] Searching: {cuisine}")

            # NOTE: ["cuisine"~"value"] is correct Overpass QL for a
            # regex/substring match on a tag VALUE. The previous version
            # built the string "cuisine=value" and dropped it into
            # ["{that}"] which Overpass parses as an (invalid) tag KEY,
            # so every query silently returned zero results.
            query = f"""
            [bbox:{self.bbox[0]},{self.bbox[1]},{self.bbox[2]},{self.bbox[3]}]
            [timeout:60];
            (
              node["amenity"="restaurant"]["cuisine"~"{cuisine}"];
              way["amenity"="restaurant"]["cuisine"~"{cuisine}"];
            );
            out center;
            """

            result = None
            last_error = None
            for attempt in range(1, self.max_retries + 2):  # initial try + retries
                try:
                    result = self.api.query(query)
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"     Attempt {attempt} failed for '{cuisine}': {e}"
                    )
                    if attempt <= self.max_retries:
                        time.sleep(self.sleep_between_queries * 2)

            if result is None:
                logger.warning(f"     Giving up on '{cuisine}' after retries: {last_error}")
                time.sleep(self.sleep_between_queries)
                continue

            nodes = list(result.nodes)
            ways = list(result.ways)

            for node in nodes:
                restaurant = self._extract_restaurant_from_node(node)
                if restaurant:
                    self._add_restaurant(restaurant)

            for way in ways:
                restaurant = self._extract_restaurant_from_way(way)
                if restaurant:
                    self._add_restaurant(restaurant)

            logger.info(
                f"     Found: {len(nodes) + len(ways)} records | "
                f"Total unique so far: {len(self.all_restaurants)}"
            )

            # Be polite to the public Overpass endpoint
            time.sleep(self.sleep_between_queries)

        logger.info(f"\nTotal unique restaurants found: {len(self.all_restaurants)}")

        return list(self.all_restaurants.values())

    def _add_restaurant(self, restaurant: Dict) -> None:
        """Add restaurant to dedup dict, keyed by name+address+rounded coords."""
        loc = restaurant.get("location", {})
        lat = round(loc.get("lat", 0.0), 5) if loc.get("lat") is not None else None
        lng = round(loc.get("lng", 0.0), 5) if loc.get("lng") is not None else None

        key = (restaurant.get("title", ""), restaurant.get("address", ""), lat, lng)
        if key not in self.all_restaurants:
            self.all_restaurants[key] = restaurant

    def _build_address(self, tags: Dict) -> Optional[str]:
        if "addr:full" in tags:
            return tags["addr:full"]

        # Build from parts if at least one component exists
        parts = []
        if "addr:housenumber" in tags:
            parts.append(tags["addr:housenumber"])
        if "addr:street" in tags:
            parts.append(tags["addr:street"])
        if "addr:ward" in tags:
            parts.append(tags["addr:ward"])
        if "addr:district" in tags:
            parts.append(tags["addr:district"])
        if "addr:city" in tags:
            parts.append(tags["addr:city"])

        return ", ".join(parts) if parts else None

    def _build_common_fields(self, tags: Dict, lat, lon) -> Optional[Dict]:
        if "name" not in tags:
            return None

        restaurant = {
            "title": tags.get("name", ""),
            "source": "OSM",
            "location": {"lat": float(lat), "lng": float(lon)},
        }

        address = self._build_address(tags)
        if address:
            restaurant["address"] = address

        phone = tags.get("phone") or tags.get("contact:phone")
        if phone:
            restaurant["phone"] = phone

        website = tags.get("website") or tags.get("contact:website")
        if website:
            restaurant["website"] = website

        if "opening_hours" in tags:
            restaurant["opening_hours"] = tags["opening_hours"]

        if "cuisine" in tags:
            restaurant["cuisine"] = tags["cuisine"]

        if "rating" in tags:
            try:
                restaurant["rating"] = float(tags["rating"])
            except (TypeError, ValueError):
                pass

        return restaurant

    def _extract_restaurant_from_node(self, node: overpy.Node) -> Optional[Dict]:
        return self._build_common_fields(node.tags, node.lat, node.lon)

    def _extract_restaurant_from_way(self, way: overpy.Way) -> Optional[Dict]:
        # "out center;" guarantees center_lat/center_lon on ways, so no
        # extra per-way API call is needed (the old fallback made one
        # network round-trip per way, which is slow and fragile).
        center_lat = getattr(way, "center_lat", None)
        center_lon = getattr(way, "center_lon", None)
        if center_lat is None or center_lon is None:
            return None

        return self._build_common_fields(way.tags, center_lat, center_lon)

    def save_to_json(self, output_path: str = "enhanced_osm_restaurants.json"):
        """Save results to JSON."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(list(self.all_restaurants.values()), f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(self.all_restaurants)} restaurants to {output_path}")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Enhanced OSM Restaurant Query")
    logger.info("=" * 60)

    try:
        query = EnhancedOSMQuery()
        restaurants = query.query_by_cuisine()
        query.save_to_json("data_pipeline/data_raw/04_raw_places_osm_enhanced.json")

        logger.info("=" * 60)
        logger.info(f"Found {len(restaurants)} restaurants")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
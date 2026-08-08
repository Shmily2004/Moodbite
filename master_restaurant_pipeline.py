"""
MoodBite - Master Restaurant Discovery Pipeline

Orchestrates collection from multiple sources:
1. Foody.vn
2. Tôi Đi Đâu
3. OSM (existing)
4. Deduplicates
5. Merges into final dataset

Run this to update the complete restaurant database.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict, Tuple
from difflib import SequenceMatcher
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

class RestaurantDeduplicator:
    """Intelligent deduplication across sources using fuzzy matching."""
    
    @staticmethod
    def similarity_score(str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0-1)."""
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    @staticmethod
    def normalize_address(address: str) -> str:
        """Normalize address for comparison."""
        if not address:
            return ""
        # Remove extra spaces, lowercase, remove common suffixes
        norm = address.lower().strip()
        for suffix in [", hà nội", "hà nội", ", việt nam"]:
            norm = norm.replace(suffix, "")
        return norm.strip()
    
    @staticmethod
    def deduplicate_restaurants(restaurants: List[Dict]) -> List[Dict]:
        """
        Deduplicate restaurants across sources.
        
        Strategy:
        1. Group by name similarity (>0.8)
        2. Within groups, compare addresses
        3. Keep best record from each group (prefer sources with more complete data)
        """
        
        if not restaurants:
            return []
        
        logger.info(f"🔄 Deduplicating {len(restaurants)} restaurants...")
        
        # Score each restaurant's completeness
        def completeness_score(r: Dict) -> int:
            score = 0
            if r.get("name"): score += 2
            if r.get("address"): score += 2
            if r.get("latitude") and r.get("longitude"): score += 2
            if r.get("rating"): score += 1
            if r.get("review_count"): score += 1
            if r.get("image_urls"): score += 1
            if r.get("phone"): score += 1
            return score
        
        # Mark duplicates
        keep_indices = set(range(len(restaurants)))
        duplicates_found = 0
        
        for i in range(len(restaurants)):
            if i not in keep_indices:
                continue
            
            r1 = restaurants[i]
            name1 = r1.get("name", "")
            addr1 = RestaurantDeduplicator.normalize_address(r1.get("address", ""))
            
            for j in range(i + 1, len(restaurants)):
                if j not in keep_indices:
                    continue
                
                r2 = restaurants[j]
                name2 = r2.get("name", "")
                addr2 = RestaurantDeduplicator.normalize_address(r2.get("address", ""))
                
                # Check if same restaurant
                name_sim = RestaurantDeduplicator.similarity_score(name1, name2)
                addr_sim = RestaurantDeduplicator.similarity_score(addr1, addr2) if addr1 and addr2 else 0
                
                is_duplicate = False
                
                # Both name AND address similar = definitely duplicate
                if name_sim > 0.85 and addr_sim > 0.75:
                    is_duplicate = True
                # Very similar name + one has no address = duplicate
                elif name_sim > 0.9 and (not addr1 or not addr2):
                    is_duplicate = True
                
                if is_duplicate:
                    # Keep the more complete record
                    score1 = completeness_score(r1)
                    score2 = completeness_score(r2)
                    
                    if score1 >= score2:
                        keep_indices.discard(j)
                    else:
                        keep_indices.discard(i)
                    
                    duplicates_found += 1
        
        deduped = [restaurants[i] for i in sorted(keep_indices)]
        logger.info(f"✅ Removed {duplicates_found} duplicates → {len(deduped)} unique restaurants")
        
        return deduped
    
    @staticmethod
    def merge_records(records: List[Dict]) -> Dict:
        """
        Merge multiple records for same restaurant.
        Use best data from each source.
        """
        
        merged = {
            "name": records[0].get("name"),
            "address": records[0].get("address"),
            "latitude": records[0].get("latitude"),
            "longitude": records[0].get("longitude"),
        }
        
        # Merge ratings (average from multiple sources)
        ratings = [r.get("rating") for r in records if r.get("rating")]
        if ratings:
            merged["rating"] = np.mean(ratings)
        
        # Merge review counts (sum)
        review_counts = [r.get("review_count") for r in records if r.get("review_count")]
        if review_counts:
            merged["review_count"] = sum(review_counts)
        
        # Merge image URLs (dedupe)
        all_images = []
        for r in records:
            if isinstance(r.get("image_urls"), list):
                all_images.extend(r.get("image_urls", []))
        
        if all_images:
            merged["image_urls"] = list(set(all_images))[:10]  # Keep top 10 unique
        
        # Take phone from any source
        for r in records:
            if r.get("phone"):
                merged["phone"] = r.get("phone")
                break
        
        # List all sources
        merged["sources"] = [r.get("source", "Unknown") for r in records]
        merged["last_updated"] = datetime.now().isoformat()
        
        return merged


class MasterPipeline:
    """Master pipeline coordinator."""
    
    def __init__(self, output_dir: str = "data_pipeline/data_cleaned"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.final_dataset_path = self.output_dir / "dataset_moodbite_enhanced.csv"
    
    def run_full_pipeline(self):
        """Execute complete pipeline."""
        
        logger.info("=" * 60)
        logger.info("MoodBite - Master Restaurant Discovery Pipeline")
        logger.info("=" * 60)
        logger.info("")
        
        # Step 1: Load existing dataset
        logger.info("📥 Step 1: Load existing dataset...")
        existing_df = self._load_existing_dataset()
        logger.info(f"   ✅ Loaded {len(existing_df)} restaurants from existing dataset")
        
        # Step 2: Scrape Foody (when ready)
        logger.info("\n📥 Step 2: Scrape Foody.vn...")
        logger.info("   ℹ️  Ready to run (requires beautifulsoup4, requests)")
        logger.info("   Command: python foody_parser.py")
        
        # Step 3: Scrape Tôi Đi Đâu (when ready)
        logger.info("\n📥 Step 3: Scrape Tôi Đi Đâu...")
        logger.info("   ℹ️  Ready to run (requires beautifulsoup4, requests)")
        logger.info("   Command: python toididau_parser.py")
        
        # Step 4: Deduplicate & merge
        logger.info("\n🔄 Step 4: Deduplication...")
        logger.info("   Waiting for source data to merge...")
        
        # Step 5: Final dataset
        logger.info("\n💾 Step 5: Save enhanced dataset...")
        logger.info(f"   Output: {self.final_dataset_path}")
        
        logger.info("\n" + "=" * 60)
        logger.info("Pipeline ready! Follow steps above to collect data.")
        logger.info("=" * 60)
    
    def _load_existing_dataset(self) -> pd.DataFrame:
        """Load current dataset."""
        
        dataset_path = self.output_dir / "dataset_moodbite_features.csv"
        
        if not dataset_path.exists():
            logger.error(f"❌ Dataset not found: {dataset_path}")
            return pd.DataFrame()
        
        return pd.read_csv(dataset_path)
    
    def merge_all_sources(self, foody_csv: str, toididau_csv: str, osm_csv: str = None) -> pd.DataFrame:
        """
        Merge all data sources into single dataset.
        
        Args:
            foody_csv: Path to Foody data
            toididau_csv: Path to Tôi Đi Đâu data
            osm_csv: Path to OSM data (optional)
        """
        
        logger.info("🔀 Merging all sources...")
        
        dfs = []
        
        # Load each source
        for name, path in [("Foody", foody_csv), ("ToiDiDau", toididau_csv)]:
            try:
                df = pd.read_csv(path)
                df["source"] = name
                dfs.append(df)
                logger.info(f"  ✅ Loaded {len(df)} from {name}")
            except Exception as e:
                logger.warning(f"  ⚠️  Could not load {name}: {e}")
        
        # Load OSM if provided
        if osm_csv:
            try:
                df = pd.read_csv(osm_csv)
                df["source"] = "OSM"
                dfs.append(df)
                logger.info(f"  ✅ Loaded {len(df)} from OSM")
            except Exception as e:
                logger.warning(f"  ⚠️  Could not load OSM: {e}")
        
        # Combine all
        combined = pd.concat(dfs, ignore_index=True)
        logger.info(f"  📊 Combined: {len(combined)} records")
        
        # Deduplicate
        records = combined.to_dict('records')
        deduped = RestaurantDeduplicator.deduplicate_restaurants(records)
        
        result_df = pd.DataFrame(deduped)
        logger.info(f"  ✅ Final: {len(result_df)} unique restaurants")
        
        return result_df
    
    def save_dataset(self, df: pd.DataFrame):
        """Save final dataset."""
        
        df.to_csv(self.final_dataset_path, index=False)
        logger.info(f"✅ Saved to {self.final_dataset_path}")
        
        # Print summary
        logger.info(f"\n📊 Dataset Summary:")
        logger.info(f"   Total restaurants: {len(df)}")
        logger.info(f"   With ratings: {df['rating'].notna().sum()}")
        logger.info(f"   With coordinates: {(df['latitude'].notna() & df['longitude'].notna()).sum()}")
        logger.info(f"   With images: {df['image_urls'].notna().sum()}")


if __name__ == "__main__":
    pipeline = MasterPipeline()
    pipeline.run_full_pipeline()

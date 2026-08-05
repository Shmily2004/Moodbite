import pandas as pd
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Restaurant:
    id: str
    name: str
    category: str
    lat: float
    lng: float
    mood_score: float
    distance: float

class RecommendationService:
    def __init__(self, dataset_path: str = "data_pipeline/data_cleaned/dataset_moodbite_features.csv"):
        """Load restaurant dataset"""
        self.dataset_path = Path(dataset_path)
        self.restaurants = self._load_dataset()
    
    def _load_dataset(self) -> pd.DataFrame:
        """Load CSV dataset"""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset not found: {self.dataset_path}")
        
        df = pd.read_csv(self.dataset_path)
        print(f"✅ Loaded {len(df)} restaurants")
        return df
    
    def recommend(self, mood: str, user_lat: float = 21.0285, user_lng: float = 105.8542, top_k: int = 5) -> List[Dict]:
        """
        Recommend restaurants based on mood
        
        Args:
            mood: User mood (happy, sad, excited, relaxed, etc.)
            user_lat, user_lng: User location (default: Hà Nội center)
            top_k: Number of recommendations
        
        Returns:
            List of recommended restaurants
        """
        df = self.restaurants.copy()
        
        # Mood scoring (example - có thể improve sau)
        mood_keywords = {
            "happy": ["restaurant", "cafe", "bar"],
            "sad": ["cafe", "quiet"],
            "excited": ["fast_food", "bar"],
            "relaxed": ["cafe", "restaurant"],
        }
        
        # Simple scoring based on category
        df['mood_match_score'] = df['categoryName'].apply(
            lambda x: self._calculate_mood_score(x, mood, mood_keywords)
        )
        
        # Sort by mood score
        top_restaurants = df.nlargest(top_k, 'mood_match_score')
        
        # Format output
        recommendations = []
        for idx, row in top_restaurants.iterrows():
            recommendations.append({
                "name": row['title'],
                "category": row['categoryName'],
                "address": row.get('address', 'N/A'),
                "lat": row['location/lat'],
                "lng": row['location/lng'],
                "mood_match_score": float(row['mood_match_score']),
                "mood": mood
            })
        
        return recommendations
    
    @staticmethod
    def _calculate_mood_score(category: str, mood: str, mood_keywords: dict) -> float:
        """Calculate match score between category and mood"""
        keywords = mood_keywords.get(mood.lower(), [])
        
        score = 0
        for keyword in keywords:
            if keyword.lower() in category.lower():
                score += 1
        
        return score if score > 0 else 0.1  # Minimum score để không bị filter

# Initialize service (global)
recommendation_service = RecommendationService()
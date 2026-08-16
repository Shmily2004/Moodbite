from pydantic import BaseModel
from typing import List, Optional


class RecommendationItem(BaseModel):
    placeId: Optional[str]
    name: str
    category: Optional[str]
    address: Optional[str]
    price: Optional[float]
    rating: Optional[float]
    reviews_count: Optional[int]
    lat: float
    lng: float
    distance_km: float
    mood_match_score: float
    mood: str


class RecommendResponse(BaseModel):
    status: str
    mood: str
    recommendations: List[RecommendationItem]
    total_recommendations: int


class DishRestaurant(BaseModel):
    name: str
    category: Optional[str]
    address: Optional[str]
    lat: float
    lng: float
    distance_km: float
    mood_match_score: float


class DishSuggestion(BaseModel):
    dish_name: str
    cuisine: Optional[str]
    spice_level: Optional[str]
    temperature: Optional[str]
    dish_confidence: Optional[str]
    restaurants: List[DishRestaurant]


class SuggestDishResponse(BaseModel):
    status: str
    mood: str
    suggested_dishes: List[DishSuggestion]
    total_dishes: int


class RestaurantDetailsResponse(BaseModel):
    status: str
    placeId: str
    has_details: bool
    name: Optional[str] = None
    price: Optional[float] = None
    atmosphere: Optional[str] = None
    opening_hours: Optional[str] = None
    images: List[str] = []
    reviews: List[dict] = []
    menu_url: Optional[str] = None
    website: Optional[str] = None
    google_maps_url: Optional[str] = None


class ModelInfoResponse(BaseModel):
    model: str
    task: str
    classes: List[str]
    status: str


class HealthResponse(BaseModel):
    status: str
    services: dict

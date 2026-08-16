from fastapi import FastAPI
from pathlib import Path


def init_app(app: FastAPI):
    @app.on_event("startup")
    async def _startup():
        # Lazy initialize infrastructure and services; assign to app.state for DI
        try:
            from src.infrastructure.repositories.csv_restaurant_repository import CSVRestaurantRepository
            from src.application.services.recommendation_service import RecommendationService
            from src.application.services.dish_recommendation_service import DishRecommendationService
            from src.application.services.restaurant_details_service import restaurant_details_service as restaurant_details_service_global
            from src.application.services.depth_estimation_service import DepthEstimationService

            repo = CSVRestaurantRepository("data_pipeline/data_cleaned/dataset_moodbite_features.csv")
            recommender = RecommendationService(repository=repo)
            # dish service prefers a RecommendationService instance; create one bound to repo
            dish_service = DishRecommendationService(base_service=recommender)
            depth_service = DepthEstimationService()

            app.state.recommendation_service = recommender
            app.state.dish_recommendation_service = dish_service
            # keep existing global restaurant details service
            app.state.restaurant_details_service = restaurant_details_service_global
            app.state.depth_estimation_service = depth_service

            print("✅ App startup: services initialized and registered on app.state")
        except Exception as e:
            # Startup should not necessarily crash the app; log and continue.
            print(f"⚠️ Startup wiring had an issue: {e}")

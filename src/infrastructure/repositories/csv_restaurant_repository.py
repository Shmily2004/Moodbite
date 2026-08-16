from pathlib import Path
import pandas as pd
from typing import Optional


class CSVRestaurantRepository:
    def __init__(self, path: str = "data_pipeline/data_cleaned/dataset_moodbite_features.csv"):
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.exists()

    def load_all(self) -> pd.DataFrame:
        if not self.exists():
            raise FileNotFoundError(f"Dataset not found: {self.path}")
        return pd.read_csv(self.path)

    def get_by_place_id(self, place_id: str) -> Optional[dict]:
        df = self.load_all()
        row = df[df.get("placeId") == place_id]
        if row.empty:
            return None
        return row.iloc[0].to_dict()

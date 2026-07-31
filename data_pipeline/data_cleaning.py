import os
import pandas as pd
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def clean_data(raw_file: str = None):
    """
    MoodBite Data Cleaning Pipeline
    - Handles missing values
    - Removes duplicates
    - Filters invalid records
    """
    BASE_DIR = Path.cwd()
    RAW_DIR = BASE_DIR / 'data_pipeline' / 'data_raw'
    CLEANED_DIR = BASE_DIR / 'data_pipeline' / 'data_cleaned'

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    if raw_file is None:
        csv_files = list(RAW_DIR.glob('*.csv'))
        if not csv_files:
            logger.warning(f"No CSV files found in {RAW_DIR}")
            return
        raw_path = csv_files[0]
    else:
        raw_path = Path(raw_file)

    logger.info(f'Cleaning data from: {raw_path}')
    
    try:
        df = pd.read_csv(raw_path)
    except Exception as e:
        logger.error(f"Failed to read {raw_path}: {e}")
        return

    initial_count = len(df)
    
    # 1. Remove duplicates
    df = df.drop_duplicates()
    logger.info(f"Removed {initial_count - len(df)} duplicate records.")

    # 2. Handle missing essential values
    essential_cols = ['title', 'location/lat', 'location/lng']
    available_essential = [col for col in essential_cols if col in df.columns]
    
    if available_essential:
        before_drop = len(df)
        df = df.dropna(subset=available_essential)
        logger.info(f"Dropped {before_drop - len(df)} records with missing essential fields: {available_essential}")

    # 3. Fill non-essential missing values
    if 'totalScore' in df.columns:
        df['totalScore'] = df['totalScore'].fillna(0)
    
    if 'categoryName' in df.columns:
        df['categoryName'] = df['categoryName'].fillna('Unknown')

    # 4. Save cleaned data
    output_path = CLEANED_DIR / 'dataset_moodbite_clean.csv'
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"Cleaned data saved to {output_path}")

if __name__ == "__main__":
    clean_data()

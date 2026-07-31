import os
import pandas as pd
from pathlib import Path

def clean_data():
    """
    MoodBite Data Cleaning Pipeline
    Refactored from 01_data_cleaning.ipynb
    """
    BASE_DIR = Path.cwd()
    # Giả sử chạy từ root hoặc thư mục data_pipeline
    RAW_DIR = BASE_DIR / 'data_pipeline' / 'data_raw'
    CLEANED_DIR = BASE_DIR / 'data_pipeline' / 'data_cleaned'

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    print(f'Raw directory: {RAW_DIR}')
    print(f'Cleaned directory: {CLEANED_DIR}')

    csv_files = list(RAW_DIR.glob('*.csv'))
    print(f'CSV files found: {len(csv_files)}')
    
    # Logic tiếp theo sẽ được bổ sung dựa trên yêu cầu cụ thể của pipeline
    # ...

if __name__ == "__main__":
    clean_data()

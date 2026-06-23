import os
import gzip
import shutil
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Optional
import yaml

# Configure logging without emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pipeline.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class LocalDataLoader:
    """Loads data from manually downloaded files."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.data_dir = Path(self.config['pipeline']['data_dir'])
        self.raw_dir = self.data_dir / 'raw'
        self.processed_dir = self.data_dir / 'processed'
        
        # City mapping
        self.city_mapping = {
            'nyc': {'name': 'New York City', 'code': 'nyc'},
            'barcelona': {'name': 'Barcelona', 'code': 'bcn'},
            'edinburgh': {'name': 'Edinburgh', 'code': 'edi'}
        }
        
    def extract_gz_if_needed(self, city_code: str) -> bool:
        """Extract .gz files to CSV if needed."""
        city_raw_dir = self.raw_dir / city_code
        
        if not city_raw_dir.exists():
            logger.error(f"Directory not found: {city_raw_dir}")
            return False
        
        gz_files = list(city_raw_dir.glob('*.gz'))
        
        if not gz_files:
            logger.info(f"No .gz files found in {city_code}, assuming already extracted")
            return True
        
        for gz_path in gz_files:
            csv_path = gz_path.with_suffix('')
            
            if csv_path.exists():
                logger.info(f"CSV already exists for {gz_path.name}, skipping extraction")
                continue
            
            try:
                logger.info(f"Extracting {gz_path.name}...")
                with gzip.open(gz_path, 'rb') as f_in:
                    with open(csv_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                logger.info(f"Extracted {gz_path.name} -> {csv_path.name}")
            except Exception as e:
                logger.error(f"Failed to extract {gz_path}: {e}")
                return False
        
        return True
    
    def load_city_data(self, city_code: str) -> Dict[str, pd.DataFrame]:
        """Load all data files for a city."""
        city_dir_name = city_code
        city_raw_dir = self.raw_dir / city_dir_name
        
        if not city_raw_dir.exists():
            logger.error(f"City directory not found: {city_raw_dir}")
            logger.info(f"Expected path: {city_raw_dir.absolute()}")
            return {}
        
        # Extract .gz files first
        self.extract_gz_if_needed(city_dir_name)
        
        dataframes = {}
        
        # File patterns
        file_patterns = {
            'listings': 'listings.csv',
            'calendar': 'calendar.csv',
            'reviews': 'reviews.csv',
            'neighbourhoods': 'neighbourhoods.csv'
        }
        
        for key, filename in file_patterns.items():
            file_path = city_raw_dir / filename
            
            if file_path.exists():
                try:
                    logger.info(f"Loading {key} from {file_path}...")
                    
                    # Special handling for large calendar file
                    if key == 'calendar':
                        # Only load first 100,000 rows for testing to avoid memory issues
                        df = pd.read_csv(file_path, nrows=100000, low_memory=False)
                        logger.info(f"Loaded sample of calendar: {len(df):,} rows (limited for performance)")
                    else:
                        df = pd.read_csv(file_path)
                    
                    dataframes[key] = df
                    logger.info(f"Loaded {key}: {len(df):,} rows, {len(df.columns)} columns")
                    
                except Exception as e:
                    logger.error(f"Failed to load {file_path}: {e}")
                    dataframes[key] = pd.DataFrame()
            else:
                logger.warning(f"File not found: {file_path}")
                dataframes[key] = pd.DataFrame()
        
        return dataframes
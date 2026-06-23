import pandas as pd
import numpy as np
import re
from typing import Dict, Optional, List, Tuple
import logging
from datetime import datetime
import yaml

logger = logging.getLogger(__name__)

class DataCleaner:
    """Cleans and standardizes Airbnb data."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.date_format = self.config['processing'].get('date_format', '%Y-%m-%d')
        self.price_currency = self.config['processing'].get('price_currency', 'USD')
        
    def clean_price(self, price_str) -> Optional[float]:
        """Clean price string to numeric value."""
        if pd.isna(price_str):
            return None
        
        # Remove currency symbols, commas, and spaces
        cleaned = re.sub(r'[$,€£]', '', str(price_str))
        cleaned = re.sub(r'[^\d.]', '', cleaned)  # Keep only digits and dots
        cleaned = cleaned.strip()
        
        try:
            price = float(cleaned)
            if price < 0 or price > 10000:
                return None
            return price
        except ValueError:
            return None
    
    def clean_date(self, date_str) -> Optional[pd.Timestamp]:
        """Parse and standardize date strings."""
        if pd.isna(date_str):
            return None
        
        try:
            date = pd.to_datetime(date_str)
            if date < pd.Timestamp('2000-01-01') or date > pd.Timestamp('2030-12-31'):
                return None
            return date
        except Exception:
            return None
    
    def normalize_room_type(self, room_type: str) -> str:
        """Normalize room type to standard categories."""
        if pd.isna(room_type):
            return 'Unknown'
        
        mapping = {
            'entire home/apt': 'Entire Home/Apartment',
            'entire home': 'Entire Home/Apartment',
            'entire house': 'Entire Home/Apartment',
            'entire apartment': 'Entire Home/Apartment',
            'private room': 'Private Room',
            'shared room': 'Shared Room',
            'hotel room': 'Hotel Room'
        }
        
        cleaned = str(room_type).lower().strip()
        return mapping.get(cleaned, cleaned.title())
    
    def normalize_neighbourhood(self, neighbourhood: str) -> str:
        """Standardize neighbourhood names."""
        if pd.isna(neighbourhood):
            return 'Unknown'
        
        # Remove common prefixes/suffixes
        cleaned = str(neighbourhood).strip()
        cleaned = re.sub(r'^Neighbourhood: ', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^Neighborhood: ', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.title()
    
    def handle_missing_values(self, df: pd.DataFrame, strategy: str = 'explicit') -> pd.DataFrame:
        """
        Handle missing values according to specified strategy.
        
        Args:
            df: DataFrame to process
            strategy: 'explicit' (preserve nulls), 'drop', or 'impute'
        """
        if strategy == 'drop':
            # Only drop rows with missing critical fields
            critical_cols = ['id', 'price', 'latitude', 'longitude']
            existing_critical = [c for c in critical_cols if c in df.columns]
            if existing_critical:
                df = df.dropna(subset=existing_critical)
        
        # For explicit strategy, we keep nulls as is
        # They'll be handled in the star schema as NULLs
        
        return df
    
    def clean_all(self, data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        Apply all cleaning operations to all datasets.
        
        Args:
            data: Dictionary of DataFrames
            
        Returns:
            Cleaned DataFrames
        """
        cleaned = {}
        
        for name, df in data.items():
            if len(df) == 0:
                cleaned[name] = df
                continue
            
            logger.info(f"Cleaning {name}...")
            df_clean = df.copy()
            
            # Clean prices if column exists
            if 'price' in df_clean.columns:
                df_clean['price_clean'] = df_clean['price'].apply(self.clean_price)
            
            # Clean dates if column exists
            if 'date' in df_clean.columns:
                df_clean['date_clean'] = df_clean['date'].apply(self.clean_date)
            
            # Normalize room types
            if 'room_type' in df_clean.columns:
                df_clean['room_type_clean'] = df_clean['room_type'].apply(self.normalize_room_type)
            
            # Normalize neighbourhood
            if 'neighbourhood' in df_clean.columns and df_clean['neighbourhood'].notna().any():
                df_clean['neighbourhood_clean'] = df_clean['neighbourhood'].apply(self.normalize_neighbourhood)
            elif 'neighbourhood_cleansed' in df_clean.columns and df_clean['neighbourhood_cleansed'].notna().any():
                df_clean['neighbourhood_clean'] = df_clean['neighbourhood_cleansed'].apply(self.normalize_neighbourhood)
            elif 'neighbourhood' in df_clean.columns:
                df_clean['neighbourhood_clean'] = df_clean['neighbourhood'].apply(self.normalize_neighbourhood)
            elif 'neighbourhood_cleansed' in df_clean.columns:
                df_clean['neighbourhood_clean'] = df_clean['neighbourhood_cleansed'].apply(self.normalize_neighbourhood)
            
            # Handle missing values
            df_clean = self.handle_missing_values(df_clean, strategy='explicit')
            
            cleaned[name] = df_clean
            logger.info(f"  ✅ Cleaned {name}: {len(df_clean)} rows")
        
        return cleaned
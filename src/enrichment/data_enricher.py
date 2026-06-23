import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging
import yaml
import re

logger = logging.getLogger(__name__)

class DataEnricher:
    """Enriches Airbnb data with derived fields."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
    
    def enrich_listings(self, listings_df: pd.DataFrame) -> pd.DataFrame:
        """Add derived fields to listings."""
        if len(listings_df) == 0:
            return listings_df
        
        df = listings_df.copy()
        
        # Calculate price per bedroom - handle nulls
        if 'price_clean' in df.columns and 'bedrooms' in df.columns:
            # Ensure bedrooms is numeric and handle nulls
            df['bedrooms'] = pd.to_numeric(df['bedrooms'], errors='coerce')
            df['price_per_bedroom'] = df.apply(
                lambda row: row['price_clean'] / row['bedrooms'] if pd.notna(row['price_clean']) and pd.notna(row['bedrooms']) and row['bedrooms'] > 0 else None,
                axis=1
            )
        
        # Calculate host tenure - handle nulls
        if 'host_since' in df.columns:
            df['host_since_clean'] = pd.to_datetime(df['host_since'], errors='coerce')
            df['host_tenure_years'] = df['host_since_clean'].apply(
                lambda x: (pd.Timestamp.now() - x).days / 365.25 if pd.notna(x) else None
            )
        
        # Create host type categories - handle nulls
        if 'calculated_host_listings_count' in df.columns:
            df['calculated_host_listings_count'] = pd.to_numeric(
                df['calculated_host_listings_count'], errors='coerce'
            )
            
            def classify_host(count):
                if pd.isna(count):
                    return 'Unknown'
                elif count <= 1:
                    return 'Single Listing'
                elif count <= 3:
                    return 'Small Host'
                elif count <= 10:
                    return 'Medium Host'
                else:
                    return 'Large Host'
            
            df['host_type'] = df['calculated_host_listings_count'].apply(classify_host)
        
        # Create price tiers - handle nulls
        if 'price_clean' in df.columns:
            # Only apply cut to non-null values
            price_clean_nonull = df['price_clean'].dropna()
            
            if len(price_clean_nonull) > 0:
                # Define bins
                bins = [0, 50, 100, 200, 500, float('inf')]
                labels = ['Budget', 'Economy', 'Mid-Range', 'Premium', 'Luxury']
                
                # Create a function to assign tiers
                def assign_price_tier(price):
                    if pd.isna(price):
                        return 'Unknown'
                    elif price <= 50:
                        return 'Budget'
                    elif price <= 100:
                        return 'Economy'
                    elif price <= 200:
                        return 'Mid-Range'
                    elif price <= 500:
                        return 'Premium'
                    else:
                        return 'Luxury'
                
                df['price_tier'] = df['price_clean'].apply(assign_price_tier)
        
        # Copy over superhost flag
        if 'host_is_superhost' in df.columns:
            df['is_superhost'] = df['host_is_superhost'].apply(
                lambda x: True if x in ['t', 'true', 'True', 1, '1'] else False
            )
        
        return df
    
    def enrich_calendar(self, calendar_df: pd.DataFrame, 
                        listings_df: pd.DataFrame) -> pd.DataFrame:
        """Enrich calendar with listing information."""
        if len(calendar_df) == 0 or len(listings_df) == 0:
            return calendar_df
        
        df = calendar_df.copy()
        
        # Clean price
        if 'price' in df.columns:
            df['price_clean'] = df['price'].apply(self._clean_price)
        
        # Merge with listings for additional context
        if 'listing_id' in df.columns and 'id' in listings_df.columns:
            # Select only needed columns from listings
            listings_subset = listings_df[['id', 'price_clean', 'room_type_clean', 
                                         'neighbourhood_clean', 'accommodates', 
                                         'bedrooms', 'beds']].copy()
            # Rename to avoid conflicts
            listings_subset = listings_subset.rename(columns={
                'price_clean': 'listing_price',
                'room_type_clean': 'room_type',
                'neighbourhood_clean': 'neighbourhood'
            })
            
            df = df.merge(listings_subset, left_on='listing_id', 
                         right_on='id', how='left', suffixes=('', '_listing'))
        
        return df
    
    def enrich_reviews(self, reviews_df: pd.DataFrame) -> pd.DataFrame:
        """Add features to reviews."""
        if len(reviews_df) == 0:
            return reviews_df
        
        df = reviews_df.copy()
        
        # Clean dates
        if 'date' in df.columns:
            df['review_date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Extract review length
        if 'comments' in df.columns:
            # Ensure comments are strings
            df['comments'] = df['comments'].astype(str)
            df['review_length'] = df['comments'].str.len()
            df['review_word_count'] = df['comments'].str.split().str.len()
        
        return df
    
    def aggregate_calendar_stats(self, calendar_df: pd.DataFrame) -> pd.DataFrame:
        """Create calendar aggregates per listing."""
        if len(calendar_df) == 0:
            return pd.DataFrame()
        
        df = calendar_df.copy()
        
        # Available flag
        if 'available' in df.columns:
            df['is_available'] = df['available'] == 't'
        
        # Group by listing
        agg_dict = {}
        
        if 'is_available' in df.columns:
            # Calculate occupancy rate (available = t means available)
            agg_dict['occupancy_rate'] = (1 - df.groupby('listing_id')['is_available'].mean()) * 100
            agg_dict['available_days'] = df.groupby('listing_id')['is_available'].sum()
        
        if 'price_clean' in df.columns:
            agg_dict['avg_price'] = df.groupby('listing_id')['price_clean'].mean()
            agg_dict['min_price'] = df.groupby('listing_id')['price_clean'].min()
            agg_dict['max_price'] = df.groupby('listing_id')['price_clean'].max()
            agg_dict['price_std'] = df.groupby('listing_id')['price_clean'].std()
        
        # Combine aggregates
        if agg_dict:
            result = pd.DataFrame()
            for key, series in agg_dict.items():
                if key == 'price_std':
                    # Handle std dev for single values
                    result[key] = series
                else:
                    result[key] = series
            result = result.reset_index()
            result = result.rename(columns={'index': 'listing_id'})
            return result
        
        return pd.DataFrame()
    
    def enrich_all(self, data: Dict[str, pd.DataFrame], 
                   city_code: str) -> Dict[str, pd.DataFrame]:
        """Apply all enrichment to all datasets."""
        enriched = {}
        
        # Enrich listings first (used by others)
        if 'listings' in data and len(data['listings']) > 0:
            enriched['listings'] = self.enrich_listings(data['listings'])
            logger.info(f"Enriched listings: {len(enriched['listings'])} rows")
        else:
            enriched['listings'] = pd.DataFrame()
        
        # Enrich calendar using listings
        if 'calendar' in data and len(data['calendar']) > 0 and len(enriched['listings']) > 0:
            enriched['calendar'] = self.enrich_calendar(
                data['calendar'], 
                enriched['listings']
            )
            logger.info(f"Enriched calendar: {len(enriched['calendar'])} rows")
            
            # Create calendar aggregates
            enriched['calendar_stats'] = self.aggregate_calendar_stats(
                enriched['calendar']
            )
            logger.info(f"Created calendar_stats: {len(enriched['calendar_stats'])} rows")
        elif 'calendar' in data and len(data['calendar']) > 0:
            enriched['calendar'] = data['calendar']
            logger.info(f"Calendar loaded without enrichment: {len(enriched['calendar'])} rows")
        
        # Enrich reviews
        if 'reviews' in data and len(data['reviews']) > 0:
            enriched['reviews'] = self.enrich_reviews(data['reviews'])
            logger.info(f"Enriched reviews: {len(enriched['reviews'])} rows")
        else:
            enriched['reviews'] = pd.DataFrame()
        
        # Copy neighbourhoods as-is
        if 'neighbourhoods' in data and len(data['neighbourhoods']) > 0:
            enriched['neighbourhoods'] = data['neighbourhoods']
            logger.info(f"Neighbourhoods: {len(enriched['neighbourhoods'])} rows")
        else:
            enriched['neighbourhoods'] = pd.DataFrame()
        
        return enriched
    
    def _clean_price(self, price_str) -> Optional[float]:
        """Helper to clean price."""
        if pd.isna(price_str):
            return None
        try:
            cleaned = re.sub(r'[$,€£]', '', str(price_str))
            cleaned = re.sub(r'[^\d.]', '', cleaned)
            return float(cleaned) if cleaned else None
        except:
            return None

    def _clean_price_safe(self, price_str):
        """Safely clean price without raising exceptions."""
        try:
            return self._clean_price(price_str)
        except Exception:
            return None
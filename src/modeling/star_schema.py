import sqlite3
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Optional
import yaml
import json

logger = logging.getLogger(__name__)

class StarSchemaBuilderSQLite:
    """Builds star schema in SQLite."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.data_dir = Path(self.config['pipeline']['data_dir'])
        self.processed_dir = self.data_dir / 'processed'
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def build_schema(self, data: Dict[str, pd.DataFrame], city_code: str) -> sqlite3.Connection:
        """
        Build star schema for a city.
        
        Args:
            data: Dictionary of enriched DataFrames
            city_code: City code
            
        Returns:
            SQLite connection with schema
        """
        # Create database file
        db_path = self.processed_dir / city_code / f"{city_code}.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Delete existing DB if it exists (fresh start)
        if db_path.exists():
            db_path.unlink()
        
        conn = sqlite3.connect(str(db_path))
        
        try:
            # Register tables - use names as they are (listings, calendar, reviews, etc.)
            for name, df in data.items():
                if len(df) > 0:
                    # Use the original name (listings, calendar, reviews, neighbourhoods)
                    df.to_sql(name, conn, if_exists='replace', index=False)
                    logger.info(f"Loaded {name}: {len(df):,} rows into SQLite")
            
            # Create star schema - use the actual table names
            self._create_dimension_tables(conn)
            self._create_fact_tables(conn)
            self._create_analytics_views(conn)
            
            logger.info(f"Star schema built for {city_code}")
            
        except Exception as e:
            logger.error(f"Failed to build schema for {city_code}: {e}")
            raise
        
        return conn
    
    def _get_table_columns(self, conn: sqlite3.Connection, table_name: str) -> list:
        """Get list of column names for a table."""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cursor.fetchall()]
    
    def _create_dimension_tables(self, conn: sqlite3.Connection):
        """Create dimension tables."""
        cursor = conn.cursor()
        
        # Check if listings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='listings'")
        if not cursor.fetchone():
            logger.error("Listings table not found in database")
            return
        
        # Get available columns in listings
        listings_cols = self._get_table_columns(conn, 'listings')
        logger.info(f"Available columns in listings: {listings_cols[:10]}...")
        
        # Build column list dynamically
        dim_listing_cols = []
        
        # Required columns with fallbacks
        col_mappings = {
            'listing_key': 'id',
            'listing_id': 'id',
            'name': 'name',
            'neighbourhood': 'neighbourhood_clean',
            'room_type': 'room_type_clean',
            'property_type': 'property_type',
            'accommodates': 'accommodates',
            'bedrooms': 'bedrooms',
            'beds': 'beds',
            'bathrooms': 'bathrooms',
            'base_price': 'price_clean',
            'host_id': 'host_id',
            'host_name': 'host_name',
            'host_is_superhost': 'host_is_superhost',
            'host_tenure_years': 'host_tenure_years',
            'host_type': 'host_type',
            'latitude': 'latitude',
            'longitude': 'longitude'
        }
        
        # Build SELECT clause with fallbacks
        select_parts = []
        for alias, col in col_mappings.items():
            if col in listings_cols:
                select_parts.append(f"{col} AS {alias}")
            else:
                # Use NULL as fallback
                select_parts.append(f"NULL AS {alias}")
        
        # Try to add optional columns if they exist
        optional_cols = ['description', 'amenities', 'host_since', 'host_response_time', 
                        'host_response_rate', 'price_tier']
        for col in optional_cols:
            if col in listings_cols:
                select_parts.append(col)
            else:
                # Try to find alternative
                if col == 'price_tier':
                    # Try to find price_tier or create from price
                    if 'price_tier' in listings_cols:
                        select_parts.append('price_tier')
                    else:
                        select_parts.append('NULL AS price_tier')
                elif col == 'amenities' and 'amenities' in listings_cols:
                    select_parts.append('amenities')
                else:
                    select_parts.append(f"NULL AS {col}")
        
        select_clause = ",\n            ".join(select_parts)
        
        # 1. Dim Listing
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS dim_listing AS
        SELECT 
            {select_clause}
        FROM listings
        WHERE id IS NOT NULL
        """)
        
        logger.info("dim_listing created")
        
        # 2. Dim Host
        # Check what host columns exist
        host_cols = ['host_id', 'host_name', 'host_since', 'host_location', 'host_about',
                    'host_response_time', 'host_response_rate', 'host_acceptance_rate',
                    'host_is_superhost', 'host_thumbnail_url', 'host_picture_url',
                    'host_neighbourhood', 'host_listings_count', 
                    'calculated_host_listings_count', 'host_tenure_years', 'host_type']
        
        host_select_parts = []
        for col in host_cols:
            if col in listings_cols:
                if col == 'host_id':
                    host_select_parts.append(f"{col} AS host_key")
                    host_select_parts.append(f"{col}")
                else:
                    host_select_parts.append(col)
            else:
                host_select_parts.append(f"NULL AS {col}")
        
        host_select = ",\n            ".join(host_select_parts)
        
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS dim_host AS
        SELECT DISTINCT
            {host_select}
        FROM listings
        WHERE host_id IS NOT NULL
        """)
        
        logger.info("dim_host created")
        
        # 3. Dim Neighbourhood
        if 'neighbourhood_clean' in listings_cols:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_neighbourhood AS
            SELECT DISTINCT
                neighbourhood_clean AS neighbourhood_key,
                neighbourhood_clean AS neighbourhood,
                neighbourhood_group_cleansed AS neighbourhood_group
            FROM listings
            WHERE neighbourhood_clean IS NOT NULL
            """)
        else:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_neighbourhood AS
            SELECT DISTINCT
                neighbourhood AS neighbourhood_key,
                neighbourhood AS neighbourhood,
                NULL AS neighbourhood_group
            FROM listings
            WHERE neighbourhood IS NOT NULL
            """)
        
        logger.info("dim_neighbourhood created")
        
        # 4. Dim Date (using calendar data if available)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='calendar'")
        if cursor.fetchone():
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_date AS
            SELECT DISTINCT
                date AS date_key,
                date AS full_date,
                strftime('%Y', date) AS year,
                strftime('%m', date) AS month,
                strftime('%d', date) AS day,
                strftime('%w', date) AS day_of_week,
                CASE 
                    WHEN strftime('%w', date) IN ('0', '6') THEN 'Weekend'
                    ELSE 'Weekday'
                END AS day_type,
                strftime('%W', date) AS week,
                CASE 
                    WHEN strftime('%m', date) IN ('12', '01', '02') THEN 'Winter'
                    WHEN strftime('%m', date) IN ('03', '04', '05') THEN 'Spring'
                    WHEN strftime('%m', date) IN ('06', '07', '08') THEN 'Summer'
                    ELSE 'Fall'
                END AS season
            FROM calendar
            WHERE date IS NOT NULL
            """)
            logger.info("dim_date created")
        
        conn.commit()
    
    def _create_fact_tables(self, conn: sqlite3.Connection):
        """Create fact tables."""
        cursor = conn.cursor()
        
        # Check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        logger.info(f"Available tables: {tables}")
        
        # Get listings columns
        listings_cols = self._get_table_columns(conn, 'listings') if 'listings' in tables else []
        
        # 1. Fact Listing Daily
        if "calendar" in tables and "listings" in tables:
            try:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS fact_listing_daily AS
                SELECT 
                    c.listing_id,
                    c.date AS date_key,
                    l.price_clean AS price,
                    CASE WHEN c.available = 't' THEN 1 ELSE 0 END AS is_available,
                    c.minimum_nights,
                    c.maximum_nights,
                    c.price_clean AS daily_price,
                    CASE 
                        WHEN c.available = 't' THEN 0 
                        ELSE c.price_clean 
                    END AS revenue_proxy,
                    l.id AS listing_key,
                    l.host_id AS host_key,
                    l.neighbourhood_clean AS neighbourhood_key,
                    l.accommodates,
                    l.bedrooms,
                    l.beds,
                    l.room_type_clean AS room_type
                FROM calendar c
                JOIN listings l ON c.listing_id = l.id
                WHERE c.price_clean IS NOT NULL
                  AND l.price_clean IS NOT NULL
                """)
                logger.info("fact_listing_daily created")
            except Exception as e:
                logger.warning(f"Could not create fact_listing_daily: {e}")
        
        # 2. Fact Listing Summary
        if "listings" in tables:
            # Build summary with available columns
            summary_cols = [
                "l.id AS listing_key",
                "l.host_id AS host_key",
                "l.neighbourhood_clean AS neighbourhood_key",
                "l.price_clean AS price",
                "l.room_type_clean AS room_type", 
                "l.minimum_nights",
                "l.maximum_nights"
            ]
            
            # Add optional columns if they exist
            optional_summary_cols = ['availability_365', 'number_of_reviews', 'reviews_per_month', 
                                    'calculated_host_listings_count', 'price_per_bedroom',
                                    'host_tenure_years', 'review_scores_rating', 
                                    'review_scores_accuracy', 'review_scores_cleanliness',
                                    'review_scores_checkin', 'review_scores_communication',
                                    'review_scores_location', 'review_scores_value',
                                    'instant_bookable', 'host_is_superhost']
            
            for col in optional_summary_cols:
                if col in listings_cols:
                    summary_cols.append(col)
                else:
                    summary_cols.append(f"NULL AS {col}")
            
            # Add calculated fields
            summary_cols.append("""
                CASE 
                    WHEN l.availability_365 IS NOT NULL THEN (365 - l.availability_365) / 365.0 * 100
                    ELSE NULL
                END AS estimated_occupancy_rate
            """)
            summary_cols.append("""
                CASE 
                    WHEN l.availability_365 IS NOT NULL AND l.price_clean IS NOT NULL 
                    THEN (365 - l.availability_365) * l.price_clean
                    ELSE NULL
                END AS estimated_annual_revenue
            """)
            
            summary_select = ",\n                ".join(summary_cols)
            
            try:
                cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS fact_listing_summary AS
                SELECT 
                    {summary_select}
                FROM listings l
                WHERE l.id IS NOT NULL
                """)
                logger.info("fact_listing_summary created")
            except Exception as e:
                logger.warning(f"Could not create fact_listing_summary: {e}")
        
        # 3. Fact Reviews
        if "reviews" in tables and "listings" in tables:
            try:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS fact_reviews AS
                SELECT 
                    r.listing_id AS listing_key,
                    r.date AS review_date_key,
                    r.reviewer_id,
                    r.comments,
                    r.review_length,
                    r.review_word_count,
                    l.id AS listing_key_dim,
                    l.host_id AS host_key
                FROM reviews r
                JOIN listings l ON r.listing_id = l.id
                WHERE r.date IS NOT NULL
                """)
                logger.info("fact_reviews created")
            except Exception as e:
                logger.warning(f"Could not create fact_reviews: {e}")
        
        conn.commit()
    
    def _create_analytics_views(self, conn: sqlite3.Connection):
        """Create useful analytical views."""
        cursor = conn.cursor()
        
        # Check if fact tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        
        # View: Listing performance
        if "fact_listing_summary" in tables and "listings" in tables:
            try:
                cursor.execute("""
                CREATE VIEW IF NOT EXISTS v_listing_performance AS
                SELECT 
                    ls.id AS listing_id,
                    ls.name,
                    ls.neighbourhood_clean AS neighbourhood,
                    ls.room_type_clean AS room_type,
                    ls.price_clean AS price,
                    fs.estimated_occupancy_rate,
                    fs.estimated_annual_revenue,
                    fs.number_of_reviews,
                    fs.review_scores_rating,
                    fs.host_is_superhost,
                    fs.host_tenure_years
                FROM listings ls
                JOIN fact_listing_summary fs ON ls.id = fs.listing_key
                """)
                logger.info("v_listing_performance created")
            except Exception as e:
                logger.warning(f"Could not create v_listing_performance: {e}")
        
        # View: Daily market summary
        if "fact_listing_daily" in tables:
            try:
                cursor.execute("""
                CREATE VIEW IF NOT EXISTS v_daily_market_summary AS
                SELECT 
                    date_key,
                    COUNT(DISTINCT listing_id) AS active_listings,
                    AVG(price) AS avg_daily_price,
                    SUM(CASE WHEN is_available = 1 THEN 1 ELSE 0 END) AS available_listings,
                    SUM(CASE WHEN is_available = 0 THEN 1 ELSE 0 END) AS occupied_listings,
                    SUM(revenue_proxy) AS total_daily_revenue
                FROM fact_listing_daily
                GROUP BY date_key
                ORDER BY date_key
                """)
                logger.info("v_daily_market_summary created")
            except Exception as e:
                logger.warning(f"Could not create v_daily_market_summary: {e}")
        
        # View: Host performance
        if "dim_host" in tables and "listings" in tables:
            try:
                cursor.execute("""
                CREATE VIEW IF NOT EXISTS v_host_performance AS
                SELECT 
                    h.host_id,
                    h.host_name,
                    h.host_is_superhost,
                    h.host_type,
                    COUNT(DISTINCT l.id) AS total_listings,
                    AVG(l.price_clean) AS avg_listing_price,
                    AVG(l.review_scores_rating) AS avg_rating,
                    SUM(l.number_of_reviews) AS total_reviews,
                    AVG(l.availability_365) AS avg_availability,
                    AVG(l.price_per_bedroom) AS avg_price_per_bedroom,
                    AVG(l.host_tenure_years) AS avg_tenure_years
                FROM dim_host h
                JOIN listings l ON h.host_id = l.host_id
                GROUP BY h.host_id, h.host_name, h.host_is_superhost, h.host_type
                """)
                logger.info("v_host_performance created")
            except Exception as e:
                logger.warning(f"Could not create v_host_performance: {e}")
        
        conn.commit()
    
    def run_analytical_query(self, conn: sqlite3.Connection, query: str) -> pd.DataFrame:
        """Run an analytical query and return results."""
        try:
            result = pd.read_sql_query(query, conn)
            logger.info(f"Query executed: {len(result)} rows returned")
            return result
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
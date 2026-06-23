import sys
import os
from pathlib import Path
import logging
import argparse
import yaml
from datetime import datetime
import pandas as pd
import numpy as np
import sqlite3
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from ingestion.local_loader import LocalDataLoader
from cleaning.data_cleaner import DataCleaner
from enrichment.data_enricher import DataEnricher
from modeling.star_schema import StarSchemaBuilderSQLite

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pipeline.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DataPipelineSQLite:
    """End-to-end data pipeline for Airbnb assessment using SQLite."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.data_dir = Path(self.config['pipeline']['data_dir'])
        self.processed_dir = self.data_dir / 'processed'
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        self.loader = LocalDataLoader(config_path)
        self.cleaner = DataCleaner(config_path)
        self.enricher = DataEnricher(config_path)
        self.schema_builder = StarSchemaBuilderSQLite(config_path)
        
        # Track pipeline runs
        self.run_metadata = {
            'timestamp': datetime.now().isoformat(),
            'cities_processed': [],
            'status': 'started'
        }
    
    def _convert_to_serializable(self, obj):
        """Convert numpy/pandas types to Python native types for JSON serialization."""
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Series):
            return obj.to_list()
        elif isinstance(obj, dict):
            return {k: self._convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            return str(obj)
    
    def process_city(self, city_code: str) -> dict:
        """
        Process a single city through the entire pipeline.
        
        Args:
            city_code: City code (nyc, barcelona, edinburgh)
            
        Returns:
            Dict: Processing results and metadata
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing {city_code.upper()}")
        logger.info(f"{'='*60}")
        
        results = {
            'city': city_code,
            'status': 'processing',
            'tables': {},
            'quality_report': {}
        }
        
        try:
            # Step 1: Load raw data
            logger.info("Step 1: Loading raw data...")
            raw_data = self.loader.load_city_data(city_code)
            
            if not raw_data:
                raise ValueError(f"No data loaded for {city_code}")
            
            results['tables']['raw'] = {name: len(df) for name, df in raw_data.items() if len(df) > 0}
            
            # Step 2: Clean data
            logger.info("Step 2: Cleaning data...")
            cleaned_data = self.cleaner.clean_all(raw_data)
            
            results['tables']['cleaned'] = {name: len(df) for name, df in cleaned_data.items() if len(df) > 0}
            
            # Step 3: Enrich data
            logger.info("Step 3: Enriching data...")
            enriched_data = self.enricher.enrich_all(cleaned_data, city_code)
            
            results['tables']['enriched'] = {name: len(df) for name, df in enriched_data.items() if len(df) > 0}
            
            # Step 4: Build SQLite star schema
            logger.info("Step 4: Building star schema...")
            conn = self.schema_builder.build_schema(enriched_data, city_code)
            conn.close()
            
            # Step 5: Save processed data as Parquet
            logger.info("Step 5: Saving processed data...")
            city_processed_dir = self.processed_dir / city_code
            city_processed_dir.mkdir(exist_ok=True)
            
            for name, df in enriched_data.items():
                if len(df) > 0:
                    df.to_parquet(city_processed_dir / f"{name}.parquet")
                    logger.info(f"  Saved {name}.parquet ({len(df):,} rows)")
            
            # Step 6: Generate quality report
            logger.info("Step 6: Generating quality report...")
            quality_report = self.generate_quality_report(enriched_data, city_code)
            
            # Convert numpy types to Python types for JSON serialization
            quality_report_serializable = self._convert_to_serializable(quality_report)
            results['quality_report'] = quality_report_serializable
            
            # Save quality report
            with open(city_processed_dir / 'quality_report.json', 'w', encoding='utf-8') as f:
                json.dump(quality_report_serializable, f, indent=2, ensure_ascii=False)
            
            results['status'] = 'success'
            self.run_metadata['cities_processed'].append(city_code)
            
            logger.info(f"Successfully processed {city_code}")
            
        except Exception as e:
            logger.error(f"Failed to process {city_code}: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
        
        return results
    
    def generate_quality_report(self, data: dict, city_code: str) -> dict:
        """Generate data quality report."""
        report = {
            'city': city_code,
            'total_records': {},
            'null_rates': {},
            'duplicates': {},
            'validation_errors': {}
        }
        
        for name, df in data.items():
            if len(df) == 0:
                continue
            
            report['total_records'][name] = int(len(df))
            
            # Null rates
            null_rates = {}
            for col in df.columns:
                null_pct = (df[col].isna().sum() / len(df)) * 100
                if null_pct > 5:
                    null_rates[col] = float(round(null_pct, 2))
            report['null_rates'][name] = null_rates
            
            # Duplicates
            if 'id' in df.columns:
                report['duplicates'][name] = int(df['id'].duplicated().sum())
            
            # Validation errors
            validation_errors = []
            if 'price_clean' in df.columns:
                invalid_price = ((df['price_clean'] < 0) | (df['price_clean'] > 10000)).sum()
                if invalid_price > 0:
                    validation_errors.append(f"Invalid prices: {int(invalid_price)}")
            
            if 'latitude' in df.columns and 'longitude' in df.columns:
                invalid_lat = ((df['latitude'] < -90) | (df['latitude'] > 90)).sum()
                invalid_lon = ((df['longitude'] < -180) | (df['longitude'] > 180)).sum()
                if invalid_lat > 0:
                    validation_errors.append(f"Invalid latitudes: {int(invalid_lat)}")
                if invalid_lon > 0:
                    validation_errors.append(f"Invalid longitudes: {int(invalid_lon)}")
            
            report['validation_errors'][name] = validation_errors
        
        return report
    
    def run_all_cities(self):
        """Run pipeline for all cities in config."""
        logger.info("Starting pipeline for all cities")
        
        cities = ['nyc', 'barcelona', 'edinburgh']
        results = {}
        
        for city in cities:
            results[city] = self.process_city(city)
        
        # Save pipeline metadata
        self.run_metadata['status'] = 'completed'
        self.run_metadata['results'] = self._convert_to_serializable(results)
        
        with open(self.processed_dir / 'pipeline_metadata.json', 'w', encoding='utf-8') as f:
            json.dump(self.run_metadata, f, indent=2, ensure_ascii=False)
        
        logger.info("\n" + "="*60)
        logger.info("Pipeline Completed")
        logger.info("="*60)
        
        # Summary
        for city, result in results.items():
            status = result['status']
            if status == 'success':
                total_rows = sum(result['tables']['enriched'].values())
                logger.info(f"{city.upper()}: Success ({total_rows:,} rows processed)")
            else:
                logger.info(f"{city.upper()}: Failed - {result.get('error', 'Unknown error')}")
        
        return results

def main():
    parser = argparse.ArgumentParser(description='Run Airbnb data pipeline')
    parser.add_argument('--cities', nargs='+', 
                       choices=['nyc', 'barcelona', 'edinburgh', 'all'],
                       default=['all'],
                       help='Cities to process')
    parser.add_argument('--config', default='config/config.yaml',
                       help='Config file path')
    
    args = parser.parse_args()
    
    # Determine cities to process
    if 'all' in args.cities:
        cities = ['nyc', 'barcelona', 'edinburgh']
    else:
        cities = args.cities
    
    # Initialize pipeline
    pipeline = DataPipelineSQLite(args.config)
    
    # Process cities
    for city in cities:
        pipeline.process_city(city)
    
    # Generate summary report
    print("\n" + "="*50)
    print("Pipeline Summary")
    print("="*50)
    print(f"Cities processed: {', '.join(cities)}")
    print(f"Output directory: {pipeline.processed_dir}")
    print("\nCheck pipeline.log for detailed logs")

if __name__ == "__main__":
    main()
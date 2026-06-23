"""
File checker to verify manually downloaded files.
"""

import os
from pathlib import Path
import pandas as pd
import gzip
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_file(file_path):
    """Check if a file is valid and readable."""
    try:
        if str(file_path).endswith('.gz'):
            # Try to read first few lines of gzipped CSV
            with gzip.open(file_path, 'rt') as f:
                header = f.readline()
                sample = f.readline()
                logger.info(f"✅ {file_path.name}: Valid GZIP (Header: {header[:50]}...)")
                return True
        else:
            # Regular CSV
            df_sample = pd.read_csv(file_path, nrows=5)
            logger.info(f"✅ {file_path.name}: Valid CSV ({len(df_sample.columns)} columns)")
            return True
    except Exception as e:
        logger.error(f"❌ {file_path.name}: Error - {e}")
        return False

# Check all files
for city in ['nyc', 'barcelona', 'edinburgh']:
    city_dir = Path(f'data/raw/{city}')
    if city_dir.exists():
        logger.info(f"\n=== Checking {city.upper()} ===")
        for file_path in city_dir.glob('*'):
            if file_path.is_file():
                check_file(file_path)
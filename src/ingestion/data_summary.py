import pandas as pd
import gzip
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def summarize_csv(file_path, is_gz=False):
    """Quick summary of a CSV file."""
    try:
        if is_gz:
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                df = pd.read_csv(f, nrows=5)
        else:
            df = pd.read_csv(file_path, nrows=5)
        
        # Get total rows without loading everything
        if is_gz:
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                total_rows = sum(1 for _ in f) - 1  # Subtract header
        else:
            total_rows = sum(1 for _ in open(file_path)) - 1
        
        return {
            'rows': total_rows,
            'columns': len(df.columns),
            'sample_columns': list(df.columns[:5])
        }
    except Exception as e:
        return {'error': str(e)}

def main():
    cities = ['nyc', 'barcelona', 'edinburgh']
    files = ['listings.csv.gz', 'calendar.csv.gz', 'reviews.csv.gz', 
             'neighbourhoods.csv', 'neighbourhoods.geojson']
    
    print("\n" + "="*70)
    print("DATA FILES SUMMARY")
    print("="*70)
    
    for city in cities:
        print(f"\n📁 {city.upper()}")
        print("-"*50)
        
        city_dir = Path(f'data/raw/{city}')
        if not city_dir.exists():
            print(f"  ❌ Directory not found: {city_dir}")
            continue
        
        for file in files:
            file_path = city_dir / file
            if not file_path.exists():
                print(f"  ⚠️  {file}: Not found")
                continue
            
            is_gz = file.endswith('.gz')
            summary = summarize_csv(file_path, is_gz)
            
            if 'error' in summary:
                print(f"  ❌ {file}: {summary['error']}")
            else:
                status = "✅" if summary['rows'] > 0 else "⚠️"
                print(f"  {status} {file}: {summary['rows']:,} rows, {summary['columns']} columns")
                if summary['columns'] > 0:
                    print(f"      Columns: {', '.join(summary['sample_columns'])}")

if __name__ == "__main__":
    main()
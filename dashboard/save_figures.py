import streamlit as st
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import sqlite3
from pathlib import Path

# Set Plotly to use kaleido for image export
pio.kaleido.scope.default_format = "png"

def get_connection(city):
    """Get SQLite connection."""
    db_path = f'data/processed/{city}/{city}.db'
    if not Path(db_path).exists():
        db_path = f'../data/processed/{city}/{city}.db'
    if Path(db_path).exists():
        return sqlite3.connect(db_path)
    return None

def query_db(conn, query):
    return pd.read_sql_query(query, conn)

def load_city_data(city):
    """Load data for a city."""
    conn = get_connection(city)
    if conn is None:
        return None
    
    data = {}
    
    # Summary stats
    try:
        df = query_db(conn, """
            SELECT 
                COUNT(*) as total_listings,
                AVG(price) as avg_price,
                AVG(estimated_occupancy_rate) as avg_occupancy,
                AVG(review_scores_rating) as avg_rating,
                SUM(CASE WHEN host_is_superhost = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pct_superhost
            FROM fact_listing_summary
            WHERE price IS NOT NULL AND price < 1000
        """)
        data['summary'] = df if not df.empty else pd.DataFrame()
    except:
        data['summary'] = pd.DataFrame()
    
    # Price distribution
    try:
        df = query_db(conn, """
            SELECT 
                price,
                room_type,
                neighbourhood_key as neighbourhood
            FROM fact_listing_summary
            WHERE price IS NOT NULL AND price < 1000
            LIMIT 10000
        """)
        data['prices'] = df if not df.empty else pd.DataFrame()
    except:
        data['prices'] = pd.DataFrame()
    
    # Neighbourhood averages
    try:
        df = query_db(conn, """
            SELECT 
                neighbourhood_key as neighbourhood,
                AVG(price) as avg_price,
                COUNT(*) as listing_count,
                AVG(review_scores_rating) as avg_rating
            FROM fact_listing_summary
            WHERE neighbourhood_key IS NOT NULL AND price IS NOT NULL AND price < 1000
            GROUP BY neighbourhood_key
            HAVING COUNT(*) > 10
            ORDER BY avg_price DESC
            LIMIT 20
        """)
        data['neighbourhoods'] = df if not df.empty else pd.DataFrame()
    except:
        data['neighbourhoods'] = pd.DataFrame()
    
    # Rating distribution
    try:
        df = query_db(conn, """
            SELECT 
                review_scores_rating as rating
            FROM fact_listing_summary
            WHERE review_scores_rating IS NOT NULL
        """)
        data['ratings'] = df if not df.empty else pd.DataFrame()
    except:
        data['ratings'] = pd.DataFrame()
    
    # Room type distribution
    try:
        df = query_db(conn, """
            SELECT 
                room_type,
                COUNT(*) as count,
                AVG(price) as avg_price
            FROM fact_listing_summary
            WHERE room_type IS NOT NULL
            GROUP BY room_type
        """)
        data['room_types'] = df if not df.empty else pd.DataFrame()
    except:
        data['room_types'] = pd.DataFrame()
    
    conn.close()
    return data

def load_all_cities():
    """Load data for all cities."""
    cities = ['nyc', 'barcelona', 'edinburgh']
    city_names = {'nyc': 'NYC', 'barcelona': 'Barcelona', 'edinburgh': 'Edinburgh'}
    
    all_data = {}
    for city in cities:
        data = load_city_data(city)
        if data is not None and 'summary' in data and not data['summary'].empty:
            all_data[city_names[city]] = data
    
    return all_data

# Load data
print("Loading data...")
all_data = load_all_cities()

if not all_data:
    print("No data found!")
    exit()

# Figure 1: Price Distribution (NYC shown as example)
selected_city = 'NYC'
city_data = all_data[selected_city]

prices_df = city_data.get('prices')
if prices_df is not None and not prices_df.empty:
    fig = px.histogram(
        prices_df, 
        x='price', 
        nbins=50,
        title=f'{selected_city} - Price Distribution',
        labels={'price': 'Price ($)', 'count': 'Number of Listings'},
        color_discrete_sequence=['#FF5A5F']
    )
    fig.update_layout(height=400, showlegend=False)
    fig.write_image('reports/figures/dashboard_price_distribution.png')
    print("✅ Saved: dashboard_price_distribution.png")

# Figure 2: Room Type Distribution
room_types_df = city_data.get('room_types')
if room_types_df is not None and not room_types_df.empty:
    fig = px.pie(
        room_types_df,
        values='count',
        names='room_type',
        title=f'{selected_city} - Room Types',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    fig.update_layout(height=400)
    fig.write_image('reports/figures/dashboard_room_types.png')
    print("✅ Saved: dashboard_room_types.png")

# Figure 3: Price by Neighbourhood
neighbourhoods_df = city_data.get('neighbourhoods')
if neighbourhoods_df is not None and not neighbourhoods_df.empty:
    fig = px.bar(
        neighbourhoods_df,
        x='neighbourhood',
        y='avg_price',
        color='listing_count',
        title=f'{selected_city} - Average Price by Neighbourhood',
        labels={'avg_price': 'Average Price ($)', 'neighbourhood': 'Neighbourhood'},
        color_continuous_scale='Viridis'
    )
    fig.update_layout(height=400)
    fig.write_image('reports/figures/dashboard_neighbourhoods.png')
    print("✅ Saved: dashboard_neighbourhoods.png")

# Figure 4: Rating Distribution
ratings_df = city_data.get('ratings')
if ratings_df is not None and not ratings_df.empty:
    fig = px.histogram(
        ratings_df,
        x='rating',
        nbins=20,
        title=f'{selected_city} - Review Score Distribution',
        labels={'rating': 'Review Score', 'count': 'Number of Listings'},
        color_discrete_sequence=['#2ecc71']
    )
    fig.update_layout(height=400)
    fig.write_image('reports/figures/dashboard_ratings.png')
    print("✅ Saved: dashboard_ratings.png")

# Figure 5: Cross-City Radar
comparison_data = []
for city, data in all_data.items():
    if data and 'summary' in data and not data['summary'].empty:
        summary = data['summary'].iloc[0]
        comparison_data.append({
            'city': city,
            'avg_price': summary.get('avg_price', 0),
            'avg_occupancy': summary.get('avg_occupancy', 0) or 0,
            'avg_rating': summary.get('avg_rating', 0) or 0,
            'pct_superhost': summary.get('pct_superhost', 0) or 0
        })

if comparison_data:
    comp_df = pd.DataFrame(comparison_data)
    
    metrics = ['avg_price', 'avg_occupancy', 'avg_rating', 'pct_superhost']
    metric_labels = ['Avg Price', 'Occupancy', 'Rating', 'Superhost %']
    
    fig = go.Figure()
    
    for city in comp_df['city'].unique():
        city_data_row = comp_df[comp_df['city'] == city].iloc[0]
        normalized = []
        for m in metrics:
            max_val = comp_df[m].max()
            min_val = comp_df[m].min()
            if max_val > min_val:
                normalized.append((city_data_row[m] - min_val) / (max_val - min_val) * 100)
            else:
                normalized.append(50)
        
        fig.add_trace(go.Scatterpolar(
            r=normalized,
            theta=metric_labels,
            fill='toself',
            name=city,
            line=dict(width=2)
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title='Cross-City Market Comparison (Normalized)',
        height=500,
        showlegend=True
    )
    fig.write_image('reports/figures/dashboard_radar.png')
    print("✅ Saved: dashboard_radar.png")

print("\n✅ All dashboard figures saved to reports/figures/")
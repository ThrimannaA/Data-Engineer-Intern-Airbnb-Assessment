import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from pathlib import Path
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Page config
st.set_page_config(
    page_title="Airbnb Market Intelligence",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #FF5A5F;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #484848;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 600;
        color: #FF5A5F;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #767676;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">🏠 Airbnb Market Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Cross-City Comparison: NYC · Barcelona · Edinburgh</div>', unsafe_allow_html=True)

# Helper functions
def get_db_path(city):
    """Get database path for a city."""
    # Try multiple possible paths
    possible_paths = [
        f'data/processed/{city}/{city}.db',
        f'../data/processed/{city}/{city}.db',
        f'./data/processed/{city}/{city}.db'
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            return path
    return None

def get_connection(city):
    """Get SQLite connection."""
    db_path = get_db_path(city)
    if db_path is None:
        return None
    try:
        return sqlite3.connect(db_path)
    except Exception as e:
        st.warning(f"Could not connect to {city}: {e}")
        return None

def query_db(conn, query):
    """Run query and return DataFrame."""
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        # Don't show warning for every query failure
        return pd.DataFrame()

def get_median(conn, column, table, condition=""):
    """Get median value using SQLite."""
    try:
        query = f"""
            SELECT {column} as value
            FROM {table}
            WHERE {column} IS NOT NULL {condition}
            ORDER BY {column}
        """
        df = pd.read_sql_query(query, conn)
        if len(df) > 0:
            return df['value'].median()
        return None
    except:
        return None

def is_dataframe_empty(df):
    """Check if a DataFrame is empty or None."""
    if df is None:
        return True
    if isinstance(df, bool):
        return True
    if not isinstance(df, pd.DataFrame):
        return True
    return df.empty

# Cache data loading
@st.cache_data(ttl=3600)
def load_city_data(city):
    """Load all data for a city."""
    conn = get_connection(city)
    if conn is None:
        return None
    
    data = {}
    
    # Summary stats - SQLite compatible
    try:
        df = query_db(conn, """
            SELECT 
                COUNT(*) as total_listings,
                AVG(price) as avg_price,
                AVG(estimated_occupancy_rate) as avg_occupancy,
                AVG(review_scores_rating) as avg_rating,
                SUM(CASE WHEN host_is_superhost IN ('t', 'true', '1') OR host_is_superhost = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as pct_superhost
            FROM fact_listing_summary
            WHERE (price IS NULL OR price < 1000)
        """)
        
        # Calculate median separately
        median_price = get_median(conn, 'price', 'fact_listing_summary', 'AND price < 1000')
        
        if not df.empty:
            data['summary'] = df
            if median_price is not None:
                data['summary']['median_price'] = median_price
            else:
                data['summary']['median_price'] = df['avg_price'].iloc[0]
        else:
            data['summary'] = pd.DataFrame()
    except Exception as e:
        data['summary'] = pd.DataFrame()
    
    # Price distribution
    try:
        df = query_db(conn, """
            SELECT 
                price,
                room_type,
                neighbourhood_key as neighbourhood,
                estimated_occupancy_rate
            FROM fact_listing_summary
            WHERE (price IS NULL OR price < 1000)
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
            WHERE neighbourhood_key IS NOT NULL AND (price IS NULL OR price < 1000)
            GROUP BY neighbourhood_key
            HAVING COUNT(*) > 10
            ORDER BY CASE WHEN AVG(price) IS NOT NULL THEN AVG(price) ELSE COUNT(*) END DESC
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
        if data is not None:
            # Check if summary exists and has data
            if 'summary' in data and data['summary'] is not None and isinstance(data['summary'], pd.DataFrame) and not data['summary'].empty:
                all_data[city_names[city]] = data
    
    return all_data

# Load all data
with st.spinner("Loading data..."):
    all_data = load_all_cities()

if not all_data:
    st.error("⚠️ No data found. Please run the pipeline first.")
    st.code("""
    # Run the pipeline:
    python src/pipeline/run_pipeline.py --cities all
    """)
    st.stop()

# Sidebar
st.sidebar.markdown("## 🎯 Controls")
selected_city = st.sidebar.selectbox(
    "Select City",
    list(all_data.keys())
)

# Show data availability
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Data Availability")
for city, data in all_data.items():
    if data and 'summary' in data and data['summary'] is not None and isinstance(data['summary'], pd.DataFrame) and not data['summary'].empty:
        total = data['summary'].iloc[0]['total_listings']
        st.sidebar.markdown(f"✅ {city}: {total:,.0f} listings")
    else:
        st.sidebar.markdown(f"❌ {city}: No data")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📝 About")
st.sidebar.markdown("""
Data sourced from Inside Airbnb.  
Dashboard for Expernetic Assessment.
""")

# Main content
city_data = all_data[selected_city]

# Check if summary exists
if 'summary' not in city_data or city_data['summary'] is None or city_data['summary'].empty:
    st.warning(f"No data available for {selected_city}")
    st.stop()

# Summary metrics
summary = city_data['summary'].iloc[0]

st.markdown("## 📊 Market Overview")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total = summary.get('total_listings', 0)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{total:,.0f}</div>
        <div class="metric-label">Total Listings</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    avg_price = summary.get('avg_price')
    price_val = "N/A" if pd.isna(avg_price) or avg_price is None else f"${avg_price:.0f}"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{price_val}</div>
        <div class="metric-label">Average Price</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    median_price = summary.get('median_price')
    median_val = "N/A" if pd.isna(median_price) or median_price is None else f"${median_price:.0f}"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{median_val}</div>
        <div class="metric-label">Median Price</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    occ = summary.get('avg_occupancy', 0)
    if pd.isna(occ):
        occ = 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{occ:.1f}%</div>
        <div class="metric-label">Avg Occupancy</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    rating = summary.get('avg_rating', 0)
    if pd.isna(rating):
        rating = 0
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{rating:.2f}</div>
        <div class="metric-label">Avg Rating</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Charts Section
st.markdown("## 📈 Visualizations")

# Row 1: Price Distribution + Room Types
col1, col2 = st.columns(2)

with col1:
    st.subheader("Price Distribution")
    prices_df = city_data.get('prices')
    if prices_df is not None and isinstance(prices_df, pd.DataFrame) and not prices_df.empty:
        has_prices = prices_df['price'].notna().any()
        if has_prices:
            fig = px.histogram(
                prices_df, 
                x='price', 
                nbins=50,
                title=f'{selected_city} - Price Distribution',
                labels={'price': 'Price ($)', 'count': 'Number of Listings'},
                color_discrete_sequence=['#FF5A5F']
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        elif 'estimated_occupancy_rate' in prices_df.columns and prices_df['estimated_occupancy_rate'].notna().any():
            fig = px.histogram(
                prices_df, 
                x='estimated_occupancy_rate', 
                nbins=20,
                title=f'{selected_city} - Estimated Occupancy Rate Distribution (Price unavailable)',
                labels={'estimated_occupancy_rate': 'Occupancy Rate (%)', 'count': 'Number of Listings'},
                color_discrete_sequence=['#FF5A5F']
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No price or occupancy data available")
    else:
        st.info("No price data available")

with col2:
    st.subheader("Room Type Distribution")
    room_types_df = city_data.get('room_types')
    if room_types_df is not None and isinstance(room_types_df, pd.DataFrame) and not room_types_df.empty:
        fig = px.pie(
            room_types_df,
            values='count',
            names='room_type',
            title=f'{selected_city} - Room Types',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No room type data available")

# Row 2: Price by Neighbourhood
st.subheader("Price by Neighbourhood")
neighbourhoods_df = city_data.get('neighbourhoods')
if neighbourhoods_df is not None and isinstance(neighbourhoods_df, pd.DataFrame) and not neighbourhoods_df.empty:
    has_prices = neighbourhoods_df['avg_price'].notna().any()
    if has_prices:
        fig = px.bar(
            neighbourhoods_df,
            x='neighbourhood',
            y='avg_price',
            color='listing_count',
            title=f'{selected_city} - Average Price by Neighbourhood',
            labels={'avg_price': 'Average Price ($)', 'neighbourhood': 'Neighbourhood'},
            color_continuous_scale='Viridis'
        )
    else:
        # Fallback to Listing Count by Neighbourhood if no prices are available
        # Sort by listing count descending
        neighbourhoods_df_sorted = neighbourhoods_df.sort_values(by='listing_count', ascending=False).head(20)
        fig = px.bar(
            neighbourhoods_df_sorted,
            x='neighbourhood',
            y='listing_count',
            color='avg_rating',
            title=f'{selected_city} - Listing Count by Neighbourhood (Price data unavailable)',
            labels={'listing_count': 'Number of Listings', 'neighbourhood': 'Neighbourhood', 'avg_rating': 'Avg Rating'},
            color_continuous_scale='Plasma'
        )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No neighbourhood data available")

# Row 3: Rating Distribution
st.subheader("Rating Distribution")
ratings_df = city_data.get('ratings')
if ratings_df is not None and isinstance(ratings_df, pd.DataFrame) and not ratings_df.empty:
    fig = px.histogram(
        ratings_df,
        x='rating',
        nbins=20,
        title=f'{selected_city} - Review Score Distribution',
        labels={'rating': 'Review Score', 'count': 'Number of Listings'},
        color_discrete_sequence=['#2ecc71']
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No rating data available")

# Cross-city comparison
st.markdown("---")
st.markdown("## 🌍 Cross-City Comparison")

# Prepare comparison data
comparison_data = []
for city, data in all_data.items():
    if data and 'summary' in data and data['summary'] is not None and isinstance(data['summary'], pd.DataFrame) and not data['summary'].empty:
        summary = data['summary'].iloc[0]
        avg_price = summary.get('avg_price')
        avg_price_val = 0.0 if pd.isna(avg_price) or avg_price is None else float(avg_price)
        
        median_price = summary.get('median_price')
        median_price_val = avg_price_val if pd.isna(median_price) or median_price is None else float(median_price)
        
        comparison_data.append({
            'city': city,
            'total_listings': int(summary.get('total_listings', 0)),
            'avg_price': avg_price_val,
            'median_price': median_price_val,
            'avg_occupancy': summary.get('avg_occupancy', 0) if not pd.isna(summary.get('avg_occupancy', 0)) else 0.0,
            'avg_rating': summary.get('avg_rating', 0) if not pd.isna(summary.get('avg_rating', 0)) else 0.0,
            'pct_superhost': summary.get('pct_superhost', 0) if not pd.isna(summary.get('pct_superhost', 0)) else 0.0
        })

if comparison_data:
    comp_df = pd.DataFrame(comparison_data)
    
    # Radar chart
    metrics = ['avg_price', 'median_price', 'avg_occupancy', 'avg_rating', 'pct_superhost']
    metric_labels = ['Avg Price', 'Median Price', 'Occupancy', 'Rating', 'Superhost %']
    
    fig = go.Figure()
    
    for city in comp_df['city'].unique():
        city_data_row = comp_df[comp_df['city'] == city].iloc[0]
        
        # Normalize values
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
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=10)
            )
        ),
        title='Cross-City Market Comparison (Normalized)',
        height=500,
        showlegend=True,
        legend=dict(
            x=1.1,
            y=0.5
        )
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Bar chart comparison
    st.subheader("Key Metrics Comparison")
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Average Price', 'Average Rating', 'Occupancy Rate', 'Superhost %')
    )
    
    metrics_config = [
        ('avg_price', 'Average Price ($)', 1, 1),
        ('avg_rating', 'Average Rating', 1, 2),
        ('avg_occupancy', 'Occupancy Rate (%)', 2, 1),
        ('pct_superhost', 'Superhost (%)', 2, 2)
    ]
    
    for metric, title, row, col in metrics_config:
        if metric in comp_df.columns:
            fig.add_trace(
                go.Bar(
                    x=comp_df['city'],
                    y=comp_df[metric],
                    name=title,
                    marker_color=['#FF5A5F', '#00A699', '#FC642D']
                ),
                row=row, col=col
            )
            fig.update_yaxes(title_text=title, row=row, col=col)
    
    fig.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No comparison data available")


# Debug info (only in development)
if st.sidebar.checkbox("Show Debug Info"):
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🐛 Debug Info")
    st.sidebar.write("Data keys:", list(all_data.keys()))
    for city, data in all_data.items():
        if data:
            st.sidebar.write(f"{city}: {list(data.keys()) if data else 'Empty'}")
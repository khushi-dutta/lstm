import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import sqlite3
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import os
import time
import warnings
warnings.filterwarnings('ignore')

# Try to import the flood prediction system
try:
    from flood_prediction_lstm import FloodPredictionSystem
    from real_time_alert_system import FloodAlertSystem
except ImportError:
    st.error("Required modules not found. Please ensure all files are present.")
    st.stop()

# Configure Streamlit page
st.set_page_config(
    page_title="🌊 Kerala Flood Prediction System",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling with slower animations
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        animation: fadeIn 2s ease-in;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
        transition: all 0.8s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .alert-high {
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        animation: slideInRight 1.5s ease-out;
    }
    .alert-medium {
        background-color: #fff3e0;
        border-left: 5px solid #ff9800;
        animation: slideInRight 1.8s ease-out;
    }
    .alert-low {
        background-color: #f3e5f5;
        border-left: 5px solid #9c27b0;
        animation: slideInRight 2.1s ease-out;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    /* Slow fade-in animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Slow slide-in animation */
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(100px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    /* Smooth transitions for all elements - will be updated by JavaScript */
    * {
        transition: all 0.6s ease-in-out !important;
    }
    
    /* Slower chart animations */
    .js-plotly-plot .plotly .svg-container {
        animation: chartFadeIn 2.5s ease-in-out;
    }
    
    @keyframes chartFadeIn {
        from { opacity: 0; transform: scale(0.95); }
        to { opacity: 1; transform: scale(1); }
    }
    
    /* Slower data loading indicator */
    .stSpinner > div {
        animation-duration: 2s !important;
    }
    
    /* Map stability - prevent excessive re-renders */
    .folium-map {
        pointer-events: auto !important;
        position: relative !important;
    }
    
    /* Stable hover effects for map markers */
    .leaflet-marker-icon {
        transition: none !important;
    }
    
    /* Prevent map container from triggering refreshes */
    iframe[src*="folium"] {
        pointer-events: auto;
        position: relative;
    }
    
    /* Reduce map update frequency */
    .leaflet-container {
        outline: none;
    }
</style>
""", unsafe_allow_html=True)

class FloodDashboardApp:
    def __init__(self):
        """Initialize the dashboard app"""
        self.init_session_state()
        
    def init_session_state(self):
        """Initialize session state variables"""
        if 'model_loaded' not in st.session_state:
            st.session_state.model_loaded = False
        if 'fps' not in st.session_state:
            st.session_state.fps = None
        if 'alert_system' not in st.session_state:
            st.session_state.alert_system = None
        if 'map_stable' not in st.session_state:
            st.session_state.map_stable = True
        if 'last_map_data' not in st.session_state:
            st.session_state.last_map_data = None
            
    def load_model(self):
        """Load the flood prediction model"""
        if not st.session_state.model_loaded:
            try:
                with st.spinner("Loading flood prediction model..."):
                    st.session_state.fps = FloodPredictionSystem()
                    st.session_state.alert_system = FloodAlertSystem()
                    
                    # Check if model files exist
                    model_files = [
                        'flood_lstm_model.keras',
                        'flood_lstm_model_scalers.pkl',
                        'flood_lstm_model_label_encoder.pkl',
                        'kerala_flood_data.csv'
                    ]
                    
                    missing_files = []
                    for file in model_files:
                        if not os.path.exists(file):
                            missing_files.append(file)
                    
                    if missing_files:
                        st.error(f"Missing required files: {', '.join(missing_files)}")
                        st.info("Please ensure all model files are present in the application directory.")
                        return False
                    
                    # Load model and data
                    st.session_state.fps.load_model()
                    st.session_state.fps.load_and_preprocess_data()
                    st.session_state.model_loaded = True
                    st.success("Model loaded successfully!")
                    return True
                    
            except Exception as e:
                st.error(f"Error loading model: {str(e)}")
                st.info("Running in demo mode with sample data.")
                return False
        return True

    def get_demo_data(self, show_progress=False):
        """Generate demo data for when model files are not available"""
        districts = ['Thiruvananthapuram', 'Kollam', 'Pathanamthitta', 'Alappuzha', 
                    'Kottayam', 'Idukki', 'Ernakulam', 'Thrissur', 'Palakkad', 
                    'Malappuram', 'Kozhikode', 'Wayanad', 'Kannur', 'Kasaragod']
        
        data = []
        
        if show_progress:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        for i, district in enumerate(districts):
            try:
                if show_progress:
                    progress = (i + 1) / len(districts)
                    progress_bar.progress(progress)
                    status_text.text(f'Loading data for {district}... ({i+1}/{len(districts)})')
                    import time
                    # Use configurable animation speed for data loading
                    delay = st.session_state.get('animation_speed', 1.5) * 0.15
                    time.sleep(delay)  # Configurable data generation speed
                
                # Add some variation to make data more realistic over time
                base_time = datetime.now()
                time_variation = np.random.uniform(-2, 2)  # hours variation
                
                risk_score = float(np.random.uniform(0.1, 0.9))
                alert_level = 'Red' if risk_score > 0.7 else 'Orange' if risk_score > 0.5 else 'Yellow'
                
                data.append({
                    'district': str(district),
                    'risk_score': risk_score,
                    'alert_level': str(alert_level),
                    'rainfall_mm': float(np.random.uniform(0, 150)),
                    'water_level_m': float(np.random.uniform(0, 8)),
                    'temperature_c': float(np.random.uniform(22, 35)),
                    'humidity_percent': float(np.random.uniform(60, 95)),
                    'last_updated': base_time + timedelta(hours=time_variation)
                })
            except Exception as e:
                # Add fallback data if there's an error
                data.append({
                    'district': str(district),
                    'risk_score': 0.5,
                    'alert_level': 'Yellow',
                    'rainfall_mm': 50.0,
                    'water_level_m': 2.0,
                    'temperature_c': 28.0,
                    'humidity_percent': 75.0,
                    'last_updated': datetime.now()
                })
        
        if show_progress:
            progress_bar.empty()
            status_text.empty()
            st.success("✅ Data loaded successfully!")
            import time
            time.sleep(1)  # Show success message briefly
        
        return pd.DataFrame(data)

    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">🌊 Kerala Flood Prediction System</h1>', 
                   unsafe_allow_html=True)
        st.markdown("---")

    def render_sidebar(self):
        """Render the sidebar with controls"""
        st.sidebar.title("🎛️ Dashboard Controls")
        
        # Auto-refresh settings
        st.sidebar.markdown("### ⏱️ Auto-Refresh Settings")
        auto_refresh = st.sidebar.checkbox("🔄 Enable Auto-Refresh", value=False)
        
        if auto_refresh:
            refresh_interval = st.sidebar.selectbox(
                "⏱️ Refresh Interval",
                [10, 15, 30, 60, 120],
                index=1,  # Default to 15 seconds
                format_func=lambda x: f"{x} seconds" if x < 60 else f"{x//60} minute{'s' if x//60 > 1 else ''}"
            )
            
            # Auto-refresh logic with map interaction check
            import time
            if 'last_refresh' not in st.session_state:
                st.session_state.last_refresh = time.time()
            
            current_time = time.time()
            time_since_refresh = current_time - st.session_state.last_refresh
            
            # Only auto-refresh if not interacting with map and enough time has passed
            should_refresh = (
                time_since_refresh > refresh_interval and 
                st.session_state.get('map_stable', True)
            )
            
            if should_refresh:
                st.session_state.last_refresh = current_time
                st.rerun()
            
            # Show countdown
            time_left = max(0, refresh_interval - int(time_since_refresh))
            if time_left > 0:
                st.sidebar.info(f"⏲️ Next refresh in: {time_left}s")
            else:
                st.sidebar.info("⏲️ Ready to refresh...")
        
        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Now", type="primary"):
            if 'last_refresh' in st.session_state:
                st.session_state.last_refresh = time.time()
            st.session_state.force_refresh = True
            # Clear map cache to force map update
            if 'current_map_key' in st.session_state:
                del st.session_state.current_map_key
            if 'folium_map' in st.session_state:
                del st.session_state.folium_map
            st.rerun()
            
        # Pause auto-refresh option
        pause_refresh = st.sidebar.checkbox("⏸️ Pause Auto-Refresh", value=False, 
                                          help="Temporarily pause automatic updates")
        if pause_refresh:
            st.sidebar.info("🔒 Auto-refresh paused")
            auto_refresh = False
        
        st.sidebar.markdown("---")
        
        # District selection
        districts = ['All Districts', 'Thiruvananthapuram', 'Kollam', 'Pathanamthitta', 
                    'Alappuzha', 'Kottayam', 'Idukki', 'Ernakulam', 'Thrissur', 
                    'Palakkad', 'Malappuram', 'Kozhikode', 'Wayanad', 'Kannur', 'Kasaragod']
        
        selected_district = st.sidebar.selectbox("📍 Select District", districts)
        
        # Time range selection
        time_range = st.sidebar.selectbox(
            "📅 Time Range",
            ["Last 24 Hours", "Last 7 Days", "Last 30 Days"]
        )
        
        # Alert level filter
        alert_levels = st.sidebar.multiselect(
            "🚨 Alert Levels",
            ["Red", "Orange", "Yellow"],
            default=["Red", "Orange", "Yellow"]
        )
        
        st.sidebar.markdown("---")
        
        # Animation speed settings
        st.sidebar.markdown("### ⚡ Animation Settings")
        animation_speed = st.sidebar.select_slider(
            "🎬 Animation Speed",
            options=["Very Slow", "Slow", "Normal", "Fast"],
            value="Slow",
            help="Controls how fast charts and data updates appear"
        )
        
        # Store animation speed in session state
        speed_map = {
            "Very Slow": 3.0,
            "Slow": 1.5,
            "Normal": 0.8,
            "Fast": 0.3
        }
        st.session_state.animation_speed = speed_map[animation_speed]
        
        st.sidebar.markdown("---")
        
        # System info
        st.sidebar.markdown("### 📊 System Status")
        st.sidebar.success("✅ Model: Active")
        st.sidebar.info(f"🕒 Last Update: {datetime.now().strftime('%H:%M:%S')}")
        
        if auto_refresh and 'last_refresh' in st.session_state:
            time_since_refresh = int(time.time() - st.session_state.last_refresh)
            st.sidebar.metric("⏱️ Time Since Refresh", f"{time_since_refresh}s")
        
        return selected_district, time_range, alert_levels, auto_refresh

    def render_overview_metrics(self, data):
        """Render overview metrics"""
        st.subheader("📊 Current Flood Risk Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            high_risk = len(data[data['alert_level'] == 'Red'])
            st.metric(
                label="🔴 High Risk Districts",
                value=high_risk,
                delta=f"{high_risk}/14 districts"
            )
        
        with col2:
            medium_risk = len(data[data['alert_level'] == 'Orange'])
            st.metric(
                label="🟠 Medium Risk Districts",
                value=medium_risk,
                delta=f"{medium_risk}/14 districts"
            )
        
        with col3:
            avg_risk = data['risk_score'].mean()
            st.metric(
                label="📈 Average Risk Score",
                value=f"{avg_risk:.2f}",
                delta=f"{'↑' if avg_risk > 0.5 else '↓'} {abs(avg_risk - 0.5):.2f}"
            )
        
        with col4:
            max_rainfall = data['rainfall_mm'].max()
            st.metric(
                label="🌧️ Max Rainfall (24h)",
                value=f"{max_rainfall:.1f} mm",
                delta="Last 24 hours"
            )

    @st.cache_data
    def create_map_data(_self, data_hash):
        """Create map data with caching to prevent frequent refreshes"""
        # Kerala coordinates (approximate center)
        kerala_center = [10.8505, 76.2711]
        
        # Create base map with stable settings
        m = folium.Map(
            location=kerala_center,
            zoom_start=7,
            tiles='OpenStreetMap',
            prefer_canvas=True  # Better performance
        )
        return m, kerala_center

    def render_map(self, data):
        """Render the flood risk map with hover-stable rendering"""
        st.subheader("🗺️ Kerala Flood Risk Map")
        
        # Create a stable hash of the essential data for caching
        essential_data = data[['district', 'risk_score', 'alert_level']].round(2)  # Round to reduce micro-changes
        data_string = essential_data.to_string()
        data_hash = abs(hash(data_string)) % 10000  # Stable, shorter hash
        
        # Check if map data has actually changed
        current_map_key = f"map_{data_hash}"
        
        # Only regenerate map if data actually changed
        if 'current_map_key' not in st.session_state or st.session_state.current_map_key != current_map_key:
            # Use cached map creation
            m, kerala_center = self.create_map_data(data_hash)
            
            # District coordinates (approximate)
            district_coords = {
                'Thiruvananthapuram': [8.5241, 76.9366],
                'Kollam': [8.8932, 76.6141],
                'Pathanamthitta': [9.2648, 76.7870],
                'Alappuzha': [9.4981, 76.3388],
                'Kottayam': [9.5916, 76.5222],
                'Idukki': [9.8901, 76.9525],
                'Ernakulam': [9.9312, 76.2673],
                'Thrissur': [10.5276, 76.2144],
                'Palakkad': [10.7867, 76.6548],
                'Malappuram': [11.0480, 76.0710],
                'Kozhikode': [11.2588, 75.7804],
                'Wayanad': [11.6854, 76.1320],
                'Kannur': [11.8745, 75.3704],
                'Kasaragod': [12.4996, 74.9869]
            }
            
            # Add markers for each district
            for _, row in data.iterrows():
                district = row['district']
                if district in district_coords:
                    coords = district_coords[district]
                    
                    # Color based on alert level
                    color = {'Red': 'red', 'Orange': 'orange', 'Yellow': 'yellow'}.get(
                        row['alert_level'], 'blue'
                    )
                    
                    folium.CircleMarker(
                        location=coords,
                        radius=10 + (row['risk_score'] * 20),
                        popup=f"""
                        <div style="font-family: Arial, sans-serif;">
                        <b>{district}</b><br>
                        <hr style="margin: 5px 0;">
                        Risk Score: {row['risk_score']:.2f}<br>
                        Alert Level: <span style="color: {color}; font-weight: bold;">{row['alert_level']}</span><br>
                        Rainfall: {row['rainfall_mm']:.1f} mm<br>
                        Water Level: {row['water_level_m']:.1f} m
                        </div>
                        """,
                        color='black',
                        weight=2,
                        fillColor=color,
                        fillOpacity=0.7
                    ).add_to(m)
            
            # Store the map and key in session state
            st.session_state.folium_map = m
            st.session_state.current_map_key = current_map_key
        else:
            # Use cached map
            m = st.session_state.folium_map
        
        # Display map with very stable settings to prevent hover refreshes
        map_container = st.container()
        
        with map_container:
            # Use a consistent key that doesn't change on hover
            stable_map_key = f"kerala_flood_map_stable"
            
            # Configure st_folium with minimal return data to prevent refreshes
            map_data = st_folium(
                m, 
                width=700, 
                height=500,
                key=stable_map_key,
                returned_objects=[],  # Don't return any objects to prevent refreshes
                use_container_width=True,
                # Additional stability settings
                feature_group_to_add=None,
                zoom=None  # Don't track zoom changes
            )
            
            # Add map interaction info
            st.caption("💡 Click on district markers to view detailed information. Map updates only when data changes significantly.")

    def render_charts(self, data):
        """Render various charts and visualizations with slower animations"""
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Risk Score Distribution")
                try:
                    fig_bar = px.bar(
                        data.sort_values('risk_score', ascending=False),
                        x='district',
                        y='risk_score',
                        color='alert_level',
                        color_discrete_map={'Red': '#ff4444', 'Orange': '#ff8800', 'Yellow': '#ffdd00'},
                        title="District-wise Flood Risk Scores"
                    )
                    # Add configurable animation speed
                    animation_duration = int(st.session_state.get('animation_speed', 1.5) * 1000)
                    fig_bar.update_layout(
                        xaxis_tickangle=45,
                        transition_duration=animation_duration,
                        transition_easing="cubic-in-out"
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating bar chart: {str(e)}")
                    st.info("Chart data preview:")
                    st.dataframe(data[['district', 'risk_score', 'alert_level']].head())
        
            with col2:
                st.subheader("🌧️ Weather Conditions")
                try:
                    fig_scatter = px.scatter(
                        data,
                        x='rainfall_mm',
                        y='water_level_m',
                        size='risk_score',
                        color='alert_level',
                        hover_data=['district'],
                        color_discrete_map={'Red': '#ff4444', 'Orange': '#ff8800', 'Yellow': '#ffdd00'},
                        title="Rainfall vs Water Level"
                    )
                    animation_duration = int(st.session_state.get('animation_speed', 1.5) * 1000)
                    fig_scatter.update_layout(
                        transition_duration=animation_duration,
                        transition_easing="cubic-in-out"
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating scatter plot: {str(e)}")
                    st.info("Weather data preview:")
                    st.dataframe(data[['district', 'rainfall_mm', 'water_level_m']].head())
        
            # Add a configurable delay between chart renders for smoother experience
            delay = st.session_state.get('animation_speed', 1.5) * 0.2
            time.sleep(delay)
            
            # Additional charts
            col3, col4 = st.columns(2)
            
            with col3:
                st.subheader("🌡️ Temperature & Humidity")
                try:
                    fig_temp = px.scatter(
                        data,
                        x='temperature_c',
                        y='humidity_percent',
                        color='alert_level',
                        size='risk_score',
                        hover_data=['district'],
                        color_discrete_map={'Red': '#ff4444', 'Orange': '#ff8800', 'Yellow': '#ffdd00'},
                        title="Temperature vs Humidity"
                    )
                    animation_duration = int(st.session_state.get('animation_speed', 1.5) * 1000)
                    fig_temp.update_layout(
                        transition_duration=animation_duration,
                        transition_easing="cubic-in-out"
                    )
                    st.plotly_chart(fig_temp, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating temperature chart: {str(e)}")
                    st.info("Temperature data preview:")
                    st.dataframe(data[['district', 'temperature_c', 'humidity_percent']].head())
            
            with col4:
                st.subheader("📈 Alert Level Distribution")
                try:
                    alert_counts = data['alert_level'].value_counts()
                    fig_pie = px.pie(
                        values=alert_counts.values,
                        names=alert_counts.index,
                        color_discrete_map={'Red': '#ff4444', 'Orange': '#ff8800', 'Yellow': '#ffdd00'},
                        title="Alert Level Distribution"
                    )
                    animation_duration = int(st.session_state.get('animation_speed', 1.5) * 1000)
                    fig_pie.update_layout(
                        transition_duration=animation_duration,
                        transition_easing="cubic-in-out"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                except Exception as e:
                    st.error(f"Error creating pie chart: {str(e)}")
                    st.info("Alert level data preview:")
                    st.dataframe(data['alert_level'].value_counts())
        
        except Exception as e:
            st.error(f"Error rendering charts: {str(e)}")
            st.info("Displaying raw data instead:")
            st.dataframe(data)

    def render_data_table(self, data):
        """Render detailed data table"""
        st.subheader("📋 Detailed District Data")
        
        # Format the data for display
        display_data = data.copy()
        display_data['risk_score'] = display_data['risk_score'].round(3)
        display_data['rainfall_mm'] = display_data['rainfall_mm'].round(1)
        display_data['water_level_m'] = display_data['water_level_m'].round(2)
        display_data['temperature_c'] = display_data['temperature_c'].round(1)
        display_data['humidity_percent'] = display_data['humidity_percent'].round(1)
        
        # Style the dataframe
        def color_alert_level(val):
            color_map = {'Red': 'color: white; background-color: #ff4444',
                        'Orange': 'color: white; background-color: #ff8800',
                        'Yellow': 'color: black; background-color: #ffdd00'}
            return color_map.get(val, '')
        
        styled_df = display_data.style.applymap(color_alert_level, subset=['alert_level'])
        st.dataframe(styled_df, use_container_width=True)

    def render_alerts_section(self):
        """Render recent alerts section"""
        st.subheader("🚨 Recent Alerts")
        
        # Sample recent alerts (in a real app, this would come from the database)
        recent_alerts = [
            {"time": "2 hours ago", "district": "Idukki", "level": "Red", 
             "message": "Heavy rainfall detected. Immediate evacuation recommended."},
            {"time": "4 hours ago", "district": "Wayanad", "level": "Orange", 
             "message": "Rising water levels. Monitor situation closely."},
            {"time": "6 hours ago", "district": "Kozhikode", "level": "Yellow", 
             "message": "Moderate rainfall expected. Stay alert."}
        ]
        
        for alert in recent_alerts:
            alert_class = f"alert-{'high' if alert['level'] == 'Red' else 'medium' if alert['level'] == 'Orange' else 'low'}"
            st.markdown(f"""
            <div class="metric-card {alert_class}">
                <strong>🚨 {alert['level']} Alert - {alert['district']}</strong><br>
                <small>{alert['time']}</small><br>
                {alert['message']}
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

    def run(self):
        """Main application runner"""
        self.render_header()
        
        # Load model
        model_loaded = self.load_model()
        
        # Render sidebar
        selected_district, time_range, alert_levels, auto_refresh = self.render_sidebar()
        
        # Get data (real or demo) with stability check
        show_loading = auto_refresh or st.session_state.get('force_refresh', False)
        
        # Check if we should use cached data to prevent unnecessary refreshes
        use_cached_data = (
            st.session_state.get('last_map_data') is not None and
            not show_loading and
            not st.session_state.get('force_refresh', False) and
            not auto_refresh  # Don't use cached data if auto-refresh is enabled
        )
        
        if use_cached_data:
            data = st.session_state.last_map_data
        else:
            if model_loaded and st.session_state.fps:
                try:
                    # In a real implementation, you would get predictions here
                    data = self.get_demo_data(show_progress=show_loading)  # Using demo data for now
                except Exception as e:
                    st.warning(f"Using demo data due to error: {str(e)}")
                    data = self.get_demo_data(show_progress=show_loading)
            else:
                data = self.get_demo_data(show_progress=show_loading)
            
            # Cache the data for map stability
            st.session_state.last_map_data = data.copy()
        
        # Reset force refresh flag
        if 'force_refresh' in st.session_state:
            st.session_state.force_refresh = False
        
        # Filter data based on sidebar selections
        if selected_district != 'All Districts':
            data = data[data['district'] == selected_district]
        
        data = data[data['alert_level'].isin(alert_levels)]
        
        # Render main content
        try:
            if not data.empty:
                self.render_overview_metrics(data)
                st.markdown("---")
                
                # Two columns layout
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    try:
                        self.render_map(data)
                    except Exception as e:
                        st.error(f"Error rendering map: {str(e)}")
                        st.info("Map rendering failed, but dashboard continues...")
                    
                    try:
                        self.render_charts(data)
                    except Exception as e:
                        st.error(f"Error rendering charts: {str(e)}")
                        st.info("Chart rendering failed, showing data table instead...")
                    
                    try:
                        self.render_data_table(data)
                    except Exception as e:
                        st.error(f"Error rendering data table: {str(e)}")
                        st.dataframe(data)
                
                with col2:
                    try:
                        self.render_alerts_section()
                    except Exception as e:
                        st.error(f"Error rendering alerts: {str(e)}")
                        st.info("Alerts section temporarily unavailable")
            else:
                st.warning("No data available for the selected filters.")
        
        except Exception as e:
            st.error(f"Critical error in main content rendering: {str(e)}")
            st.info("Attempting to display basic information...")
            if 'data' in locals() and not data.empty:
                st.dataframe(data)
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666;'>
            🌊 Kerala Flood Prediction System | Built with Streamlit<br>
            For emergency assistance, call: 1077 (Kerala State Disaster Management Authority)
        </div>
        """, unsafe_allow_html=True)

# Main application entry point
if __name__ == "__main__":
    app = FloodDashboardApp()
    app.run()
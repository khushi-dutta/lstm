import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import sqlite3
from datetime import datetime, timedelta
from flood_prediction_lstm import FloodPredictionSystem
from real_time_alert_system import FloodAlertSystem
import folium
from streamlit_folium import st_folium

# Configure Streamlit page
st.set_page_config(
    page_title="Kerala Flood Prediction Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

class FloodDashboard:
    def __init__(self):
        self.fps = FloodPredictionSystem()
        self.alert_system = FloodAlertSystem()
        self.load_model()
    
    @st.cache_resource
    def load_model(_self):
        """Load the trained model with caching"""
        try:
            _self.fps.load_model()
            _self.fps.load_and_preprocess_data()
            return True
        except:
            return False
    
    def get_alert_data(self):
        """Get recent alerts from database"""
        try:
            conn = sqlite3.connect(self.alert_system.db_path)
            alerts_df = pd.read_sql_query('''
                SELECT * FROM alerts 
                WHERE timestamp > datetime('now', '-7 days')
                ORDER BY timestamp DESC
            ''', conn)
            conn.close()
            return alerts_df
        except:
            return pd.DataFrame()
    
    def create_prediction_map(self, predictions_data):
        """Create an interactive map with predictions"""
        kerala_center = [10.8505, 76.2711]
        m = folium.Map(location=kerala_center, zoom_start=7)
        
        colors = {'Yellow': 'yellow', 'Orange': 'orange', 'Red': 'red'}
        
        for _, row in predictions_data.iterrows():
            color = colors.get(row['predicted_alert'], 'blue')
            
            popup_html = f"""
            <b>{row['district']}</b><br>
            Predicted Alert: <b style="color:{color}">{row['predicted_alert']}</b><br>
            Confidence: {row['confidence']:.1%}<br>
            Day: {row['day']}<br>
            """
            
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color=color, icon='exclamation-triangle', prefix='fa'),
                tooltip=f"{row['district']} - {row['predicted_alert']}"
            ).add_to(m)
        
        return m
    
    def run_dashboard(self):
        """Main dashboard function"""
        
        # Title and header
        st.title("🌊 Kerala Flood Prediction Dashboard")
        st.markdown("Real-time flood risk assessment using LSTM neural networks")
        
        # Sidebar
        st.sidebar.header("🔧 Control Panel")
        
        # Model status
        model_loaded = self.load_model()
        if model_loaded:
            st.sidebar.success("✅ Model Loaded")
        else:
            st.sidebar.error("❌ Model Not Available")
            st.error("Please train the model first by running flood_prediction_lstm.py")
            return
        
        # Refresh button
        if st.sidebar.button("🔄 Refresh Data"):
            st.cache_resource.clear()
            st.experimental_rerun()
        
        # Date selector
        forecast_days = st.sidebar.slider("Forecast Days", 1, 7, 3)
        
        # Alert threshold
        alert_threshold = st.sidebar.slider("Alert Threshold", 0.5, 1.0, 0.7, 0.05)
        
        # Main dashboard
        col1, col2, col3, col4 = st.columns(4)
        
        # Get current predictions for all districts
        all_predictions = []
        high_risk_count = 0
        medium_risk_count = 0
        
        for district in self.fps.districts:
            try:
                predictions = self.fps.predict_flood_risk(district, days_ahead=forecast_days)
                district_info = self.fps.df[self.fps.df['city'] == district].iloc[0]
                
                for pred in predictions:
                    pred_data = {
                        'district': district,
                        'latitude': district_info['latitude'],
                        'longitude': district_info['longitude'],
                        'day': pred['day'],
                        'predicted_alert': pred['predicted_alert'],
                        'confidence': pred['confidence'],
                        'red_prob': pred['probabilities'].get('Red', 0),
                        'orange_prob': pred['probabilities'].get('Orange', 0),
                        'yellow_prob': pred['probabilities'].get('Yellow', 0)
                    }
                    all_predictions.append(pred_data)
                    
                    if pred['predicted_alert'] == 'Red' and pred['confidence'] > alert_threshold:
                        high_risk_count += 1
                    elif pred['predicted_alert'] == 'Orange' and pred['confidence'] > alert_threshold:
                        medium_risk_count += 1
            except:
                pass
        
        predictions_df = pd.DataFrame(all_predictions)
        
        # KPIs
        with col1:
            st.metric("🔴 High Risk Alerts", high_risk_count)
        
        with col2:
            st.metric("🟠 Medium Risk Alerts", medium_risk_count)
        
        with col3:
            total_districts = len(self.fps.districts)
            st.metric("📍 Districts Monitored", total_districts)
        
        with col4:
            if not predictions_df.empty:
                avg_confidence = predictions_df['confidence'].mean()
                st.metric("📊 Avg Confidence", f"{avg_confidence:.1%}")
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🗺️ Prediction Map", "📊 Analytics", "🚨 Active Alerts", "📈 Trends"])
        
        with tab1:
            st.header("Flood Risk Prediction Map")
            
            if not predictions_df.empty:
                # Filter by day
                selected_day = st.selectbox("Select Forecast Day", sorted(predictions_df['day'].unique()))
                day_predictions = predictions_df[predictions_df['day'] == selected_day]
                
                # Create map
                prediction_map = self.create_prediction_map(day_predictions)
                st_folium(prediction_map, width=700, height=500)
                
                # District selector for detailed prediction
                col1, col2 = st.columns([1, 2])
                with col1:
                    selected_district = st.selectbox("District Details", self.fps.districts)
                
                with col2:
                    if selected_district:
                        district_preds = predictions_df[predictions_df['district'] == selected_district]
                        
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            x=district_preds['day'],
                            y=district_preds['red_prob'],
                            name='Red Risk',
                            marker_color='red'
                        ))
                        fig.add_trace(go.Bar(
                            x=district_preds['day'],
                            y=district_preds['orange_prob'],
                            name='Orange Risk',
                            marker_color='orange'
                        ))
                        fig.add_trace(go.Bar(
                            x=district_preds['day'],
                            y=district_preds['yellow_prob'],
                            name='Yellow Risk',
                            marker_color='yellow'
                        ))
                        
                        fig.update_layout(
                            title=f"Risk Probabilities - {selected_district}",
                            xaxis_title="Days Ahead",
                            yaxis_title="Probability",
                            barmode='stack'
                        )
                        st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.header("Risk Analytics")
            
            if not predictions_df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Risk distribution
                    alert_counts = predictions_df['predicted_alert'].value_counts()
                    fig = px.pie(values=alert_counts.values, names=alert_counts.index,
                               title="Risk Level Distribution",
                               color_discrete_map={'Red': 'red', 'Orange': 'orange', 'Yellow': 'yellow'})
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # District-wise risk
                    district_risk = predictions_df.groupby('district')['confidence'].mean().sort_values(ascending=False)
                    fig = px.bar(x=district_risk.values, y=district_risk.index,
                               orientation='h', title="Average Risk by District")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Confidence distribution
                fig = px.histogram(predictions_df, x='confidence', nbins=20,
                                 title="Prediction Confidence Distribution")
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.header("Active Flood Alerts")
            
            # Get alerts from database
            alerts_df = self.get_alert_data()
            
            if not alerts_df.empty:
                # Filter high-confidence alerts
                high_conf_alerts = alerts_df[alerts_df['confidence'] > alert_threshold]
                
                if not high_conf_alerts.empty:
                    st.subheader(f"🚨 {len(high_conf_alerts)} Active High-Confidence Alerts")
                    
                    for _, alert in high_conf_alerts.iterrows():
                        with st.container():
                            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                            
                            with col1:
                                alert_color = "🔴" if alert['alert_level'] == 'Red' else "🟠" if alert['alert_level'] == 'Orange' else "🟡"
                                st.write(f"{alert_color} **{alert['district']}**")
                            
                            with col2:
                                st.write(f"**{alert['alert_level']}**")
                            
                            with col3:
                                st.write(f"{alert['confidence']:.1%}")
                            
                            with col4:
                                st.write(f"Day {alert['day_ahead']}")
                            
                            st.write("---")
                else:
                    st.success("✅ No high-confidence alerts currently active")
            else:
                st.info("No alert data available")
        
        with tab4:
            st.header("Historical Trends")
            
            # Load historical data
            try:
                historical_df = self.fps.df.copy()
                historical_df['date'] = pd.to_datetime(historical_df['date'])
                
                # Time series of alerts by level
                monthly_alerts = historical_df.groupby([
                    historical_df['date'].dt.to_period('M'), 'flood_alert_flag'
                ]).size().unstack(fill_value=0)
                
                fig = go.Figure()
                for alert_level in ['Yellow', 'Orange', 'Red']:
                    if alert_level in monthly_alerts.columns:
                        fig.add_trace(go.Scatter(
                            x=monthly_alerts.index.astype(str),
                            y=monthly_alerts[alert_level],
                            mode='lines+markers',
                            name=alert_level,
                            line=dict(color={'Yellow': 'yellow', 'Orange': 'orange', 'Red': 'red'}[alert_level])
                        ))
                
                fig.update_layout(
                    title="Monthly Alert Trends (Historical)",
                    xaxis_title="Month",
                    yaxis_title="Number of Alerts"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Seasonal patterns
                seasonal_data = historical_df.groupby(historical_df['date'].dt.month)['flood_alert_flag'].apply(
                    lambda x: (x == 'Red').sum()
                )
                
                fig = px.bar(x=seasonal_data.index, y=seasonal_data.values,
                           title="Red Alert Frequency by Month",
                           labels={'x': 'Month', 'y': 'Red Alert Count'})
                st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error loading historical data: {e}")
        
        # Footer
        st.markdown("---")
        st.markdown("🌊 **Kerala Flood Prediction System** - Powered by LSTM Neural Networks")
        st.markdown("Last updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

def main():
    """Run the Streamlit dashboard"""
    dashboard = FloodDashboard()
    dashboard.run_dashboard()

if __name__ == "__main__":
    main()
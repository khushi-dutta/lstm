#!/usr/bin/env python3
"""
Quick Demo of Kerala Flood Prediction System
Demonstrates key features without full model training
"""
import pandas as pd
import numpy as np
import folium
import json
from datetime import datetime, timedelta

def load_sample_data():
    """Load and show sample flood data"""
    print("📊 Loading Kerala Flood Data...")
    df = pd.read_csv('kerala_flood_data.csv')
    
    print(f"✅ Loaded {len(df)} records from {df['date'].min()} to {df['date'].max()}")
    print(f"🏘️ Districts covered: {df['city'].nunique()} districts")
    
    # Show recent high-risk alerts
    recent_data = df[df['date'] >= '2025-08-01'].copy()
    high_risk = recent_data[recent_data['flood_alert_flag'].isin(['Red', 'Orange'])]
    
    print(f"\n🚨 Recent High-Risk Alerts (Aug 2025): {len(high_risk)} alerts")
    
    alert_summary = high_risk.groupby(['city', 'flood_alert_flag']).size().reset_index(name='count')
    for _, row in alert_summary.head(10).iterrows():
        emoji = "🔴" if row['flood_alert_flag'] == 'Red' else "🟠"
        print(f"  {emoji} {row['city']}: {row['count']} {row['flood_alert_flag']} alerts")
    
    return df, high_risk

def create_demo_prediction():
    """Create demo flood predictions"""
    print("\n🔮 Generating Demo Predictions...")
    
    districts = ['Ernakulam', 'Thiruvananthapuram', 'Kottayam', 'Alappuzha', 'Thrissur']
    predictions = []
    
    for i, district in enumerate(districts):
        # Simulate predictions with varying risk levels
        risk_level = np.random.choice(['Yellow', 'Orange', 'Red'], p=[0.6, 0.25, 0.15])
        confidence = np.random.uniform(0.65, 0.95)
        
        # Get coordinates from data
        df = pd.read_csv('kerala_flood_data.csv')
        district_info = df[df['city'] == district].iloc[0]
        
        prediction = {
            'district': district,
            'latitude': district_info['latitude'],
            'longitude': district_info['longitude'],
            'predicted_alert': risk_level,
            'confidence': confidence,
            'day_ahead': 1,
            'water_level_trend': 'Increasing' if risk_level in ['Orange', 'Red'] else 'Stable',
            'precipitation_forecast': np.random.uniform(50, 250),
            'timestamp': datetime.now().isoformat()
        }
        predictions.append(prediction)
        
        emoji = "🔴" if risk_level == 'Red' else "🟠" if risk_level == 'Orange' else "🟡"
        trend_emoji = "📈" if prediction['water_level_trend'] == 'Increasing' else "📊"
        print(f"  {emoji} {district}: {risk_level} alert ({confidence:.1%} confidence) {trend_emoji}")
    
    return predictions

def create_interactive_map(predictions, historical_data):
    """Create interactive flood prediction map"""
    print("\n🗺️ Creating Interactive Map...")
    
    # Center map on Kerala
    kerala_center = [10.8505, 76.2711]
    m = folium.Map(location=kerala_center, zoom_start=7, tiles='OpenStreetMap')
    
    # Color mapping
    colors = {'Yellow': 'yellow', 'Orange': 'orange', 'Red': 'red'}
    
    # Add prediction markers
    for pred in predictions:
        color = colors.get(pred['predicted_alert'], 'blue')
        
        popup_html = f"""
        <div style="font-family: Arial; width: 250px;">
            <h4 style="color: {color}; margin: 0;">{pred['district']}</h4>
            <hr style="margin: 5px 0;">
            <b>Prediction:</b> {pred['predicted_alert']} Alert<br>
            <b>Confidence:</b> {pred['confidence']:.1%}<br>
            <b>Water Level:</b> {pred['water_level_trend']}<br>
            <b>Precipitation:</b> {pred['precipitation_forecast']:.1f}mm<br>
            <b>Coordinates:</b> {pred['latitude']:.3f}, {pred['longitude']:.3f}<br>
            <small><i>Generated: {pred['timestamp'][:19]}</i></small>
        </div>
        """
        
        folium.Marker(
            location=[pred['latitude'], pred['longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(
                color=color, 
                icon='exclamation-triangle', 
                prefix='fa'
            ),
            tooltip=f"{pred['district']} - {pred['predicted_alert']} Alert"
        ).add_to(m)
    
    # Add recent historical alerts as circles
    recent_alerts = historical_data.sample(min(20, len(historical_data)))
    for _, alert in recent_alerts.iterrows():
        color = colors.get(alert['flood_alert_flag'], 'blue')
        
        folium.CircleMarker(
            location=[alert['latitude'], alert['longitude']],
            radius=5,
            popup=f"Historical: {alert['city']} - {alert['flood_alert_flag']} ({alert['date']})",
            color=color,
            fillColor=color,
            fillOpacity=0.3,
            tooltip=f"Historical: {alert['city']} - {alert['flood_alert_flag']}"
        ).add_to(m)
    
    # Add legend
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 180px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px; border-radius: 5px;">
    <h4 style="margin: 0 0 10px 0;">Flood Alert Levels</h4>
    <i class="fa fa-map-marker" style="color:red"></i> Red: High Risk (>7m water level)<br>
    <i class="fa fa-map-marker" style="color:orange"></i> Orange: Medium Risk (5-7m)<br>
    <i class="fa fa-map-marker" style="color:yellow"></i> Yellow: Low Risk (<5m)<br>
    <br><i class="fa fa-circle" style="color:grey"></i> Historical alerts
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Save map
    map_path = 'kerala_flood_demo_map.html'
    m.save(map_path)
    print(f"✅ Interactive map saved: {map_path}")
    
    return map_path

def generate_emergency_contacts():
    """Generate emergency contact information"""
    contacts = {
        "Kerala State Disaster Management Authority": {
            "phone": "+91-471-2721566",
            "email": "ksdma@kerala.gov.in",
            "website": "www.ksdma.kerala.gov.in"
        },
        "Emergency Services": {
            "Police": "100",
            "Fire": "101", 
            "Ambulance": "108",
            "Disaster Helpline": "1077"
        },
        "District Emergency Contacts": {
            "Ernakulam": "+91-484-2368407",
            "Thiruvananthapuram": "+91-471-2463977",
            "Kottayam": "+91-481-2560244",
            "Alappuzha": "+91-477-2251194",
            "Thrissur": "+91-487-2420022"
        }
    }
    
    return contacts

def create_alert_summary(predictions):
    """Create alert summary report"""
    print("\n📋 Alert Summary Report")
    print("=" * 40)
    
    # Count alerts by level
    alert_counts = {}
    for pred in predictions:
        level = pred['predicted_alert']
        alert_counts[level] = alert_counts.get(level, 0) + 1
    
    total_districts = len(predictions)
    
    for level in ['Red', 'Orange', 'Yellow']:
        count = alert_counts.get(level, 0)
        percentage = (count / total_districts) * 100 if total_districts > 0 else 0
        emoji = "🔴" if level == 'Red' else "🟠" if level == 'Orange' else "🟡"
        print(f"{emoji} {level}: {count} districts ({percentage:.1f}%)")
    
    # High confidence alerts
    high_conf_alerts = [p for p in predictions if p['confidence'] > 0.8]
    print(f"\n🎯 High Confidence Alerts (>80%): {len(high_conf_alerts)}")
    
    for alert in high_conf_alerts:
        emoji = "🔴" if alert['predicted_alert'] == 'Red' else "🟠" if alert['predicted_alert'] == 'Orange' else "🟡"
        print(f"  {emoji} {alert['district']}: {alert['predicted_alert']} ({alert['confidence']:.1%})")
    
    # Emergency contacts
    print(f"\n🚨 Emergency Contacts:")
    contacts = generate_emergency_contacts()
    print(f"  Disaster Helpline: {contacts['Emergency Services']['Disaster Helpline']}")
    print(f"  KSDMA: {contacts['Kerala State Disaster Management Authority']['phone']}")
    
    return {
        'total_districts': total_districts,
        'alert_counts': alert_counts,
        'high_confidence_alerts': len(high_conf_alerts),
        'emergency_contacts': contacts
    }

def save_demo_results(predictions, summary, map_path):
    """Save demo results to files"""
    # Save predictions as JSON
    with open('demo_predictions.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'predictions': predictions,
            'summary': summary,
            'map_file': map_path
        }, f, indent=2)
    
    # Create markdown report
    report = f"""# Kerala Flood Prediction Demo Report

## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Alert Summary
- **Total Districts Analyzed**: {summary['total_districts']}
- **High Confidence Alerts**: {summary['high_confidence_alerts']}

### Alert Distribution:
"""
    
    for level in ['Red', 'Orange', 'Yellow']:
        count = summary['alert_counts'].get(level, 0)
        percentage = (count / summary['total_districts']) * 100 if summary['total_districts'] > 0 else 0
        report += f"- **{level}**: {count} districts ({percentage:.1f}%)\n"
    
    report += f"""
## District Predictions:
"""
    
    for pred in predictions:
        report += f"""
### {pred['district']}
- **Alert Level**: {pred['predicted_alert']}
- **Confidence**: {pred['confidence']:.1%}
- **Water Level Trend**: {pred['water_level_trend']}
- **Precipitation Forecast**: {pred['precipitation_forecast']:.1f}mm
- **Location**: {pred['latitude']:.3f}, {pred['longitude']:.3f}
"""
    
    report += f"""
## Emergency Contacts
- **Disaster Helpline**: 1077
- **Police**: 100
- **Fire**: 101
- **Ambulance**: 108

## Interactive Map
View the interactive map: [{map_path}]({map_path})

---
*This is a demonstration of the Kerala Flood Prediction System*
"""
    
    with open('demo_report.md', 'w') as f:
        f.write(report)
    
    print(f"\n💾 Results saved:")
    print(f"  - Predictions: demo_predictions.json")
    print(f"  - Report: demo_report.md")
    print(f"  - Map: {map_path}")

def main():
    """Main demo function"""
    print("🌊 Kerala Flood Prediction System - DEMO")
    print("=" * 50)
    print("This demo showcases the key features of our flood prediction system")
    print("without requiring a fully trained ML model.")
    
    try:
        # Load sample data
        df, historical_alerts = load_sample_data()
        
        # Generate demo predictions
        predictions = create_demo_prediction()
        
        # Create interactive map
        map_path = create_interactive_map(predictions, historical_alerts)
        
        # Create summary report
        summary = create_alert_summary(predictions)
        
        # Save results
        save_demo_results(predictions, summary, map_path)
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"\n📱 Next Steps:")
        print(f"1. Open '{map_path}' in your browser to view the interactive map")
        print(f"2. Check 'demo_report.md' for the full report")
        print(f"3. Run 'python flood_prediction_lstm.py' for full ML training")
        print(f"4. Run 'python real_time_alert_system.py' for monitoring")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
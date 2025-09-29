import pandas as pd
import numpy as np
import json
import time
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import sqlite3
from flood_prediction_lstm import FloodPredictionSystem
import schedule
import threading

class FloodAlertSystem:
    def __init__(self, model_path='flood_lstm_model', db_path='flood_alerts.db'):
        """Initialize the real-time flood alert system"""
        self.model_path = model_path
        self.db_path = db_path
        self.fps = FloodPredictionSystem()
        self.setup_database()
        
        # Alert settings
        self.alert_thresholds = {
            'Red': 0.7,
            'Orange': 0.6,
            'Yellow': 0.5
        }
        
        # Contact settings (configure these)
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': 'your_email@gmail.com',
            'sender_password': 'your_app_password',  # Use app password for Gmail
            'recipients': ['emergency@kerala.gov.in', 'disaster@kerala.gov.in']
        }
        
        # Webhook URLs for different alert levels
        self.webhooks = {
            'Red': 'https://hooks.slack.com/services/YOUR/RED/WEBHOOK',
            'Orange': 'https://hooks.slack.com/services/YOUR/ORANGE/WEBHOOK',
            'Yellow': 'https://hooks.slack.com/services/YOUR/YELLOW/WEBHOOK'
        }
    
    def setup_database(self):
        """Setup SQLite database for storing alerts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                district TEXT,
                latitude REAL,
                longitude REAL,
                alert_level TEXT,
                confidence REAL,
                day_ahead INTEGER,
                sent_email BOOLEAN DEFAULT 0,
                sent_webhook BOOLEAN DEFAULT 0,
                active BOOLEAN DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                district TEXT,
                alert_level TEXT,
                confidence REAL,
                actual_outcome TEXT,
                accuracy_score REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Database setup complete")
    
    def load_trained_model(self):
        """Load the pre-trained LSTM model"""
        try:
            self.fps.load_model(self.model_path)
            # Load the processed data for context
            self.fps.load_and_preprocess_data()
            print("✅ Trained model loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def get_current_weather_data(self, district):
        """
        Get current weather data from API (placeholder)
        In production, integrate with weather APIs like OpenWeatherMap
        """
        # This is a placeholder - integrate with actual weather API
        try:
            # Example API call (replace with actual weather service)
            # api_key = "your_weather_api_key"
            # url = f"http://api.openweathermap.org/data/2.5/weather?q={district},IN&appid={api_key}"
            # response = requests.get(url)
            # data = response.json()
            
            # For demo, return simulated current data
            current_data = {
                'water_level': np.random.uniform(2, 8),
                'precipitation': np.random.uniform(0, 250),
                'temperature': np.random.uniform(20, 35),
                'humidity': np.random.uniform(60, 95)
            }
            return current_data
        except Exception as e:
            print(f"Error fetching weather data for {district}: {e}")
            return None
    
    def check_flood_risk(self):
        """Check flood risk for all districts and generate alerts"""
        print(f"🔍 Checking flood risk at {datetime.now()}")
        
        new_alerts = []
        
        for district in self.fps.districts:
            try:
                # Get predictions
                predictions = self.fps.predict_flood_risk(district, days_ahead=3)
                
                # Get district coordinates
                district_info = self.fps.df[self.fps.df['city'] == district].iloc[0]
                lat, lon = district_info['latitude'], district_info['longitude']
                
                for pred in predictions:
                    alert_level = pred['predicted_alert']
                    confidence = pred['confidence']
                    
                    # Check if alert meets threshold
                    if confidence >= self.alert_thresholds.get(alert_level, 0.5):
                        alert = {
                            'timestamp': datetime.now().isoformat(),
                            'district': district,
                            'latitude': lat,
                            'longitude': lon,
                            'alert_level': alert_level,
                            'confidence': confidence,
                            'day_ahead': pred['day'],
                            'probabilities': pred['probabilities']
                        }
                        
                        # Check if this is a new alert (not already in database)
                        if self.is_new_alert(alert):
                            new_alerts.append(alert)
                            self.store_alert(alert)
                            
            except Exception as e:
                print(f"Error checking {district}: {e}")
        
        if new_alerts:
            print(f"🚨 {len(new_alerts)} new alerts generated")
            self.process_alerts(new_alerts)
        else:
            print("✅ No new high-risk alerts")
        
        return new_alerts
    
    def is_new_alert(self, alert):
        """Check if this alert is new (not already stored recently)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check for similar alert in last 6 hours
        six_hours_ago = (datetime.now() - timedelta(hours=6)).isoformat()
        cursor.execute('''
            SELECT COUNT(*) FROM alerts 
            WHERE district = ? AND alert_level = ? 
            AND timestamp > ? AND active = 1
        ''', (alert['district'], alert['alert_level'], six_hours_ago))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count == 0
    
    def store_alert(self, alert):
        """Store alert in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alerts (timestamp, district, latitude, longitude, 
                              alert_level, confidence, day_ahead)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (alert['timestamp'], alert['district'], alert['latitude'], 
              alert['longitude'], alert['alert_level'], alert['confidence'], 
              alert['day_ahead']))
        
        conn.commit()
        conn.close()
    
    def process_alerts(self, alerts):
        """Process and send new alerts"""
        for alert in alerts:
            print(f"🚨 Processing {alert['alert_level']} alert for {alert['district']}")
            
            # Send email notification
            if alert['alert_level'] in ['Red', 'Orange']:
                self.send_email_alert(alert)
            
            # Send webhook notification
            self.send_webhook_alert(alert)
            
            # Generate emergency response recommendations
            self.generate_emergency_response(alert)
    
    def send_email_alert(self, alert):
        """Send email alert to authorities"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = ', '.join(self.email_config['recipients'])
            msg['Subject'] = f"🚨 FLOOD ALERT: {alert['alert_level']} - {alert['district']}"
            
            body = f"""
            FLOOD ALERT NOTIFICATION
            ========================
            
            Alert Level: {alert['alert_level']}
            District: {alert['district']}
            Coordinates: {alert['latitude']:.4f}, {alert['longitude']:.4f}
            Confidence: {alert['confidence']:.1%}
            Predicted for: Day {alert['day_ahead']}
            Timestamp: {alert['timestamp']}
            
            IMMEDIATE ACTION REQUIRED
            
            Please take necessary precautionary measures and alert local authorities.
            
            This is an automated alert from the Kerala Flood Prediction System.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email alert sent for {alert['district']}")
            
            # Update database
            self.update_alert_status(alert, 'email', True)
            
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")
    
    def send_webhook_alert(self, alert):
        """Send webhook notification (Slack, Teams, etc.)"""
        try:
            webhook_url = self.webhooks.get(alert['alert_level'])
            if not webhook_url or 'YOUR' in webhook_url:
                print(f"⚠️ Webhook not configured for {alert['alert_level']} alerts")
                return
            
            # Format message for Slack
            message = {
                "text": f"🚨 Flood Alert: {alert['alert_level']}",
                "attachments": [
                    {
                        "color": "danger" if alert['alert_level'] == 'Red' else "warning",
                        "fields": [
                            {"title": "District", "value": alert['district'], "short": True},
                            {"title": "Alert Level", "value": alert['alert_level'], "short": True},
                            {"title": "Confidence", "value": f"{alert['confidence']:.1%}", "short": True},
                            {"title": "Day Ahead", "value": str(alert['day_ahead']), "short": True},
                            {"title": "Coordinates", "value": f"{alert['latitude']:.4f}, {alert['longitude']:.4f}", "short": False}
                        ],
                        "footer": "Kerala Flood Prediction System",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=message)
            if response.status_code == 200:
                print(f"✅ Webhook alert sent for {alert['district']}")
                self.update_alert_status(alert, 'webhook', True)
            else:
                print(f"❌ Webhook failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Failed to send webhook alert: {e}")
    
    def update_alert_status(self, alert, notification_type, success):
        """Update alert notification status in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        column = f"sent_{notification_type}"
        cursor.execute(f'''
            UPDATE alerts SET {column} = ?
            WHERE district = ? AND timestamp = ?
        ''', (success, alert['district'], alert['timestamp']))
        
        conn.commit()
        conn.close()
    
    def generate_emergency_response(self, alert):
        """Generate emergency response recommendations"""
        recommendations = {
            'Red': [
                "Immediate evacuation of low-lying areas",
                "Deploy emergency response teams",
                "Activate flood shelters",
                "Issue public warnings via all channels",
                "Coordinate with local authorities and NGOs",
                "Ensure medical facilities are prepared"
            ],
            'Orange': [
                "Alert emergency response teams",
                "Prepare flood shelters",
                "Issue weather warnings to public",
                "Monitor water levels closely",
                "Prepare evacuation routes"
            ],
            'Yellow': [
                "Monitor weather conditions",
                "Issue advisory to residents",
                "Check drainage systems",
                "Prepare emergency equipment"
            ]
        }
        
        response_plan = {
            'alert': alert,
            'recommendations': recommendations.get(alert['alert_level'], []),
            'emergency_contacts': {
                'District Collector': f"+91-XXX-XXXX-XXX",
                'Fire Department': "101",
                'Police': "100",
                'Ambulance': "108",
                'Disaster Management': "+91-XXX-XXXX-XXX"
            },
            'nearest_shelters': [
                f"Shelter location 1 in {alert['district']}",
                f"Shelter location 2 in {alert['district']}"
            ]
        }
        
        # Save emergency response plan
        with open(f"emergency_response_{alert['district']}_{datetime.now().strftime('%Y%m%d_%H%M')}.json", 'w') as f:
            json.dump(response_plan, f, indent=2)
        
        print(f"📋 Emergency response plan generated for {alert['district']}")
    
    def get_alert_statistics(self):
        """Get alert statistics from database"""
        conn = sqlite3.connect(self.db_path)
        
        # Recent alerts
        recent_alerts = pd.read_sql_query('''
            SELECT * FROM alerts 
            WHERE timestamp > datetime('now', '-24 hours')
            ORDER BY timestamp DESC
        ''', conn)
        
        # Alert counts by level
        alert_counts = pd.read_sql_query('''
            SELECT alert_level, COUNT(*) as count 
            FROM alerts 
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY alert_level
        ''', conn)
        
        # District-wise alerts
        district_alerts = pd.read_sql_query('''
            SELECT district, COUNT(*) as count 
            FROM alerts 
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY district
            ORDER BY count DESC
        ''', conn)
        
        conn.close()
        
        return {
            'recent_alerts': recent_alerts,
            'alert_counts': alert_counts,
            'district_alerts': district_alerts
        }
    
    def start_monitoring(self, check_interval_minutes=30):
        """Start continuous monitoring"""
        print(f"🚀 Starting flood monitoring system...")
        print(f"Check interval: {check_interval_minutes} minutes")
        
        # Load model
        if not self.load_trained_model():
            print("❌ Cannot start monitoring without trained model")
            return
        
        # Schedule regular checks
        schedule.every(check_interval_minutes).minutes.do(self.check_flood_risk)
        
        # Initial check
        self.check_flood_risk()
        
        print("✅ Monitoring system started")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute for scheduled tasks
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")

def main():
    """Main function for the alert system"""
    print("🌊 Kerala Flood Real-Time Alert System 🚨")
    print("=" * 50)
    
    # Initialize alert system
    alert_system = FloodAlertSystem()
    
    # Configure email settings (replace with actual credentials)
    print("⚠️ Please configure email settings in the code before running")
    print("⚠️ Please configure webhook URLs for Slack/Teams notifications")
    
    # Get user choice
    choice = input("\nChoose an option:\n1. Start monitoring (requires trained model)\n2. Check current alerts\n3. View statistics\nEnter choice (1-3): ")
    
    if choice == '1':
        interval = int(input("Enter check interval in minutes (default 30): ") or 30)
        alert_system.start_monitoring(check_interval_minutes=interval)
    
    elif choice == '2':
        if alert_system.load_trained_model():
            alerts = alert_system.check_flood_risk()
            if alerts:
                for alert in alerts:
                    print(f"🚨 {alert['district']}: {alert['alert_level']} (Confidence: {alert['confidence']:.1%})")
            else:
                print("✅ No high-risk alerts currently")
    
    elif choice == '3':
        stats = alert_system.get_alert_statistics()
        print("\n📊 Alert Statistics (Last 7 days):")
        print(stats['alert_counts'])
        print("\n📍 District-wise Alerts:")
        print(stats['district_alerts'])
    
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
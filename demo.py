#!/usr/bin/env python3
"""
Demo script for Kerala Flood Prediction System
This script demonstrates the complete workflow of the flood prediction system.
"""

import os
import sys
import time
from datetime import datetime
import pandas as pd

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"🌊 {title}")
    print("="*60)

def print_step(step, description):
    """Print a formatted step"""
    print(f"\n📍 Step {step}: {description}")
    print("-" * 40)

def main():
    """Main demo function"""
    print_header("KERALA FLOOD PREDICTION SYSTEM DEMO")
    print("This demo will walk through the complete flood prediction workflow")
    print(f"Demo started at: {datetime.now()}")
    
    # Check if data file exists
    print_step(1, "Checking Data Availability")
    if not os.path.exists('kerala_flood_data.csv'):
        print("❌ Data file not found. Generating sample data...")
        try:
            import data
            print("✅ Sample data generated successfully!")
        except Exception as e:
            print(f"❌ Error generating data: {e}")
            return False
    else:
        print("✅ Data file found!")
        # Show data summary
        df = pd.read_csv('kerala_flood_data.csv')
        print(f"📊 Data Summary:")
        print(f"   - Total records: {len(df):,}")
        print(f"   - Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"   - Districts: {df['city'].nunique()}")
        print(f"   - Alert distribution: {df['flood_alert_flag'].value_counts().to_dict()}")
    
    # Check dependencies
    print_step(2, "Checking Dependencies")
    required_packages = [
        'tensorflow', 'pandas', 'numpy', 'scikit-learn', 
        'matplotlib', 'seaborn', 'folium', 'joblib'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing!")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install -r requirements.txt")
        return False
    
    # Model Training Demo
    print_step(3, "Training LSTM Model (This may take a few minutes)")
    
    try:
        from flood_prediction_lstm import FloodPredictionSystem
        
        print("🧠 Initializing LSTM model...")
        fps = FloodPredictionSystem()
        
        print("📊 Loading and preprocessing data...")
        fps.load_and_preprocess_data()
        
        print("🔄 Preparing training sequences...")
        fps.prepare_training_data()
        
        print("🏗️ Building neural network architecture...")
        fps.build_lstm_model()
        
        print("🎯 Training model (reduced epochs for demo)...")
        history = fps.train_model(epochs=10, batch_size=32)  # Reduced for demo
        
        print("📈 Evaluating model performance...")
        fps.evaluate_model()
        
        print("💾 Saving trained model...")
        fps.save_model()
        
        print("✅ Model training completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during model training: {e}")
        return False
    
    # Prediction Demo
    print_step(4, "Testing Flood Predictions")
    
    try:
        # Test predictions for a few districts
        test_districts = ['Ernakulam', 'Thiruvananthapuram', 'Kottayam']
        
        for district in test_districts:
            print(f"\n🔍 Predicting flood risk for {district}:")
            predictions = fps.predict_flood_risk(district, days_ahead=3)
            
            for pred in predictions:
                confidence_emoji = "🔴" if pred['confidence'] > 0.8 else "🟠" if pred['confidence'] > 0.6 else "🟡"
                print(f"   Day {pred['day']}: {pred['predicted_alert']} alert "
                      f"{confidence_emoji} (Confidence: {pred['confidence']:.1%})")
        
        print("✅ Prediction test completed!")
        
    except Exception as e:
        print(f"❌ Error during prediction testing: {e}")
        return False
    
    # Alert System Demo
    print_step(5, "Testing Alert System")
    
    try:
        print("🚨 Generating geo-tagged alerts...")
        alerts = fps.generate_geo_tagged_alerts(alert_threshold=0.5)  # Lower threshold for demo
        
        if alerts:
            print(f"📧 Generated {len(alerts)} alerts:")
            for alert in alerts[:5]:  # Show first 5 alerts
                print(f"   📍 {alert['district']}: {alert['alert_level']} alert "
                      f"(Day {alert['day']}, Confidence: {alert['confidence']:.1%})")
            
            if len(alerts) > 5:
                print(f"   ... and {len(alerts) - 5} more alerts")
            
            print("🗺️ Creating interactive map...")
            fps.create_alert_map(alerts, 'demo_flood_map.html')
            print("✅ Interactive map created: demo_flood_map.html")
            
        else:
            print("ℹ️ No high-risk alerts generated (this is normal for demo)")
        
    except Exception as e:
        print(f"❌ Error during alert system testing: {e}")
        return False
    
    # Database and Real-time System Demo
    print_step(6, "Testing Real-time Alert System")
    
    try:
        from real_time_alert_system import FloodAlertSystem
        
        print("🔄 Initializing real-time alert system...")
        alert_system = FloodAlertSystem()
        
        print("📊 Setting up database...")
        alert_system.setup_database()
        
        print("🧠 Loading trained model...")
        if alert_system.load_trained_model():
            print("✅ Model loaded successfully!")
            
            print("🔍 Running one-time flood risk check...")
            new_alerts = alert_system.check_flood_risk()
            
            if new_alerts:
                print(f"🚨 Generated {len(new_alerts)} new alerts")
                for alert in new_alerts:
                    print(f"   📍 {alert['district']}: {alert['alert_level']} "
                          f"(Confidence: {alert['confidence']:.1%})")
            else:
                print("✅ No new high-risk alerts at this time")
            
            print("📊 Getting alert statistics...")
            stats = alert_system.get_alert_statistics()
            print(f"   Recent alerts: {len(stats['recent_alerts'])}")
            
        else:
            print("❌ Failed to load model for real-time system")
            return False
        
    except Exception as e:
        print(f"❌ Error during real-time system testing: {e}")
        return False
    
    # Dashboard Demo
    print_step(7, "Dashboard Information")
    
    print("📊 Interactive Dashboard:")
    print("   To launch the dashboard, run: streamlit run dashboard.py")
    print("   Then open your browser to: http://localhost:8501")
    print("   Features:")
    print("   - 🗺️ Interactive prediction maps")
    print("   - 📊 Real-time analytics")
    print("   - 🚨 Active alerts monitoring")
    print("   - 📈 Historical trends")
    
    # Summary
    print_step(8, "Demo Summary")
    
    print("✅ All systems tested successfully!")
    print("\n📋 Generated Files:")
    generated_files = [
        'kerala_flood_data.csv',
        'flood_lstm_model.keras',
        'flood_lstm_model_scalers.pkl',
        'flood_lstm_model_label_encoder.pkl',
        'flood_lstm_model_config.json',
        'flood_alerts.db',
        'demo_flood_map.html',
        'flood_alerts.json',
        'confusion_matrix.png'
    ]
    
    for file in generated_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file} ({size:,} bytes)")
        else:
            print(f"   ❌ {file} (not found)")
    
    print("\n🚀 Next Steps:")
    print("1. Launch dashboard: streamlit run dashboard.py")
    print("2. Start monitoring: python real_time_alert_system.py")
    print("3. Configure email/webhook settings in config.json")
    print("4. Integrate with real weather APIs")
    print("5. Deploy to production server")
    
    print("\n⚠️ Important Notes:")
    print("- This is a demonstration system")
    print("- Configure email settings before production use")
    print("- Integrate real weather data for accurate predictions")
    print("- Always verify predictions with official weather services")
    
    print_header("DEMO COMPLETED SUCCESSFULLY! 🎉")
    print(f"Demo finished at: {datetime.now()}")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🌊 Kerala Flood Prediction System is ready to use! 🚨")
            sys.exit(0)
        else:
            print("\n❌ Demo failed. Please check error messages above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during demo: {e}")
        sys.exit(1)
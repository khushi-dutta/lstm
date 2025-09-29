#!/usr/bin/env python3
"""
Test script for the Kerala Flood Prediction System
"""
import os
import sys
from flood_prediction_lstm import FloodPredictionSystem

def test_system():
    """Test the flood prediction system"""
    print("🌊 Testing Kerala Flood Prediction System")
    print("=" * 50)
    
    try:
        # Initialize system
        fps = FloodPredictionSystem()
        
        # Check if model exists
        model_files = [
            'flood_lstm_model.keras',
            'flood_lstm_model_scalers.pkl',
            'flood_lstm_model_label_encoder.pkl',
            'flood_lstm_model_config.json'
        ]
        
        model_exists = all(os.path.exists(f) for f in model_files)
        
        if not model_exists:
            print("📚 Model not found. Training new model...")
            # Load and preprocess data
            fps.load_and_preprocess_data()
            
            # Prepare training data
            fps.prepare_training_data()
            
            # Build and train model (quick training for demo)
            fps.build_lstm_model()
            print("🔧 Training model (this may take a few minutes)...")
            history = fps.train_model(epochs=20, batch_size=32)
            
            # Save model
            fps.save_model()
            print("💾 Model saved!")
        else:
            print("📂 Loading existing model...")
            fps.load_model()
            fps.load_and_preprocess_data()
        
        print("✅ Model loaded successfully!")
        
        # Test predictions for key districts
        print("\n🔮 Testing predictions for key districts:")
        test_districts = ['Ernakulam', 'Thiruvananthapuram', 'Kottayam']
        
        for district in test_districts:
            print(f"\n📍 {district}:")
            try:
                preds = fps.predict_flood_risk(district, days_ahead=3)
                for p in preds:
                    confidence_emoji = "🔴" if p['confidence'] > 0.8 else "🟡" if p['confidence'] > 0.6 else "🟢"
                    alert_emoji = "🚨" if p['predicted_alert'] == 'Red' else "⚠️" if p['predicted_alert'] == 'Orange' else "ℹ️"
                    print(f"  Day {p['day']}: {p['predicted_alert']} {alert_emoji} (Confidence: {p['confidence']:.1%} {confidence_emoji})")
            except Exception as e:
                print(f"  ❌ Error predicting for {district}: {e}")
        
        # Generate geo-tagged alerts
        print("\n🚨 Generating geo-tagged alerts...")
        try:
            alerts = fps.generate_geo_tagged_alerts(alert_threshold=0.5)
            print(f"Generated {len(alerts)} high-risk alerts!")
            
            if alerts:
                print("\nHigh-Risk Alerts:")
                for alert in alerts[:5]:  # Show first 5 alerts
                    print(f"  📍 {alert['district']}: {alert['alert_level']} alert")
                    print(f"     Day {alert['day']}, Confidence: {alert['confidence']:.1%}")
                    print(f"     Location: ({alert['latitude']:.3f}, {alert['longitude']:.3f})")
                
                # Create interactive map
                fps.create_alert_map(alerts, 'demo_flood_map.html')
                print(f"\n🗺️ Interactive map created: demo_flood_map.html")
                print("   Open this file in your browser to view the alerts!")
            else:
                print("✅ No high-risk alerts at this time")
        
        except Exception as e:
            print(f"❌ Error generating alerts: {e}")
        
        print("\n✅ System test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data():
    """Test data loading"""
    print("\n📊 Testing data loading...")
    try:
        fps = FloodPredictionSystem()
        df = fps.load_and_preprocess_data()
        print(f"✅ Data loaded: {df.shape[0]} records, {df.shape[1]} columns")
        print(f"📅 Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"🏘️ Districts: {len(fps.districts)} ({', '.join(fps.districts)})")
        return True
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Kerala Flood Prediction System - Test Suite")
    print("=" * 60)
    
    # Test data loading
    if not test_data():
        print("❌ Data test failed. Exiting.")
        return
    
    # Test full system
    if test_system():
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nNext steps:")
        print("1. Check 'demo_flood_map.html' for interactive map")
        print("2. Run 'python flood_prediction_lstm.py' for full training")
        print("3. Run 'python real_time_alert_system.py' for monitoring")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
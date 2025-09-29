import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Deep Learning libraries
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# For alerts and notifications
import json
import folium
from folium import plugins

class FloodPredictionSystem:
    def __init__(self, data_path='kerala_flood_data.csv'):
        """Initialize the flood prediction system"""
        self.data_path = data_path
        self.model = None
        self.scalers = {}
        self.label_encoder = LabelEncoder()
        self.sequence_length = 7  # Use 7 days of data to predict next day
        self.districts = []
        
    def load_and_preprocess_data(self):
        """Load and preprocess the flood data"""
        print("Loading and preprocessing data...")
        
        # Load data
        self.df = pd.read_csv(self.data_path)
        self.df['date'] = pd.to_datetime(self.df['date'])
        
        # Get unique districts
        self.districts = sorted(self.df['city'].unique())
        print(f"Districts: {self.districts}")
        
        # Encode flood alert flags
        self.df['alert_encoded'] = self.label_encoder.fit_transform(self.df['flood_alert_flag'])
        
        # Create features for each district
        district_data = []
        
        for district in self.districts:
            district_df = self.df[self.df['city'] == district].copy()
            district_df = district_df.sort_values('date').reset_index(drop=True)
            
            # Add temporal features
            district_df['day_of_year'] = district_df['date'].dt.dayofyear
            district_df['month'] = district_df['date'].dt.month
            district_df['is_monsoon'] = district_df['month'].isin([6, 7, 8, 9]).astype(int)
            
            # Add rolling averages
            district_df['water_level_ma3'] = district_df['water_level_m'].rolling(3).mean()
            district_df['precipitation_ma3'] = district_df['precipitation_mm'].rolling(3).mean()
            
            # Add lag features
            district_df['water_level_lag1'] = district_df['water_level_m'].shift(1)
            district_df['precipitation_lag1'] = district_df['precipitation_mm'].shift(1)
            
            # Add rate of change
            district_df['water_level_change'] = district_df['water_level_m'].diff()
            district_df['precipitation_change'] = district_df['precipitation_mm'].diff()
            
            district_df['district'] = district
            district_data.append(district_df)
        
        # Combine all district data
        self.processed_df = pd.concat(district_data, ignore_index=True)
        self.processed_df = self.processed_df.dropna()
        
        print(f"Data shape after preprocessing: {self.processed_df.shape}")
        return self.processed_df
    
    def create_sequences(self, district_data, features, target):
        """Create sequences for LSTM training"""
        X, y = [], []
        
        for i in range(self.sequence_length, len(district_data)):
            X.append(district_data[features].iloc[i-self.sequence_length:i].values)
            y.append(district_data[target].iloc[i])
        
        return np.array(X), np.array(y)
    
    def prepare_training_data(self):
        """Prepare training sequences for all districts"""
        print("Preparing training sequences...")
        
        # Feature columns
        feature_cols = [
            'water_level_m', 'precipitation_mm', 'day_of_year', 'month', 
            'is_monsoon', 'water_level_ma3', 'precipitation_ma3',
            'water_level_lag1', 'precipitation_lag1', 'water_level_change', 'precipitation_change'
        ]
        
        all_X, all_y = [], []
        
        for district in self.districts:
            district_data = self.processed_df[self.processed_df['district'] == district].copy()
            
            # Scale features for this district
            scaler = MinMaxScaler()
            district_data[feature_cols] = scaler.fit_transform(district_data[feature_cols])
            self.scalers[district] = scaler
            
            # Create sequences
            X_district, y_district = self.create_sequences(
                district_data, feature_cols, 'alert_encoded'
            )
            
            if len(X_district) > 0:
                all_X.append(X_district)
                all_y.append(y_district)
        
        # Combine all sequences
        self.X = np.vstack(all_X)
        self.y = np.hstack(all_y)
        
        print(f"Training data shape: X={self.X.shape}, y={self.y.shape}")
        
        # Split data
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X, self.y, test_size=0.2, random_state=42, stratify=self.y
        )
        
        return self.X_train, self.X_test, self.y_train, self.y_test
    
    def build_lstm_model(self):
        """Build the LSTM model architecture"""
        print("Building LSTM model...")
        
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=(self.sequence_length, self.X.shape[2])),
            Dropout(0.2),
            BatchNormalization(),
            
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            BatchNormalization(),
            
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            
            Dense(32, activation='relu'),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(len(self.label_encoder.classes_), activation='softmax')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        return model
    
    def train_model(self, epochs=100, batch_size=32):
        """Train the LSTM model"""
        print("Training LSTM model...")
        
        # Callbacks
        early_stopping = EarlyStopping(
            monitor='val_loss', patience=15, restore_best_weights=True
        )
        
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss', factor=0.2, patience=10, min_lr=0.0001
        )
        
        # Train model
        history = self.model.fit(
            self.X_train, self.y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(self.X_test, self.y_test),
            callbacks=[early_stopping, reduce_lr],
            verbose=1
        )
        
        return history
    
    def evaluate_model(self):
        """Evaluate the trained model"""
        print("\nEvaluating model...")
        
        # Predictions
        y_pred = self.model.predict(self.X_test)
        y_pred_classes = np.argmax(y_pred, axis=1)
        
        # Classification report
        target_names = self.label_encoder.classes_
        print("\nClassification Report:")
        print(classification_report(self.y_test, y_pred_classes, target_names=target_names))
        
        # Confusion Matrix
        cm = confusion_matrix(self.y_test, y_pred_classes)
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=target_names, yticklabels=target_names)
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig('confusion_matrix.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return y_pred, y_pred_classes
    
    def predict_flood_risk(self, district, days_ahead=7):
        """Predict flood risk for a specific district"""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        # Get recent data for the district
        district_data = self.processed_df[self.processed_df['district'] == district].copy()
        district_data = district_data.sort_values('date').tail(self.sequence_length * 2)
        
        feature_cols = [
            'water_level_m', 'precipitation_mm', 'day_of_year', 'month', 
            'is_monsoon', 'water_level_ma3', 'precipitation_ma3',
            'water_level_lag1', 'precipitation_lag1', 'water_level_change', 'precipitation_change'
        ]
        
        # Scale features
        scaled_features = self.scalers[district].transform(district_data[feature_cols])
        
        predictions = []
        current_sequence = scaled_features[-self.sequence_length:]
        
        for day in range(days_ahead):
            # Reshape for prediction
            X_pred = current_sequence.reshape(1, self.sequence_length, len(feature_cols))
            
            # Predict
            pred = self.model.predict(X_pred, verbose=0)
            pred_class = np.argmax(pred, axis=1)[0]
            pred_prob = pred[0]
            
            predictions.append({
                'day': day + 1,
                'predicted_alert': self.label_encoder.inverse_transform([pred_class])[0],
                'probabilities': {
                    alert: float(prob) for alert, prob in 
                    zip(self.label_encoder.classes_, pred_prob)
                },
                'confidence': float(np.max(pred_prob))
            })
            
            # Update sequence (simplified - in practice, you'd need actual future features)
            current_sequence = np.roll(current_sequence, -1, axis=0)
            # For demo, we'll duplicate the last row's pattern
            current_sequence[-1] = current_sequence[-2] * (0.9 + np.random.random() * 0.2)
        
        return predictions
    
    def generate_geo_tagged_alerts(self, alert_threshold=0.7):
        """Generate geo-tagged flood alerts for all districts"""
        alerts = []
        
        for district in self.districts:
            try:
                predictions = self.predict_flood_risk(district, days_ahead=3)
                
                # Get district coordinates
                district_info = self.df[self.df['city'] == district].iloc[0]
                lat, lon = district_info['latitude'], district_info['longitude']
                
                # Check for high-risk predictions
                for pred in predictions:
                    if (pred['predicted_alert'] in ['Orange', 'Red'] and 
                        pred['confidence'] > alert_threshold):
                        
                        alerts.append({
                            'district': district,
                            'latitude': lat,
                            'longitude': lon,
                            'day': pred['day'],
                            'alert_level': pred['predicted_alert'],
                            'confidence': pred['confidence'],
                            'probabilities': pred['probabilities'],
                            'timestamp': datetime.now().isoformat()
                        })
            except Exception as e:
                print(f"Error predicting for {district}: {e}")
        
        return alerts
    
    def create_alert_map(self, alerts, save_path='flood_alerts_map.html'):
        """Create an interactive map with flood alerts"""
        # Center map on Kerala
        kerala_center = [10.8505, 76.2711]
        m = folium.Map(location=kerala_center, zoom_start=7)
        
        # Color mapping for alert levels
        colors = {'Yellow': 'yellow', 'Orange': 'orange', 'Red': 'red'}
        
        for alert in alerts:
            color = colors.get(alert['alert_level'], 'blue')
            
            # Create popup content
            popup_html = f"""
            <b>{alert['district']}</b><br>
            Alert Level: <b style="color:{color}">{alert['alert_level']}</b><br>
            Day: {alert['day']}<br>
            Confidence: {alert['confidence']:.2%}<br>
            Coordinates: ({alert['latitude']:.4f}, {alert['longitude']:.4f})<br>
            Timestamp: {alert['timestamp'][:19]}
            """
            
            folium.Marker(
                location=[alert['latitude'], alert['longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color=color, icon='exclamation-triangle', prefix='fa'),
                tooltip=f"{alert['district']} - {alert['alert_level']} Alert"
            ).add_to(m)
        
        # Add a legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 150px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <b>Flood Alert Levels</b><br>
        <i class="fa fa-circle" style="color:yellow"></i> Yellow: Low Risk<br>
        <i class="fa fa-circle" style="color:orange"></i> Orange: Medium Risk<br>
        <i class="fa fa-circle" style="color:red"></i> Red: High Risk<br>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Save map
        m.save(save_path)
        print(f"Alert map saved to {save_path}")
        
        return m
    
    def save_model(self, model_path='flood_lstm_model'):
        """Save the trained model and preprocessors"""
        self.model.save(f'{model_path}.keras')
        joblib.dump(self.scalers, f'{model_path}_scalers.pkl')
        joblib.dump(self.label_encoder, f'{model_path}_label_encoder.pkl')
        
        # Save configuration
        config = {
            'sequence_length': self.sequence_length,
            'districts': self.districts,
            'feature_columns': [
                'water_level_m', 'precipitation_mm', 'day_of_year', 'month', 
                'is_monsoon', 'water_level_ma3', 'precipitation_ma3',
                'water_level_lag1', 'precipitation_lag1', 'water_level_change', 'precipitation_change'
            ]
        }
        
        with open(f'{model_path}_config.json', 'w') as f:
            json.dump(config, f)
        
        print(f"Model and preprocessors saved with prefix: {model_path}")
    
    def load_model(self, model_path='flood_lstm_model'):
        """Load a trained model and preprocessors"""
        self.model = tf.keras.models.load_model(f'{model_path}.keras')
        self.scalers = joblib.load(f'{model_path}_scalers.pkl')
        self.label_encoder = joblib.load(f'{model_path}_label_encoder.pkl')
        
        with open(f'{model_path}_config.json', 'r') as f:
            config = json.load(f)
            self.sequence_length = config['sequence_length']
            self.districts = config['districts']
        
        print("Model and preprocessors loaded successfully!")

def main():
    """Main function to run the flood prediction system"""
    print("🌊 Kerala Flood Prediction System with LSTM 🌊")
    print("=" * 50)
    
    # Initialize system
    fps = FloodPredictionSystem()
    
    # Load and preprocess data
    fps.load_and_preprocess_data()
    
    # Prepare training data
    fps.prepare_training_data()
    
    # Build and train model
    fps.build_lstm_model()
    print(fps.model.summary())
    
    # Train the model
    history = fps.train_model(epochs=50, batch_size=32)
    
    # Evaluate model
    fps.evaluate_model()
    
    # Generate predictions and alerts
    print("\n🚨 Generating Flood Alerts...")
    alerts = fps.generate_geo_tagged_alerts(alert_threshold=0.6)
    
    print(f"Generated {len(alerts)} high-risk flood alerts")
    
    # Display alerts
    if alerts:
        print("\nHigh-Risk Flood Alerts:")
        print("-" * 60)
        for alert in alerts:
            print(f"📍 {alert['district']}: {alert['alert_level']} alert "
                  f"(Day {alert['day']}, Confidence: {alert['confidence']:.2%})")
        
        # Create interactive map
        fps.create_alert_map(alerts)
        
        # Save alerts to JSON
        with open('flood_alerts.json', 'w') as f:
            json.dump(alerts, f, indent=2)
        print("Alerts saved to flood_alerts.json")
    
    # Save model
    fps.save_model()
    
    # Example: Predict for a specific district
    print("\n🔍 Example Prediction for Ernakulam:")
    predictions = fps.predict_flood_risk('Ernakulam', days_ahead=5)
    for pred in predictions:
        print(f"Day {pred['day']}: {pred['predicted_alert']} "
              f"(Confidence: {pred['confidence']:.2%})")
    
    print("\n✅ Flood prediction system setup complete!")
    print("Check 'flood_alerts_map.html' for interactive map")
    print("Check 'flood_alerts.json' for detailed alert data")

if __name__ == "__main__":
    main()
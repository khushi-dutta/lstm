# 🌊 Kerala Flood Prediction Streamlit App

## Deployment Guide

This guide will help you deploy the Kerala Flood Prediction Streamlit app on various platforms.

## 🚀 Quick Start (Local Development)

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the App**
   ```bash
   streamlit run app.py
   ```

3. **Open in Browser**
   - The app will automatically open at `http://localhost:8501`

## 🌐 Deployment Options

### 1. Streamlit Community Cloud (Recommended)

**Steps:**
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select your repository
5. Set main file as `app.py`
6. Deploy!

**Requirements:**
- GitHub repository (public or private)
- Streamlit account (free)

### 2. Heroku Deployment

**Files needed:**
- `Procfile` (created below)
- `setup.sh` (created below)

**Steps:**
1. Create Heroku account
2. Install Heroku CLI
3. Run deployment script:
   ```bash
   ./deploy_heroku.sh
   ```

### 3. Docker Deployment

**Build Docker image:**
```bash
docker build -t flood-prediction-app .
```

**Run container:**
```bash
docker run -p 8501:8501 flood-prediction-app
```

### 4. AWS/GCP/Azure Cloud Deployment

Refer to cloud-specific documentation in the `deployment/` folder.

## 📁 File Structure

```
flood-detection/
├── app.py                          # Main Streamlit app
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker configuration
├── .streamlit/config.toml          # Streamlit configuration
├── flood_prediction_lstm.py        # ML model code
├── real_time_alert_system.py       # Alert system
├── config.json                     # Configuration file
├── kerala_flood_data.csv           # Training data
├── *.pkl, *.keras                  # Model files
└── deployment/                     # Deployment scripts
```

## 🔧 Configuration

### Environment Variables
Set these environment variables for production:

- `STREAMLIT_SERVER_PORT`: Port number (default: 8501)
- `STREAMLIT_SERVER_ADDRESS`: Server address (default: 0.0.0.0)
- `STREAMLIT_THEME_PRIMARY_COLOR`: Primary color
- `STREAMLIT_BROWSER_GATHER_USAGE_STATS`: false

### Model Files
Ensure these files are present:
- `flood_lstm_model.keras`
- `flood_lstm_model_scalers.pkl`
- `flood_lstm_model_label_encoder.pkl`
- `kerala_flood_data.csv`

## 📊 Features

- **Real-time Flood Prediction**: LSTM-based predictions for all Kerala districts
- **Interactive Map**: Geo-tagged risk visualization
- **Alert System**: Multi-level warning system
- **Dashboard Analytics**: Comprehensive charts and metrics
- **Responsive Design**: Works on desktop and mobile

## 🐛 Troubleshooting

### Common Issues:

1. **Model files not found**
   - Ensure all `.pkl` and `.keras` files are in the root directory
   - App will run in demo mode if files are missing

2. **Memory issues on deployment**
   - Consider using lighter TensorFlow versions
   - Implement model caching

3. **Slow loading**
   - Enable caching with `@st.cache_resource`
   - Optimize data loading

## 🔒 Security Notes

- Remove sensitive data from `config.json` before deployment
- Use environment variables for secrets
- Enable HTTPS in production

## 📞 Support

For deployment issues:
- Check Streamlit documentation: https://docs.streamlit.io
- Community forum: https://discuss.streamlit.io
- Create an issue in the GitHub repository
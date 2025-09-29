# Streamlit Community Cloud Deployment

## Prerequisites
- GitHub account
- Streamlit account (free at streamlit.io)

## Steps

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Kerala Flood Prediction App"
   git branch -M main
   git remote add origin https://github.com/yourusername/kerala-flood-prediction.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Connect your GitHub account
   - Select repository: `yourusername/kerala-flood-prediction`
   - Set main file: `app.py`
   - Click "Deploy!"

3. **Configuration**
   - App will automatically use `.streamlit/config.toml`
   - No additional configuration needed

## Advantages
- ✅ Free hosting
- ✅ Automatic updates from GitHub
- ✅ HTTPS enabled
- ✅ Custom domain support
- ✅ Easy sharing

## Limitations
- Resource limits (1GB RAM)
- May sleep after inactivity
- Public repositories preferred

## URL Format
Your app will be available at:
`https://yourusername-kerala-flood-prediction-app-streamlit-app.streamlit.app`
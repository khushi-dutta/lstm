@echo off
echo 🌊 Kerala Flood Prediction System - Windows Setup 🌊
echo ================================================

echo.
echo 📋 Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
) else (
    python --version
    echo ✅ Python found!
)

echo.
echo 📦 Installing required packages...
echo This may take a few minutes...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install packages
    pause
    exit /b 1
)

echo.
echo 📦 Installing additional dashboard dependencies...
pip install streamlit streamlit-folium
if errorlevel 1 (
    echo ⚠️ Warning: Dashboard dependencies failed to install
    echo Dashboard may not work properly
)

echo.
echo ✅ Installation completed!
echo.
echo 🚀 What would you like to do?
echo 1. Run complete demo
echo 2. Train model only
echo 3. Launch dashboard
echo 4. Start monitoring system
echo 5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo 📊 Running complete demo...
    python demo.py
) else if "%choice%"=="2" (
    echo.
    echo 🧠 Training LSTM model...
    python flood_prediction_lstm.py
) else if "%choice%"=="3" (
    echo.
    echo 📊 Launching dashboard...
    echo Open your browser to http://localhost:8501
    streamlit run dashboard.py
) else if "%choice%"=="4" (
    echo.
    echo 🚨 Starting monitoring system...
    python real_time_alert_system.py
) else if "%choice%"=="5" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice. Please run the script again.
)

echo.
echo Press any key to exit...
pause >nul
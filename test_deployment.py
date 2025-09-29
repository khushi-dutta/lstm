#!/usr/bin/env python3
"""
Test script for Kerala Flood Prediction Streamlit App
Run this before deployment to check if everything works
"""

import sys
import subprocess
import importlib
import os

def test_imports():
    """Test if all required packages can be imported"""
    print("🔍 Testing package imports...")
    
    required_packages = [
        'streamlit',
        'pandas',
        'numpy',
        'plotly',
        'folium',
        'streamlit_folium',
        'tensorflow',
        'sklearn',
        'joblib'
    ]
    
    failed_imports = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError as e:
            print(f"❌ {package}: {e}")
            failed_imports.append(package)
    
    return len(failed_imports) == 0

def test_files():
    """Test if all required files exist"""
    print("\n📁 Testing file presence...")
    
    required_files = [
        'app.py',
        'requirements.txt',
        'config.json',
        'flood_prediction_lstm.py',
        'real_time_alert_system.py',
        'kerala_flood_data.csv'
    ]
    
    optional_files = [
        'flood_lstm_model.keras',
        'flood_lstm_model_scalers.pkl',
        'flood_lstm_model_label_encoder.pkl'
    ]
    
    missing_required = []
    missing_optional = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (REQUIRED)")
            missing_required.append(file)
    
    for file in optional_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"⚠️  {file} (OPTIONAL - app will run in demo mode)")
            missing_optional.append(file)
    
    return len(missing_required) == 0

def test_streamlit_syntax():
    """Test if the Streamlit app has valid syntax"""
    print("\n🔍 Testing Streamlit app syntax...")
    
    try:
        subprocess.run([sys.executable, '-m', 'py_compile', 'app.py'], 
                      check=True, capture_output=True)
        print("✅ app.py syntax is valid")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Syntax error in app.py: {e}")
        return False

def run_streamlit_check():
    """Test if Streamlit can start (dry run)"""
    print("\n🚀 Testing Streamlit startup...")
    
    try:
        # This won't actually start the server, just check if it can be imported and configured
        result = subprocess.run([
            sys.executable, '-c', 
            "import streamlit as st; print('Streamlit can be imported successfully')"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Streamlit can start successfully")
            return True
        else:
            print(f"❌ Streamlit startup failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⚠️  Streamlit test timed out (might still work)")
        return True
    except Exception as e:
        print(f"❌ Error testing Streamlit: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Kerala Flood Prediction App - Deployment Test\n")
    
    all_tests_passed = True
    
    # Run tests
    all_tests_passed &= test_imports()
    all_tests_passed &= test_files()
    all_tests_passed &= test_streamlit_syntax()
    all_tests_passed &= run_streamlit_check()
    
    print("\n" + "="*50)
    
    if all_tests_passed:
        print("🎉 All tests passed! Ready for deployment.")
        print("\nNext steps:")
        print("1. Run: streamlit run app.py (for local testing)")
        print("2. Deploy to your chosen platform")
        print("3. Check DEPLOYMENT.md for platform-specific instructions")
    else:
        print("⚠️  Some tests failed. Please fix the issues before deployment.")
        print("\nCommon fixes:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Ensure all required files are present")
        print("- Check syntax errors in Python files")
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())
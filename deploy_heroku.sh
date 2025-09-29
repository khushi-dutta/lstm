#!/bin/bash

# Heroku Deployment Script
echo "🚀 Deploying Kerala Flood Prediction App to Heroku..."

# Login to Heroku
echo "Please login to Heroku:"
heroku login

# Create Heroku app
echo "Creating Heroku app..."
APP_NAME="kerala-flood-prediction-$(date +%s)"
heroku create $APP_NAME

# Set buildpacks
heroku buildpacks:set heroku/python -a $APP_NAME

# Deploy
echo "Deploying to Heroku..."
git add .
git commit -m "Deploy to Heroku"
git push heroku main

# Open app
echo "🎉 Deployment complete! Opening app..."
heroku open -a $APP_NAME

echo "App URL: https://$APP_NAME.herokuapp.com"
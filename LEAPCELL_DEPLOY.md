# Leapcell Deployment Guide

## Prerequisites
1. Sign up at [leapcell.io](https://leapcell.io)
2. Connect your GitHub account

## Deployment Steps

1. **Create New Project**
   - Choose "Deploy from GitHub"
   - Select your QuickKart repository
   - Choose the `deployment` branch

2. **Configuration**
   - **Framework**: Docker
   - **Build Command**: (auto-detected from Dockerfile)
   - **Start Command**: (auto-detected from Dockerfile)

3. **Environment Variables**
   - Add `GOOGLE_MAPS_API_KEY` with your API key
   - Add `FLASK_ENV=production`

4. **Deploy**
   - Click Deploy
   - Leapcell will build the Docker image and deploy

## Features
✅ Playwright scraper support  
✅ Automatic Docker builds  
✅ Free tier available  
✅ Easy GitHub integration  

## Expected Behavior
- App will be available at your Leapcell URL
- Scrapers should work properly with Playwright
- Database will be initialized automatically
# Render Deployment Guide

## Quick Deploy to Render

### Option 1: Using render.yaml (Recommended)
1. Connect your GitHub repository to Render
2. Select the `deployment` branch
3. Render will automatically detect the `render.yaml` file
4. Set your environment variables in Render dashboard:
   - `GOOGLE_MAPS_API_KEY` (your Google Maps API key)

### Option 2: Manual Setup
1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Use these settings:
   - **Branch**: `deployment`
   - **Build Command**: `./build.sh`
   - **Start Command**: `./start.sh`
   - **Environment**: `Docker`
   - **Dockerfile Path**: `./Dockerfile`

### Environment Variables
Add these in your Render dashboard:
- `GOOGLE_MAPS_API_KEY`: Your Google Maps API key
- `FLASK_ENV`: `production`
- `PYTHONPATH`: `/app`

### Features
- ✅ Production-ready Gunicorn server
- ✅ Playwright web scraping support
- ✅ SQLite database auto-initialization
- ✅ Health checks enabled
- ✅ Optimized for Render's infrastructure

### Port Configuration
- Render automatically assigns port 10000
- The app is configured to use this port by default
- Health check endpoint: `/`

### Performance Settings
- 1 worker with 4 threads (optimized for Render's free tier)
- 120-second timeout for web scraping operations
- Keep-alive connections for better performance
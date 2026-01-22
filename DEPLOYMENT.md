# Deploying QuickKart to Render (Free)

This project is configured for deployment on [Render](https://render.com), which offers a free tier for web services and native Docker support.

> **Note:** The `deployment` branch contains the necessary `Dockerfile` and configuration for production. ALWAYS deploy from this branch.

## Prerequisites

1.  **GitHub Repo**: Ensure your code is pushed to GitHub (specifically the `deployment` branch).
2.  **Render Account**: Sign up at [dashboard.render.com](https://dashboard.render.com).

## Step-by-Step Deployment Guide

### 1. Create a New Web Service
1.  Click **New +** button in the Render dashboard.
2.  Select **Web Service**.
3.  Connect your GitHub repository (`QuickKart`).

### 2. Configure the Service
Use the following settings:

| Setting | Value | Note |
| :--- | :--- | :--- |
| **Name** | `quickkart` | Or any name you like |
| **Branch** | `deployment` | **CRITICAL**: Select the deployment branch |
| **Runtime** | `Docker` | It should auto-detect the Dockerfile |
| **Region** | *Nearest to you* | e.g., Singapore or Frankfurt |
| **Plan** | **Free** | 512MB RAM, 0.1 CPU |

### 3. Environment Variables
You MUST set the API key for the app to work.
1.  Scroll down to the **Environment Variables** section.
2.  Click **Add Environment Variable**.
3.  **Key**: `GOOGLE_MAPS_API_KEY`
4.  **Value**: `Your_Actual_Google_Maps_Key` (Copy from your `.env` file)

### 4. Deploy
1.  Click **Create Web Service**.
2.  Render will start building the Docker image. This may take 5-10 minutes for the first build as it installs browsers.
3.  Once finished, you will see a green **Live** badge.

## Important Notes for Free Tier

- **Spin Down**: "Free" services go to sleep after 15 minutes of inactivity. The first request after sleep will take ~50 seconds to load.
- **RAM Limit**: The free tier has 512MB RAM.
    - *Potential Issue*: Running multiple Playwright browsers concurrently might hit this limit.
    - *Solution*: If the app crashes, consider upgrading to the "Starter" plan ($7/mo) or reducing the worker count in `gunicorn.conf.py` to `2` or `1`.

## Troubleshooting

- **Build Failures**: Check the "Logs" tab in Render for error messages.
- **Application Error**: If the URL shows an error, check the Logs. It's often due to missing Environment Variables or memory limits.

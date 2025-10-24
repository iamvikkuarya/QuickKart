# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for Playwright and other packages
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and dependencies as root
RUN playwright install --with-deps chromium

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p static/css static/js static/assets

# Create a non-root user for security
RUN useradd -m -u 1000 appuser

# Set proper permissions for playwright cache
RUN mkdir -p /home/appuser/.cache && chown -R appuser:appuser /home/appuser/.cache

# Change ownership of app directory
RUN chown -R appuser:appuser /app

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Switch to non-root user
USER appuser

# Install browsers again as the appuser to ensure proper permissions
RUN playwright install chromium

# Run the application (Railway expects to use PORT env var)
CMD ["sh", "-c", "python -c \"import os; from app import app; app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))\""]
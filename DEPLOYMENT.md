# QuickKart Deployment Guide

This guide covers deploying QuickKart to production environments.

## Prerequisites

- Docker (for containerized deployment)
- Python 3.11+
- 2GB+ RAM (Playwright browsers require memory)
- Google Maps API key

## Environment Variables

Create a `.env` file with:

```bash
GOOGLE_MAPS_API_KEY=your_actual_api_key_here
FLASK_ENV=production
PORT=5000  # Optional, defaults to 5000
```

## Docker Deployment

### Build the Image

```bash
docker build -t quickkart .
```

### Run the Container

```bash
docker run -d \
  -p 5000:5000 \
  -e GOOGLE_MAPS_API_KEY=your_key \
  -e PORT=5000 \
  --name quickkart \
  quickkart
```

### Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  quickkart:
    build: .
    ports:
      - "5000:5000"
    environment:
      - GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}
      - FLASK_ENV=production
      - PORT=5000
    restart: unless-stopped
    volumes:
      - ./product.db:/app/product.db
```

Run with:
```bash
docker-compose up -d
```

## Manual Deployment

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Initialize Database

```bash
python -c "from src.core.db import init_db; init_db()"
```

### 3. Run with Gunicorn

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app:app
```

## Platform-Specific Deployment

### Render

1. Connect your GitHub repository
2. Set build command: `pip install -r requirements.txt && playwright install chromium`
3. Set start command: `./start.sh`
4. Add environment variable: `GOOGLE_MAPS_API_KEY`
5. Choose instance with at least 2GB RAM

### Railway

1. Connect GitHub repository
2. Add environment variable: `GOOGLE_MAPS_API_KEY`
3. Railway will auto-detect and use Dockerfile
4. Ensure instance has 2GB+ RAM

### Heroku

1. Create `Procfile`:
```
web: ./start.sh
```

2. Add buildpacks:
```bash
heroku buildpacks:add heroku/python
heroku buildpacks:add https://github.com/mxschmitt/heroku-playwright-buildpack
```

3. Set config vars:
```bash
heroku config:set GOOGLE_MAPS_API_KEY=your_key
```

## Performance Optimization

### Memory Management

- Playwright browsers use ~200-300MB per instance
- Recommended: 2GB RAM minimum
- Use `--workers 2` for Gunicorn (adjust based on available RAM)

### Caching

- Search results cached for 5 minutes
- ETA data cached for 5 minutes
- Location cached for 7 days (client-side)

### Timeouts

- Scraper timeout: 15 seconds
- ETA timeout: 20-25 seconds
- Gunicorn timeout: 120 seconds

## Monitoring

### Health Check Endpoint

```bash
curl http://localhost:5000/
```

### Logs

```bash
# Docker
docker logs quickkart

# Manual
tail -f gunicorn.log
```

## Troubleshooting

### Playwright Installation Issues

```bash
# Install system dependencies
apt-get update && apt-get install -y \
    libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2

# Reinstall browsers
playwright install chromium --with-deps
```

### Memory Issues

- Reduce Gunicorn workers: `--workers 1`
- Increase timeout: `--timeout 180`
- Use headless mode (already enabled)

### Database Issues

```bash
# Reset database
rm product.db
python -c "from src.core.db import init_db; init_db()"
```

## Security Considerations

1. **Never commit `.env` file** - Contains API keys
2. **Use HTTPS in production** - Configure reverse proxy (nginx/Caddy)
3. **Rate limiting** - Consider adding rate limiting for API endpoints
4. **CORS** - Configure CORS if needed for external access

## Scaling

For high traffic:

1. Use Redis for caching instead of in-memory
2. Increase Gunicorn workers based on CPU cores
3. Use load balancer for multiple instances
4. Consider separate scraper service

## Updates

To update deployment:

```bash
git pull origin deployment
docker-compose down
docker-compose build
docker-compose up -d
```

## Support

For issues, check:
- GitHub Issues: https://github.com/iamvikkuarya/QuickKart/issues
- Logs: Check application and container logs
- Health: Verify all scrapers are working

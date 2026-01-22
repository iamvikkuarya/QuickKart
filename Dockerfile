# Use the official Playwright Python image which includes browsers
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

# Set the working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn explicitly if not in requirements (it is now, but safe to have)
RUN pip install gunicorn

# Copy the rest of the application
COPY . .

# Expose port (default Flask/Gunicorn port or $PORT)
ENV PORT=5000
EXPOSE $PORT

# Run the application
# We use a shell script to allow for additional startup logic if needed
COPY start.sh .
RUN chmod +x start.sh

CMD ["./start.sh"]
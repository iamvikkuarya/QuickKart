#!/bin/bash
# start.sh

# Ensure browsers are installed (redundant with the base image but safe)
# playwright install

# Start Gunicorn
# Access logs to stdout/stderr
exec gunicorn wsgi:app \
    --bind 0.0.0.0:$PORT \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
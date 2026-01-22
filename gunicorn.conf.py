# Gunicorn configuration settings
import multiprocessing

workers = 4  # Adjust based on available RAM/CPU
timeout = 120  # Increased timeout for scrapers (default is 30s)
bind = "0.0.0.0:$PORT"
accesslog = "-"
errorlog = "-"

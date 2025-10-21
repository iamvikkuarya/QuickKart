# db.py
import sqlite3
import os
import tempfile

# Use /tmp for database in production, current directory for local
if os.environ.get("FLASK_ENV") == "production":
    DB_NAME = "/tmp/product.db"
else:
    DB_NAME = "product.db"

def init_db():
    try:
        # Ensure directory exists
        db_dir = os.path.dirname(DB_NAME)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # raw scraped products (platform-specific)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            quantity TEXT,
            platform TEXT,
            price TEXT,
            product_url TEXT,
            image_url TEXT,
            in_stock BOOLEAN,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        conn.close()
        print(f"✅ Database initialized at {DB_NAME}")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def get_db_connection():
    """Get database connection, initialize if needed"""
    try:
        if not os.path.exists(DB_NAME):
            init_db()
        return sqlite3.connect(DB_NAME)
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
        # Return in-memory database as fallback
        return sqlite3.connect(":memory:")

if __name__ == "__main__":
    init_db()
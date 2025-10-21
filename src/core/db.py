# db.py
import sqlite3

DB_NAME = "product.db"

def init_db():
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

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized")
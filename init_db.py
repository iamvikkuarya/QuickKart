import sqlite3

def initialize_db():
    conn = sqlite3.connect("products.db")  # This creates the file if it doesn't exist
    cursor = conn.cursor()

    # Create the table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_search_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_term TEXT NOT NULL,
            platform TEXT NOT NULL,
            product_name TEXT NOT NULL,
            product_price TEXT,
            product_quantity TEXT,
            product_delivery_time TEXT,
            product_image TEXT,
            product_url TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_db()

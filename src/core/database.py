"""
Database management module for QuickCompare.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
from contextlib import contextmanager


class DatabaseManager:
    """Manages SQLite database operations for the application."""
    
    DEFAULT_DB_NAME = "product.db"
    
    def __init__(self, db_name: str = None):
        self.db_name = db_name or self.DEFAULT_DB_NAME
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_name)
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize the database with required tables."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            
            # Raw scraped products (platform-specific)
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
            
            # Create indexes for better performance
            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_products_platform 
            ON products(platform)
            """)
            
            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_products_scraped_at 
            ON products(scraped_at)
            """)
            
            conn.commit()
    
    def save_products(self, products: List[Dict[str, Any]]):
        """Save raw scraper products into SQLite."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            for p in products:
                try:
                    cur.execute("""
                        INSERT INTO products (name, quantity, platform, price, product_url, image_url, in_stock)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        p.get("name"),
                        p.get("quantity"),
                        p.get("platform"),
                        p.get("price"),
                        p.get("product_url"),
                        p.get("image_url"),
                        int(p.get("in_stock", True))
                    ))
                except Exception as e:
                    print("⚠️ DB insert error:", e, p)
            conn.commit()
    
    def get_products_by_platform(self, platform: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get products by platform."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM products 
                WHERE platform = ? 
                ORDER BY scraped_at DESC 
                LIMIT ?
            """, (platform, limit))
            
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def get_recent_products(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """Get products scraped within the last N hours."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM products 
                WHERE scraped_at > datetime('now', '-{} hours')
                ORDER BY scraped_at DESC 
                LIMIT ?
            """.format(hours), (limit,))
            
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    
    def cleanup_old_products(self, days: int = 7):
        """Remove products older than N days."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                DELETE FROM products 
                WHERE scraped_at < datetime('now', '-{} days')
            """.format(days))
            deleted = cur.rowcount
            conn.commit()
            return deleted


# Global instance for backward compatibility
_db_manager = DatabaseManager()

# Legacy functions for backward compatibility
DB_NAME = _db_manager.DEFAULT_DB_NAME

def init_db():
    """Legacy function for backward compatibility."""
    _db_manager.init_db()

def save_products(products: List[Dict[str, Any]]):
    """Legacy function for backward compatibility."""
    _db_manager.save_products(products)


if __name__ == "__main__":
    db = DatabaseManager()
    db.init_db()
    print("✅ Database initialized")
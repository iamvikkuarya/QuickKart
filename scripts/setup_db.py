#!/usr/bin/env python3
"""
Database setup script for QuickCompare.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.database import DatabaseManager


def setup_database():
    """Initialize the database with all required tables."""
    print("🔧 Setting up QuickCompare database...")
    
    db = DatabaseManager()
    
    try:
        db.init_db()
        print(f"✅ Database initialized successfully: {db.db_name}")
        
        # Test database connection
        with db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM products")
            count = cur.fetchone()[0]
            print(f"📊 Current products in database: {count}")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False
    
    return True


def cleanup_old_data():
    """Clean up old product data."""
    print("🧹 Cleaning up old data...")
    
    db = DatabaseManager()
    
    try:
        deleted_count = db.cleanup_old_products(days=7)
        print(f"🗑️ Removed {deleted_count} old product records")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="QuickCompare database setup")
    parser.add_argument(
        "--cleanup", 
        action="store_true", 
        help="Also cleanup old data (older than 7 days)"
    )
    
    args = parser.parse_args()
    
    # Setup database
    success = setup_database()
    
    if success and args.cleanup:
        cleanup_old_data()
    
    if success:
        print("🎉 Database setup completed successfully!")
    else:
        print("💥 Database setup failed!")
        sys.exit(1)
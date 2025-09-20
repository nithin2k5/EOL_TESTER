#!/usr/bin/env python3
"""
Test .env file loading and database connection
"""

import os
from dotenv import load_dotenv
import mysql.connector

def test_env_and_db():
    """Test environment loading and database connection"""
    print("🔧 Testing .env file and database connection...")

    # Load environment variables
    load_dotenv()
    print("\n✅ Environment variables loaded from .env:")

    # Check database config
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', '12345'),
        'database': os.getenv('DB_NAME', 'EOL'),
        'raise_on_warnings': True
    }

    print(f"   Host: {db_config['host']}:{db_config['port']}")
    print(f"   User: {db_config['user']}")
    print(f"   Database: {db_config['database']}")
    print(f"   Password length: {len(db_config['password'])} characters")

    # Test connection
    print("\n🔍 Testing database connection...")
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Test query
        cursor.execute("SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = %s", (db_config['database'],))
        result = cursor.fetchone()

        print("✅ Database connection successful!")
        print(f"   Tables in {db_config['database']}: {result[0]}")

        # List table names
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        print(f"   Table names: {table_names}")

        cursor.close()
        connection.close()

        return True

    except mysql.connector.Error as err:
        print(f"❌ Database connection failed: {err}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_env_and_db()

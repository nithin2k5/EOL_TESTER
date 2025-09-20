#!/usr/bin/env python3
"""
Debug MySQL connection issue
"""

import mysql.connector

def test_connection_detailed():
    """Test connection with detailed error information"""
    try:
        print("🔍 Testing connection to MySQL EOL database...")

        # Test 1: Connect without database
        print("\n1. Testing connection without database...")
        config_no_db = {
            'host': 'localhost',
            'user': 'root',
            'password': '12345',
            'raise_on_warnings': True
        }

        conn = mysql.connector.connect(**config_no_db)
        print("✅ Connected without database")

        cursor = conn.cursor()
        cursor.execute("SELECT USER(), DATABASE(), VERSION()")
        result = cursor.fetchone()
        print(f"   User: {result[0]}")
        print(f"   Current DB: {result[1]}")
        print(f"   Version: {result[2]}")

        # Test 2: Check databases
        print("\n2. Checking available databases...")
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        db_names = [db[0] for db in databases]
        print(f"   Available databases: {db_names}")

        if 'eol' in [db.lower() for db in db_names]:
            print("✅ EOL database exists")
        else:
            print("❌ EOL database not found")

        # Test 3: Check permissions for EOL database
        print("\n3. Checking permissions...")
        cursor.execute("SHOW GRANTS FOR 'root'@'localhost'")
        grants = cursor.fetchall()
        print("   User grants:")
        for grant in grants:
            print(f"   {grant[0]}")

        # Test 4: Try to connect to EOL database
        print("\n4. Testing connection to EOL database...")
        config_with_db = {
            'host': 'localhost',
            'user': 'root',
            'password': '12345',
            'database': 'EOL',
            'raise_on_warnings': True
        }

        try:
            conn_eol = mysql.connector.connect(**config_with_db)
            print("✅ Successfully connected to EOL database!")

            cursor_eol = conn_eol.cursor()
            cursor_eol.execute("SHOW TABLES")
            tables = cursor_eol.fetchall()
            table_names = [table[0] for table in tables]
            print(f"   Tables in EOL database: {table_names}")

            cursor_eol.close()
            conn_eol.close()

        except mysql.connector.Error as err:
            print(f"❌ Failed to connect to EOL database: {err}")
            print(f"   Error code: {err.errno}")
            print(f"   SQL State: {err.sqlstate}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection_detailed()

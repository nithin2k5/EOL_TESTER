#!/usr/bin/env python3
"""
Test script for the EOL Tester C# implementation
Tests database connectivity and basic functionality
"""

import mysql.connector
from mysql.connector import Error
import sys
import os

def test_database_connection():
    """Test MySQL database connection"""
    print("Testing MySQL database connection...")
    
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'nk446420',
        'database': 'EOL'
    }
    
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("✅ Database connection successful!")
            
            cursor = connection.cursor()
            
            # Test table creation
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"📊 Found {len(tables)} tables in database")
            
            for table in tables:
                print(f"   - {table[0]}")
            
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_configuration_files():
    """Test if configuration files exist"""
    print("\nTesting configuration files...")
    
    config_files = [
        "txt_files/InputSensors.txt",
        "txt_files/ProcessStatus.txt", 
        "txt_files/EmployeeCodes.txt",
        "txt_files/HoldRegistersRead.txt",
        "txt_files/MachineOnPLCCoilAddress.txt",
        "txt_files/AlertOnPLCCoilAddress.txt"
    ]
    
    missing_files = []
    
    for file_path in config_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  {len(missing_files)} configuration files are missing")
        print("   The application will still work but may show warnings")
    else:
        print("\n✅ All configuration files found!")
    
    return len(missing_files) == 0

def test_eol_tester_import():
    """Test importing the EOL Tester class"""
    print("\nTesting EOL Tester import...")
    
    try:
        from test_console import EOLTesterGUI
        print("✅ EOLTesterGUI class imported successfully!")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 EOL Tester Implementation Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test database connection
    if test_database_connection():
        tests_passed += 1
    
    # Test configuration files
    if test_configuration_files():
        tests_passed += 1
    
    # Test import
    if test_eol_tester_import():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! EOL Tester implementation is ready!")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

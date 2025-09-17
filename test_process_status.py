#!/usr/bin/env python3
"""
Simple test script to verify the process status monitoring and database integration functionality
"""

import os
import sys
import time
from datetime import datetime

def test_mock_database():
    """Test mock database functionality"""
    print("🧪 Testing Mock Database...")
    try:
        from mock_database import MockDatabase
        
        with MockDatabase() as db:
            # Test data
            test_data = {
                "LOT_NUMBER": f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "PART_NUMBER": "ALC001_TEST",
                "EMP_CODE": "TEST_EMP",
                "TEST_DATE": datetime.now().strftime("%Y-%m-%d"),
                "TEST_TIME": datetime.now().strftime("%H:%M:%S"),
                "L1_VALUE": 12.5,
                "L2_VALUE": 10.2,
                "L3_VALUE": 15.1,
                "L4_VALUE": 12.0,
                "P1_VALUE": 6.8,
                "P2_VALUE": 5.6,
                "P3_VALUE": 7.9,
                "P4_VALUE": 4.7,
                "OVERALL_RESULT": "PASS",
                "FAILED_DEVICES": "",
                "TEST_DURATION": 45.5
            }
            
            # Insert test result
            success = db.insert_test_result(test_data)
            if success:
                print("✅ Test result inserted successfully")
            else:
                print("❌ Failed to insert test result")
                return False
            
            # Get test history
            history = db.get_test_history(limit=5)
            if history:
                print(f"✅ Retrieved {len(history)} test records")
                print(f"   Latest record: {history[0]['LOT_NUMBER']} - {history[0]['OVERALL_RESULT']}")
            else:
                print("⚠️ No test history found")
            
            return True
            
    except Exception as e:
        print(f"❌ Mock database test failed: {e}")
        return False

def test_process_status_file():
    """Test process status file reading"""
    print("\n🧪 Testing Process Status File...")
    try:
        process_file = "txt_files/ProcessStatus.txt"
        if os.path.exists(process_file):
            with open(process_file, 'r') as f:
                content = f.read().strip()
                if content:
                    addresses = [addr.strip() for addr in content.split(',') if addr.strip()]
                    print(f"✅ Found {len(addresses)} process addresses: {addresses}")
                    return True
                else:
                    print("⚠️ ProcessStatus.txt is empty")
                    return False
        else:
            print(f"❌ ProcessStatus.txt not found at {process_file}")
            return False
            
    except Exception as e:
        print(f"❌ Process status file test failed: {e}")
        return False

def test_environment_setup():
    """Test environment configuration"""
    print("\n🧪 Testing Environment Setup...")
    try:
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        # Check key environment variables
        machine_id = os.getenv('MACHINE_ID', 'NOT_SET')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_name = os.getenv('DB_NAME', 'EOL')
        
        print(f"✅ Machine ID: {machine_id}")
        print(f"✅ Database Host: {db_host}")
        print(f"✅ Database Name: {db_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment setup test failed: {e}")
        return False

def test_imports():
    """Test critical imports"""
    print("\n🧪 Testing Critical Imports...")
    try:
        # Test tkinter
        import tkinter as tk
        print("✅ tkinter imported successfully")
        
        # Test PIL
        from PIL import Image, ImageTk
        print("✅ PIL imported successfully")
        
        # Test mysql connector
        import mysql.connector
        print("✅ mysql.connector imported successfully")
        
        # Test pymodbus (should handle gracefully if missing)
        try:
            from pymodbus.client.serial import ModbusSerialClient
            print("✅ pymodbus imported successfully")
        except ImportError:
            print("⚠️ pymodbus not available (will use simulation mode)")
        
        # Test dotenv
        from dotenv import load_dotenv
        print("✅ python-dotenv imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def simulate_process_cycle():
    """Simulate a complete process cycle"""
    print("\n🧪 Simulating Process Cycle...")
    try:
        # Simulate process steps
        process_steps = [
            "AUTO", "HOME", "1st PULL PASS", "1st PULL NG", 
            "2nd PULL PASS", "2nd PULL NG", "TEST RESULT PASS", "TEST RESULT NG"
        ]
        
        print("🔄 Simulating process steps:")
        for i, step in enumerate(process_steps):
            print(f"   Step {i+1}: {step}")
            time.sleep(0.5)  # Simulate step duration
            
        print("✅ Process cycle simulation completed")
        
        # Simulate test result storage
        from mock_database import MockDatabase
        with MockDatabase() as db:
            test_data = {
                "LOT_NUMBER": f"SIM_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "PART_NUMBER": "SIMULATION_TEST",
                "EMP_CODE": "SIM_EMP",
                "TEST_DATE": datetime.now().strftime("%Y-%m-%d"),
                "TEST_TIME": datetime.now().strftime("%H:%M:%S"),
                "L1_VALUE": 11.2,
                "L2_VALUE": 9.8,
                "L3_VALUE": 14.5,
                "L4_VALUE": 11.8,
                "P1_VALUE": 6.2,
                "P2_VALUE": 5.1,
                "P3_VALUE": 7.4,
                "P4_VALUE": 4.3,
                "OVERALL_RESULT": "PASS",
                "FAILED_DEVICES": "",
                "TEST_DURATION": 42.3
            }
            
            success = db.insert_test_result(test_data)
            if success:
                print("✅ Simulated test result stored successfully")
                return True
            else:
                print("❌ Failed to store simulated test result")
                return False
                
    except Exception as e:
        print(f"❌ Process cycle simulation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 EOL Tester Functionality Test Suite")
    print("=" * 50)
    
    test_results = []
    
    # Run tests
    test_results.append(("Environment Setup", test_environment_setup()))
    test_results.append(("Critical Imports", test_imports()))
    test_results.append(("Process Status File", test_process_status_file()))
    test_results.append(("Mock Database", test_mock_database()))
    test_results.append(("Process Cycle Simulation", simulate_process_cycle()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print("-" * 50)
    print(f"Total: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! The EOL Tester is ready to run.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Please review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)







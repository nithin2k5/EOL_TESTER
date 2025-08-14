#!/usr/bin/env python3
"""
Simple Test Runner for EOL Testing System
Run this script to execute all tests
"""

import sys
import os
import time
from datetime import datetime

def print_banner():
    """Print a nice banner for the test runner"""
    print("=" * 70)
    print("🧪 EOL TESTING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    required_files = [
        "mock_data.py",
        "mock_database.py", 
        "mock_plc.py",
        "test_eol_functionality.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files found")
    return True

def run_individual_tests():
    """Run individual component tests"""
    print("\n🔧 Running individual component tests...")
    
    # Test mock data
    try:
        print("  Testing mock_data.py...")
        import mock_data
        print("  ✅ mock_data.py imported successfully")
    except Exception as e:
        print(f"  ❌ mock_data.py failed: {e}")
        return False
    
    # Test mock database
    try:
        print("  Testing mock_database.py...")
        import mock_database
        print("  ✅ mock_database.py imported successfully")
    except Exception as e:
        print(f"  ❌ mock_database.py failed: {e}")
        return False
    
    # Test mock PLC
    try:
        print("  Testing mock_plc.py...")
        import mock_plc
        print("  ✅ mock_plc.py imported successfully")
    except Exception as e:
        print(f"  ❌ mock_plc.py failed: {e}")
        return False
    
    print("✅ All individual component tests passed")
    return True

def run_unit_tests():
    """Run the comprehensive unit test suite"""
    print("\n🧪 Running comprehensive unit test suite...")
    
    try:
        from test_eol_functionality import run_all_tests
        success = run_all_tests()
        return success
    except Exception as e:
        print(f"❌ Unit test suite failed: {e}")
        return False

def run_quick_demo():
    """Run a quick demonstration of the system"""
    print("\n🎬 Running quick system demonstration...")
    
    try:
        # Import mock components
        from mock_data import MOCK_EMPLOYEE_CODES, MOCK_PART_SPECIFICATIONS
        from mock_database import get_mock_database
        from mock_plc import get_mock_plc
        
        # Initialize components
        db = get_mock_database()
        plc = get_mock_plc()
        
        print("  🔧 Components initialized")
        
        # Demo employee validation
        emp_code = MOCK_EMPLOYEE_CODES[0]
        emp_result = db.validate_employee_code(emp_code)
        print(f"  👤 Employee validation: {emp_code} -> {'Valid' if emp_result['valid'] else 'Invalid'}")
        
        # Demo part selection
        part_num = list(MOCK_PART_SPECIFICATIONS.keys())[0]
        part_specs = db.get_part_specifications(part_num)
        print(f"  📦 Part selection: {part_num} -> {part_specs['model_name'] if part_specs else 'Not found'}")
        
        # Demo PLC connection
        plc.connect()
        print(f"  🔌 PLC connection: {'Connected' if plc.is_socket_open() else 'Failed'}")
        
        # Demo PLC operations
        result = plc.write_coil(100, True)
        print(f"  🔧 PLC coil write: {'Success' if not result.isError() else 'Failed'}")
        
        # Demo process simulation
        plc.start_process_simulation()
        time.sleep(2)
        status = plc.get_process_status()
        print(f"  🚀 Process simulation: Step {status['step'] + 1}/{len(status['coils'])}")
        
        # Cleanup
        plc.stop_process_simulation()
        plc.disconnect()
        db.close()
        
        print("  ✅ Quick demo completed successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ Quick demo failed: {e}")
        return False

def main():
    """Main test runner function"""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Cannot run tests - missing dependencies")
        sys.exit(1)
    
    # Run individual tests
    if not run_individual_tests():
        print("\n❌ Individual component tests failed")
        sys.exit(1)
    
    # Ask user what to run
    print("\n📋 What would you like to run?")
    print("1. Quick system demonstration")
    print("2. Comprehensive unit test suite")
    print("3. Both")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                success = run_quick_demo()
                break
            elif choice == "2":
                success = run_unit_tests()
                break
            elif choice == "3":
                print("\n🔄 Running both quick demo and unit tests...")
                demo_success = run_quick_demo()
                test_success = run_unit_tests()
                success = demo_success and test_success
                break
            elif choice == "4":
                print("\n👋 Exiting test runner")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
        except KeyboardInterrupt:
            print("\n\n👋 Test runner interrupted by user")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
    
    # Print final results
    print("\n" + "=" * 70)
    if success:
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("✅ The EOL testing system is working correctly")
    else:
        print("⚠️ SOME TESTS FAILED")
        print("❌ Please check the error messages above")
    print("=" * 70)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

"""
Comprehensive Test Suite for EOL Testing System
This file tests all the EOL testing functionality using mock data and simulators
"""

import unittest
import time
import threading
from datetime import datetime, date
import tkinter as tk
from unittest.mock import patch, MagicMock

# Import mock components
from mock_data import (
    MOCK_EMPLOYEE_CODES, MOCK_PART_SPECIFICATIONS, MOCK_PLC_REGISTERS,
    MOCK_LOADCELL_DATA, MOCK_POSITION_DATA, MOCK_TEST_RESULTS,
    get_mock_loadcell_value, get_mock_position_value, get_mock_test_result,
    generate_mock_lot_number, get_mock_process_status
)
from mock_database import MockDatabase, get_mock_database, reset_mock_database
from mock_plc import MockPLCClient, get_mock_plc, reset_mock_plc

# Import the main EOL testing class
try:
    from test_console import EOLTesterGUI
except ImportError:
    print("⚠️ Warning: test_console.py not found. Some tests may be skipped.")
    EOLTesterGUI = None


class TestEOLFunctionality(unittest.TestCase):
    """Test suite for EOL testing functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        print("\n🚀 Setting up EOL Testing Test Environment...")
        
        # Initialize mock components
        cls.mock_db = get_mock_database()
        cls.mock_plc = get_mock_plc()
        
        # Create root window for GUI tests
        cls.root = tk.Tk()
        cls.root.withdraw()  # Hide window during tests
        
        print("✅ Test environment setup completed")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        print("\n🧹 Cleaning up test environment...")
        
        # Close mock components
        if cls.mock_db:
            cls.mock_db.close()
        if cls.mock_plc:
            cls.mock_plc.disconnect()
        
        # Destroy root window
        if cls.root:
            cls.root.destroy()
        
        print("✅ Test environment cleanup completed")
    
    def setUp(self):
        """Set up each individual test"""
        print(f"\n🧪 Running test: {self._testMethodName}")
        
        # Reset mock components to clean state
        reset_mock_database()
        reset_mock_plc()
        
        # Get fresh instances
        self.mock_db = get_mock_database()
        self.mock_plc = get_mock_plc()
    
    def tearDown(self):
        """Clean up after each test"""
        # Clean up is handled in setUp for next test
        pass
    
    def test_mock_database_initialization(self):
        """Test mock database initialization"""
        print("Testing mock database initialization...")
        
        # Test database connection
        self.assertIsNotNone(self.mock_db)
        self.assertTrue(hasattr(self.mock_db, 'connection'))
        self.assertTrue(hasattr(self.mock_db, 'cursor'))
        
        # Test sample data insertion
        test_history = self.mock_db.get_test_history(limit=5)
        self.assertGreater(len(test_history), 0)
        
        # Test part specifications
        part_specs = self.mock_db.get_part_specifications("ALC001")
        self.assertIsNotNone(part_specs)
        self.assertEqual(part_specs["part_number"], "ALC001")
        
        print("✅ Mock database initialization test passed")
    
    def test_mock_plc_initialization(self):
        """Test mock PLC initialization"""
        print("Testing mock PLC initialization...")
        
        # Test PLC client creation
        self.assertIsNotNone(self.mock_plc)
        self.assertFalse(self.mock_plc.is_connected)
        
        # Test connection
        self.assertTrue(self.mock_plc.connect())
        self.assertTrue(self.mock_plc.is_socket_open())
        
        # Test disconnection
        self.assertTrue(self.mock_plc.disconnect())
        self.assertFalse(self.mock_plc.is_socket_open())
        
        print("✅ Mock PLC initialization test passed")
    
    def test_employee_validation(self):
        """Test employee code validation"""
        print("Testing employee code validation...")
        
        # Test valid employee codes
        for emp_code in MOCK_EMPLOYEE_CODES[:3]:  # Test first 3 codes
            result = self.mock_db.validate_employee_code(emp_code)
            self.assertTrue(result["valid"])
            self.assertEqual(result["emp_code"], emp_code)
        
        # Test invalid employee code
        result = self.mock_db.validate_employee_code("INVALID123")
        self.assertFalse(result["valid"])
        self.assertIn("not found", result["message"])
        
        print("✅ Employee validation test passed")
    
    def test_part_specifications_retrieval(self):
        """Test part specifications retrieval"""
        print("Testing part specifications retrieval...")
        
        # Test all mock parts
        for part_num in MOCK_PART_SPECIFICATIONS.keys():
            part_specs = self.mock_db.get_part_specifications(part_num)
            
            self.assertIsNotNone(part_specs)
            self.assertEqual(part_specs["part_number"], part_num)
            self.assertIn("specifications", part_specs)
            self.assertIn("L1", part_specs["specifications"])
            self.assertIn("P1", part_specs["specifications"])
        
        # Test non-existent part
        part_specs = self.mock_db.get_part_specifications("NONEXISTENT")
        self.assertIsNone(part_specs)
        
        print("✅ Part specifications retrieval test passed")
    
    def test_lot_number_generation(self):
        """Test lot number generation"""
        print("Testing lot number generation...")
        
        # Test lot increment functionality
        date_str = "241201"
        machine_id = "001"
        
        # Get first increment
        increment1 = self.mock_db.get_next_lot_increment(date_str, machine_id)
        self.assertEqual(increment1, 1)
        
        # Get second increment
        increment2 = self.mock_db.get_next_lot_increment(date_str, machine_id)
        self.assertEqual(increment2, 2)
        
        # Test different machine
        increment_diff_machine = self.mock_db.get_next_lot_increment(date_str, "002")
        self.assertEqual(increment_diff_machine, 1)
        
        # Test different date
        increment_diff_date = self.mock_db.get_next_lot_increment("241130", machine_id)
        self.assertEqual(increment_diff_date, 1)
        
        print("✅ Lot number generation test passed")
    
    def test_plc_coil_operations(self):
        """Test PLC coil operations"""
        print("Testing PLC coil operations...")
        
        # Connect to PLC
        self.mock_plc.connect()
        
        # Test writing coils
        result = self.mock_plc.write_coil(100, True)  # M100
        self.assertFalse(result.isError())
        
        result = self.mock_plc.write_coil(101, False)  # M101
        self.assertFalse(result.isError())
        
        # Test reading coils
        result = self.mock_plc.read_coils(100, 2)
        self.assertFalse(result.isError())
        self.assertEqual(result._value, [True, False])
        
        # Test invalid coil address
        result = self.mock_plc.write_coil(999, True)
        self.assertTrue(result.isError())
        
        self.mock_plc.disconnect()
        
        print("✅ PLC coil operations test passed")
    
    def test_plc_register_operations(self):
        """Test PLC register operations"""
        print("Testing PLC register operations...")
        
        # Connect to PLC
        self.mock_plc.connect()
        
        # Test writing registers
        test_value = 123.45
        result = self.mock_plc.write_register(100, test_value)
        self.assertFalse(result.isError())
        
        # Test reading registers
        result = self.mock_plc.read_holding_registers(100, 1)
        self.assertFalse(result.isError())
        self.assertEqual(result._value[0], test_value)
        
        # Test reading multiple registers
        result = self.mock_plc.read_holding_registers(100, 3)
        self.assertFalse(result.isError())
        self.assertEqual(len(result._value), 3)
        
        # Test invalid register address
        result = self.mock_plc.write_register(999, 0)
        self.assertTrue(result.isError())
        
        self.mock_plc.disconnect()
        
        print("✅ PLC register operations test passed")
    
    def test_plc_process_simulation(self):
        """Test PLC process simulation"""
        print("Testing PLC process simulation...")
        
        # Connect to PLC
        self.mock_plc.connect()
        
        # Start process simulation
        self.mock_plc.start_process_simulation()
        
        # Wait for simulation to progress
        time.sleep(2)
        
        # Check process status
        status = self.mock_plc.get_process_status()
        self.assertIsNotNone(status)
        self.assertTrue(status["active"])
        self.assertGreater(status["step"], 0)
        
        # Stop simulation
        self.mock_plc.stop_process_simulation()
        
        # Wait for stop
        time.sleep(1)
        
        # Check if stopped
        status = self.mock_plc.get_process_status()
        self.assertFalse(status["active"])
        
        self.mock_plc.disconnect()
        
        print("✅ PLC process simulation test passed")
    
    def test_test_result_storage(self):
        """Test test result storage in database"""
        print("Testing test result storage...")
        
        # Create test data
        test_data = {
            "LOT_NUMBER": "2412010010003",
            "PART_NUMBER": "ALC001",
            "EMP_CODE": "EMP001",
            "TEST_DATE": "2024-12-01",
            "TEST_TIME": "11:00:00",
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
        success = self.mock_db.insert_test_result(test_data)
        self.assertTrue(success)
        
        # Verify insertion
        test_history = self.mock_db.get_test_history(limit=10)
        found = False
        for result in test_history:
            if result["LOT_NUMBER"] == test_data["LOT_NUMBER"]:
                found = True
                self.assertEqual(result["PART_NUMBER"], test_data["PART_NUMBER"])
                self.assertEqual(result["EMP_CODE"], test_data["EMP_CODE"])
                self.assertEqual(result["OVERALL_RESULT"], test_data["OVERALL_RESULT"])
                break
        
        self.assertTrue(found, "Test result not found in database")
        
        print("✅ Test result storage test passed")
    
    def test_mock_data_helpers(self):
        """Test mock data helper functions"""
        print("Testing mock data helper functions...")
        
        # Test load cell value generation
        l1_value = get_mock_loadcell_value("L1", 0)
        self.assertIn(l1_value, MOCK_LOADCELL_DATA["L1"])
        
        # Test position sensor value generation
        p1_value = get_mock_position_value("P1", 0)
        self.assertIn(p1_value, MOCK_POSITION_DATA["P1"])
        
        # Test test result generation
        pass_result = get_mock_test_result(pass_test=True, index=0)
        self.assertIn("L1", pass_result)
        self.assertIn("P1", pass_result)
        
        fail_result = get_mock_test_result(pass_test=False, index=0)
        self.assertIn("L1", fail_result)
        self.assertIn("P1", fail_result)
        
        # Test lot number generation
        lot_number = generate_mock_lot_number("241201", "001")
        self.assertTrue(lot_number.startswith("241201001"))
        
        # Test process status
        process_status = get_mock_process_status(0)
        self.assertIsNotNone(process_status)
        self.assertEqual(process_status["name"], "AUTO")
        
        print("✅ Mock data helper functions test passed")
    
    def test_plc_error_simulation(self):
        """Test PLC error simulation"""
        print("Testing PLC error simulation...")
        
        # Connect to PLC
        self.mock_plc.connect()
        
        # Simulate error
        self.mock_plc.simulate_error("E001")
        
        # Check error state
        status = self.mock_plc.get_process_status()
        self.assertTrue(status["coils"]["M106"])  # Error coil
        self.assertEqual(status["registers"]["D202"], 1)  # Error code
        
        # Clear error
        self.mock_plc.clear_error()
        
        # Check error cleared
        status = self.mock_plc.get_process_status()
        self.assertFalse(status["coils"]["M106"])
        self.assertEqual(status["registers"]["D202"], 0)
        
        self.mock_plc.disconnect()
        
        print("✅ PLC error simulation test passed")
    
    def test_database_connection_management(self):
        """Test database connection management"""
        print("Testing database connection management...")
        
        # Test context manager
        with MockDatabase() as db:
            self.assertIsNotNone(db)
            self.assertTrue(hasattr(db, 'connection'))
            
            # Test basic query
            result = db.fetch_one("SELECT COUNT(*) FROM TBL_EMPLOYEE_CODES")
            self.assertIsNotNone(result)
            self.assertGreater(result[0], 0)
        
        # Database should be closed automatically
        print("✅ Database connection management test passed")
    
    def test_plc_connection_management(self):
        """Test PLC connection management"""
        print("Testing PLC connection management...")
        
        # Test connection lifecycle
        plc = MockPLCClient()
        
        # Initial state
        self.assertFalse(plc.is_connected)
        
        # Connect
        self.assertTrue(plc.connect())
        self.assertTrue(plc.is_socket_open())
        
        # Disconnect
        self.assertTrue(plc.disconnect())
        self.assertFalse(plc.is_socket_open())
        
        print("✅ PLC connection management test passed")
    
    def test_mock_data_integrity(self):
        """Test mock data integrity and consistency"""
        print("Testing mock data integrity...")
        
        # Test part specifications consistency
        for part_num, part_data in MOCK_PART_SPECIFICATIONS.items():
            # Check required fields
            self.assertIn("part_number", part_data)
            self.assertIn("model_name", part_data)
            self.assertIn("specifications", part_data)
            
            # Check specifications structure
            specs = part_data["specifications"]
            for device in ["L1", "L2", "L3", "L4", "P1", "P2", "P3", "P4"]:
                self.assertIn(device, specs)
                device_spec = specs[device]
                self.assertIn("min", device_spec)
                self.assertIn("max", device_spec)
                self.assertIn("unit", device_spec)
                
                # Check value consistency
                self.assertLess(device_spec["min"], device_spec["max"])
        
        # Test PLC register consistency
        self.assertEqual(len(MOCK_PLC_REGISTERS["coils"]), 8)
        self.assertEqual(len(MOCK_PLC_REGISTERS["registers"]), 12)
        
        # Test process steps consistency
        self.assertGreater(len(MOCK_PROCESS_STEPS), 0)
        for i, step in enumerate(MOCK_PROCESS_STEPS):
            self.assertEqual(step["step"], i)
            self.assertIn("name", step)
            self.assertIn("duration", step)
            self.assertGreater(step["duration"], 0)
        
        print("✅ Mock data integrity test passed")


class TestEOLIntegration(unittest.TestCase):
    """Integration tests for EOL testing system"""
    
    @classmethod
    def setUpClass(cls):
        """Set up integration test environment"""
        print("\n🔗 Setting up EOL Integration Test Environment...")
        
        # Initialize all mock components
        cls.mock_db = get_mock_database()
        cls.mock_plc = get_mock_plc()
        
        # Create root window
        cls.root = tk.Tk()
        cls.root.withdraw()
        
        print("✅ Integration test environment setup completed")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up integration test environment"""
        print("\n🧹 Cleaning up integration test environment...")
        
        if cls.mock_db:
            cls.mock_db.close()
        if cls.mock_plc:
            cls.mock_plc.disconnect()
        if cls.root:
            cls.root.destroy()
        
        print("✅ Integration test environment cleanup completed")
    
    def setUp(self):
        """Set up each integration test"""
        print(f"\n🔗 Running integration test: {self._testMethodName}")
        
        # Reset all components
        reset_mock_database()
        reset_mock_plc()
        
        self.mock_db = get_mock_database()
        self.mock_plc = get_mock_plc()
    
    def test_complete_eol_workflow(self):
        """Test complete EOL workflow from start to finish"""
        print("Testing complete EOL workflow...")
        
        # Step 1: Employee validation
        emp_code = "EMP001"
        emp_result = self.mock_db.validate_employee_code(emp_code)
        self.assertTrue(emp_result["valid"])
        print(f"✅ Employee {emp_code} validated")
        
        # Step 2: Part selection
        part_number = "ALC001"
        part_specs = self.mock_db.get_part_specifications(part_number)
        self.assertIsNotNone(part_specs)
        print(f"✅ Part {part_number} selected")
        
        # Step 3: PLC connection and start
        self.mock_plc.connect()
        self.assertTrue(self.mock_plc.is_socket_open())
        
        # Start process
        start_result = self.mock_plc.write_coil(0, True)  # P0000 HIGH
        self.assertFalse(start_result.isError())
        print("✅ PLC process started")
        
        # Step 4: Monitor process progression
        time.sleep(3)  # Let process run
        
        # Check process status
        status = self.mock_plc.get_process_status()
        self.assertTrue(status["active"])
        self.assertGreater(status["step"], 0)
        print(f"✅ Process progressed to step {status['step']}")
        
        # Step 5: Wait for completion
        max_wait = 30  # Maximum wait time in seconds
        start_time = time.time()
        
        while status["active"] and (time.time() - start_time) < max_wait:
            time.sleep(1)
            status = self.mock_plc.get_process_status()
        
        # Step 6: Verify completion
        self.assertFalse(status["active"], "Process did not complete within timeout")
        print("✅ Process completed")
        
        # Step 7: Check test results
        test_values = status["registers"]
        self.assertGreater(test_values["D100"], 0)  # L1 value
        self.assertGreater(test_values["D104"], 0)  # P1 value
        print("✅ Test values generated")
        
        # Step 8: Generate lot number
        date_str = "241201"
        machine_id = "001"
        lot_increment = self.mock_db.get_next_lot_increment(date_str, machine_id)
        lot_number = f"{date_str}{machine_id}{lot_increment:04d}"
        print(f"✅ Lot number generated: {lot_number}")
        
        # Step 9: Store test results
        test_data = {
            "LOT_NUMBER": lot_number,
            "PART_NUMBER": part_number,
            "EMP_CODE": emp_code,
            "TEST_DATE": "2024-12-01",
            "TEST_TIME": datetime.now().strftime("%H:%M:%S"),
            "L1_VALUE": test_values["D100"],
            "L2_VALUE": test_values["D101"],
            "L3_VALUE": test_values["D102"],
            "L4_VALUE": test_values["D103"],
            "P1_VALUE": test_values["D104"],
            "P2_VALUE": test_values["D105"],
            "P3_VALUE": test_values["D106"],
            "P4_VALUE": test_values["D107"],
            "OVERALL_RESULT": "PASS",
            "FAILED_DEVICES": "",
            "TEST_DURATION": time.time() - start_time
        }
        
        success = self.mock_db.insert_test_result(test_data)
        self.assertTrue(success)
        print("✅ Test results stored in database")
        
        # Step 10: Verify storage
        test_history = self.mock_db.get_test_history(limit=5)
        found = False
        for result in test_history:
            if result["LOT_NUMBER"] == lot_number:
                found = True
                break
        
        self.assertTrue(found, "Test result not found in database")
        print("✅ Test result verification completed")
        
        # Cleanup
        self.mock_plc.disconnect()
        
        print("🎉 Complete EOL workflow test passed!")
    
    def test_multiple_test_cycles(self):
        """Test multiple consecutive test cycles"""
        print("Testing multiple test cycles...")
        
        # Connect PLC
        self.mock_plc.connect()
        
        cycle_results = []
        
        # Run 3 test cycles
        for cycle in range(3):
            print(f"🔄 Starting cycle {cycle + 1}")
            
            # Start cycle
            start_result = self.mock_plc.write_coil(0, True)
            self.assertFalse(start_result.isError())
            
            # Wait for completion
            start_time = time.time()
            max_wait = 20
            
            while self.mock_plc.get_process_status()["active"] and (time.time() - start_time) < max_wait:
                time.sleep(0.5)
            
            # Check completion
            status = self.mock_plc.get_process_status()
            self.assertFalse(status["active"], f"Cycle {cycle + 1} did not complete")
            
            # Record results
            cycle_results.append({
                "cycle": cycle + 1,
                "duration": time.time() - start_time,
                "test_values": status["registers"].copy()
            })
            
            print(f"✅ Cycle {cycle + 1} completed in {cycle_results[-1]['duration']:.1f}s")
            
            # Brief pause between cycles
            time.sleep(1)
        
        # Verify all cycles completed
        self.assertEqual(len(cycle_results), 3)
        
        # Verify test values were generated for each cycle
        for result in cycle_results:
            self.assertGreater(result["test_values"]["D100"], 0)  # L1 value
            self.assertGreater(result["test_values"]["D104"], 0)  # P1 value
        
        print("✅ Multiple test cycles test passed")
        
        # Cleanup
        self.mock_plc.disconnect()


def run_all_tests():
    """Run all tests with detailed output"""
    print("🧪 Starting Comprehensive EOL Testing Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add unit tests
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestEOLFunctionality))
    
    # Add integration tests
    test_suite.addTest(unittest.TestLoader().loadTestsFromTestCase(TestEOLIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n💥 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️ {len(result.failures) + len(result.errors)} TESTS FAILED")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run all tests
    success = run_all_tests()
    
    # Exit with appropriate code
    exit(0 if success else 1)

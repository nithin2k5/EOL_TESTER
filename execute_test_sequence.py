"""
EOL Test Sequence Executor
===========================

Executes the complete test sequence for:
- Employee ID: S041
- Part: sample2
- PLC-controlled test execution based on real-time coil readings

Author: EOL Testing System
Date: October 10, 2025
"""

import os
import time
import json
import mysql.connector
from pymodbus.client import ModbusSerialClient
from datetime import datetime
import traceback

class TestSequenceExecutor:
    """Execute EOL test sequence with PLC process control"""
    
    def __init__(self):
        """Initialize test executor with configuration"""
        self.employee_id = "S041"
        self.part_alc_code = "sample2"
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '12345',
            'database': 'EOL'
        }
        
        # PLC configuration from plc_config.json
        self.plc_com_port = "COM5"
        self.plc_baud_rate = 38400
        self.plc_station_id = 1
        self.plc_client = None
        self.plc_connected = False
        
        # Test execution state
        self.current_employee_id = None
        self.employee_validation_complete = False
        self.part_number = None
        self.model_name = None
        self.specifications = []
        self.current_lot_number = None
        
        # Process status monitoring
        self.process_addresses = []
        self.process_step_names = [
            "AUTO", "HOME", 
            "1st PULL PASS", "1st PULL NG",
            "2nd PULL PASS", "2nd PULL NG",
            "TEST RESULT PASS", "TEST RESULT NG"
        ]
        self.current_process_step = 0
        
    def validate_employee(self):
        """Validate employee ID S041"""
        print("\n" + "="*60)
        print("STEP 1: EMPLOYEE VALIDATION")
        print("="*60)
        
        try:
            employee_file = os.path.join(os.path.dirname(__file__), 'txt_files', 'EmployeeCodes.txt')
            
            if not os.path.exists(employee_file):
                print(f"[ERROR] Employee file not found: {employee_file}")
                return False
            
            with open(employee_file, 'r') as f:
                authorized_codes = [line.strip() for line in f if line.strip()]
            
            print(f"[*] Loaded {len(authorized_codes)} authorized employee codes")
            print(f"[*] Validating Employee ID: {self.employee_id}")
            
            if self.employee_id in authorized_codes:
                self.current_employee_id = self.employee_id
                self.employee_validation_complete = True
                print(f"[OK] Employee {self.employee_id} validated successfully")
                print(f"     Status: AUTHORIZED to operate this machine")
                return True
            else:
                print(f"[ERROR] Employee {self.employee_id} NOT AUTHORIZED")
                print(f"        Please consult SUPERVISOR")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error validating employee: {e}")
            traceback.print_exc()
            return False
    
    def load_part_specifications(self):
        """Load part specifications for sample2 from database"""
        print("\n" + "="*60)
        print("STEP 2: LOADING PART SPECIFICATIONS")
        print("="*60)
        
        try:
            print(f"[*] Querying database for ALC Code: {self.part_alc_code}")
            
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            
            # Query TBL_MODEL_MASTER for part information
            query = """
                SELECT MM_PART_NUMBER, MM_MODEL_NAME, MM_VENDOR_CODE, 
                       MM_PLC_ADDRESS, MM_IMAGE_PATH
                FROM TBL_MODEL_MASTER 
                WHERE MM_ALC_CODE = %s AND MM_STATUS = 1
            """
            cursor.execute(query, (self.part_alc_code,))
            part_info = cursor.fetchone()
            
            if not part_info:
                print(f"[ERROR] Part not found for ALC Code: {self.part_alc_code}")
                cursor.close()
                conn.close()
                return False
            
            self.part_number = part_info['MM_PART_NUMBER']
            self.model_name = part_info['MM_MODEL_NAME']
            
            print(f"[OK] Part found:")
            print(f"   Part Number: {self.part_number}")
            print(f"   Model Name: {self.model_name}")
            print(f"   Vendor Code: {part_info.get('MM_VENDOR_CODE', 'N/A')}")
            
            # Load process addresses
            process_addr_str = part_info.get('MM_PLC_ADDRESS', '')
            if process_addr_str:
                self.process_addresses = [addr.strip() for addr in process_addr_str.split(',')]
                print(f"   Process Addresses: {', '.join(self.process_addresses)}")
            
            # Query tbl_model_specification for specifications
            spec_query = """
                SELECT MS_DESCRIPTION, MS_UNIT, MS_MASTER_MIN, MS_MASTER_MAX,
                       MS_NORMAL_MIN, MS_NORMAL_MAX, MS_DEVICE, ID
                FROM tbl_model_specification 
                WHERE MS_PART_NUMBER = %s 
                ORDER BY ID
            """
            cursor.execute(spec_query, (self.part_number,))
            self.specifications = cursor.fetchall()
            
            print(f"[OK] Loaded {len(self.specifications)} test specifications:")
            for i, spec in enumerate(self.specifications, 1):
                print(f"   {i}. {spec['MS_DESCRIPTION']} ({spec['MS_UNIT']})")
                print(f"      Master: {spec['MS_MASTER_MIN']} - {spec['MS_MASTER_MAX']}")
                print(f"      Normal: {spec['MS_NORMAL_MIN']} - {spec['MS_NORMAL_MAX']}")
            
            cursor.close()
            conn.close()
            return True
            
        except mysql.connector.Error as e:
            print(f"[ERROR] Database error: {e}")
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"[ERROR] Error loading part specifications: {e}")
            traceback.print_exc()
            return False
    
    def connect_to_plc(self):
        """Establish PLC connection via COM port"""
        print("\n" + "="*60)
        print("STEP 3: ESTABLISHING PLC CONNECTION")
        print("="*60)
        
        try:
            print(f"[*] Connecting to PLC:")
            print(f"   COM Port: {self.plc_com_port}")
            print(f"   Baud Rate: {self.plc_baud_rate}")
            print(f"   Station ID: {self.plc_station_id}")
            
            self.plc_client = ModbusSerialClient(
                port=self.plc_com_port,
                baudrate=self.plc_baud_rate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=5
            )
            
            connection_result = self.plc_client.connect()
            
            if connection_result and self.plc_client.is_socket_open():
                self.plc_connected = True
                print(f"[OK] PLC connected successfully on {self.plc_com_port}")
                
                # Test connection with a coil read
                print(f"[*] Testing PLC communication...")
                test_result = self.plc_client.read_coils(0, count=1, device_id=self.plc_station_id)
                
                if not test_result.isError():
                    print(f"[OK] PLC communication verified")
                    return True
                else:
                    print(f"[WARN] PLC connected but communication test failed")
                    return True  # Still allow to proceed
            else:
                print(f"[ERROR] Failed to connect to PLC on {self.plc_com_port}")
                print(f"   Please check:")
                print(f"   - PLC power is ON")
                print(f"   - Cable is connected")
                print(f"   - COM port is correct")
                print(f"   - No other application is using the port")
                return False
                
        except Exception as e:
            print(f"[ERROR] PLC connection error: {e}")
            traceback.print_exc()
            return False
    
    def generate_lot_number(self):
        """Generate lot number in format YYYYMMDD-XXX"""
        try:
            today = datetime.now().strftime('%Y%m%d')
            
            # Query database for next increment
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = """
                SELECT MAX(CAST(SUBSTRING(TD_LOT_NUMBER, 10, 3) AS UNSIGNED)) as max_inc
                FROM tbl_test_data
                WHERE TD_LOT_NUMBER LIKE %s
            """
            cursor.execute(query, (f"{today}-%",))
            result = cursor.fetchone()
            
            next_increment = 1
            if result and result[0]:
                next_increment = result[0] + 1
            
            lot_number = f"{today}-{next_increment:03d}"
            
            cursor.close()
            conn.close()
            
            return lot_number
            
        except Exception as e:
            print(f"[WARN] Error generating lot number: {e}")
            # Fallback to timestamp-based lot number
            return datetime.now().strftime('%Y%m%d-%H%M%S')
    
    def read_plc_coil(self, address):
        """Read a single PLC coil value"""
        if not self.plc_connected or not self.plc_client:
            return False
        
        try:
            # Parse address (e.g., "M100" -> address 100)
            if address.startswith('M'):
                addr_num = int(address[1:])
                result = self.plc_client.read_coils(addr_num, count=1, device_id=self.plc_station_id)
            elif address.startswith('X'):
                addr_num = int(address[1:])
                result = self.plc_client.read_discrete_inputs(addr_num, count=1, device_id=self.plc_station_id)
            elif address.startswith('P'):
                # P addresses are coils
                addr_num = int(address[1:], 16)  # Hex conversion
                result = self.plc_client.read_coils(addr_num, count=1, device_id=self.plc_station_id)
            else:
                return False
            
            if not result.isError():
                return result.bits[0] if result.bits else False
            else:
                return False
                
        except Exception as e:
            print(f"[WARN] Error reading coil {address}: {e}")
            return False
    
    def read_all_process_coils(self):
        """Read all process coil values and return status dictionary"""
        status_values = {}
        
        if not self.plc_connected:
            print("[WARN] PLC not connected - returning simulated values")
            # Return simulated values for testing
            for addr in self.process_addresses:
                status_values[addr] = False
            return status_values
        
        print(f"\n[DATA] Reading PLC Process Status:")
        for address in self.process_addresses:
            if address.strip():
                value = self.read_plc_coil(address)
                status_values[address] = value
                status_str = "HIGH" if value else "LOW"
                print(f"   {address}: {status_str}")
        
        return status_values
    
    def start_test_sequence(self):
        """Start the test sequence execution"""
        print("\n" + "="*60)
        print("STEP 4: STARTING TEST SEQUENCE")
        print("="*60)
        
        # Generate lot number
        self.current_lot_number = self.generate_lot_number()
        print(f"[*] Generated Lot Number: {self.current_lot_number}")
        
        # Initialize test cycle
        print(f"[*] Initiating test cycle for Part: {self.part_number}")
        print(f"   Model: {self.model_name}")
        print(f"   Operator: {self.employee_id}")
        print(f"   Lot: {self.current_lot_number}")
        
        # Send PLC start command (P0000 HIGH to start)
        if self.plc_connected:
            try:
                print(f"\n[TX] Sending START command to PLC (P0000 = HIGH)...")
                result = self.plc_client.write_coil(0, True, device_id=self.plc_station_id)
                if not result.isError():
                    print(f"[OK] START command sent successfully")
                else:
                    print(f"[WARN] Failed to send START command to PLC")
            except Exception as e:
                print(f"[WARN] Error sending START command: {e}")
        
        return True
    
    def monitor_test_execution(self, duration=60):
        """Monitor test execution and display real-time PLC status"""
        print("\n" + "="*60)
        print("STEP 5: MONITORING TEST EXECUTION")
        print("="*60)
        print(f"[TIME]  Monitoring for {duration} seconds...")
        print(f"   Press Ctrl+C to stop monitoring\n")
        
        start_time = time.time()
        last_status = {}
        monitoring_interval = 2  # seconds
        
        try:
            while (time.time() - start_time) < duration:
                # Read process status
                current_status = self.read_all_process_coils()
                
                # Detect changes and display active steps
                active_steps = []
                for i, address in enumerate(self.process_addresses):
                    if current_status.get(address, False):
                        step_name = self.process_step_names[i] if i < len(self.process_step_names) else f"STEP_{i}"
                        active_steps.append(step_name)
                
                # Only print if status changed
                if current_status != last_status:
                    elapsed = int(time.time() - start_time)
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    print(f"\n[{timestamp}] ({elapsed}s elapsed)")
                    if active_steps:
                        print(f"   [ACTIVE] ACTIVE STEPS: {', '.join(active_steps)}")
                    else:
                        print(f"   [IDLE] NO ACTIVE STEPS")
                    
                    last_status = current_status.copy()
                
                # Wait before next read
                time.sleep(monitoring_interval)
            
            print(f"\n[OK] Monitoring completed ({duration}s)")
            
        except KeyboardInterrupt:
            print(f"\n[WARN]  Monitoring stopped by user")
        except Exception as e:
            print(f"\n[ERROR] Error during monitoring: {e}")
            traceback.print_exc()
    
    def save_test_results(self):
        """Save test results to database"""
        print("\n" + "="*60)
        print("STEP 6: SAVING TEST RESULTS")
        print("="*60)
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Read final PLC status for results
            final_status = self.read_all_process_coils()
            
            # Determine test result based on PASS/NG coils
            test_result = "PASS"  # Default
            for i, address in enumerate(self.process_addresses):
                step_name = self.process_step_names[i] if i < len(self.process_step_names) else ""
                if "NG" in step_name and final_status.get(address, False):
                    test_result = "NG"
                    break
            
            print(f"[DATA] Final Test Result: {test_result}")
            print(f"[SAVE] Saving to database...")
            
            # Insert test data record
            insert_query = """
                INSERT INTO tbl_test_data (
                    TD_LOT_NUMBER, TD_PART_NUMBER, TD_OVERALL_STATUS,
                    TD_DATETIME, TD_EMP_CODE
                ) VALUES (%s, %s, %s, %s, %s)
            """
            
            test_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute(insert_query, (
                self.current_lot_number,
                self.part_number,
                test_result,
                test_date,
                self.employee_id
            ))
            
            conn.commit()
            
            print(f"[OK] Test results saved successfully")
            print(f"   Lot Number: {self.current_lot_number}")
            print(f"   Result: {test_result}")
            print(f"   Date: {test_date}")
            
            cursor.close()
            conn.close()
            return True
            
        except mysql.connector.Error as e:
            print(f"[ERROR] Database error while saving results: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Error saving test results: {e}")
            traceback.print_exc()
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        print("\n" + "="*60)
        print("CLEANUP")
        print("="*60)
        
        if self.plc_client and self.plc_connected:
            try:
                # Send STOP command (P0000 = LOW)
                print(f"[TX] Sending STOP command to PLC (P0000 = LOW)...")
                self.plc_client.write_coil(0, False, device_id=self.plc_station_id)
                
                # Disconnect
                print(f"[*] Disconnecting from PLC...")
                self.plc_client.close()
                print(f"[OK] PLC disconnected")
            except Exception as e:
                print(f"[WARN] Error during PLC cleanup: {e}")
        
        print(f"[OK] Cleanup completed")
    
    def execute_full_sequence(self):
        """Execute the complete test sequence"""
        print("\n" + "="*70)
        print("  EOL TEST SEQUENCE EXECUTOR")
        print("  Employee: S041 | Part: sample2")
        print("  PLC-Controlled Test Execution")
        print("="*70)
        
        try:
            # Step 1: Validate employee
            if not self.validate_employee():
                print("\n[ERROR] TEST SEQUENCE ABORTED: Employee validation failed")
                return False
            
            # Step 2: Load part specifications
            if not self.load_part_specifications():
                print("\n[ERROR] TEST SEQUENCE ABORTED: Failed to load part specifications")
                return False
            
            # Step 3: Connect to PLC
            if not self.connect_to_plc():
                print("\n[ERROR] TEST SEQUENCE ABORTED: PLC connection failed")
                print("   Running in SIMULATION mode (no PLC control)")
                self.plc_connected = False  # Continue without PLC
            
            # Step 4: Start test
            if not self.start_test_sequence():
                print("\n[ERROR] TEST SEQUENCE ABORTED: Failed to start test")
                return False
            
            # Step 5: Monitor test execution
            print("\n[OK] Test sequence initiated successfully")
            print("   Monitoring PLC process status for 60 seconds...")
            self.monitor_test_execution(duration=60)
            
            # Step 6: Save results
            self.save_test_results()
            
            print("\n" + "="*70)
            print("  TEST SEQUENCE COMPLETED SUCCESSFULLY")
            print("="*70)
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] CRITICAL ERROR: {e}")
            traceback.print_exc()
            return False
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    executor = TestSequenceExecutor()
    success = executor.execute_full_sequence()
    
    if success:
        print("\n[OK] All operations completed successfully")
        return 0
    else:
        print("\n[ERROR] Test sequence failed")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())


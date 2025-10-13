"""
Automated PLC Sequence Test
Tests the complete PLC auto sequence fixes without requiring GUI interaction
"""

import os
import time
from dotenv import load_dotenv
from pymodbus.client import ModbusSerialClient

class PLCSequenceTest:
    def __init__(self):
        """Initialize test with PLC configuration"""
        load_dotenv()
        self.com_port = os.getenv('PLC_COM_PORT', 'COM5')
        self.baudrate = int(os.getenv('PLC_BAUD_RATE', '38400'))
        self.station_id = int(os.getenv('PLC_STATION_ID', '1'))
        self.client = None
        self.test_results = []
        
    def log_test(self, message, status="INFO"):
        """Log test message with status"""
        timestamp = time.strftime('%H:%M:%S')
        symbols = {"PASS": "✅", "FAIL": "❌", "INFO": "ℹ️", "WARN": "⚠️"}
        symbol = symbols.get(status, "•")
        log_msg = f"[{timestamp}] {symbol} {message}"
        print(log_msg)
        self.test_results.append((status, message))
        
    def connect(self):
        """Connect to PLC with optimized settings"""
        try:
            self.log_test(f"Connecting to PLC on {self.com_port} (38400 baud)...")
            
            self.client = ModbusSerialClient(
                port=self.com_port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=10,
                retries=2
            )
            
            if self.client.connect():
                self.log_test(f"Connected to PLC on {self.com_port}", "PASS")
                return True
            else:
                self.log_test(f"Failed to connect to PLC", "FAIL")
                return False
                
        except Exception as e:
            self.log_test(f"Connection error: {e}", "FAIL")
            return False
    
    def test_pulse_m0067(self):
        """Test M0067 pulse sequence"""
        self.log_test("TEST: M0067 Auto Coil Pulse Trigger", "INFO")
        
        try:
            # Pulse M0067: HIGH → 200ms → LOW
            self.log_test("  Writing M0067 HIGH (pulse start)...")
            result_high = self.client.write_coil(67, True, device_id=self.station_id)
            
            if result_high.isError():
                self.log_test(f"  Failed to set M0067 HIGH: {result_high}", "FAIL")
                return False
            
            self.log_test("  M0067 set to HIGH successfully", "PASS")
            time.sleep(0.2)  # Hold for 200ms
            
            self.log_test("  Writing M0067 LOW (pulse complete)...")
            result_low = self.client.write_coil(67, False, device_id=self.station_id)
            
            if result_low.isError():
                self.log_test(f"  Failed to set M0067 LOW: {result_low}", "FAIL")
                return False
            
            self.log_test("  M0067 pulse completed successfully", "PASS")
            self.log_test("✅ M0067 Auto Trigger Pulse: PASS", "PASS")
            return True
            
        except Exception as e:
            self.log_test(f"  Error during M0067 pulse: {e}", "FAIL")
            return False
    
    def test_write_p0000(self):
        """Test P0000 start signal"""
        self.log_test("TEST: P0000 Start Signal Write", "INFO")
        
        try:
            result = self.client.write_coil(0, True, device_id=self.station_id)
            
            if result.isError():
                self.log_test(f"  Failed to write P0000: {result}", "FAIL")
                return False
            
            self.log_test("  P0000 set to HIGH successfully", "PASS")
            self.log_test("✅ P0000 Start Signal: PASS", "PASS")
            return True
            
        except Exception as e:
            self.log_test(f"  Error writing P0000: {e}", "FAIL")
            return False
    
    def test_bulk_read(self):
        """Test bulk read of process coils M0067-M0087"""
        self.log_test("TEST: Bulk Read of Process Coils (M0067-M0087)", "INFO")
        
        try:
            # Read 21 coils from M67 to M87
            min_addr = 67
            max_addr = 87
            count = max_addr - min_addr + 1
            
            self.log_test(f"  Reading {count} coils from M{min_addr} to M{max_addr}...")
            result = self.client.read_coils(min_addr, count=count, device_id=self.station_id)
            
            if result.isError():
                self.log_test(f"  Bulk read failed: {result}", "FAIL")
                return False
            
            # Extract the 8 key process coils
            process_addresses = [67, 68, 76, 85, 78, 87, 75, 79]  # M0067, M0068, etc.
            label_names = ["AUTO", "HOME", "1st", "2nd", "TEST", "5", "PASS", "NG"]
            
            status_str = "  Status: "
            for i, addr in enumerate(process_addresses):
                index = addr - min_addr
                if index < len(result.bits):
                    is_high = result.bits[index]
                    label = label_names[i] if i < len(label_names) else str(i)
                    status_str += f"{label}:{'✓' if is_high else '✗'} "
            
            self.log_test(status_str, "PASS")
            self.log_test(f"✅ Bulk Read: PASS ({len(result.bits)} coils read)", "PASS")
            return True
            
        except Exception as e:
            self.log_test(f"  Error during bulk read: {e}", "FAIL")
            return False
    
    def test_sequence_monitoring(self, duration=20):
        """Monitor PLC sequence for specified duration"""
        self.log_test(f"TEST: PLC Sequence Monitoring ({duration} seconds)", "INFO")
        
        process_addresses = [67, 68, 76, 85, 78, 87, 75, 79]
        label_names = ["AUTO", "HOME", "1st", "2nd", "TEST", "5", "PASS", "NG"]
        
        start_time = time.time()
        last_status = None
        progression_detected = False
        
        while (time.time() - start_time) < duration:
            try:
                # Bulk read
                result = self.client.read_coils(67, count=21, device_id=self.station_id)
                
                if not result.isError():
                    # Build status string
                    status_str = ""
                    for i, addr in enumerate(process_addresses):
                        index = addr - 67
                        if index < len(result.bits):
                            is_high = result.bits[index]
                            label = label_names[i]
                            status_str += f"{label}:{'✓' if is_high else '✗'} "
                    
                    # Check if status changed (progression detected)
                    if last_status and status_str != last_status:
                        self.log_test(f"🔄 PROGRESSION DETECTED!", "PASS")
                        progression_detected = True
                    
                    elapsed = int(time.time() - start_time)
                    self.log_test(f"  [{elapsed:2d}s] {status_str}")
                    last_status = status_str
                    
                    # Check for completion
                    if index < len(result.bits):
                        pass_bit = result.bits[75-67] if 75-67 < len(result.bits) else False
                        ng_bit = result.bits[79-67] if 79-67 < len(result.bits) else False
                        
                        if pass_bit:
                            self.log_test("🎯 Test PASSED detected!", "PASS")
                            break
                        elif ng_bit:
                            self.log_test("🎯 Test NG detected!", "PASS")
                            break
                else:
                    self.log_test(f"  Read error: {result}", "WARN")
                    
            except Exception as e:
                self.log_test(f"  Read exception: {e}", "WARN")
            
            time.sleep(3)  # 3 second intervals matching production code
        
        if progression_detected:
            self.log_test("✅ Sequence Monitoring: PASS (progression detected)", "PASS")
            return True
        else:
            self.log_test("⚠️ Sequence Monitoring: No progression detected in test period", "WARN")
            return False
    
    def test_connection_stability(self):
        """Test connection remains stable"""
        self.log_test("TEST: Connection Stability (10 reads)", "INFO")
        
        success_count = 0
        for i in range(10):
            try:
                # Check socket
                is_open = self.client.is_socket_open()
                if not is_open:
                    self.log_test(f"  Read {i+1}: Socket closed!", "FAIL")
                    continue
                
                # Perform read
                result = self.client.read_coils(67, count=21, device_id=self.station_id)
                if not result.isError():
                    success_count += 1
                    self.log_test(f"  Read {i+1}/10: Success")
                else:
                    self.log_test(f"  Read {i+1}/10: Error - {result}", "WARN")
                
                time.sleep(3)  # 3 second intervals
                
            except Exception as e:
                self.log_test(f"  Read {i+1}/10: Exception - {e}", "FAIL")
        
        success_rate = (success_count / 10) * 100
        self.log_test(f"  Success rate: {success_rate:.0f}% ({success_count}/10)", 
                     "PASS" if success_rate >= 80 else "FAIL")
        
        if success_rate >= 80:
            self.log_test("✅ Connection Stability: PASS", "PASS")
            return True
        else:
            self.log_test("❌ Connection Stability: FAIL", "FAIL")
            return False
    
    def disconnect(self):
        """Disconnect from PLC"""
        try:
            if self.client:
                self.client.close()
                self.log_test("Disconnected from PLC")
        except Exception as e:
            self.log_test(f"Disconnect error: {e}", "WARN")
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "="*70)
        print("  PLC AUTO SEQUENCE FIX - AUTOMATED TEST SUITE")
        print("="*70 + "\n")
        
        # Test 1: Connection
        if not self.connect():
            print("\n❌ Cannot connect to PLC - Check hardware and configuration")
            return False
        
        print()
        time.sleep(1)
        
        # Test 2: P0000 Write
        test_p0000 = self.test_write_p0000()
        print()
        time.sleep(1)
        
        # Test 3: M0067 Pulse
        test_m0067 = self.test_pulse_m0067()
        print()
        time.sleep(1)
        
        # Test 4: Bulk Read
        test_bulk = self.test_bulk_read()
        print()
        time.sleep(2)
        
        # Test 5: Connection Stability
        test_stability = self.test_connection_stability()
        print()
        time.sleep(2)
        
        # Test 6: Sequence Monitoring (if time permits)
        print("\n" + "-"*70)
        print("OPTIONAL: Monitor PLC sequence for 20 seconds")
        print("This will show if the PLC progresses through steps")
        print("-"*70 + "\n")
        
        try:
            user_input = input("Run sequence monitoring test? (y/n): ").strip().lower()
            if user_input == 'y':
                test_sequence = self.test_sequence_monitoring(20)
            else:
                test_sequence = None
                self.log_test("Sequence monitoring test skipped by user")
        except:
            test_sequence = None
            self.log_test("Sequence monitoring test skipped")
        
        # Summary
        print("\n" + "="*70)
        print("  TEST SUMMARY")
        print("="*70 + "\n")
        
        tests = [
            ("Connection", True),  # We connected
            ("P0000 Write", test_p0000),
            ("M0067 Pulse", test_m0067),
            ("Bulk Read", test_bulk),
            ("Connection Stability", test_stability),
        ]
        
        if test_sequence is not None:
            tests.append(("Sequence Monitoring", test_sequence))
        
        passed = 0
        failed = 0
        
        for test_name, result in tests:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name:.<30} {status}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print()
        print(f"  Total Tests: {passed + failed}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Success Rate: {(passed/(passed+failed)*100) if (passed+failed) > 0 else 0:.0f}%")
        print()
        
        if failed == 0:
            print("="*70)
            print("  ✅ ALL TESTS PASSED - PLC FIX IS WORKING!")
            print("="*70 + "\n")
            return True
        else:
            print("="*70)
            print(f"  ❌ {failed} TEST(S) FAILED - REVIEW NEEDED")
            print("="*70 + "\n")
            return False

def main():
    """Run automated PLC sequence tests"""
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║              PLC AUTO SEQUENCE FIX - AUTOMATED TEST                      ║
║                                                                          ║
║  This script tests the fixes for:                                       ║
║  • PLC stuck at step 0 (M0067)                                          ║
║  • Auto sequence not starting                                           ║
║  • Connection stability                                                 ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("\nPre-Test Checklist:")
    print("  • Is PLC powered ON?")
    print("  • Is PLC connected to COM port?")
    print("  • Is PLC in RUN mode?")
    print("  • Is COM port available (not used by other software)?")
    print()
    
    try:
        input("Press ENTER when ready to start testing...")
    except:
        pass
    
    print()
    
    tester = PLCSequenceTest()
    
    try:
        success = tester.run_all_tests()
        return success
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        return False
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        tester.disconnect()
        print("\nTest suite completed.\n")

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)


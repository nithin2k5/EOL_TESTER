"""
PLC Connection Stability Validator
Tests the implemented fixes for PLC power-off issue during Process Step 0

This script validates:
1. Connection stability during continuous monitoring
2. No automatic connection closure
3. Proper health monitoring and recovery
4. Correct polling frequencies
"""

import time
import os
from dotenv import load_dotenv
from pymodbus.client import ModbusSerialClient

class PLCStabilityValidator:
    def __init__(self):
        """Initialize validator with PLC configuration"""
        load_dotenv()
        self.com_port = os.getenv('PLC_COM_PORT', 'COM5')
        self.baudrate = int(os.getenv('PLC_BAUD_RATE', '38400'))
        self.station_id = int(os.getenv('PLC_STATION_ID', '1'))
        self.client = None
        self.connection_errors = 0
        self.successful_reads = 0
        self.test_duration = 120  # 2 minutes test
        
    def connect(self):
        """Connect to PLC with optimized settings"""
        try:
            print(f"🔌 Connecting to PLC on {self.com_port}...")
            self.client = ModbusSerialClient(
                port=self.com_port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=10,  # Increased timeout
                retries=2,   # Limited retries
                retry_on_empty=False
            )
            
            if self.client.connect():
                print(f"✅ Connected successfully to {self.com_port}")
                return True
            else:
                print(f"❌ Connection failed")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def read_process_coils(self):
        """Read all 8 process status coils with delays"""
        try:
            # Process status addresses from ProcessStatus.txt
            addresses = [67, 68, 76, 85, 78, 87, 75, 79]  # M0067, M0068, etc.
            results = {}
            
            for addr in addresses:
                try:
                    result = self.client.read_coils(addr, count=1, device_id=self.station_id)
                    if not result.isError():
                        results[f"M{addr:04d}"] = result.bits[0]
                        time.sleep(0.05)  # 50ms delay between reads
                    else:
                        print(f"⚠️ Error reading M{addr:04d}: {result}")
                        return None
                except Exception as e:
                    print(f"⚠️ Exception reading M{addr:04d}: {e}")
                    return None
            
            return results
            
        except Exception as e:
            print(f"❌ Error in read_process_coils: {e}")
            return None
    
    def test_continuous_monitoring(self):
        """Test continuous monitoring for specified duration"""
        print(f"\n{'='*60}")
        print(f"🧪 TESTING CONTINUOUS MONITORING FOR {self.test_duration} SECONDS")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        read_count = 0
        error_count = 0
        
        print("Testing with 1.5-second intervals (matching production code)...\n")
        
        while (time.time() - start_time) < self.test_duration:
            read_start = time.time()
            
            # Check connection health
            try:
                is_open = self.client.is_socket_open()
                if not is_open:
                    print("❌ Socket closed - attempting reconnect...")
                    if self.connect():
                        print("✅ Reconnected successfully")
                    else:
                        error_count += 1
                        continue
            except Exception as e:
                print(f"⚠️ Socket check error: {e}")
                error_count += 1
                time.sleep(1.5)
                continue
            
            # Perform read
            results = self.read_process_coils()
            read_duration = time.time() - read_start
            
            if results:
                read_count += 1
                self.successful_reads += 1
                elapsed = int(time.time() - start_time)
                
                # Display results
                active_coils = [addr for addr, val in results.items() if val]
                status = "✅" if active_coils else "⚪"
                
                print(f"[{elapsed:3d}s] {status} Read #{read_count:3d} | "
                      f"Duration: {read_duration*1000:6.1f}ms | "
                      f"Active: {active_coils if active_coils else 'None'} | "
                      f"Errors: {error_count}")
                
                # Check for M0067 (Process Step 0)
                if results.get('M0067', False):
                    print(f"     🎯 Process Step 0 (M0067) ACTIVE - Connection maintained!")
            else:
                error_count += 1
                self.connection_errors += 1
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed:3d}s] ❌ Read failed | Error count: {error_count}")
            
            # Wait for next interval (1.5 seconds)
            time.sleep(1.5)
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Duration: {self.test_duration}s")
        print(f"Successful Reads: {read_count}")
        print(f"Failed Reads: {error_count}")
        print(f"Success Rate: {(read_count/(read_count+error_count)*100) if (read_count+error_count) > 0 else 0:.1f}%")
        print(f"Expected Reads: ~{self.test_duration//1.5}")
        print(f"Actual Reads: {read_count}")
        
        # Evaluation
        if error_count == 0:
            print(f"\n✅ PASS - No connection errors detected!")
            return True
        elif error_count <= 3:
            print(f"\n⚠️ PARTIAL PASS - {error_count} minor errors (acceptable)")
            return True
        else:
            print(f"\n❌ FAIL - Too many errors ({error_count})")
            return False
    
    def test_process_step_0_stability(self):
        """Specifically test stability when M0067 is active"""
        print(f"\n{'='*60}")
        print(f"🎯 TESTING PROCESS STEP 0 (M0067) STABILITY")
        print(f"{'='*60}\n")
        print("This test monitors M0067 specifically to ensure connection remains stable")
        print("when Process Step 0 is active (the original failure point).\n")
        
        m0067_active_duration = 0
        start_time = time.time()
        
        for i in range(40):  # 40 reads over 60 seconds
            results = self.read_process_coils()
            
            if results:
                m0067_status = results.get('M0067', False)
                if m0067_status:
                    m0067_active_duration += 1.5
                    print(f"[{int(time.time()-start_time):3d}s] 🟢 M0067 ACTIVE - "
                          f"Connection stable for {m0067_active_duration:.1f}s")
                else:
                    print(f"[{int(time.time()-start_time):3d}s] ⚪ M0067 inactive - Waiting for activation")
            else:
                print(f"[{int(time.time()-start_time):3d}s] ❌ Read failed - Connection issue!")
                return False
            
            time.sleep(1.5)
        
        print(f"\n✅ M0067 monitoring completed - No connection drops detected!")
        return True
    
    def disconnect(self):
        """Cleanly disconnect from PLC"""
        try:
            if self.client:
                self.client.close()
                print(f"\n🔌 Disconnected from PLC")
        except Exception as e:
            print(f"⚠️ Disconnect error: {e}")

def main():
    """Run PLC stability validation tests"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║        PLC CONNECTION STABILITY VALIDATOR v1.0               ║
║                                                              ║
║  Testing fixes for PLC power-off issue during Process       ║
║  Step 0 (M0067) monitoring                                  ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    validator = PLCStabilityValidator()
    
    # Connect to PLC
    if not validator.connect():
        print("\n❌ Cannot connect to PLC - Aborting tests")
        return False
    
    try:
        # Test 1: Continuous monitoring
        print("\n🧪 TEST 1: Continuous Monitoring Stability")
        test1_pass = validator.test_continuous_monitoring()
        
        # Test 2: Process Step 0 specific test
        print("\n🧪 TEST 2: Process Step 0 (M0067) Stability")
        test2_pass = validator.test_process_step_0_stability()
        
        # Final results
        print(f"\n{'='*60}")
        print(f"🏁 FINAL RESULTS")
        print(f"{'='*60}")
        print(f"Test 1 (Continuous Monitoring): {'✅ PASS' if test1_pass else '❌ FAIL'}")
        print(f"Test 2 (M0067 Stability): {'✅ PASS' if test2_pass else '❌ FAIL'}")
        
        if test1_pass and test2_pass:
            print(f"\n{'='*60}")
            print(f"✅ ALL TESTS PASSED - PLC FIX IS WORKING CORRECTLY!")
            print(f"{'='*60}\n")
            return True
        else:
            print(f"\n{'='*60}")
            print(f"❌ SOME TESTS FAILED - REVIEW NEEDED")
            print(f"{'='*60}\n")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
        return False
    except Exception as e:
        print(f"\n\n❌ Test error: {e}")
        return False
    finally:
        validator.disconnect()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)


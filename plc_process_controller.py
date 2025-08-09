"""
PLC Process Status Controller
A standalone tool to operate PLC process status in a loop

This script will:
1. Connect to the PLC
2. Test if we can control process status coils
3. Run process steps in a continuous loop
4. Provide real-time feedback on process status

Process Steps:
- M0067: AUTO
- M0068: HOME  
- M0076: 1st PULL PASS
- M0085: 1st PULL NG
- M0078: 2nd PULL PASS
- M0087: 2nd PULL NG
- M0075: TEST RESULT PASS
- M0079: TEST RESULT NG
"""

import time
import os
import sys
from pymodbus.client import ModbusSerialClient
from dotenv import load_dotenv
import threading
import signal

# Load environment variables
load_dotenv()

class PLCProcessController:
    def __init__(self):
        self.running = False
        self.plc_client = None
        self.current_step = 0
        self.step_start_time = 0
        self.control_mode = "UNKNOWN"
        
        # Process status addresses from ProcessStatus.txt
        self.process_addresses = ["M0067", "M0068", "M0076", "M0085", "M0078", "M0087", "M0075", "M0079"]
        self.step_names = ["AUTO", "HOME", "1st PULL PASS", "1st PULL NG", "2nd PULL PASS", "2nd PULL NG", "TEST RESULT PASS", "TEST RESULT NG"]
        
        # PLC connection settings
        self.station_id = int(os.getenv('PLC_STATION_ID', '1'))
        self.com_port = os.getenv('PLC_COM_PORT', 'COM3')
        self.baud_rate = int(os.getenv('PLC_BAUD_RATE', '115200'))
        
        # Step timing
        self.step_duration = 3.0  # 3 seconds per step
        
        print("🎮 PLC Process Status Controller Initialized")
        print(f"📡 PLC Settings: {self.com_port}, {self.baud_rate} baud, Station ID: {self.station_id}")
        print(f"📋 Process Steps: {len(self.process_addresses)} steps configured")
        
    def connect_plc(self):
        """Connect to PLC via serial/modbus"""
        try:
            print(f"🔗 Connecting to PLC on {self.com_port}...")
            
            # Create Modbus serial client
            self.plc_client = ModbusSerialClient(
                port=self.com_port,
                baudrate=self.baud_rate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1
            )
            
            # Connect
            if self.plc_client.connect():
                print("✅ PLC Connected Successfully!")
                
                # Test basic communication
                response = self.plc_client.read_coils(address=0x0000, count=1, slave=self.station_id)
                if not response.isError():
                    print("✅ PLC Communication Test Passed")
                    return True
                else:
                    print(f"❌ PLC Communication Test Failed: {response}")
                    return False
            else:
                print("❌ Failed to connect to PLC")
                return False
                
        except Exception as e:
            print(f"❌ PLC Connection Error: {e}")
            return False
    
    def disconnect_plc(self):
        """Disconnect from PLC"""
        try:
            if self.plc_client:
                self.plc_client.close()
                print("🔌 PLC Disconnected")
        except Exception as e:
            print(f"Error disconnecting PLC: {e}")
    
    def set_plc_enable(self, enable=True):
        """Set PLC main enable (P0000)"""
        try:
            if not self.plc_client:
                return False
                
            response = self.plc_client.write_coil(
                address=0x0000,  # P0000
                value=enable,
                slave=self.station_id
            )
            
            if not response.isError():
                status = "ENABLED" if enable else "DISABLED"
                print(f"✅ PLC {status} (P0000 = {enable})")
                return True
            else:
                print(f"❌ Failed to set PLC enable: {response}")
                return False
                
        except Exception as e:
            print(f"❌ Error setting PLC enable: {e}")
            return False
    
    def test_process_control(self):
        """Test if we can control process status coils"""
        try:
            print("\n🧪 TESTING PROCESS CONTROL CAPABILITY...")
            
            if not self.plc_client:
                print("❌ PLC not connected")
                return False
            
            # Test M0067 (AUTO step)
            test_address = 0x0067  # M0067
            
            # Try to set it HIGH
            write_response = self.plc_client.write_coil(
                address=test_address,
                value=True,
                slave=self.station_id
            )
            
            if write_response.isError():
                print(f"❌ Cannot write to M0067: {write_response}")
                self.control_mode = "READ_ONLY"
                return False
            
            print("🔧 Set M0067 HIGH, testing if it stays...")
            time.sleep(0.5)
            
            # Read it back
            read_response = self.plc_client.read_coils(
                address=test_address,
                count=1,
                slave=self.station_id
            )
            
            if not read_response.isError():
                actual_value = read_response.bits[0]
                if actual_value:
                    print("✅ SUCCESS: We CAN control process status!")
                    self.control_mode = "MANUAL"
                    return True
                else:
                    print("❌ PLC overrode our control - using monitor mode")
                    self.control_mode = "MONITOR"
                    return False
            else:
                print(f"❌ Cannot read M0067: {read_response}")
                self.control_mode = "READ_ONLY"
                return False
                
        except Exception as e:
            print(f"❌ Error testing process control: {e}")
            self.control_mode = "ERROR"
            return False
    
    def read_all_process_status(self):
        """Read all process status coils"""
        try:
            if not self.plc_client:
                return {}
                
            status_values = {}
            
            for address_str in self.process_addresses:
                try:
                    # Convert M0067 -> 0x0067
                    hex_part = address_str[1:]  # Remove 'M'
                    coil_address = int(hex_part, 16)
                    
                    response = self.plc_client.read_coils(
                        address=coil_address,
                        count=1,
                        slave=self.station_id
                    )
                    
                    if not response.isError():
                        status_values[address_str] = response.bits[0]
                    else:
                        status_values[address_str] = False
                        
                except Exception as e:
                    print(f"Error reading {address_str}: {e}")
                    status_values[address_str] = False
            
            return status_values
            
        except Exception as e:
            print(f"Error reading process status: {e}")
            return {}
    
    def set_process_step(self, step_index, value):
        """Set a specific process step HIGH or LOW"""
        try:
            if step_index >= len(self.process_addresses):
                return False
                
            address_str = self.process_addresses[step_index]
            step_name = self.step_names[step_index] if step_index < len(self.step_names) else f"STEP_{step_index}"
            
            # Convert M0067 -> 0x0067
            hex_part = address_str[1:]
            coil_address = int(hex_part, 16)
            
            response = self.plc_client.write_coil(
                address=coil_address,
                value=value,
                slave=self.station_id
            )
            
            if not response.isError():
                status = "HIGH" if value else "LOW"
                print(f"🔧 Set {step_name} ({address_str}) to {status}")
                return True
            else:
                print(f"❌ Failed to set {step_name}: {response}")
                return False
                
        except Exception as e:
            print(f"Error setting process step: {e}")
            return False
    
    def reset_all_process_steps(self):
        """Reset all process steps to LOW"""
        try:
            print("🔄 Resetting all process steps...")
            success_count = 0
            
            for i in range(len(self.process_addresses)):
                if self.set_process_step(i, False):
                    success_count += 1
                    time.sleep(0.1)  # Small delay between writes
            
            print(f"✅ Reset {success_count}/{len(self.process_addresses)} process steps")
            return success_count == len(self.process_addresses)
            
        except Exception as e:
            print(f"Error resetting process steps: {e}")
            return False
    
    def run_process_cycle(self):
        """Run one complete process cycle"""
        try:
            print(f"\n🔄 STARTING PROCESS CYCLE - Mode: {self.control_mode}")
            
            if self.control_mode == "MANUAL":
                return self.run_manual_cycle()
            else:
                return self.run_monitor_cycle()
                
        except Exception as e:
            print(f"Error in process cycle: {e}")
            return False
    
    def run_manual_cycle(self):
        """Run manual control cycle - we control each step"""
        try:
            print("🎮 MANUAL CONTROL MODE - We control each step")
            
            # Reset all steps first
            if not self.reset_all_process_steps():
                return False
                
            time.sleep(1)
            
            # Step through each process
            for step in range(len(self.process_addresses)):
                step_name = self.step_names[step] if step < len(self.step_names) else f"STEP_{step}"
                address = self.process_addresses[step]
                
                print(f"\n⏭️  STEP {step + 1}: {step_name} ({address})")
                
                # Activate current step
                if not self.set_process_step(step, True):
                    print(f"❌ Failed to activate {step_name}")
                    continue
                
                # Wait for step duration
                print(f"⏱️  Running {step_name} for {self.step_duration} seconds...")
                time.sleep(self.step_duration)
                
                # Deactivate current step
                if not self.set_process_step(step, False):
                    print(f"⚠️ Failed to deactivate {step_name}")
                
                # Check if we should stop
                if not self.running:
                    break
            
            print("✅ Manual cycle completed")
            return True
            
        except Exception as e:
            print(f"Error in manual cycle: {e}")
            return False
    
    def run_monitor_cycle(self):
        """Run monitor cycle - just watch what PLC does"""
        try:
            print("👁️ MONITOR MODE - Watching PLC control")
            
            cycle_start = time.time()
            last_status = {}
            
            # Monitor for 30 seconds or until test completion
            while time.time() - cycle_start < 30 and self.running:
                current_status = self.read_all_process_status()
                
                # Check for changes
                active_steps = []
                for i, address in enumerate(self.process_addresses):
                    if current_status.get(address, False):
                        step_name = self.step_names[i] if i < len(self.step_names) else f"STEP_{i}"
                        active_steps.append(f"{step_name}({address})")
                
                # Log changes
                if active_steps != last_status.get('active_steps', []):
                    if active_steps:
                        print(f"📊 ACTIVE: {', '.join(active_steps)}")
                    else:
                        print("📊 NO ACTIVE STEPS")
                    last_status['active_steps'] = active_steps
                
                # Check for test completion (TEST RESULT PASS or NG)
                test_pass = current_status.get("M0075", False)  # TEST RESULT PASS
                test_ng = current_status.get("M0079", False)    # TEST RESULT NG
                
                if test_pass or test_ng:
                    result = "PASS" if test_pass else "NG"
                    print(f"🎯 TEST COMPLETED: {result}")
                    break
                
                time.sleep(0.5)  # Check every 500ms
            
            print("✅ Monitor cycle completed")
            return True
            
        except Exception as e:
            print(f"Error in monitor cycle: {e}")
            return False
    
    def run_continuous_loop(self):
        """Run process cycles continuously"""
        try:
            print("\n🔄 STARTING CONTINUOUS PROCESS LOOP")
            print("Press Ctrl+C to stop")
            
            cycle_count = 0
            
            while self.running:
                cycle_count += 1
                print(f"\n{'='*50}")
                print(f"🔄 CYCLE #{cycle_count}")
                print(f"{'='*50}")
                
                # Run one cycle
                success = self.run_process_cycle()
                
                if not success:
                    print("❌ Cycle failed - waiting 5 seconds before retry")
                    time.sleep(5)
                    continue
                
                # Wait between cycles
                print(f"✅ Cycle #{cycle_count} completed")
                print("⏳ Waiting 3 seconds before next cycle...")
                time.sleep(3)
                
                # Safety check - don't run forever in manual mode
                if self.control_mode == "MANUAL" and cycle_count >= 10:
                    print("⚠️ Manual mode safety limit reached (10 cycles)")
                    break
            
        except KeyboardInterrupt:
            print("\n⏹️ Loop stopped by user")
        except Exception as e:
            print(f"❌ Error in continuous loop: {e}")
        finally:
            self.stop()
    
    def start(self):
        """Start the PLC process controller"""
        try:
            print("🚀 STARTING PLC PROCESS CONTROLLER")
            print("="*50)
            
            # Connect to PLC
            if not self.connect_plc():
                print("❌ Cannot start - PLC connection failed")
                return False
            
            # Enable PLC
            if not self.set_plc_enable(True):
                print("❌ Cannot enable PLC")
                return False
            
            # Test control capability
            can_control = self.test_process_control()
            
            print(f"\n📋 CONFIGURATION:")
            print(f"   Control Mode: {self.control_mode}")
            print(f"   Can Control: {'YES' if can_control else 'NO'}")
            print(f"   Step Duration: {self.step_duration}s")
            print(f"   Process Steps: {len(self.process_addresses)}")
            
            # Start the main loop
            self.running = True
            self.run_continuous_loop()
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting controller: {e}")
            return False
    
    def stop(self):
        """Stop the controller"""
        try:
            print("\n⏹️ STOPPING PLC PROCESS CONTROLLER")
            self.running = False
            
            # Reset all process steps
            if self.control_mode == "MANUAL":
                print("🔄 Resetting process steps...")
                self.reset_all_process_steps()
            
            # Disconnect PLC
            self.disconnect_plc()
            print("✅ Controller stopped")
            
        except Exception as e:
            print(f"Error stopping controller: {e}")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n⏹️ Shutdown signal received...")
    if 'controller' in globals():
        controller.stop()
    sys.exit(0)

def main():
    """Main function"""
    global controller
    
    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🎮 PLC Process Status Controller")
    print("="*50)
    
    # Create and start controller
    controller = PLCProcessController()
    
    try:
        # Start the controller
        controller.start()
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        if controller:
            controller.stop()

if __name__ == "__main__":
    main()

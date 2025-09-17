"""
Mock PLC Simulator for EOL Testing System
This file simulates PLC communication without requiring real hardware
"""

import time
import threading
from datetime import datetime
from mock_data import MOCK_PLC_REGISTERS, MOCK_PROCESS_STEPS, MOCK_LOADCELL_DATA, MOCK_POSITION_DATA

class MockPLCClient:
    """Mock PLC client that simulates Modbus communication"""
    
    def __init__(self):
        """Initialize mock PLC client"""
        self.is_connected = False
        self.station_id = 1
        self.registers = MOCK_PLC_REGISTERS.copy()
        self.process_step = 0
        self.test_active = False
        self.simulation_thread = None
        self.simulation_running = False
        
        # Initialize all coils to False
        for coil in self.registers["coils"]:
            self.registers["coils"][coil] = False
        
        # Initialize all registers to 0
        for reg in self.registers["registers"]:
            self.registers["registers"][reg] = 0
        
        print("🔧 Mock PLC Client initialized")
    
    def connect(self):
        """Simulate PLC connection"""
        try:
            time.sleep(0.1)  # Simulate connection delay
            self.is_connected = True
            print("✅ Mock PLC connected successfully")
            return True
        except Exception as e:
            print(f"❌ Mock PLC connection failed: {e}")
            return False
    
    def disconnect(self):
        """Simulate PLC disconnection"""
        try:
            self.is_connected = False
            self.stop_simulation()
            print("✅ Mock PLC disconnected")
            return True
        except Exception as e:
            print(f"❌ Mock PLC disconnection failed: {e}")
            return False
    
    def is_socket_open(self):
        """Check if PLC connection is open"""
        return self.is_connected
    
    def write_coil(self, address, value, device_id=1):
        """Write to a PLC coil"""
        try:
            if not self.is_connected:
                return MockModbusResult(True, "Not connected")
            
            # Convert address to coil name
            coil_name = f"M{address}"
            if coil_name in self.registers["coils"]:
                self.registers["coils"][coil_name] = value
                print(f"🔧 Mock PLC: Set coil {coil_name} to {value}")
                
                # Handle special coil operations
                if coil_name == "M100" and value:  # AUTO coil activated
                    self.start_process_simulation()
                elif coil_name == "M100" and not value:  # AUTO coil deactivated
                    self.stop_process_simulation()
                
                return MockModbusResult(False, "Success")
            else:
                print(f"⚠️ Mock PLC: Unknown coil address {address}")
                return MockModbusResult(True, f"Unknown coil address {address}")
                
        except Exception as e:
            print(f"❌ Mock PLC write_coil error: {e}")
            return MockModbusResult(True, str(e))
    
    def read_coils(self, start_address, count, device_id=1):
        """Read PLC coils"""
        try:
            if not self.is_connected:
                return MockModbusResult(True, "Not connected")
            
            coils = []
            for i in range(count):
                coil_name = f"M{start_address + i}"
                if coil_name in self.registers["coils"]:
                    coils.append(self.registers["coils"][coil_name])
                else:
                    coils.append(False)
            
            print(f"🔧 Mock PLC: Read {count} coils starting from M{start_address}: {coils}")
            return MockModbusResult(False, coils)
            
        except Exception as e:
            print(f"❌ Mock PLC read_coils error: {e}")
            return MockModbusResult(True, str(e))
    
    def read_discrete_inputs(self, start_address, count, device_id=1):
        """Read PLC discrete inputs"""
        try:
            if not self.is_connected:
                return MockModbusResult(True, "Not connected")
            
            inputs = []
            for i in range(count):
                input_name = f"I{start_address + i}"
                # Simulate some inputs as active
                if input_name == "I100":  # Emergency stop
                    inputs.append(False)
                elif input_name == "I101":  # Safety door
                    inputs.append(True)
                elif input_name == "I102":  # Part present
                    inputs.append(self.test_active)
                else:
                    inputs.append(False)
            
            print(f"🔧 Mock PLC: Read {count} discrete inputs starting from I{start_address}: {inputs}")
            return MockModbusResult(False, inputs)
            
        except Exception as e:
            print(f"❌ Mock PLC read_discrete_inputs error: {e}")
            return MockModbusResult(True, str(e))
    
    def write_register(self, address, value, device_id=1):
        """Write to a PLC register"""
        try:
            if not self.is_connected:
                return MockModbusResult(True, "Not connected")
            
            # Convert address to register name
            reg_name = f"D{address}"
            if reg_name in self.registers["registers"]:
                self.registers["registers"][reg_name] = value
                print(f"🔧 Mock PLC: Set register {reg_name} to {value}")
                return MockModbusResult(False, "Success")
            else:
                print(f"⚠️ Mock PLC: Unknown register address {address}")
                return MockModbusResult(True, f"Unknown register address {address}")
                
        except Exception as e:
            print(f"❌ Mock PLC write_register error: {e}")
            return MockModbusResult(True, str(e))
    
    def read_holding_registers(self, start_address, count, device_id=1):
        """Read PLC holding registers"""
        try:
            if not self.is_connected:
                return MockModbusResult(True, "Not connected")
            
            registers = []
            for i in range(count):
                reg_name = f"D{start_address + i}"
                if reg_name in self.registers["registers"]:
                    registers.append(self.registers["registers"][reg_name])
                else:
                    registers.append(0)
            
            print(f"🔧 Mock PLC: Read {count} registers starting from D{start_address}: {registers}")
            return MockModbusResult(False, registers)
            
        except Exception as e:
            print(f"❌ Mock PLC read_holding_registers error: {e}")
            return MockModbusResult(True, str(e))
    
    def start_process_simulation(self):
        """Start the process simulation"""
        if not self.simulation_running:
            self.simulation_running = True
            self.test_active = True
            self.process_step = 0
            self.simulation_thread = threading.Thread(target=self.run_process_simulation)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
            print("🚀 Mock PLC: Process simulation started")
    
    def stop_process_simulation(self):
        """Stop the process simulation"""
        self.simulation_running = False
        self.test_active = False
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=1.0)
        print("🛑 Mock PLC: Process simulation stopped")
    
    def run_process_simulation(self):
        """Run the process simulation in background thread"""
        try:
            while self.simulation_running and self.process_step < len(MOCK_PROCESS_STEPS):
                step_info = MOCK_PROCESS_STEPS[self.process_step]
                print(f"🔄 Mock PLC: Process step {self.process_step + 1}/{len(MOCK_PROCESS_STEPS)} - {step_info['name']}")
                
                # Activate current step coil
                coil_name = f"M{100 + self.process_step}"
                if coil_name in self.registers["coils"]:
                    self.registers["coils"][coil_name] = True
                
                # Simulate step duration
                time.sleep(step_info["duration"])
                
                # Deactivate current step coil
                self.registers["coils"][coil_name] = False
                
                # Move to next step
                self.process_step += 1
                
                # If this was the last step, complete the test
                if self.process_step >= len(MOCK_PROCESS_STEPS):
                    self.complete_test()
                    break
            
            # Reset process if simulation stopped
            if not self.simulation_running:
                self.reset_process()
                
        except Exception as e:
            print(f"❌ Mock PLC simulation error: {e}")
            self.reset_process()
    
    def complete_test(self):
        """Complete the test and generate results"""
        try:
            print("🎉 Mock PLC: Test completed, generating results")
            
            # Set completion coil
            self.registers["coils"]["M105"] = True
            
            # Generate test values
            self.generate_test_values()
            
            # Wait briefly then reset
            time.sleep(1.0)
            self.reset_process()
            
        except Exception as e:
            print(f"❌ Mock PLC test completion error: {e}")
    
    def generate_test_values(self):
        """Generate realistic test values"""
        try:
            import random
            
            # Generate load cell values (L1-L4)
            for i, device in enumerate(["L1", "L2", "L3", "L4"]):
                if device in MOCK_LOADCELL_DATA:
                    # Get a random value from mock data
                    value = random.choice(MOCK_LOADCELL_DATA[device])
                    self.registers["registers"][f"D{100 + i}"] = value
                    print(f"🔧 Mock PLC: Generated {device} = {value}")
            
            # Generate position sensor values (P1-P4)
            for i, device in enumerate(["P1", "P2", "P3", "P4"]):
                if device in MOCK_POSITION_DATA:
                    # Get a random value from mock data
                    value = random.choice(MOCK_POSITION_DATA[device])
                    self.registers["registers"][f"D{104 + i}"] = value
                    print(f"🔧 Mock PLC: Generated {device} = {value}")
            
            # Set process step register
            self.registers["registers"]["D200"] = self.process_step
            self.registers["registers"]["D201"] = 1  # Test counter
            
            print("✅ Mock PLC: Test values generated successfully")
            
        except Exception as e:
            print(f"❌ Mock PLC value generation error: {e}")
    
    def reset_process(self):
        """Reset the process to initial state"""
        try:
            print("🔄 Mock PLC: Resetting process to initial state")
            
            # Reset all coils to False
            for coil in self.registers["coils"]:
                self.registers["coils"][coil] = False
            
            # Reset all registers to 0
            for reg in self.registers["registers"]:
                self.registers["registers"][reg] = 0
            
            # Reset process step
            self.process_step = 0
            self.test_active = False
            
            print("✅ Mock PLC: Process reset completed")
            
        except Exception as e:
            print(f"❌ Mock PLC process reset error: {e}")
    
    def get_process_status(self):
        """Get current process status"""
        try:
            status = {
                "step": self.process_step,
                "step_name": MOCK_PROCESS_STEPS[self.process_step]["name"] if self.process_step < len(MOCK_PROCESS_STEPS) else "UNKNOWN",
                "active": self.test_active,
                "coils": self.registers["coils"].copy(),
                "registers": self.registers["registers"].copy()
            }
            return status
        except Exception as e:
            print(f"❌ Mock PLC get_process_status error: {e}")
            return None
    
    def simulate_error(self, error_code="E001"):
        """Simulate a PLC error"""
        try:
            print(f"⚠️ Mock PLC: Simulating error {error_code}")
            
            # Set error coil
            self.registers["coils"]["M106"] = True
            
            # Set error code in register
            self.registers["registers"]["D202"] = int(error_code[1:])
            
            # Stop simulation
            self.stop_process_simulation()
            
        except Exception as e:
            print(f"❌ Mock PLC error simulation failed: {e}")
    
    def clear_error(self):
        """Clear PLC error state"""
        try:
            print("🔧 Mock PLC: Clearing error state")
            
            # Clear error coil
            self.registers["coils"]["M106"] = False
            
            # Clear error code
            self.registers["registers"]["D202"] = 0
            
        except Exception as e:
            print(f"❌ Mock PLC clear error failed: {e}")


class MockModbusResult:
    """Mock Modbus result class"""
    
    def __init__(self, is_error, value):
        self._is_error = is_error
        self._value = value
    
    def isError(self):
        """Check if result is an error"""
        return self._is_error
    
    def __str__(self):
        return f"MockModbusResult(error={self._is_error}, value={self._value})"


# Global mock PLC instance
mock_plc = None

def get_mock_plc():
    """Get or create mock PLC instance"""
    global mock_plc
    if mock_plc is None:
        mock_plc = MockPLCClient()
    return mock_plc

def reset_mock_plc():
    """Reset mock PLC to initial state"""
    global mock_plc
    if mock_plc:
        mock_plc.disconnect()
    mock_plc = MockPLCClient()
    return mock_plc


# Test functions
def test_mock_plc():
    """Test the mock PLC functionality"""
    try:
        print("🧪 Testing Mock PLC...")
        
        plc = get_mock_plc()
        
        # Test connection
        assert plc.connect() == True
        assert plc.is_socket_open() == True
        
        # Test coil operations
        result = plc.write_coil(100, True)  # M100
        assert result.isError() == False
        
        result = plc.read_coils(100, 1)
        assert result.isError() == False
        assert result._value == [True]
        
        # Test register operations
        result = plc.write_register(100, 123.45)
        assert result.isError() == False
        
        result = plc.read_holding_registers(100, 1)
        assert result.isError() == False
        assert result._value == [123.45]
        
        # Test process simulation
        plc.start_process_simulation()
        time.sleep(1)  # Let simulation run briefly
        
        # Test disconnection
        assert plc.disconnect() == True
        assert plc.is_socket_open() == False
        
        print("✅ Mock PLC tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Mock PLC tests failed: {e}")
        return False


if __name__ == "__main__":
    test_mock_plc()

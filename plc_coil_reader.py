"""
PLC Coil Reader - Reads input registers from PLC using COM Port 4

This module provides a comprehensive interface for communicating with PLC (Programmable Logic Controller)
devices using the Modbus RTU protocol over a serial connection.

MODBUS BASICS:
- Modbus is a communication protocol for industrial devices
- RTU (Remote Terminal Unit) mode uses binary data over serial
- Coils = Digital outputs/inputs (ON/OFF, True/False)
- Input Registers = Read-only analog values (sensors, measurements)
- Holding Registers = Read/write analog values (setpoints, configurations)

HARDWARE REQUIREMENTS:
- PLC connected to COM Port 4
- RS-485 serial communication cable
- PLC configured for Modbus RTU protocol

AUTHOR: AI Assistant
VERSION: 1.0
"""

# Standard library imports for serial communication and timing
import serial
import time
import json
import os

# PyModbus library for Modbus protocol communication
# ModbusSerialClient provides synchronous (blocking) client for reliable serial communication
from pymodbus.client import ModbusSerialClient

# Exception handling for Modbus communication errors
from pymodbus.exceptions import ConnectionException, ModbusException

# Advanced error reporting and debugging
import traceback
import sys

class PLCCoilReader:
    """
    Main class for reading PLC coils and registers via Modbus RTU protocol.

    This class encapsulates all PLC communication functionality including:
    - Serial port connection management
    - Modbus protocol handling
    - Error recovery and status monitoring
    - Multiple data type support (coils, registers)

    USAGE EXAMPLE:
        plc = PLCCoilReader(com_port="COM4", baudrate=38400, station_id=1)
        if plc.establish_connection():
            coil_value = plc.read_single_coil(0)
            plc.disconnect()
    """

    def __init__(self, com_port=None, baudrate=None, station_id=None):
        """
        Initialize the PLC Coil Reader with connection parameters.

        If no parameters are provided, loads configuration from plc_config.json

        Args:
            com_port (str, optional): Serial port name (e.g., "COM4" on Windows, "/dev/ttyUSB0" on Linux)
            baudrate (int, optional): Communication speed in bits per second
            station_id (int, optional): Modbus slave/station address of the PLC

        Attributes:
            client: ModbusSerialClient instance (None until connected)
            is_connected: Boolean flag indicating connection status
        """
        # Load configuration from file if no parameters provided
        if com_port is None or baudrate is None or station_id is None:
            config = self._load_config()
            com_port = com_port or config.get('com_port', 'COM4')
            baudrate = baudrate or config.get('baudrate', 38400)
            station_id = station_id or config.get('station_id', 1)

        # Store connection parameters for later use
        self.com_port = com_port          # Serial port (e.g., COM4)
        self.baudrate = baudrate          # Communication speed (bits per second)
        self.station_id = station_id      # PLC's Modbus slave address

        # Connection state variables
        self.client = None                # Modbus client instance (created during connection)
        self.is_connected = False         # Connection status flag

    def _load_config(self):
        """Load PLC configuration from plc_config.json file"""
        config_file = os.path.join(os.path.dirname(__file__), 'plc_config.json')
        default_config = {
            'com_port': 'COM4',
            'baudrate': 38400,
            'station_id': 1
        }

        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    plc_settings = config_data.get('plc_settings', {})
                    return {
                        'com_port': plc_settings.get('com_port', default_config['com_port']),
                        'baudrate': plc_settings.get('baudrate', default_config['baudrate']),
                        'station_id': plc_settings.get('station_id', default_config['station_id'])
                    }
            else:
                print("⚠️  plc_config.json not found, using default settings")
                return default_config
        except Exception as e:
            print(f"⚠️  Error loading config file: {e}, using defaults")
            return default_config

    def establish_connection(self):
        """
        Establish serial connection to the PLC using Modbus RTU protocol.

        This method performs the following steps:
        1. Creates a ModbusSerialClient with specified parameters
        2. Opens the serial port connection
        3. Tests the connection by reading a coil
        4. Sets connection status flags

        SERIAL PARAMETERS:
        - method='rtu': Remote Terminal Unit mode (binary protocol)
        - bytesize=8: 8 data bits per byte
        - parity='N': No parity checking
        - stopbits=1: 1 stop bit after each byte
        - timeout=1: 1 second timeout for responses

        Returns:
            bool: True if connection successful and PLC responds, False otherwise

        Raises:
            Exception: For serial port errors, permission issues, etc.
        """
        try:
            # Display connection attempt information
            print(f"Attempting to connect to PLC on {self.com_port}...")
            print(f"Baudrate: {self.baudrate}")
            print(f"Station ID: {self.station_id}")

            # STEP 1: Create Modbus RTU client with serial parameters
            # RTU mode is default for ModbusSerialClient in pymodbus 3.x
            self.client = ModbusSerialClient(
                port=self.com_port,        # Serial port (e.g., COM4)
                baudrate=self.baudrate,    # Speed: bits per second
                bytesize=8,                # Data bits: standard 8-bit bytes
                parity='N',                # Parity: None (no error checking)
                stopbits=1,                # Stop bits: standard 1 stop bit
                timeout=1                  # Response timeout: 1 second
            )

            # STEP 2: Attempt to open the serial port
            print("Opening serial port...")
            if self.client.connect():
                print("✅ Successfully connected to PLC!")
                self.is_connected = True

                # STEP 3: Test the connection by reading a coil
                # This verifies the PLC is responding and communication works
                print("Testing PLC communication...")
                try:
                    # Read coil at address 0 (common test address)
                    # unit=self.station_id specifies which PLC to talk to
                    result = self.client.read_coils(0, count=1, device_id=self.station_id)

                    # Check if the read was successful
                    if result and not result.isError():
                        print("✅ Connection test successful - PLC is responding")
                        print("PLC communication is working properly!")
                        return True
                    else:
                        print("❌ Connection test failed - PLC not responding")
                        print("PLC may be offline or configured incorrectly")
                        return False

                except Exception as e:
                    print(f"❌ Connection test failed: {e}")
                    print("This could indicate:")
                    print("  - PLC is not configured for Modbus")
                    print("  - Wrong station ID")
                    print("  - PLC communication settings mismatch")
                    return False
            else:
                print("❌ Failed to establish serial connection")
                print("This could indicate:")
                print("  - Serial port doesn't exist")
                print("  - Port is already in use")
                print("  - Permission denied")
                print("  - Cable not connected")
                return False

        except Exception as e:
            print(f"❌ Error establishing connection: {e}")
            print("Common causes:")
            print("  - Serial port driver not installed")
            print("  - Incorrect COM port number")
            print("  - Baudrate mismatch with PLC")
            print("  - Hardware connection issue")
            return False

    def read_single_coil(self, address):
        """
        Read a single coil (digital input/output) from the PLC.

        Coils in Modbus represent digital states:
        - True/ON = Logic HIGH (1) - device is active/energized
        - False/OFF = Logic LOW (0) - device is inactive/de-energized

        Common uses:
        - Digital inputs: Sensor states, button presses, limit switches
        - Digital outputs: Relay states, solenoid valves, indicator lights
        - Control flags: System status, error conditions

        Args:
            address (int): Coil address in the PLC (0-based numbering)

        Returns:
            bool or None: True if coil is ON, False if OFF, None if error

        Example:
            # Read coil at address 100 (often used for process status)
            status = plc.read_single_coil(100)
            if status:
                print("Process is running")
            else:
                print("Process is stopped")
        """
        # STEP 1: Verify connection before attempting to read
        if not self.is_connected or not self.client:
            print("❌ Not connected to PLC")
            print("Call establish_connection() first")
            return None

        try:
            # STEP 2: Send Modbus read request
            # address = starting coil address
            # 1 = number of coils to read
            # unit = PLC station ID (which PLC to talk to)
            result = self.client.read_coils(address, count=1, device_id=self.station_id)

            # STEP 3: Check if the read was successful
            if result and not result.isError():
                # Extract the coil value from the response
                # result.bits is a list of boolean values
                coil_value = result.bits[0]

                # Display the result in user-friendly format
                status = "ON" if coil_value else "OFF"
                print(f"✅ Coil {address}: {status}")

                # Return the boolean value for programmatic use
                return coil_value
            else:
                # Handle Modbus protocol errors
                print(f"❌ Error reading coil {address}: {result}")
                print("This could indicate:")
                print("  - Invalid coil address")
                print("  - PLC communication error")
                print("  - Address out of range")
                return None

        except Exception as e:
            # Handle general exceptions (serial errors, timeouts, etc.)
            print(f"❌ Error reading coil {address}: {e}")
            print("Possible causes:")
            print("  - Serial connection lost")
            print("  - PLC powered off")
            print("  - Cable disconnected")
            return None

    def read_multiple_coils(self, start_address, count):
        """
        Read multiple consecutive coils from the PLC in a single request.

        This is more efficient than reading individual coils when you need
        multiple adjacent coil values, as it reduces network overhead.

        Args:
            start_address (int): Starting coil address (0-based)
            count (int): Number of consecutive coils to read (1-2000 typical)

        Returns:
            list or None: List of boolean values, or None if error

        Example:
            # Read 8 coils starting from address 100 (addresses 100-107)
            coil_states = plc.read_multiple_coils(100, 8)
            if coil_states:
                for i, state in enumerate(coil_states):
                    addr = 100 + i
                    print(f"Coil {addr}: {'ON' if state else 'OFF'}")
        """
        # STEP 1: Verify connection
        if not self.is_connected or not self.client:
            print("❌ Not connected to PLC")
            print("Call establish_connection() first")
            return None

        try:
            # STEP 2: Send Modbus read request for multiple coils
            # This reads 'count' consecutive coils starting from 'start_address'
            result = self.client.read_coils(start_address, count=count, device_id=self.station_id)

            # STEP 3: Process the response
            if result and not result.isError():
                print(f"✅ Read {count} coils starting from address {start_address}:")

                # Display each coil's status
                for i, coil_value in enumerate(result.bits):
                    addr = start_address + i
                    status = "ON" if coil_value else "OFF"
                    print(f"  Coil {addr}: {status}")

                # Return the list of boolean values for programmatic use
                return result.bits
            else:
                # Handle Modbus protocol errors
                end_addr = start_address + count - 1
                print(f"❌ Error reading coils {start_address}-{end_addr}: {result}")
                print("This could indicate:")
                print("  - Invalid address range")
                print("  - PLC communication error")
                print(f"  - Range exceeds PLC memory (max {count} coils)")
                return None

        except Exception as e:
            # Handle general exceptions
            end_addr = start_address + count - 1
            print(f"❌ Error reading coils {start_address}-{end_addr}: {e}")
            print("Possible causes:")
            print("  - Serial connection lost")
            print("  - PLC communication timeout")
            return None

    def read_input_registers(self, start_address, count):
        """
        Read input registers (analog input values) from the PLC.

        Input Registers are 16-bit (2-byte) read-only values that typically store:
        - Analog sensor readings (temperature, pressure, flow)
        - Measurement values from ADCs (Analog-to-Digital Converters)
        - Counter values, timer values
        - Raw sensor data before scaling

        Value Range: 0-65535 (16-bit unsigned) or -32768 to +32767 (16-bit signed)
        Common scaling: Divide by 10, 100, or 1000 for decimal values

        Args:
            start_address (int): Starting input register address (0-based)
            count (int): Number of consecutive registers to read (1-125 typical)

        Returns:
            list or None: List of integer values, or None if error

        Example:
            # Read temperature sensor (addresses 0-1, scaled by 10)
            temp_regs = plc.read_input_registers(0, 2)
            if temp_regs:
                # Combine two 16-bit registers into one 32-bit value
                raw_temp = (temp_regs[0] << 16) + temp_regs[1]
                temperature = raw_temp / 10.0  # Scale by 10
                print(f"Temperature: {temperature}°C")
        """
        # STEP 1: Verify connection
        if not self.is_connected or not self.client:
            print("❌ Not connected to PLC")
            print("Call establish_connection() first")
            return None

        try:
            # STEP 2: Send Modbus read request for input registers
            # Input registers are read-only analog values
            result = self.client.read_input_registers(start_address, count=count, device_id=self.station_id)

            # STEP 3: Process the response
            if result and not result.isError():
                print(f"✅ Read {count} input registers starting from address {start_address}:")

                # Display each register's value
                for i, register_value in enumerate(result.registers):
                    addr = start_address + i
                    print(f"  Input Register {addr}: {register_value}")

                # Return the list of register values
                return result.registers
            else:
                # Handle Modbus protocol errors
                end_addr = start_address + count - 1
                print(f"❌ Error reading input registers {start_address}-{end_addr}: {result}")
                print("This could indicate:")
                print("  - Invalid register address")
                print("  - PLC communication error")
                print("  - Register not configured as input")
                return None

        except Exception as e:
            # Handle general exceptions
            end_addr = start_address + count - 1
            print(f"❌ Error reading input registers {start_address}-{end_addr}: {e}")
            print("Possible causes:")
            print("  - Serial connection lost")
            print("  - PLC communication timeout")
            return None

    def read_holding_registers(self, start_address, count):
        """
        Read holding registers (read/write analog values) from the PLC.

        Holding Registers are 16-bit (2-byte) read/write values that typically store:
        - Configuration parameters (setpoints, limits, PID settings)
        - Control values (speed, position, pressure setpoints)
        - System parameters (calibration values, scaling factors)
        - Recipe data and process parameters

        Value Range: 0-65535 (16-bit unsigned) or -32768 to +32767 (16-bit signed)
        These can be both read and written to (unlike input registers)

        Args:
            start_address (int): Starting holding register address (0-based)
            count (int): Number of consecutive registers to read (1-125 typical)

        Returns:
            list or None: List of integer values, or None if error

        Example:
            # Read PID setpoint (address 4000, scaled by 100)
            pid_regs = plc.read_holding_registers(4000, 2)
            if pid_regs:
                # Combine two 16-bit registers for higher precision
                setpoint = (pid_regs[0] << 16) + pid_regs[1]
                setpoint_value = setpoint / 100.0  # Scale by 100
                print(f"PID Setpoint: {setpoint_value}")
        """
        # STEP 1: Verify connection
        if not self.is_connected or not self.client:
            print("❌ Not connected to PLC")
            print("Call establish_connection() first")
            return None

        try:
            # STEP 2: Send Modbus read request for holding registers
            # Holding registers are read/write analog values
            result = self.client.read_holding_registers(start_address, count=count, device_id=self.station_id)

            # STEP 3: Process the response
            if result and not result.isError():
                print(f"✅ Read {count} holding registers starting from address {start_address}:")

                # Display each register's value
                for i, register_value in enumerate(result.registers):
                    addr = start_address + i
                    print(f"  Holding Register {addr}: {register_value}")

                # Return the list of register values
                return result.registers
            else:
                # Handle Modbus protocol errors
                end_addr = start_address + count - 1
                print(f"❌ Error reading holding registers {start_address}-{end_addr}: {result}")
                print("This could indicate:")
                print("  - Invalid register address")
                print("  - PLC communication error")
                print("  - Register not configured as holding")
                return None

        except Exception as e:
            # Handle general exceptions
            end_addr = start_address + count - 1
            print(f"❌ Error reading holding registers {start_address}-{end_addr}: {e}")
            print("Possible causes:")
            print("  - Serial connection lost")
            print("  - PLC communication timeout")
            return None

    def continuous_monitoring(self, addresses_to_monitor, interval=1.0):
        """
        Continuously monitor specified coil addresses at regular intervals.

        This method provides real-time monitoring of PLC coil states, useful for:
        - Process monitoring and control
        - System status monitoring
        - Debugging PLC programs
        - Alarm monitoring
        - Production line status tracking

        Args:
            addresses_to_monitor (list): List of coil addresses to monitor
            interval (float): Time between updates in seconds (default: 1.0)

        Returns:
            None: Runs indefinitely until interrupted

        Example:
            # Monitor critical process coils
            critical_addresses = [100, 101, 102, 200, 201]
            plc.continuous_monitoring(critical_addresses, interval=2.0)

        Notes:
        - Press Ctrl+C to stop monitoring
        - High-frequency monitoring (< 0.5s) may impact PLC performance
        - Consider PLC scan time when setting intervals
        """
        # STEP 1: Verify connection before starting monitoring
        if not self.is_connected:
            print("❌ Not connected to PLC")
            print("Call establish_connection() first")
            return

        # STEP 2: Display monitoring configuration
        print(f"\n🔄 Starting continuous monitoring of {len(addresses_to_monitor)} addresses...")
        print(f"Addresses to monitor: {addresses_to_monitor}")
        print(f"Update interval: {interval} seconds")
        print("Press Ctrl+C to stop monitoring\n")

        try:
            # STEP 3: Main monitoring loop
            while True:
                # Display timestamp for each update cycle
                timestamp = time.strftime('%H:%M:%S')
                print(f"\n--- PLC Status Update ({timestamp}) ---")

                # Read each coil in the monitoring list
                for addr in addresses_to_monitor:
                    self.read_single_coil(addr)

                # Wait for the specified interval before next update
                time.sleep(interval)

        except KeyboardInterrupt:
            # Handle user interruption (Ctrl+C)
            print("\n🛑 Monitoring stopped by user")
            print("Returning to main menu...")

        except Exception as e:
            # Handle unexpected errors during monitoring
            print(f"\n❌ Error during monitoring: {e}")
            print("Monitoring stopped due to error")
            print("Check PLC connection and try again")

    def disconnect(self):
        """
        Properly disconnect from the PLC and clean up resources.

        This method ensures clean disconnection by:
        1. Closing the Modbus client connection
        2. Resetting connection flags
        3. Releasing serial port resources

        Always call this method when finished with PLC communication
        to prevent resource leaks and connection issues.

        Returns:
            None

        Example:
            plc = PLCCoilReader()
            if plc.establish_connection():
                # ... do work ...
                plc.disconnect()  # Always disconnect when done
        """
        try:
            # STEP 1: Check if client exists and close connection
            if self.client:
                # Close the Modbus client connection
                self.client.close()
                print("✅ Disconnected from PLC")
                print("Serial port released")

            # STEP 2: Reset connection state
            self.is_connected = False
            self.client = None

        except Exception as e:
            # Handle disconnection errors gracefully
            print(f"❌ Error disconnecting: {e}")
            print("Connection may not have been properly closed")
            # Still reset state even if close failed
            self.is_connected = False
            self.client = None

def main():
    """
    Interactive main function that provides a menu-driven interface for PLC operations.

    This function creates a PLCCoilReader instance and provides an interactive menu
    for testing different PLC communication features. It's designed for:
    - Initial PLC connection testing
    - Manual coil and register reading
    - Troubleshooting communication issues
    - Learning PLC addressing schemes

    MENU OPTIONS:
    1. Read single coil - Test individual digital inputs/outputs
    2. Read multiple coils - Efficiently read ranges of coils
    3. Read input registers - Read analog sensor values
    4. Read holding registers - Read configuration values
    5. Continuous monitoring - Real-time status monitoring
    6. Test common addresses - Quick test of typical PLC addresses

    The function includes comprehensive error handling and ensures
    proper cleanup of connections.

    Returns:
        None: Runs until user chooses to quit

    Usage:
        python plc_coil_reader.py
    """
    # STEP 1: Display welcome message and program information
    print("🛠️  PLC Coil Reader")
    print("=" * 50)
    print("Interactive PLC Communication Tool")
    print("Connects to PLC via COM4 and reads coils/registers")
    print("=" * 50)

    # STEP 2: Create PLC reader instance with COM4 configuration
    # These settings match your specified configuration
    print("Using PLC Configuration:")
    print("  COM Port: COM4")
    print("  Baudrate: 38400")
    print("  Station ID: 1")
    print("  Protocol: Modbus RTU")
    print()

    plc_reader = PLCCoilReader(
        com_port="COM4",      # Serial port as specified
        baudrate=38400,       # Communication speed as specified
        station_id=1          # PLC slave address as specified
    )

    try:
        # STEP 3: Establish connection to PLC
        print("Connecting to PLC...")
        if not plc_reader.establish_connection():
            print("❌ Failed to connect to PLC. Exiting...")
            print("\nTroubleshooting tips:")
            print("- Check that PLC is powered on")
            print("- Verify COM4 is the correct port")
            print("- Ensure baudrate matches PLC settings")
            print("- Check RS-485 cable connection")
            return

        # STEP 4: Display main menu
        print("\n" + "=" * 50)
        print("📋 Available Operations:")
        print("1. Read single coil        - Read one digital input/output")
        print("2. Read multiple coils     - Read range of digital values")
        print("3. Read input registers    - Read analog sensor values")
        print("4. Read holding registers  - Read configuration values")
        print("5. Continuous monitoring   - Real-time status monitoring")
        print("6. Test common addresses   - Quick test of typical addresses")
        print("=" * 50)

        # STEP 5: Main interactive loop
        while True:
            try:
                # Get user choice
                choice = input("\nEnter operation number (or 'q' to quit): ").strip().lower()

                # STEP 6: Process user choice
                if choice == 'q':
                    # User wants to quit
                    print("Exiting PLC Coil Reader...")
                    break

                elif choice == '1':
                    # Read single coil
                    try:
                        addr = int(input("Enter coil address (0-based): "))
                        plc_reader.read_single_coil(addr)
                    except ValueError:
                        print("❌ Please enter a valid number")

                elif choice == '2':
                    # Read multiple coils
                    try:
                        start_addr = int(input("Enter start address: "))
                        count = int(input("Enter number of coils to read: "))
                        plc_reader.read_multiple_coils(start_addr, count)
                    except ValueError:
                        print("❌ Please enter valid numbers")

                elif choice == '3':
                    # Read input registers
                    try:
                        start_addr = int(input("Enter start address: "))
                        count = int(input("Enter number of registers: "))
                        plc_reader.read_input_registers(start_addr, count)
                    except ValueError:
                        print("❌ Please enter valid numbers")

                elif choice == '4':
                    # Read holding registers
                    try:
                        start_addr = int(input("Enter start address: "))
                        count = int(input("Enter number of registers: "))
                        plc_reader.read_holding_registers(start_addr, count)
                    except ValueError:
                        print("❌ Please enter valid numbers")

                elif choice == '5':
                    # Continuous monitoring
                    try:
                        addresses_input = input("Enter addresses to monitor (comma-separated): ")
                        addresses = [int(addr.strip()) for addr in addresses_input.split(',')]
                        interval_input = input("Enter monitoring interval (seconds, default 1.0): ").strip()
                        interval = float(interval_input) if interval_input else 1.0
                        plc_reader.continuous_monitoring(addresses, interval)
                    except ValueError:
                        print("❌ Invalid input format")

                elif choice == '6':
                    # Test common addresses
                    print("\n🔍 Testing common PLC coil addresses...")
                    print("This will test addresses typically used for:")
                    print("- System status (0, 1)")
                    print("- Process control (100, 101)")
                    print("- Machine control (1000, 1001)")
                    print()

                    # Test common coil addresses with small delays
                    common_addresses = [0, 1, 100, 101, 1000, 1001]
                    for addr in common_addresses:
                        plc_reader.read_single_coil(addr)
                        time.sleep(0.1)  # Small delay to prevent overwhelming PLC

                    print("\n✅ Common address test completed")

                else:
                    # Invalid choice
                    print("❌ Invalid choice. Please enter 1-6 or 'q' to quit.")
                    print("Type 'q' to quit the program")

            except ValueError:
                # Handle invalid number input
                print("❌ Invalid number format. Please try again.")

            except KeyboardInterrupt:
                # Handle Ctrl+C interruption
                print("\n🛑 Operation interrupted by user")
                break

            except Exception as e:
                # Handle unexpected errors
                print(f"❌ Error: {e}")
                print("Please try again or check PLC connection")
                traceback.print_exc()

    except Exception as e:
        # Handle fatal errors in main setup
        print(f"❌ Fatal error: {e}")
        print("PLC Coil Reader cannot continue")
        traceback.print_exc()

    finally:
        # STEP 7: Always ensure proper cleanup
        # This runs even if there was an error
        print("\n🔌 Cleaning up connections...")
        plc_reader.disconnect()
        print("👋 PLC Coil Reader terminated")
        print("Thank you for using PLC Coil Reader!")

if __name__ == "__main__":
    main()

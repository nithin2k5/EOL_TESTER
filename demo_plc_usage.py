#!/usr/bin/env python3
"""
Demonstration of PLC Coil Reader Usage
Complete examples showing various ways to read PLC coils and registers

This script demonstrates the full capabilities of the PLCCoilReader class:

1. BASIC CONNECTION: Simple connection test
2. COIL READING: Single and multiple coil operations
3. REGISTER READING: Input and holding register access
4. CONTINUOUS MONITORING: Real-time status monitoring
5. ERROR HANDLING: Graceful handling of communication issues

USAGE:
    python demo_plc_usage.py

REQUIREMENTS:
    - PyModbus library: pip install pymodbus
    - PLC connected to COM4
    - PLC configured for Modbus RTU protocol

Each demo function is self-contained and includes:
    - Setup and connection
    - Operation execution
    - Result display
    - Error handling
    - Clean disconnection

AUTHOR: AI Assistant
VERSION: 1.0
"""

from plc_coil_reader import PLCCoilReader
import time

def demo_basic_connection():
    """
    Demonstrate the most basic PLC connection and disconnection.

    This demo shows the fundamental connection process:
    1. Create PLCCoilReader instance with connection parameters
    2. Establish connection using establish_connection()
    3. Verify connection was successful
    4. Properly disconnect to free resources

    This is the minimum code needed to connect to a PLC.
    """
    print("🔌 Basic Connection Demo")
    print("-" * 30)
    print("Demonstrating basic PLC connection and disconnection")
    print()

    # Create PLC reader with explicit parameters
    # In a real application, you might load these from a config file
    plc = PLCCoilReader(
        com_port="COM4",      # Serial port (must match your setup)
        baudrate=38400,       # Communication speed (must match PLC)
        station_id=1          # PLC slave address (usually 1 for single PLC)
    )

    # Attempt to establish connection
    if plc.establish_connection():
        print("✅ Connected to PLC successfully!")
        print("PLC is responding to Modbus commands")
        plc.disconnect()  # Always disconnect when done
        return True
    else:
        print("❌ Failed to connect to PLC")
        print("Check PLC power, COM port, and cable connection")
        return False

def demo_coil_reading():
    """
    Demonstrate various coil reading operations.

    This demo shows three different ways to read PLC coils:
    1. Single coil reading - Read one coil at a time
    2. Multiple coil reading - Read a range of coils efficiently
    3. Process status monitoring - Read coils commonly used for process control

    Coil addresses demonstrated:
    - Address 0: Often used for system status
    - Addresses 100-104: Process control coils
    - Addresses 105-107: Status monitoring coils
    """
    print("\n📊 Coil Reading Demo")
    print("-" * 30)
    print("Demonstrating different coil reading techniques")
    print()

    # Create PLC reader with default settings (COM4, 38400, station 1)
    plc = PLCCoilReader()

    # Establish connection
    if not plc.establish_connection():
        print("Cannot demonstrate coil reading - connection failed")
        return

    try:
        # DEMO 1: Read single coil
        print("🔸 Reading single coil at address 0:")
        print("Coils represent digital ON/OFF states")
        result = plc.read_single_coil(0)
        if result is not None:
            print(f"   Result: {'System is ACTIVE' if result else 'System is INACTIVE'}")

        # DEMO 2: Read multiple coils efficiently
        print("\n🔸 Reading 5 coils starting from address 100:")
        print("Multiple coil reading is more efficient for consecutive addresses")
        results = plc.read_multiple_coils(100, 5)
        if results:
            print("   Analyzing results:")
            for i, coil_state in enumerate(results):
                addr = 100 + i
                purpose = ["Process Start", "Process Stop", "Emergency Stop", "Reset", "Auto Mode"][i] if i < 5 else f"Coil {addr}"
                print(f"   {purpose} (addr {addr}): {'ACTIVE' if coil_state else 'INACTIVE'}")

        # DEMO 3: Read process status coils
        print("\n🔸 Reading process status coils (addresses 105-107):")
        print("These addresses commonly monitor process states")
        process_addresses = [
            (105, "Process Running"),
            (106, "Process Complete"),
            (107, "Process Error")
        ]

        for addr, description in process_addresses:
            print(f"   {description}: ", end="")
            result = plc.read_single_coil(addr)
            if result is not None:
                print(f"{'YES' if result else 'NO'}")
            else:
                print("UNKNOWN")
            time.sleep(0.1)  # Small delay between reads

        print("\n✅ Coil reading demonstration completed!")

    finally:
        # Always disconnect to free resources
        plc.disconnect()
        print("Disconnected from PLC")

def demo_register_reading():
    """
    Demonstrate reading analog values from PLC registers.

    This demo shows how to read both input registers and holding registers:

    INPUT REGISTERS (read-only):
    - Contain analog sensor readings (temperature, pressure, flow)
    - Counter values, timer values
    - Raw ADC (Analog-to-Digital Converter) data
    - Range: 0-65535 (16-bit values)

    HOLDING REGISTERS (read/write):
    - Configuration parameters (setpoints, limits)
    - Control values (speed, position, pressure setpoints)
    - System parameters (calibration values)
    - Can be both read and written to

    Scaling: Values often need division by 10, 100, or 1000 for decimal precision.
    """
    print("\n📈 Register Reading Demo")
    print("-" * 30)
    print("Reading analog values from PLC registers")
    print("Note: Values may need scaling for actual measurements")
    print()

    plc = PLCCoilReader()

    if not plc.establish_connection():
        print("Cannot demonstrate register reading - connection failed")
        return

    try:
        # DEMO 1: Read input registers (analog sensor data)
        print("🔸 Reading input registers 0-7 (analog sensor values):")
        print("Input registers are read-only and store sensor measurements")
        input_results = plc.read_input_registers(0, 8)
        if input_results:
            print("   Sample scaling examples:")
            for i, value in enumerate(input_results[:3]):  # Show first 3 examples
                scaled_by_10 = value / 10.0
                scaled_by_100 = value / 100.0
                print(f"   Register {i}: {value} → {scaled_by_10} (÷10) or {scaled_by_100} (÷100)")
        print()

        # DEMO 2: Read holding registers (configuration values)
        print("🔸 Reading holding registers 0-3 (configuration values):")
        print("Holding registers are read/write and often store setpoints")
        plc.read_holding_registers(0, 4)

        print("\n✅ Register reading demonstration completed!")
        print("💡 Tip: Check your PLC documentation for correct scaling factors")
        print("   Common factors: ÷10 (one decimal), ÷100 (two decimals), ÷1000 (three decimals)")

    finally:
        plc.disconnect()
        print("Disconnected from PLC")

def demo_continuous_monitoring():
    """
    Demonstrate continuous monitoring of PLC coil states.

    This demo shows how to monitor PLC coils in real-time for:
    - Process control and monitoring
    - System status tracking
    - Debugging PLC programs
    - Quality control monitoring
    - Production line status

    The demo monitors key coil addresses for 10 seconds with updates every 2 seconds.
    In a real application, this would run continuously for process monitoring.
    """
    print("\n🔄 Continuous Monitoring Demo")
    print("-" * 30)
    print("Real-time monitoring of PLC coil states")
    print("This demo will monitor for 10 seconds with 2-second updates")
    print("In production, this would run continuously")
    print("Press Ctrl+C to stop early")
    print()

    plc = PLCCoilReader()

    if not plc.establish_connection():
        print("Cannot demonstrate monitoring - connection failed")
        return

    try:
        # Define addresses to monitor with their typical purposes
        addresses_to_monitor = [
            (0, "System Power/Status"),
            (1, "System Ready"),
            (100, "Process Start"),
            (101, "Process Active")
        ]

        print("🔸 Starting continuous monitoring...")
        print("Addresses being monitored:")
        for addr, purpose in addresses_to_monitor:
            print(f"  - Coil {addr}: {purpose}")
        print("  Update interval: 2 seconds")
        print("  Duration: 10 seconds")
        print()

        # Monitor for 10 seconds with 2-second intervals
        addresses_only = [addr for addr, _ in addresses_to_monitor]
        start_time = time.time()

        while time.time() - start_time < 10:  # Monitor for 10 seconds
            current_time = time.strftime('%H:%M:%S')
            print(f"--- PLC Status Update ({current_time}) ---")

            # Read each coil and show its purpose
            for addr, purpose in addresses_to_monitor:
                result = plc.read_single_coil(addr)
                if result is not None:
                    status = "ACTIVE" if result else "INACTIVE"
                    print(f"  {purpose}: {status}")
                else:
                    print(f"  {purpose}: ERROR")
            print()

            time.sleep(2)  # Update every 2 seconds

        print("✅ Monitoring demo completed successfully!")
        print("💡 In production, use continuous_monitoring() method for ongoing monitoring")

    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        print("This is normal - monitoring can be stopped at any time")
    finally:
        plc.disconnect()
        print("Disconnected from PLC")

def demo_error_handling():
    """
    Demonstrate error handling and recovery capabilities.

    This demo shows how the PLC reader handles various error conditions:
    - Invalid COM ports
    - PLC not responding
    - Connection timeouts
    - Hardware communication issues

    The goal is to show that the library fails gracefully and provides
    helpful error messages for troubleshooting.
    """
    print("\n⚠️  Error Handling Demo")
    print("-" * 30)
    print("Demonstrating error handling and recovery")
    print("This will intentionally try to connect to invalid configurations")
    print()

    # DEMO 1: Try to connect to non-existent COM port
    print("🔸 Test 1: Attempting connection to non-existent COM port...")
    print("Trying to connect to COM99 (which doesn't exist)")
    plc_invalid_port = PLCCoilReader(com_port="COM99")

    if plc_invalid_port.establish_connection():
        print("❌ Unexpected success - should have failed!")
        plc_invalid_port.disconnect()
    else:
        print("✅ Correctly handled connection failure")
        print("   Error was properly detected and reported")

    # Clean up
    plc_invalid_port.disconnect()
    print()

    # DEMO 2: Try to connect with wrong baudrate
    print("🔸 Test 2: Attempting connection with wrong baudrate...")
    print("Using baudrate 9600 instead of correct 38400")
    plc_wrong_baud = PLCCoilReader(com_port="COM4", baudrate=9600)

    if plc_wrong_baud.establish_connection():
        print("❌ Unexpected success with wrong baudrate!")
        plc_wrong_baud.disconnect()
    else:
        print("✅ Correctly detected baudrate mismatch")

    # Clean up
    plc_wrong_baud.disconnect()
    print()

    print("✅ Error handling demonstration completed!")
    print("💡 The PLC reader provides clear error messages for troubleshooting")
    print("   Always check:")
    print("   - COM port number")
    print("   - Baudrate settings")
    print("   - PLC power and configuration")
    print("   - Cable connections")

def main():
    """Run all demonstrations"""
    print("🛠️  PLC Coil Reader Demonstration")
    print("=" * 50)
    print("This demo will show various PLC reading capabilities")
    print("Make sure your PLC is connected to COM4 and powered on")
    print("=" * 50)

    # Run demonstrations
    if not demo_basic_connection():
        print("\n❌ Basic connection failed. Please check:")
        print("  - PLC is powered on")
        print("  - COM4 is the correct port")
        print("  - Cable connections are secure")
        print("  - PLC communication settings match")
        return

    demo_coil_reading()
    demo_register_reading()
    demo_continuous_monitoring()
    demo_error_handling()

    print("\n🎉 All demonstrations completed!")
    print("\nTo use the PLC reader in your own code:")
    print("from plc_coil_reader import PLCCoilReader")
    print("plc = PLCCoilReader()")
    print("if plc.establish_connection():")
    print("    # Read coils and registers")
    print("    plc.disconnect()")

if __name__ == "__main__":
    main()

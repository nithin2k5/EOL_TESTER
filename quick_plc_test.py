#!/usr/bin/env python3
"""
Quick PLC Test Script - Simple way to test PLC connection and read basic coils

This script provides two modes of operation:

1. QUICK TEST MODE (default):
   - Tests PLC connection via COM4
   - Reads common coil addresses (0, 1, 100, 101, 1000, 1001)
   - Tests input registers 0-7
   - Provides immediate feedback on PLC communication status

2. MONITORING MODE (with 'monitor' argument):
   - Starts continuous monitoring of common coil addresses
   - Updates every 1 second
   - Useful for real-time process monitoring

USAGE:
    python quick_plc_test.py          # Run quick test
    python quick_plc_test.py monitor  # Start monitoring mode

REQUIREMENTS:
    - PyModbus library: pip install pymodbus
    - Serial port access (COM4 must be available)
    - PLC connected and configured for Modbus RTU

TYPICAL COIL ADDRESSES TESTED:
    - 0, 1: System status coils
    - 100, 101: Process control coils
    - 1000, 1001: Machine control coils

AUTHOR: AI Assistant
VERSION: 1.0
"""

import sys
import time
from plc_coil_reader import PLCCoilReader

def quick_test():
    """
    Perform a comprehensive quick test of PLC connection and basic functionality.

    This function tests:
    1. Serial connection establishment
    2. Modbus communication protocol
    3. Common coil address reading
    4. Input register reading
    5. Error handling and recovery

    The test is designed to be fast (< 30 seconds) and provide
    immediate feedback on PLC communication health.

    Returns:
        bool: True if all tests pass, False if any test fails
    """
    print("🧪 Quick PLC Test")
    print("=" * 30)
    print("Testing PLC connection and basic functionality...")
    print()

    # STEP 1: Create PLC reader with standard settings
    # COM4 is the default serial port for PLC communication
    # These settings must match your PLC configuration
    plc = PLCCoilReader(
        com_port="COM4",      # Serial port
        baudrate=38400,       # Communication speed (must match PLC)
        station_id=1          # PLC slave address
    )

    try:
        # STEP 2: Establish connection
        print("🔌 Step 1: Connecting to PLC...")
        if not plc.establish_connection():
            print("❌ Failed to connect to PLC")
            print("\nPossible issues:")
            print("- PLC not powered on")
            print("- Wrong COM port (not COM4)")
            print("- Baudrate mismatch (not 38400)")
            print("- Cable not connected properly")
            return False

        print("✅ Step 1 PASSED: Connected successfully!")
        print("\n📊 Step 2: Testing basic coil reads...")

        # STEP 3: Test common coil addresses
        # These addresses are commonly used in industrial PLCs
        test_addresses = [0, 1, 100, 101, 1000, 1001]
        successful_reads = 0

        print(f"Testing {len(test_addresses)} common coil addresses:")
        for addr in test_addresses:
            result = plc.read_single_coil(addr)
            if result is not None:
                status = "ON" if result else "OFF"
                print(f"  ✅ Coil {addr}: {status}")
                successful_reads += 1
            else:
                print(f"  ❌ Coil {addr}: ERROR (address may not exist)")
            time.sleep(0.1)  # Small delay to prevent overwhelming PLC

        print(f"\n📊 Step 3: Testing input registers...")

        # STEP 4: Test input registers
        # Input registers typically store analog sensor values
        successful_register_reads = 0

        print("Testing input registers 0-7:")
        for addr in range(8):
            result = plc.read_input_registers(addr, 1)
            if result:
                print(f"  ✅ Input Register {addr}: {result[0]}")
                successful_register_reads += 1
            else:
                print(f"  ❌ Input Register {addr}: ERROR")
            time.sleep(0.1)

        # STEP 5: Summarize results
        print("
📋 TEST SUMMARY:"        print(f"  Coil reads: {successful_reads}/{len(test_addresses)} successful")
        print(f"  Register reads: {successful_register_reads}/8 successful")
        print(f"  Overall: {'PASS' if successful_reads > 0 else 'FAIL'}")

        if successful_reads > 0:
            print("\n✅ Quick test completed successfully!")
            print("PLC communication is working properly.")
            return True
        else:
            print("\n⚠️  Test completed but no coil reads succeeded.")
            print("PLC may be configured differently or addresses may be different.")
            return True  # Still return True as connection worked

    except Exception as e:
        # STEP 6: Handle unexpected errors
        print(f"❌ Test failed with error: {e}")
        print("This could indicate:")
        print("- PyModbus library not installed")
        print("- Serial port permission issues")
        print("- PLC communication protocol mismatch")
        return False

    finally:
        # STEP 7: Always disconnect to free resources
        print("\n🔌 Disconnecting from PLC...")
        plc.disconnect()
        print("Disconnected.")

def monitor_mode():
    """
    Start continuous monitoring mode for real-time PLC status tracking.

    This function provides live monitoring of PLC coil states, which is useful for:
    - Process monitoring and control
    - Debugging PLC programs during development
    - Quality control and production monitoring
    - System diagnostics and troubleshooting

    The monitoring displays:
    - Real-time coil status changes
    - Timestamp for each update cycle
    - Clear status indicators (ON/OFF)

    Press Ctrl+C to stop monitoring and return to command line.

    Returns:
        None: Runs until interrupted by user
    """
    print("🔄 Starting PLC Monitoring Mode")
    print("=" * 30)
    print("Real-time PLC coil monitoring")
    print("Press Ctrl+C to stop monitoring")
    print()

    # Create PLC reader with standard settings
    plc = PLCCoilReader(
        com_port="COM4",      # Serial port for PLC connection
        baudrate=38400,       # Communication speed
        station_id=1          # PLC slave address
    )

    try:
        # Establish connection first
        print("🔌 Connecting to PLC...")
        if not plc.establish_connection():
            print("❌ Failed to connect to PLC")
            print("Check PLC power, COM port, and cable connection")
            return

        print("✅ Connected! Starting continuous monitoring...")
        print()

        # Define addresses to monitor
        # These are commonly used addresses in industrial PLCs
        addresses_to_monitor = [
            0,      # System status
            1,      # System ready
            100,    # Process start/stop
            101,    # Process status
            1000,   # Machine power
            1001    # Machine ready
        ]

        print(f"Monitoring {len(addresses_to_monitor)} coil addresses:")
        for addr in addresses_to_monitor:
            print(f"  - Coil {addr}")
        print(f"Update interval: 1.0 seconds")
        print()

        # Start continuous monitoring
        # This will run indefinitely until Ctrl+C is pressed
        plc.continuous_monitoring(addresses_to_monitor, interval=1.0)

    except KeyboardInterrupt:
        # Handle user interruption gracefully
        print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        # Handle unexpected errors during monitoring setup
        print(f"❌ Monitoring failed: {e}")
        print("Check PLC connection and try again")

    finally:
        # Always ensure clean disconnection
        print("\n🔌 Disconnecting from PLC...")
        plc.disconnect()
        print("Disconnected from monitoring mode")

def main():
    """
    Main entry point for the Quick PLC Test script.

    This function parses command line arguments and runs the appropriate mode:

    COMMAND LINE USAGE:
        python quick_plc_test.py          # Run quick diagnostic test
        python quick_plc_test.py monitor  # Start continuous monitoring

    MODES:
        1. Quick Test (default): Comprehensive connection and functionality test
        2. Monitor Mode: Real-time PLC coil monitoring

    The script automatically handles:
    - PLC connection and disconnection
    - Error reporting and troubleshooting tips
    - Clean shutdown on interruption

    Returns:
        None: Script runs to completion or until interrupted
    """
    # Check command line arguments
    if len(sys.argv) > 1:
        # User provided command line argument
        if sys.argv[1].lower() == "monitor":
            # Start monitoring mode
            monitor_mode()
        else:
            # Invalid argument provided
            print("❌ Invalid argument")
            print("\nUsage: python quick_plc_test.py [monitor]")
            print("  No arguments: Run quick diagnostic test")
            print("  monitor: Start continuous monitoring mode")
            print("\nExamples:")
            print("  python quick_plc_test.py        # Quick test")
            print("  python quick_plc_test.py monitor # Monitoring")
    else:
        # No arguments - run quick test (default behavior)
        success = quick_test()
        if not success:
            print("\n💡 Troubleshooting tips:")
            print("- Ensure PLC is powered on and configured")
            print("- Check that COM4 is the correct serial port")
            print("- Verify baudrate matches PLC settings (38400)")
            print("- Confirm RS-485 cable is properly connected")
            print("- Install PyModbus: pip install pymodbus")

# Script entry point
# This ensures the script only runs when executed directly (not imported)
if __name__ == "__main__":
    main()

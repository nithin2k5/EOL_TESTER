#!/usr/bin/env python3
"""
Test PLC Connection on COM4
Simple script to verify PLC communication with specified configuration
"""

import os
import time
from plc_coil_reader import PLCCoilReader

def test_com4_connection():
    """Test PLC connection using configuration from plc_config.json"""
    print("🔌 Testing PLC Connection")
    print("=" * 40)
    
    # Create PLC reader - it will load configuration from plc_config.json
    plc = PLCCoilReader()
    
    print("Configuration:")
    print(f"  COM Port: {plc.com_port}")
    print(f"  Baudrate: {plc.baudrate}")
    print(f"  Station ID: {plc.station_id}")
    print("  Protocol: Modbus RTU")
    print()

    try:
        print("1. Attempting to establish connection...")
        if not plc.establish_connection():
            print("\n❌ Connection failed!")
            print("\nTroubleshooting steps:")
            print("  ✓ Check that PLC is powered on")
            print("  ✓ Verify COM5 is the correct serial port")
            print("  ✓ Ensure baudrate matches PLC settings (38400)")
            print("  ✓ Check RS-485 cable connections")
            print("  ✓ Verify Station ID is correct (1)")
            print("  ✓ Try different COM ports if available")
            return False

        print("\n✅ Connection successful!")
        print("\n2. Testing basic coil reads...")

        # Test some common coil addresses
        test_addresses = [0, 1, 100, 101]
        successful_reads = 0

        for addr in test_addresses:
            result = plc.read_single_coil(addr)
            if result is not None:
                status = "ON" if result else "OFF"
                print(f"   Coil {addr}: {status}")
                successful_reads += 1
            else:
                print(f"   Coil {addr}: ERROR")
            time.sleep(0.1)

        print(f"\n3. Results: {successful_reads}/{len(test_addresses)} coils read successfully")

        if successful_reads > 0:
            print("\n✅ PLC communication is working!")
            print("You can now use the PLC coil reader with these settings.")
            return True
        else:
            print("\n⚠️  Connection works but no coil data received.")
            print("This might indicate:")
            print("  - PLC is configured with different coil addresses")
            print("  - PLC program is not running")
            print("  - Coil addresses are not configured in PLC")
            return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

    finally:
        print("\n🔌 Disconnecting from PLC...")
        plc.disconnect()

def test_available_ports():
    """Test which COM ports are available"""
    print("🔍 Checking available COM ports...")
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())

        if ports:
            print("Available COM ports:")
            for port in ports:
                print(f"  {port.device}: {port.description}")
            print()
            print("COM5 available:", any(p.device == "COM5" for p in ports))
        else:
            print("No COM ports found!")
            print("This could indicate:")
            print("  - No serial devices connected")
            print("  - Serial drivers not installed")
            print("  - Virtual COM ports not configured")
    except ImportError:
        print("❌ serial.tools.list_ports not available")
        print("Install with: pip install pyserial")

def main():
    """Main function"""
    print("🧪 COM4 PLC Connection Test")
    print("=" * 50)

    # First check available ports
    test_available_ports()
    print()

    # Test PLC connection
    success = test_com4_connection()

    print("\n" + "=" * 50)
    if success:
        print("✅ TEST COMPLETED: PLC connection successful!")
        print("\nNext steps:")
        print("  1. Use plc_coil_reader.py for interactive testing")
        print("  2. Use quick_plc_test.py for automated tests")
        print("  3. Run demo_plc_usage.py to see usage examples")
    else:
        print("❌ TEST FAILED: PLC connection unsuccessful")
        print("\nCheck your hardware setup and try again.")

if __name__ == "__main__":
    main()

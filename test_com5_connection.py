"""
Test COM5 Connection
===================

Simple script to test connection to COM5 specifically.
This will help troubleshoot the COM port connection issues.

Author: EOL Testing System
"""

import time
from pymodbus.client import ModbusSerialClient
from dotenv import load_dotenv
import os

def test_com5_connection():
    """Test connection to COM5 port"""
    print("🔌 Testing COM5 Connection")
    print("=" * 40)

    try:
        # Load environment variables
        load_dotenv()

        # Get configuration
        com_port = os.getenv('PLC_COM_PORT', 'COM5').strip("'")
        baud_rate = int(os.getenv('PLC_BAUD_RATE', '38400'))
        station_id = int(os.getenv('PLC_STATION_ID', '1'))

        print(f"Configuration:")
        print(f"  - COM Port: {com_port}")
        print(f"  - Baud Rate: {baud_rate}")
        print(f"  - Station ID: {station_id}")
        print()

        # Test 1: Basic port access
        print("1️⃣ Testing basic COM5 access...")
        try:
            import serial
            test_serial = serial.Serial(port=com_port, timeout=1)
            test_serial.close()
            print("   ✅ COM5 is accessible")
        except Exception as e:
            print(f"   ❌ COM5 access failed: {e}")
            return False

        # Test 2: Modbus connection
        print("2️⃣ Testing Modbus connection...")
        client = ModbusSerialClient(
            port=com_port,
            baudrate=baud_rate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=5
        )

        if client.connect():
            print("   ✅ Modbus connection successful")

            # Test 3: Read registers
            print("3️⃣ Testing register read...")
            try:
                result = client.read_holding_registers(address=0, count=5)
                if not result.isError():
                    print("   ✅ Register read successful")
                    print(f"   📊 Register values: {result.registers}")
                else:
                    print(f"   ⚠️ Register read failed: {result}")
            except Exception as e:
                print(f"   ❌ Register read error: {e}")

            # Clean up
            client.close()
            print("4️⃣ Connection closed successfully")
            return True

        else:
            print("   ❌ Modbus connection failed")
            return False

    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def test_available_ports():
    """Test all available COM ports"""
    print("\n🔍 Testing all available COM ports...")
    print("-" * 40)

    try:
        import serial.tools.list_ports
        ports = [port.device for port in serial.tools.list_ports.comports()]

        if not ports:
            print("❌ No COM ports found")
            return

        print(f"Found ports: {', '.join(ports)}")
        print()

        for port in ports:
            print(f"Testing {port}...")

            try:
                client = ModbusSerialClient(
                    port=port,
                    baudrate=38400,
                    bytesize=8,
                    parity='N',
                    stopbits=1,
                    timeout=3
                )

                if client.connect():
                    print(f"   ✅ {port}: Connected successfully")
                    client.close()
                else:
                    print(f"   ❌ {port}: Connection failed")

            except Exception as e:
                print(f"   ❌ {port}: Error - {e}")

            print()

    except Exception as e:
        print(f"❌ Error testing ports: {e}")

if __name__ == "__main__":
    print("🧪 COM Port Connection Test")
    print("=" * 50)

    # Test COM5 specifically
    success = test_com5_connection()

    # Test all available ports
    test_available_ports()

    print("\n" + "=" * 50)
    if success:
        print("✅ COM5 connection test PASSED")
    else:
        print("❌ COM5 connection test FAILED")
        print("💡 Try closing other applications using COM5")
        print("💡 Check device manager for COM port configuration")

#!/usr/bin/env python3
"""
Simple PLC Connection Test
"""

import os
from dotenv import load_dotenv
from pymodbus.client import ModbusSerialClient
import serial.tools.list_ports

def test_connection():
    """Test PLC connection and provide clear diagnostics"""

    print("🔍 PLC CONNECTION DIAGNOSTIC")
    print("=" * 40)

    # Load configuration
    load_dotenv()
    plc_port = os.getenv('PLC_COM_PORT', 'COM4')
    plc_baud = int(os.getenv('PLC_BAUD_RATE', '9600'))
    plc_id = int(os.getenv('PLC_STATION_ID', '1'))

    print(f"Configuration:")
    print(f"  Port: {plc_port}")
    print(f"  Baud Rate: {plc_baud}")
    print(f"  Station ID: {plc_id}")
    print()

    # Check available ports
    print("1. Available COM Ports:")
    ports = list(serial.tools.list_ports.comports())
    if ports:
        for port in ports:
            status = "✅" if port.device == plc_port else "📌"
            print(f"   {status} {port.device}: {port.description}")
    else:
        print("   ❌ No COM ports found!")
        return

    if not any(port.device == plc_port for port in ports):
        print(f"\n❌ {plc_port} is not available!")
        print("   Check USB cable connection")
        return

    print("\n2. Testing Serial Connection:")
    try:
        client = ModbusSerialClient(
            port=plc_port,
            baudrate=plc_baud,
            timeout=2,
            parity='N',
            stopbits=1,
            bytesize=8
        )

        if client.connect():
            print("   ✅ Serial port opened successfully")
            print(f"      Settings: {plc_port} | {plc_baud} baud | 8-N-1")
        else:
            print("   ❌ Failed to open serial port")
            return

    except Exception as e:
        print(f"   ❌ Serial connection error: {e}")
        return

    print("\n3. Testing PLC Communication:")    # Test basic PLC communication
    try:
        response = client.read_coils(0, count=1, device_id=plc_id)

        if response is None:
            print("   ❌ PLC Communication: NO RESPONSE")
            print("   This means no PLC is connected to COM4")
        elif response.isError():
            print("   ❌ PLC Communication: ERROR RESPONSE")
            print("   PLC is connected but not responding correctly")
        else:
            print("   ✅ PLC Communication: SUCCESS!")
            print(f"      Response received: {response.bits}")
            client.close()
            return True

    except Exception as e:
        print(f"   ❌ PLC Communication: EXCEPTION - {e}")

    client.close()

    print("\n🎯 DIAGNOSIS:")
    print("❌ The issue is: NO PLC DEVICE CONNECTED TO COM4")
    print()
    print("💡 SOLUTION:")
    print("   1. Connect a physical PLC device to COM4")
    print("   2. Power on the PLC")
    print("   3. Configure PLC for Modbus RTU protocol")
    print("   4. Ensure PLC slave ID matches (currently: 1)")
    print("   5. Verify baud rate (currently: 9600)")
    print()
    print("🧪 TEST AGAIN:")
    print("   Run: python connection_test.py")
    print("   Or use comport_settings.py GUI")

    return False

if __name__ == "__main__":
    test_connection()

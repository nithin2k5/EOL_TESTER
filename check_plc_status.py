"""
Check PLC Status
================

Script to check current PLC register values and provide guidance
on how to start the continuous cycling process.

Author: EOL Testing System
"""

import time
from pymodbus.client import ModbusSerialClient
from dotenv import load_dotenv
import os

def check_plc_registers():
    """Check current PLC register values"""
    print("🔍 Checking PLC Register Status")
    print("=" * 50)

    try:
        # Load configuration
        load_dotenv()
        com_port = os.getenv('PLC_COM_PORT', 'COM5').strip("'")
        baud_rate = int(os.getenv('PLC_BAUD_RATE', '38400'))
        station_id = int(os.getenv('PLC_STATION_ID', '1'))

        print(f"Connecting to: {com_port} @ {baud_rate} baud")
        print()

        # Connect to PLC
        client = ModbusSerialClient(
            port=com_port,
            baudrate=baud_rate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=5
        )

        if not client.connect():
            print("❌ Failed to connect to PLC")
            return False

        print("✅ Connected to PLC successfully")
        print()

        # Check multiple registers
        print("📊 Reading PLC Registers...")
        print("-" * 30)

        # Register mapping
        register_names = {
            0: "AUTO (M0067)",
            1: "HOME (M0068)",
            2: "PULL1_OK (M0076)",
            3: "PULL1_NG (M0085)",
            4: "PULL2_OK (M0078)",
            5: "PULL2_NG (M0087)",
            6: "TESTRESULT_OK (M0075)",
            7: "TESTRESULT_NG (M0079)"
        }

        # Read registers
        result = client.read_holding_registers(address=0, count=10)

        if result.isError():
            print(f"❌ Failed to read registers: {result}")
            client.close()
            return False

        print("Current Register Values:")
        print("-" * 30)

        registers = result.registers
        for i in range(min(10, len(registers))):
            reg_name = register_names.get(i, f"Register {i}")
            value = registers[i]
            status = "ON" if value else "OFF"
            print("12")

        print()
        print("🔍 ANALYSIS:")
        print("-" * 30)

        # Analyze current state
        auto_active = bool(registers[0] if len(registers) > 0 else 0)
        test_complete = bool((registers[6] if len(registers) > 6 else 0) or
                           (registers[7] if len(registers) > 7 else 0))

        if not auto_active:
            print("❌ AUTO mode is OFF - No cycles will start")
            print("💡 To start continuous cycling:")
            print("   1. Set M0067 (AUTO) to ON in your PLC")
            print("   2. Or use the process monitor to send AUTO command")
            print("   3. The monitor will then detect cycles and restart them")
        else:
            print("✅ AUTO mode is ON - Cycles should start")

        if test_complete:
            print("✅ A test cycle has completed")
            if registers[6] if len(registers) > 6 else False:
                print("   Result: PASS (TESTRESULT_OK)")
            elif registers[7] if len(registers) > 7 else False:
                print("   Result: FAIL (TESTRESULT_NG)")
        else:
            print("⏳ No completed test cycles detected")

        print()
        print("🚀 NEXT STEPS:")
        print("-" * 30)
        print("1. If AUTO is OFF: Enable AUTO mode in PLC")
        print("2. Monitor will automatically detect cycle starts")
        print("3. Monitor will detect completions and restart cycles")
        print("4. Use Ctrl+C to stop continuous monitoring")

        # Clean up
        client.close()
        print("\n✅ PLC status check completed")

        return True

    except Exception as e:
        print(f"❌ Error checking PLC status: {e}")
        return False

def send_auto_command():
    """Send AUTO command to start cycling"""
    print("\n🔧 Sending AUTO Command to PLC")
    print("=" * 40)

    try:
        # Load configuration
        load_dotenv()
        com_port = os.getenv('PLC_COM_PORT', 'COM5').strip("'")
        baud_rate = int(os.getenv('PLC_BAUD_RATE', '38400'))

        # Connect to PLC
        client = ModbusSerialClient(
            port=com_port,
            baudrate=baud_rate,
            bytesize=8,
            parity='N',
            stopbits=1,
            timeout=5
        )

        if not client.connect():
            print("❌ Failed to connect to PLC")
            return False

        print("✅ Connected to PLC")

        # Send AUTO command (M0067 = coil address 67)
        print("📡 Sending AUTO command (M0067 ON)...")

        result = client.write_coil(address=67, value=True)

        if not result.isError():
            print("✅ AUTO command sent successfully")
            print("💡 PLC should now be in AUTO mode")
            print("💡 Process monitor will detect this and start cycling")
        else:
            print(f"❌ Failed to send AUTO command: {result}")

        # Clean up
        client.close()
        return True

    except Exception as e:
        print(f"❌ Error sending AUTO command: {e}")
        return False

def main():
    """Main function"""
    print("🔍 PLC Status Checker & AUTO Command Sender")
    print("=" * 60)

    # Check current status
    if not check_plc_registers():
        print("❌ Cannot check PLC status - exiting")
        return 1

    # Ask user if they want to send AUTO command
    print("\n" + "=" * 60)
    response = input("Do you want to send AUTO command to start cycling? (y/N): ").lower().strip()

    if response in ['y', 'yes']:
        send_auto_command()
        print("\n💡 Now run: python process_monitor.py")
        print("   The monitor will detect AUTO mode and start continuous cycling")
    else:
        print("\n💡 To start cycling manually:")
        print("   1. Set M0067 (AUTO) to ON in your PLC")
        print("   2. Run: python process_monitor.py")
        print("   3. The monitor will detect cycles and restart them automatically")

    return 0

if __name__ == "__main__":
    exit(main())




"""
Test Real PLC Connection
Quick script to verify PLC connectivity before running the main application
"""

import os
from dotenv import load_dotenv
from pymodbus.client import ModbusSerialClient
import serial.tools.list_ports

# Load environment
load_dotenv('.env')

def list_available_ports():
    """List all available COM ports"""
    print("\n📋 Available COM Ports:")
    print("-" * 50)
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("   ❌ No COM ports found on this system")
        return []
    
    for port in ports:
        print(f"   ✓ {port.device}: {port.description}")
    return [port.device for port in ports]

def test_plc_connection():
    """Test PLC connection using configuration from .env"""
    print("\n" + "="*60)
    print("           REAL PLC CONNECTION TEST")
    print("="*60)
    
    # Load PLC configuration
    plc_com_port = os.getenv('PLC_COM_PORT', 'COM5').strip("'\"")
    plc_baud_rate = int(os.getenv('PLC_BAUD_RATE', '38400').strip("'\""))
    plc_station_id = int(os.getenv('PLC_STATION_ID', '1').strip("'\""))
    plc_bytesize = int(os.getenv('PLC_BYTESIZE', '8'))
    plc_parity = os.getenv('PLC_PARITY', 'N')
    plc_stopbits = int(os.getenv('PLC_STOPBITS', '1'))
    plc_timeout = float(os.getenv('PLC_TIMEOUT', '1.0'))
    
    print("\n🔧 Configuration from .env file:")
    print(f"   COM Port: {plc_com_port}")
    print(f"   Baud Rate: {plc_baud_rate}")
    print(f"   Station ID: {plc_station_id}")
    print(f"   Bytesize: {plc_bytesize}")
    print(f"   Parity: {plc_parity}")
    print(f"   Stopbits: {plc_stopbits}")
    print(f"   Timeout: {plc_timeout}s")
    
    # List available ports
    available_ports = list_available_ports()
    
    # Check if configured port is available
    if plc_com_port not in available_ports:
        print(f"\n❌ ERROR: Configured port {plc_com_port} is NOT available!")
        print(f"   Please check your configuration or update .env file")
        return False
    
    print(f"\n✓ Configured port {plc_com_port} is available")
    
    # Attempt connection
    print(f"\n🔌 Attempting to connect to PLC on {plc_com_port}...")
    
    try:
        client = ModbusSerialClient(
            port=plc_com_port,
            baudrate=plc_baud_rate,
            bytesize=plc_bytesize,
            parity=plc_parity,
            stopbits=plc_stopbits,
            timeout=plc_timeout
        )
        
        if client.connect():
            print(f"✅ SUCCESS: Connected to PLC!")
            
            # Test communication by reading coil 0
            print(f"\n🔍 Testing communication (reading coil 0)...")
            result = client.read_coils(0, count=1, device_id=plc_station_id)
            
            if not result.isError():
                coil_value = result.bits[0] if result.bits else False
                print(f"✅ SUCCESS: Communication test passed!")
                print(f"   Coil 0 value: {coil_value}")
                
                # Try reading a few more coils
                print(f"\n📊 Reading first 10 coils for verification...")
                result = client.read_coils(0, count=10, device_id=plc_station_id)
                if not result.isError():
                    for i, bit in enumerate(result.bits[:10]):
                        status = "HIGH" if bit else "LOW"
                        print(f"   Coil {i}: {status}")
                else:
                    print(f"   ⚠️ Warning: Could not read multiple coils: {result}")
                
                client.close()
                
                print("\n" + "="*60)
                print("   ✅ PLC CONNECTION TEST: PASSED")
                print("   Your system is ready for real-time PLC testing!")
                print("="*60)
                return True
            else:
                print(f"❌ FAILED: Communication test failed")
                print(f"   Error: {result}")
                client.close()
                
                print("\n" + "="*60)
                print("   ❌ PLC CONNECTION TEST: FAILED (Communication Error)")
                print("   Check PLC address/station ID configuration")
                print("="*60)
                return False
        else:
            print(f"❌ FAILED: Could not connect to PLC on {plc_com_port}")
            
            print("\n" + "="*60)
            print("   ❌ PLC CONNECTION TEST: FAILED (Connection Error)")
            print("\n   Troubleshooting:")
            print("   1. Verify PLC is powered ON")
            print("   2. Check cable connections")
            print("   3. Verify COM port is correct")
            print("   4. Ensure no other application is using the port")
            print("   5. Check PLC communication parameters match")
            print("="*60)
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Exception occurred during connection test")
        print(f"   {type(e).__name__}: {str(e)}")
        
        print("\n" + "="*60)
        print("   ❌ PLC CONNECTION TEST: FAILED (Exception)")
        print(f"\n   Error Details: {str(e)}")
        print("="*60)
        return False

if __name__ == "__main__":
    try:
        success = test_plc_connection()
        
        if success:
            print("\n✨ You can now run: python test_console_clone.py")
            print("   The system will use REAL PLC communication.\n")
        else:
            print("\n⚠️  Fix the above issues before running the main application.\n")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()



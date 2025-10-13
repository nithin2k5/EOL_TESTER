"""
COM Port Checker and Troubleshooter
Helps identify and resolve COM port access issues
"""

import serial
import serial.tools.list_ports
import os
from dotenv import load_dotenv

def check_com_ports():
    """Check all available COM ports and their status"""
    print("\n" + "="*60)
    print("           COM PORT STATUS CHECK")
    print("="*60)
    
    # Load configuration
    load_dotenv('.env')
    configured_port = os.getenv('PLC_COM_PORT', 'COM5').strip("'\"")
    
    print(f"\n📋 All Available COM Ports:")
    print("-" * 60)
    
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("   ❌ No COM ports found on this system")
        return
    
    for port in ports:
        is_configured = "✓ CONFIGURED" if port.device == configured_port else ""
        print(f"   {port.device}: {port.description} {is_configured}")
        if port.hwid:
            print(f"      Hardware ID: {port.hwid}")
    
    print("\n" + "-" * 60)
    print(f"\n🔧 Configured PLC Port: {configured_port}")
    
    # Check if configured port exists
    available_ports = [p.device for p in ports]
    if configured_port not in available_ports:
        print(f"   ❌ ERROR: {configured_port} is NOT available on this system!")
        print(f"\n   Available ports you can use: {', '.join(available_ports)}")
        print(f"\n   💡 To fix: Update .env file with a valid COM port")
        return False
    else:
        print(f"   ✅ Port exists on this system")
    
    # Try to open the port
    print(f"\n🔍 Testing {configured_port} accessibility...")
    try:
        test_serial = serial.Serial(configured_port, timeout=0.1)
        test_serial.close()
        print(f"   ✅ SUCCESS: {configured_port} is available and can be opened!")
        print(f"\n   You can now run: python test_real_plc_connection.py")
        return True
    except serial.SerialException as e:
        if "Access is denied" in str(e) or "PermissionError" in str(e):
            print(f"   ❌ ERROR: {configured_port} is IN USE by another application")
            print(f"\n   📌 Troubleshooting Steps:")
            print(f"   1. Close Arduino IDE if open")
            print(f"   2. Close any serial terminal programs (PuTTY, TeraTerm, etc.)")
            print(f"   3. Close any other Python scripts using this port")
            print(f"   4. Close previous instances of test_console.py")
            print(f"\n   💡 After closing other programs, run this script again")
            return False
        else:
            print(f"   ❌ ERROR: {e}")
            return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def suggest_alternative_ports():
    """Suggest alternative COM ports if configured port is busy"""
    print("\n" + "="*60)
    print("           ALTERNATIVE PORT SUGGESTIONS")
    print("="*60)
    
    ports = serial.tools.list_ports.comports()
    available_ports = []
    
    print("\n🔍 Testing all available ports...\n")
    
    for port in ports:
        try:
            test_serial = serial.Serial(port.device, timeout=0.1)
            test_serial.close()
            available_ports.append(port.device)
            print(f"   ✅ {port.device} - AVAILABLE")
            print(f"      {port.description}")
        except:
            print(f"   ❌ {port.device} - IN USE")
            print(f"      {port.description}")
    
    if available_ports:
        print(f"\n💡 You can use these ports instead:")
        for port in available_ports:
            print(f"   • {port}")
        print(f"\n   To change: Edit .env file and set PLC_COM_PORT={available_ports[0]}")
    else:
        print(f"\n   ⚠️ No available ports found - all are in use")
        print(f"   Close other applications and try again")

if __name__ == "__main__":
    try:
        success = check_com_ports()
        
        if not success:
            # Offer to check alternative ports
            response = input("\n❓ Would you like to see alternative ports? (y/n): ")
            if response.lower() == 'y':
                suggest_alternative_ports()
        
        print("\n" + "="*60)
        print("   Test complete.")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user\n")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


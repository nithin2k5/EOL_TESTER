#!/usr/bin/env python3
"""
Test script for PLC configuration loading from .env file
"""

import sys
import os
from dotenv import load_dotenv

def test_env_loading():
    """Test environment file loading"""
    print("🧪 Testing .env file configuration loading...")
    
    # Load environment variables from .env file
    load_dotenv('.env')
    
    # Test PLC Configuration
    print("\n📡 PLC Configuration:")
    plc_com_port = os.getenv("PLC_COM_PORT", "").strip("'\"")
    plc_baud_rate = os.getenv("PLC_BAUD_RATE", "").strip("'\"")
    plc_station_id = os.getenv("PLC_STATION_ID", "").strip("'\"")
    
    print(f"   COM Port: {plc_com_port}")
    print(f"   Baud Rate: {plc_baud_rate}")
    print(f"   Station ID: {plc_station_id}")
    
    # Test Machine Configuration
    print("\n🏭 Machine Configuration:")
    machine_id = os.getenv("MACHINE_ID", "").strip("'\"")
    plc_reg_address = os.getenv("PLC_REG_ADDRESS", "").strip("'\"")
    plc_points = os.getenv("PLC_POINTS_TO_READ", "").strip("'\"")
    
    print(f"   Machine ID: EOL{machine_id}")
    print(f"   PLC Register Address: {plc_reg_address}")
    print(f"   PLC Points to Read: {plc_points}")
    
    # Test Loadcell Configuration
    print("\n⚖️ Loadcell Configuration:")
    lc1_port = os.getenv("LOADCELL_01_COM_PORT", "").strip("'\"")
    lc1_baud = os.getenv("LOADCELL_01_BAUD_RATE", "").strip("'\"")
    lc2_port = os.getenv("LOADCELL_02_COM_PORT", "").strip("'\"")
    lc2_baud = os.getenv("LOADCELL_02_BAUD_RATE", "").strip("'\"")
    
    print(f"   Loadcell 1: {lc1_port} @ {lc1_baud} baud")
    print(f"   Loadcell 2: {lc2_port} @ {lc2_baud} baud")
    
    # Test PLC RX Data parsing
    print("\n📊 PLC RX Data:")
    plc_rx_data = os.getenv("PLC_RX_DATA", "")
    if plc_rx_data:
        lines = plc_rx_data.split('\n')
        process_status_count = 0
        input_sensors_count = 0
        program_selection_count = 0
        
        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith("Process Status:"):
                current_section = "process_status"
            elif line.startswith("Input Sensors:"):
                current_section = "input_sensors"
            elif line.startswith("Program Selection:"):
                current_section = "program_selection"
            elif " --> " in line and current_section:
                if current_section == "process_status":
                    process_status_count += 1
                elif current_section == "input_sensors":
                    input_sensors_count += 1
                elif current_section == "program_selection":
                    program_selection_count += 1
        
        print(f"   Process Status addresses: {process_status_count}")
        print(f"   Input Sensor addresses: {input_sensors_count}")
        print(f"   Program Selection addresses: {program_selection_count}")
    else:
        print("   No PLC RX data found")
    
    return True

def test_plc_connection_simulation():
    """Test PLC connection simulation"""
    print("\n🔌 Testing PLC Connection Configuration...")
    
    try:
        # Import the main application to test configuration loading
        from test_console_clone import PLC_CONFIG, MACHINE_CONFIG, LOADCELL_CONFIG, PLC_RX_DATA
        
        print("✅ Configuration modules loaded successfully")
        print(f"   PLC Config: {PLC_CONFIG}")
        print(f"   Machine Config: {MACHINE_CONFIG}")
        print(f"   Loadcell Config: {LOADCELL_CONFIG}")
        print(f"   PLC RX Data sections: {list(PLC_RX_DATA.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 EOL Tester .env Configuration Test")
    print("=" * 60)
    
    # Test 1: Environment loading
    try:
        success1 = test_env_loading()
        print(f"\n✅ Environment loading test: {'PASSED' if success1 else 'FAILED'}")
    except Exception as e:
        print(f"\n❌ Environment loading test FAILED: {e}")
        success1 = False
    
    # Test 2: PLC configuration
    try:
        success2 = test_plc_connection_simulation()
        print(f"\n✅ PLC configuration test: {'PASSED' if success2 else 'FAILED'}")
    except Exception as e:
        print(f"\n❌ PLC configuration test FAILED: {e}")
        success2 = False
    
    # Summary
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 All tests PASSED! Configuration loading is working correctly.")
    else:
        print("⚠️ Some tests FAILED. Please check the configuration.")
    print("=" * 60)

if __name__ == "__main__":
    main()

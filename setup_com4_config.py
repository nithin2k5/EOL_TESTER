#!/usr/bin/env python3
"""
Setup COM4 PLC Configuration
Sets up the environment variables and configuration for COM4 PLC connection
"""

import os
import json

def setup_com4_config():
    """Setup PLC configuration for COM4 connection"""
    print("🔧 Setting up COM4 PLC Configuration")
    print("=" * 40)

    # Configuration settings
    config = {
        "com_port": "COM4",
        "baudrate": 38400,
        "station_id": 1
    }

    print("Configuration to be set:")
    print(f"  COM Port: {config['com_port']}")
    print(f"  Baudrate: {config['baudrate']}")
    print(f"  Station ID: {config['station_id']}")
    print()

    # Set environment variables for current session
    os.environ['PLC_COM_PORT'] = config['com_port']
    os.environ['PLC_BAUD_RATE'] = str(config['baudrate'])
    os.environ['PLC_STATION_ID'] = str(config['station_id'])

    print("✅ Environment variables set for current session")

    # Update plc_config.json file
    config_file = 'plc_config.json'
    try:
        # Read existing config or create new one
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config_data = json.load(f)
        else:
            config_data = {
                "plc_settings": {},
                "common_addresses": {
                    "coils": [0, 1, 100, 101, 1000, 1001],
                    "input_registers": [0, 1, 2, 3, 4, 5, 6, 7],
                    "holding_registers": [0, 1, 2, 3, 4, 5, 6, 7]
                },
                "monitoring_settings": {
                    "addresses_to_monitor": [0, 1, 100, 101],
                    "update_interval": 1.0
                }
            }

        # Update PLC settings
        config_data['plc_settings'].update({
            "com_port": config['com_port'],
            "baudrate": config['baudrate'],
            "station_id": config['station_id'],
            "description": "COM4 PLC Configuration - 38400 baud, Station ID 1"
        })

        # Save updated configuration
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=4)

        print("✅ Configuration saved to plc_config.json")

    except Exception as e:
        print(f"⚠️  Could not update config file: {e}")

    # Verify the settings
    print("\n🔍 Verification:")
    print(f"  PLC_COM_PORT: {os.environ.get('PLC_COM_PORT', 'Not set')}")
    print(f"  PLC_BAUD_RATE: {os.environ.get('PLC_BAUD_RATE', 'Not set')}")
    print(f"  PLC_STATION_ID: {os.environ.get('PLC_STATION_ID', 'Not set')}")

    print("\n✅ COM4 PLC configuration setup complete!")
    print("\nNext steps:")
    print("  1. Run: python test_com4_plc.py")
    print("  2. Or run: python plc_coil_reader.py")
    print("  3. Or run: test_com4.bat")

def test_connection():
    """Test the PLC connection after setup"""
    print("\n🧪 Testing PLC Connection...")
    try:
        from plc_coil_reader import PLCCoilReader

        plc = PLCCoilReader()
        if plc.establish_connection():
            print("✅ PLC connection successful!")
            plc.disconnect()
            return True
        else:
            print("❌ PLC connection failed")
            return False
    except ImportError:
        print("❌ Could not import PLC reader - check if pymodbus is installed")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main setup function"""
    setup_com4_config()

    # Ask if user wants to test the connection
    response = input("\nDo you want to test the PLC connection now? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        test_connection()
    else:
        print("You can test the connection later by running:")
        print("  python test_com4_plc.py")

if __name__ == "__main__":
    main()



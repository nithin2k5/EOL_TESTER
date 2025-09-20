#!/usr/bin/env python3
"""
Test ALC code processing and database connection
"""

import os
from dotenv import load_dotenv
import mysql.connector

def test_alc_processing():
    """Test ALC code processing with database"""
    print("🔧 Testing ALC code processing...")

    # Load environment
    load_dotenv()

    # Database config
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', '12345'),
        'database': os.getenv('DB_NAME', 'EOL'),
        'raise_on_warnings': True
    }

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        print("✅ Database connected successfully")

        # Test ALC code lookup (try a common ALC code)
        alc_codes_to_test = ['HI', 'fw', 'b', 'hh']

        for alc_code in alc_codes_to_test:
            print(f"\n🔍 Testing ALC code: '{alc_code}'")

            # Query TBL_MODEL_MASTER
            model_query = """
            SELECT MM_PART_NUMBER, MM_MODEL_NAME, MM_VENDOR_CODE, MM_EO_NUMBER,
                   MM_SPECIAL_DATA, MM_INITIAL_ID, MM_SUPPLIER_SECTION, MM_IMAGE_PATH,
                   MM_BARCODE_LABEL_CODE as MM_BARCODE_PRN_FILE_NAME, MM_PLC_ADDRESS
            FROM TBL_MODEL_MASTER
            WHERE MM_ALC_CODE = %s AND MM_STATUS = %s
            """

            cursor.execute(model_query, (alc_code, True))
            model_result = cursor.fetchone()

            if model_result:
                print("✅ ALC code found in database!")
                print(f"   Part Number: {model_result['MM_PART_NUMBER']}")
                print(f"   Model Name: {model_result['MM_MODEL_NAME']}")
                print(f"   PLC Address: {model_result['MM_PLC_ADDRESS']}")

                # Check specifications
                spec_query = """
                SELECT COUNT(*) as spec_count
                FROM TBL_MODEL_SPECIFICATION
                WHERE MS_PART_NUMBER = %s
                """

                cursor.execute(spec_query, (model_result['MM_PART_NUMBER'],))
                spec_result = cursor.fetchone()
                print(f"   Specifications: {spec_result['spec_count']} records")

                # Check labels
                label_query = """
                SELECT COUNT(*) as label_count
                FROM TBL_MODEL_LABEL_DETAILS
                WHERE MLD_PART_NUMBER = %s
                """

                cursor.execute(label_query, (model_result['MM_PART_NUMBER'],))
                label_result = cursor.fetchone()
                print(f"   Sensor labels: {label_result['label_count']} records")

                print("✅ This ALC code should work for testing!")
                break
            else:
                print("❌ ALC code not found in database")

        cursor.close()
        connection.close()

    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        print("💡 Make sure MySQL is running and database is set up")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def check_simulation_mode():
    """Check simulation mode settings"""
    load_dotenv()

    plc_sim = os.getenv('PLC_SIMULATION_MODE', 'true').lower() == 'true'
    db_sim = os.getenv('DATABASE_SIMULATION_MODE', 'false').lower() == 'true'

    print("\n🔧 Simulation Mode Settings:")
    print(f"   PLC Simulation: {'✅ ENABLED' if plc_sim else '❌ DISABLED'}")
    print(f"   DB Simulation: {'✅ ENABLED' if db_sim else '❌ DISABLED'}")

    if plc_sim:
        print("💡 PLC is in simulation mode - testing will use random signals")
        print("💡 To use real PLC, set PLC_SIMULATION_MODE=false in .env")

if __name__ == "__main__":
    check_simulation_mode()
    test_alc_processing()

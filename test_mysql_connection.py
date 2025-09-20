#!/usr/bin/env python3
"""
MySQL Connection Test and Setup Script for EOL Tester
"""

import mysql.connector
import os
from dotenv import load_dotenv

def test_connection(host='localhost', port=3306, user='root', password='12345', database='EOL'):
    """Test MySQL connection with given parameters"""
    try:
        config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'raise_on_warnings': True
        }

        print(f"🔍 Testing connection to MySQL...")
        print(f"   Host: {host}:{port}")
        print(f"   User: {user}")
        print(f"   Database: {database}")

        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        # Test the connection
        cursor.execute("SELECT VERSION() as version, DATABASE() as current_db")
        result = cursor.fetchone()

        print(f"✅ Connection successful!")
        print(f"   MySQL Version: {result[0]}")
        print(f"   Current Database: {result[1]}")

        cursor.close()
        connection.close()
        return True

    except mysql.connector.Error as err:
        print(f"❌ Connection failed: {err}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def setup_database():
    """Setup the EOL database and required tables"""
    # First try to connect without database to create it
    try:
        print("\n🔧 Setting up EOL database...")

        # Try different passwords
        passwords_to_try = ['12345', '', 'root', 'password', 'mysql']

        root_connection = None
        working_password = None

        for password in passwords_to_try:
            try:
                config = {
                    'host': 'localhost',
                    'user': 'root',
                    'password': password,
                    'raise_on_warnings': True
                }
                root_connection = mysql.connector.connect(**config)
                working_password = password
                print(f"✅ Connected with password: '{password}'")
                break
            except mysql.connector.Error:
                continue

        if not root_connection:
            print("❌ Could not connect with any common passwords.")
            print("Please enter your MySQL root password:")
            working_password = input("MySQL root password: ").strip()

            try:
                config = {
                    'host': 'localhost',
                    'user': 'root',
                    'password': working_password,
                    'raise_on_warnings': True
                }
                root_connection = mysql.connector.connect(**config)
                print("✅ Connected with provided password!")
            except mysql.connector.Error as err:
                print(f"❌ Still cannot connect: {err}")
                return False

        cursor = root_connection.cursor()

        # Create EOL database if it doesn't exist
        try:
            cursor.execute("CREATE DATABASE IF NOT EXISTS EOL CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ Database 'EOL' created")
        except mysql.connector.Error as err:
            if err.errno == 1007:  # Database exists
                print("ℹ️  Database 'EOL' already exists")
            else:
                raise err

        # Grant permissions to root user for EOL database
        try:
            cursor.execute("GRANT ALL PRIVILEGES ON EOL.* TO 'root'@'localhost'")
            cursor.execute("FLUSH PRIVILEGES")
            print("✅ Granted permissions to root user for EOL database")
        except mysql.connector.Error as err:
            print(f"⚠️  Permission grant warning (may already have permissions): {err}")

        # Switch to EOL database
        cursor.execute("USE EOL")

        # Create tables (skip if they already exist)
        tables = [
            ("TBL_MODEL_MASTER", """
            CREATE TABLE IF NOT EXISTS TBL_MODEL_MASTER (
                MM_PART_NUMBER VARCHAR(50) PRIMARY KEY,
                MM_MODEL_NAME VARCHAR(100),
                MM_VENDOR_CODE VARCHAR(50),
                MM_EO_NUMBER VARCHAR(50),
                MM_SPECIAL_DATA VARCHAR(100),
                MM_INITIAL_ID VARCHAR(50),
                MM_SUPPLIER_SECTION VARCHAR(100),
                MM_IMAGE_PATH VARCHAR(255),
                MM_BARCODE_PRN_FILE_NAME VARCHAR(100),
                MM_PLC_ADDRESS VARCHAR(10),
                MM_ALC_CODE VARCHAR(10),
                MM_STATUS BOOLEAN DEFAULT TRUE
            )
            """),
            ("TBL_MODEL_SPECIFICATION", """
            CREATE TABLE IF NOT EXISTS TBL_MODEL_SPECIFICATION (
                MS_PART_NUMBER VARCHAR(50),
                MS_DEVICE VARCHAR(10),
                MS_DESCRIPTION VARCHAR(100),
                MS_NORMAL_MIN DECIMAL(10,2),
                MS_UNIT VARCHAR(20),
                MS_NORMAL_MAX DECIMAL(10,2),
                PRIMARY KEY (MS_PART_NUMBER, MS_DEVICE)
            )
            """),
            ("TBL_MODEL_LABEL_DETAILS", """
            CREATE TABLE IF NOT EXISTS TBL_MODEL_LABEL_DETAILS (
                MLD_PART_NUMBER VARCHAR(50),
                MLD_LABEL_ID VARCHAR(20),
                MLD_ON_STATUS VARCHAR(50),
                MLD_OFF_STATUS VARCHAR(50),
                MLD_X INT,
                MLD_Y INT,
                MLD_FONT VARCHAR(50),
                PRIMARY KEY (MLD_PART_NUMBER, MLD_LABEL_ID)
            )
            """),
            ("TBL_TEST_DATA", """
            CREATE TABLE IF NOT EXISTS TBL_TEST_DATA (
                TD_MACHINE_ID VARCHAR(20),
                TD_PART_NUMBER VARCHAR(50),
                TD_LOT_NUMBER VARCHAR(10),
                TD_TRACEABILITY_CODE VARCHAR(50),
                TD_RECORD_DATE DATE,
                TD_DATETIME DATETIME,
                L1 DECIMAL(10,2),
                L2 DECIMAL(10,2),
                L3 DECIMAL(10,2),
                L4 DECIMAL(10,2),
                P1 DECIMAL(10,2),
                P2 DECIMAL(10,2),
                P3 DECIMAL(10,2),
                P4 DECIMAL(10,2),
                CAM1 VARCHAR(20),
                TD_OVERALL_STATUS VARCHAR(10),
                TD_EMPLOYEE_CODE VARCHAR(20),
                TD_BARCODE_SCAN_RESULT VARCHAR(10)
            )
            """),
            ("TBL_PART_RUNNING_SERIAL", """
            CREATE TABLE IF NOT EXISTS TBL_PART_RUNNING_SERIAL (
                PART_NUMBER VARCHAR(50),
                TEST_DAY_DATE DATE,
                TEST_DAY_LAST_DATE_TIME DATETIME,
                TRACEABILITY_CODE VARCHAR(50),
                RUNNING_LOT_NUMBER VARCHAR(10),
                PRIMARY KEY (PART_NUMBER, TEST_DAY_DATE)
            )
            """)
        ]

        for table_name, table_sql in tables:
            try:
                cursor.execute(table_sql)
                print(f"✅ Table '{table_name}' created/verified")
            except mysql.connector.Error as err:
                if err.errno == 1050:  # Table already exists
                    print(f"ℹ️  Table '{table_name}' already exists")
                else:
                    print(f"❌ Error creating table '{table_name}': {err}")
                    raise

        root_connection.commit()
        cursor.close()
        root_connection.close()

        print("✅ All database tables created successfully!")

        # Update .env file with correct credentials
        update_env_file(working_password)

        return True

    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def update_env_file(correct_password):
    """Update the .env file with correct database credentials"""
    try:
        env_content = f"""# EOL Tester Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD={correct_password}
DB_NAME=EOL

# PLC Connection Settings
PLC_COM_PORT=COM5
PLC_BAUD_RATE=38400
PLC_STATION_ID=1

# Loadcell Settings
LOADCELL_01_COM_PORT=
LOADCELL_01_BAUD_RATE=9600
LOADCELL_02_COM_PORT=
LOADCELL_02_BAUD_RATE=9600

# Machine Settings
MACHINE_ID=1
PLC_REG_ADDRESS=
PLC_POINTS_TO_READ=1
MODBUS_TCP_IP=
MODBUS_TCP_PORT=
PLC_RX_DATA=Process Status:
M0067 --> OFF
M0068 --> OFF
M0076 --> OFF
M0085 --> ON
M0078 --> OFF
M0087 --> OFF
M0075 --> OFF
M0079 --> OFF

Input Sensors:
P0000 --> OFF
P0001 --> OFF
P0002 --> OFF
P0004 --> OFF

Program Selection:
M0091 --> OFF
M0092 --> OFF
M0093 --> OFF
M0094 --> OFF
M0095 --> OFF
M0096 --> OFF
M0097 --> OFF
M0098 --> OFF
M0099 --> OFF
M009A --> OFF
M009B --> OFF
M009C --> OFF
M009D --> OFF
M009E --> OFF
M009F --> OFF

# Database Configuration (added by EOL Tester)
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD={correct_password}
DB_NAME=EOL

# Testing Parameters (added by EOL Tester)
ALC_INPUT_TIME_INTERVAL=3000
PRINTED_LABEL_SCAN_TIME_INTERVAL=4000
PRINTED_LABEL_SCAN_WAIT_TIME=6000
ALERT_ON_TIME_INTERVAL=5000

# Development Flags (added by EOL Tester)
PLC_SIMULATION_MODE=true
DATABASE_SIMULATION_MODE=false
DEBUG_MODE=true
ENABLE_CONSOLE_OUTPUT=true

# PLC Additional Settings (added by EOL Tester)
PLC_BYTESIZE=8
PLC_PARITY=N
PLC_STOPBITS=1
PLC_TIMEOUT=1.0
PLC_READ_TIMEOUT=500
PLC_WRITE_TIMEOUT=500
PLC_RETRIES=0

# File Paths (added by EOL Tester)
INPUT_SENSORS_FILE=txt_files/InputSensors.txt
PROCESS_STATUS_FILE=txt_files/ProcessStatus.txt
INPUT_REGISTERS_FILE=txt_files/HoldRegistersRead.txt
MACHINE_ON_PLC_ADDRESS_FILE=txt_files/MachineOnPLCCoilAddress.txt
ALERT_ON_PLC_ADDRESS_FILE=txt_files/AlertOnPLCCoilAddress.txt
EMPLOYEE_CODES_FILE=txt_files/EmployeeCodes.txt

# Screen Configuration (added by EOL Tester)
SCREEN_WIDTH=1920
SCREEN_HEIGHT=1080
"""

        with open('.env', 'w') as f:
            f.write(env_content)

        print(f"✅ .env file updated with correct password: '{correct_password}'")

    except Exception as e:
        print(f"❌ Failed to update .env file: {e}")

def main():
    print("🗄️  EOL Tester - MySQL Database Setup")
    print("=" * 50)

    # Load existing .env if it exists
    load_dotenv()

    # Test connection with current settings
    print("\n1. Testing current database configuration...")
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', '3306'))
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '12345')
    db_name = os.getenv('DB_NAME', 'EOL')

    if test_connection(db_host, db_port, db_user, db_password, db_name):
        print("\n🎉 Database connection is working! No fixes needed.")
        return

    # If connection fails, setup database
    print("\n2. Setting up database...")
    if setup_database():
        print("\n3. Testing final connection...")
        if test_connection(db_host, db_port, db_user, db_password, db_name):
            print("\n🎉 Database setup complete! EOL Tester should now work.")
        else:
            print("\n❌ Final connection test failed. Please check MySQL setup.")
    else:
        print("\n❌ Database setup failed. Please check MySQL installation and permissions.")

if __name__ == "__main__":
    main()

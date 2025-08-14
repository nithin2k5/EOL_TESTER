"""
Mock Database Simulator for EOL Testing System
This file simulates database operations without requiring a real MySQL connection
"""

import sqlite3
import os
import json
from datetime import datetime, date
from mock_data import MOCK_DATABASE_RECORDS, MOCK_PART_SPECIFICATIONS

class MockDatabase:
    """Mock database class that simulates MySQL operations using SQLite for testing"""
    
    def __init__(self, db_path=":memory:"):
        """Initialize mock database"""
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize the mock database with required tables and sample data"""
        try:
            # Create in-memory SQLite database
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            
            # Create tables
            self.create_tables()
            
            # Insert sample data
            self.insert_sample_data()
            
            print("✅ Mock database initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing mock database: {e}")
            raise
    
    def create_tables(self):
        """Create all required tables for EOL testing"""
        try:
            # Create TBL_TEST_RESULTS table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS TBL_TEST_RESULTS (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    LOT_NUMBER VARCHAR(50) UNIQUE,
                    PART_NUMBER VARCHAR(50),
                    EMP_CODE VARCHAR(20),
                    TEST_DATE DATE,
                    TEST_TIME TIME,
                    L1_VALUE DECIMAL(10,3),
                    L2_VALUE DECIMAL(10,3),
                    L3_VALUE DECIMAL(10,3),
                    L4_VALUE DECIMAL(10,3),
                    P1_VALUE DECIMAL(10,3),
                    P2_VALUE DECIMAL(10,3),
                    P3_VALUE DECIMAL(10,3),
                    P4_VALUE DECIMAL(10,3),
                    OVERALL_RESULT VARCHAR(10),
                    FAILED_DEVICES TEXT,
                    TEST_DURATION DECIMAL(10,3),
                    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create TBL_LOT_SEQUENCE table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS TBL_LOT_SEQUENCE (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    DATE VARCHAR(10),
                    MACHINE_ID VARCHAR(10),
                    LAST_INCREMENT INTEGER DEFAULT 0,
                    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(DATE, MACHINE_ID)
                )
            """)
            
            # Create TBL_PART_SPECIFICATIONS table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS TBL_PART_SPECIFICATIONS (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    PART_NUMBER VARCHAR(50) UNIQUE,
                    MODEL_NAME VARCHAR(100),
                    DESCRIPTION TEXT,
                    IMAGE_PATH VARCHAR(255),
                    SPECIFICATIONS_JSON TEXT,
                    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create TBL_EMPLOYEE_CODES table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS TBL_EMPLOYEE_CODES (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    EMP_CODE VARCHAR(20) UNIQUE,
                    EMP_NAME VARCHAR(100),
                    DEPARTMENT VARCHAR(50),
                    ACCESS_LEVEL VARCHAR(20),
                    CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.connection.commit()
            print("✅ Database tables created successfully")
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            raise
    
    def insert_sample_data(self):
        """Insert sample data into the database"""
        try:
            # Insert employee codes
            employee_codes = [
                ("EMP001", "John Doe", "Testing", "OPERATOR"),
                ("EMP002", "Jane Smith", "Testing", "SUPERVISOR"),
                ("EMP003", "Bob Johnson", "Quality", "ENGINEER"),
                ("ADMIN001", "Admin User", "IT", "ADMIN"),
                ("SUPER001", "Supervisor", "Management", "SUPERVISOR")
            ]
            
            self.cursor.executemany("""
                INSERT OR IGNORE INTO TBL_EMPLOYEE_CODES (EMP_CODE, EMP_NAME, DEPARTMENT, ACCESS_LEVEL)
                VALUES (?, ?, ?, ?)
            """, employee_codes)
            
            # Insert part specifications
            for part_num, part_data in MOCK_PART_SPECIFICATIONS.items():
                specs_json = json.dumps(part_data["specifications"])
                self.cursor.execute("""
                    INSERT OR IGNORE INTO TBL_PART_SPECIFICATIONS 
                    (PART_NUMBER, MODEL_NAME, DESCRIPTION, IMAGE_PATH, SPECIFICATIONS_JSON)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    part_data["part_number"],
                    part_data["model_name"],
                    part_data["description"],
                    part_data["image_path"],
                    specs_json
                ))
            
            # Insert sample test results
            for test_result in MOCK_DATABASE_RECORDS["test_results"]:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO TBL_TEST_RESULTS 
                    (LOT_NUMBER, PART_NUMBER, EMP_CODE, TEST_DATE, TEST_TIME,
                     L1_VALUE, L2_VALUE, L3_VALUE, L4_VALUE,
                     P1_VALUE, P2_VALUE, P3_VALUE, P4_VALUE,
                     OVERALL_RESULT, FAILED_DEVICES, TEST_DURATION)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    test_result["LOT_NUMBER"],
                    test_result["PART_NUMBER"],
                    test_result["EMP_CODE"],
                    test_result["TEST_DATE"],
                    test_result["TEST_TIME"],
                    test_result["L1_VALUE"],
                    test_result["L2_VALUE"],
                    test_result["L3_VALUE"],
                    test_result["L4_VALUE"],
                    test_result["P1_VALUE"],
                    test_result["P2_VALUE"],
                    test_result["P3_VALUE"],
                    test_result["P4_VALUE"],
                    test_result["OVERALL_RESULT"],
                    test_result["FAILED_DEVICES"],
                    test_result["TEST_DURATION"]
                ))
            
            # Insert lot sequence data
            for lot_seq in MOCK_DATABASE_RECORDS["lot_sequence"]:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO TBL_LOT_SEQUENCE (DATE, MACHINE_ID, LAST_INCREMENT)
                    VALUES (?, ?, ?)
                """, (lot_seq["DATE"], lot_seq["MACHINE_ID"], lot_seq["LAST_INCREMENT"]))
            
            self.connection.commit()
            print("✅ Sample data inserted successfully")
            
        except Exception as e:
            print(f"❌ Error inserting sample data: {e}")
            raise
    
    def execute_query(self, query, params=None):
        """Execute a database query"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.rowcount
                
        except Exception as e:
            print(f"❌ Database query error: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            raise
    
    def fetch_one(self, query, params=None):
        """Fetch a single row from database"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            return self.cursor.fetchone()
            
        except Exception as e:
            print(f"❌ Database fetch error: {e}")
            raise
    
    def fetch_all(self, query, params=None):
        """Fetch all rows from database"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            
            return self.cursor.fetchall()
            
        except Exception as e:
            print(f"❌ Database fetch error: {e}")
            raise
    
    def insert_test_result(self, test_data):
        """Insert a new test result"""
        try:
            query = """
                INSERT INTO TBL_TEST_RESULTS 
                (LOT_NUMBER, PART_NUMBER, EMP_CODE, TEST_DATE, TEST_TIME,
                 L1_VALUE, L2_VALUE, L3_VALUE, L4_VALUE,
                 P1_VALUE, P2_VALUE, P3_VALUE, P4_VALUE,
                 OVERALL_RESULT, FAILED_DEVICES, TEST_DURATION)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                test_data.get("LOT_NUMBER"),
                test_data.get("PART_NUMBER"),
                test_data.get("EMP_CODE"),
                test_data.get("TEST_DATE"),
                test_data.get("TEST_TIME"),
                test_data.get("L1_VALUE"),
                test_data.get("L2_VALUE"),
                test_data.get("L3_VALUE"),
                test_data.get("L4_VALUE"),
                test_data.get("P1_VALUE"),
                test_data.get("P2_VALUE"),
                test_data.get("P3_VALUE"),
                test_data.get("P4_VALUE"),
                test_data.get("OVERALL_RESULT"),
                test_data.get("FAILED_DEVICES"),
                test_data.get("TEST_DURATION")
            )
            
            result = self.execute_query(query, params)
            print(f"✅ Test result inserted successfully. Rows affected: {result}")
            return True
            
        except Exception as e:
            print(f"❌ Error inserting test result: {e}")
            return False
    
    def get_part_specifications(self, part_number):
        """Get part specifications from database"""
        try:
            query = "SELECT * FROM TBL_PART_SPECIFICATIONS WHERE PART_NUMBER = ?"
            result = self.fetch_one(query, (part_number,))
            
            if result:
                # Parse specifications JSON
                specs_json = result[5]  # SPECIFICATIONS_JSON column
                specifications = json.loads(specs_json) if specs_json else {}
                
                return {
                    "part_number": result[1],
                    "model_name": result[2],
                    "description": result[3],
                    "image_path": result[4],
                    "specifications": specifications
                }
            else:
                return None
                
        except Exception as e:
            print(f"❌ Error getting part specifications: {e}")
            return None
    
    def validate_employee_code(self, emp_code):
        """Validate employee code against database"""
        try:
            query = "SELECT * FROM TBL_EMPLOYEE_CODES WHERE EMP_CODE = ?"
            result = self.fetch_one(query, (emp_code,))
            
            if result:
                return {
                    "valid": True,
                    "emp_code": result[1],
                    "emp_name": result[2],
                    "department": result[3],
                    "access_level": result[4]
                }
            else:
                return {"valid": False, "message": "Employee code not found"}
                
        except Exception as e:
            print(f"❌ Error validating employee code: {e}")
            return {"valid": False, "message": f"Database error: {e}"}
    
    def get_next_lot_increment(self, date_str, machine_id):
        """Get next lot increment for given date and machine"""
        try:
            # Check if record exists
            query = "SELECT LAST_INCREMENT FROM TBL_LOT_SEQUENCE WHERE DATE = ? AND MACHINE_ID = ?"
            result = self.fetch_one(query, (date_str, machine_id))
            
            if result:
                # Update existing record
                new_increment = result[0] + 1
                update_query = "UPDATE TBL_LOT_SEQUENCE SET LAST_INCREMENT = ? WHERE DATE = ? AND MACHINE_ID = ?"
                self.execute_query(update_query, (new_increment, date_str, machine_id))
                return new_increment
            else:
                # Insert new record
                new_increment = 1
                insert_query = "INSERT INTO TBL_LOT_SEQUENCE (DATE, MACHINE_ID, LAST_INCREMENT) VALUES (?, ?, ?)"
                self.execute_query(insert_query, (date_str, machine_id, new_increment))
                return new_increment
                
        except Exception as e:
            print(f"❌ Error getting next lot increment: {e}")
            return 1
    
    def get_test_history(self, limit=50):
        """Get test history from database"""
        try:
            query = """
                SELECT * FROM TBL_TEST_RESULTS 
                ORDER BY CREATED_AT DESC 
                LIMIT ?
            """
            results = self.fetch_all(query, (limit,))
            
            # Convert to list of dictionaries
            test_history = []
            for row in results:
                test_history.append({
                    "LOT_NUMBER": row[1],
                    "PART_NUMBER": row[2],
                    "EMP_CODE": row[3],
                    "TEST_DATE": row[4],
                    "TEST_TIME": row[5],
                    "L1_VALUE": row[6],
                    "L2_VALUE": row[7],
                    "L3_VALUE": row[8],
                    "L4_VALUE": row[9],
                    "P1_VALUE": row[10],
                    "P2_VALUE": row[11],
                    "P3_VALUE": row[12],
                    "P4_VALUE": row[13],
                    "OVERALL_RESULT": row[14],
                    "FAILED_DEVICES": row[15],
                    "TEST_DURATION": row[16],
                    "CREATED_AT": row[17]
                })
            
            return test_history
            
        except Exception as e:
            print(f"❌ Error getting test history: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            print("✅ Database connection closed")
        except Exception as e:
            print(f"❌ Error closing database: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

# Global mock database instance
mock_db = None

def get_mock_database():
    """Get or create mock database instance"""
    global mock_db
    if mock_db is None:
        mock_db = MockDatabase()
    return mock_db

def reset_mock_database():
    """Reset mock database to initial state"""
    global mock_db
    if mock_db:
        mock_db.close()
    mock_db = MockDatabase()
    return mock_db

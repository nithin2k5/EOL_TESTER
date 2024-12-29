import mysql.connector
from mysql.connector import Error
from datetime import datetime
import logging

class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.cursor = None
        # Configure logging
        logging.basicConfig(
            filename='database.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def connect(self):
        """Establish connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host='localhost',          # Change as per your MySQL host
                database='eol_tester_db',  # Your database name
                user='root',              # Your MySQL username
                password='password'        # Your MySQL password
            )
            
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
                logging.info("Successfully connected to MySQL database")
                return True
                
        except Error as e:
            logging.error(f"Error connecting to MySQL: {e}")
            return False
            
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            # Test Results Table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_results (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    lot_number VARCHAR(50),
                    model_name VARCHAR(100),
                    test_date DATETIME,
                    l1_value FLOAT,
                    p1_value FLOAT,
                    p2_value FLOAT,
                    result VARCHAR(20),
                    alc_code VARCHAR(50)
                )
            """)
            
            # Test Specifications Table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_specifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    description VARCHAR(100),
                    device VARCHAR(50),
                    unit VARCHAR(20),
                    spec_min FLOAT,
                    spec_max FLOAT
                )
            """)
            
            # Label Positions Table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS label_positions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    model_name VARCHAR(100),
                    label_name VARCHAR(10),
                    position_x INT,
                    position_y INT
                )
            """)
            
            self.connection.commit()
            logging.info("Database tables created successfully")
            return True
            
        except Error as e:
            logging.error(f"Error creating tables: {e}")
            return False

    def save_test_result(self, lot_number, model_name, l1, p1, p2, result, alc_code):
        """Save test results to database"""
        try:
            sql = """INSERT INTO test_results 
                    (lot_number, model_name, test_date, l1_value, p1_value, p2_value, result, alc_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            values = (lot_number, model_name, datetime.now(), l1, p1, p2, result, alc_code)
            
            self.cursor.execute(sql, values)
            self.connection.commit()
            logging.info(f"Test result saved for lot number: {lot_number}")
            return True
            
        except Error as e:
            logging.error(f"Error saving test result: {e}")
            return False

    def save_label_positions(self, model_name, label_positions):
        """Save label positions for a model"""
        try:
            # First delete existing positions for this model
            self.cursor.execute("DELETE FROM label_positions WHERE model_name = %s", (model_name,))
            
            # Insert new positions
            sql = "INSERT INTO label_positions (model_name, label_name, position_x, position_y) VALUES (%s, %s, %s, %s)"
            values = [(model_name, label, pos[0], pos[1]) for label, pos in label_positions.items()]
            
            self.cursor.executemany(sql, values)
            self.connection.commit()
            logging.info(f"Label positions saved for model: {model_name}")
            return True
            
        except Error as e:
            logging.error(f"Error saving label positions: {e}")
            return False

    def get_label_positions(self, model_name):
        """Retrieve label positions for a model"""
        try:
            self.cursor.execute(
                "SELECT label_name, position_x, position_y FROM label_positions WHERE model_name = %s",
                (model_name,)
            )
            positions = {row[0]: (row[1], row[2]) for row in self.cursor.fetchall()}
            return positions
            
        except Error as e:
            logging.error(f"Error retrieving label positions: {e}")
            return {}

    def close(self):
        """Close database connection"""
        try:
            if self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
                logging.info("Database connection closed")
                
        except Error as e:
            logging.error(f"Error closing database connection: {e}") 
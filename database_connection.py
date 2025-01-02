import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error

class ComPortSettings:
    def __init__(self, root):
        # ... (previous code remains same)
        self.db_config = {
            'host': 'localhost',
            'port': '3360',
            'user': 'root',
            'password': 'nk446420',
            'database': 'EOL'
        }
        self.test_database_connection()

    def test_database_connection(self):
        try:
            connection = mysql.connector.connect(**self.db_config)
            
            if connection.is_connected():
                cursor = connection.cursor()
                
                # Create test table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS com_port_settings (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        device_type VARCHAR(50),
                        com_port VARCHAR(20),
                        baud_rate INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                connection.commit()
                messagebox.showinfo(
                    "Success", 
                    "Database connection successful!\n"
                    "Table 'com_port_settings' created/verified."
                )
                
                cursor.close()
                connection.close()
                return True
                
        except Error as e:
            messagebox.showerror(
                "Database Error", 
                f"Failed to connect to database!\nError: {str(e)}"
            )
            return False

    def save_settings_to_db(self, device_type, com_port, baud_rate):
        try:
            connection = mysql.connector.connect(**self.db_config)
            
            if connection.is_connected():
                cursor = connection.cursor()
                
                sql = """INSERT INTO com_port_settings 
                        (device_type, com_port, baud_rate) 
                        VALUES (%s, %s, %s)"""
                values = (device_type, com_port, baud_rate)
                
                cursor.execute(sql, values)
                connection.commit()
                
                cursor.close()
                connection.close()
                return True
                
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to save settings!\nError: {str(e)}")
            return False
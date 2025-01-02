import mysql.connector as mysql
from mysql.connector import Error as MySQLError

def test_database_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost:3306',          # Change as per your MySQL host
                database='EOL',  # Your database name
                user='root',              # Your MySQL username
                password='nk446420'  # Replace with your MySQL password
        )
        
        if connection.is_connected():
            print("Connected to MySQL Server")
            
            # Fetch MySQL server version
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION();")
            server_version = cursor.fetchone()[0]
            print(f"MySQL Server version: {server_version}")
            
            # Fetch the database name
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()[0]
            print(f"Connected to database: {db_name}")
            
            return True

    except MySQLError as e:
        print(f"Error connecting to MySQL: {e}")
        return False

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection closed")

if __name__ == "__main__":
    test_database_connection()
import mysql.connector

import config
import db

machine_id = config.get('MACHINE_ID', 'M1')
db_config = db.get_config()

try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # Check if we need to create the table first (though adminconsole.init_database likely did it)
    
    sample_employees = [
        ("John Doe", "EMP001", "pass123", "Tester", "QA", "1234567890", machine_id),
        ("Jane Smith", "EMP002", "pass456", "Senior Tester", "QA", "0987654321", machine_id)
    ]
    
    query = """
        INSERT INTO EMPLOYEE_INFO (
            EMPLOYEE_FULL_NAME, EMPLOYEE_NUMBER, PASSWORD,
            DESIGNATION, DEPARTMENT, MOBILE_NUMBER, MACHINE_ID, IS_ACTIVE
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
    """
    
    cursor.executemany(query, sample_employees)
    conn.commit()
    print("Successfully added sample employees!")
    print("Employee Codes:")
    print("EMP001 (Password: pass123)")
    print("EMP002 (Password: pass456)")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals() and conn.is_connected():
        cursor.close()
        conn.close()

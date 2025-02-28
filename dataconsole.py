import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import mysql.connector
from datetime import datetime

class DataConsole:
    def __init__(self):
        # Create main application window
        self.root = tk.Tk()
        self.root.title("EOL (END OF LINE) TESTER")
        self.root.geometry("1000x600")
        
        self.create_header()
        self.create_input_section()
        self.create_table()
        self.create_footer()

        self.db_config = {
            'host': 'localhost',
            'user': 'your_username',
            'password': 'your_password',
            'database': 'your_database'
        }

    def create_header(self):
        header_frame = tk.Frame(self.root, bg="pink")
        header_frame.pack(fill=tk.X)

        header_label = tk.Label(header_frame, text="EOL (END OF LINE) TESTER", 
                              font=("Arial", 20, "bold"), bg="pink")
        header_label.pack(pady=10)

    def create_input_section(self):
        input_frame = tk.Frame(self.root, padx=10, pady=10)
        input_frame.pack(fill=tk.X)

        # Part Number
        part_label = tk.Label(input_frame, text="PART NUMBER:", font=("Arial", 12))
        part_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.part_combobox = ttk.Combobox(input_frame, state="readonly", width=20)
        self.part_combobox.grid(row=0, column=1, padx=5, pady=5)

        # Start Date Label
        start_date_label = tk.Label(input_frame, text="START DATE:", font=("Arial", 12))
        start_date_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")

        # Set start date to beginning of current month and end date to current date
        current_date = datetime.now()
        start_of_month = current_date.replace(day=1)

        self.start_date_entry = DateEntry(input_frame, width=20, 
                                        date_pattern='yyyy-mm-dd',
                                        showweeknumbers=False,
                                        showothermonthdays=False,
                                        firstweekday='sunday',
                                        showtoday=True,
                                        selectmode='day')
        self.start_date_entry.bind('<Button-1>', lambda e: self.start_date_entry._select())
        self.start_date_entry.grid(row=0, column=3, padx=5, pady=5)
        self.start_date_entry.set_date(start_of_month)

        # End Date Label
        end_date_label = tk.Label(input_frame, text="END DATE:", font=("Arial", 12))
        end_date_label.grid(row=0, column=4, padx=5, pady=5, sticky="e")

        self.end_date_entry = DateEntry(input_frame, width=20, 
                                      date_pattern='yyyy-mm-dd',
                                      showweeknumbers=False,
                                      showothermonthdays=False,
                                      firstweekday='sunday',
                                      showtoday=True,
                                      selectmode='day')
        self.end_date_entry.bind('<Button-1>', lambda e: self.end_date_entry._select())
        self.end_date_entry.grid(row=0, column=5, padx=5, pady=5)
        self.end_date_entry.set_date(current_date)

        # Result
        result_label = tk.Label(input_frame, text="RESULT:", font=("Arial", 12))
        result_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.result_combobox = ttk.Combobox(input_frame, state="readonly", width=20, 
                                          values=["ALL", "PASS", "NG"])
        self.result_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.result_combobox.set("ALL")  # Set default value

        # Part Status
        status_label = tk.Label(input_frame, text="PART STATUS:", font=("Arial", 12))
        status_label.grid(row=2, column=2, padx=5, pady=5, sticky="e")
        self.status_combobox = ttk.Combobox(input_frame, state="readonly", width=20,
                                          values=["ACTIVE", "INACTIVE"])
        self.status_combobox.grid(row=2, column=3, padx=5, pady=5)
        self.status_combobox.set("ACTIVE")  # Set default value

        # Buttons
        self.search_button = tk.Button(input_frame, text="Search", bg="red", 
                                     fg="white", font=("Arial", 12),
                                     command=self.search_records)
        self.search_button.grid(row=0, column=10, padx=10, pady=5)

        self.export_button = tk.Button(input_frame, text="Export", bg="green", 
                                     fg="white", font=("Arial", 12))
        self.export_button.grid(row=0, column=11, padx=10, pady=5)

    def create_table(self):
        self.columns = ["NO", "MACHINE ID", "PART NUMBER", "ALC", "LOT NUMBER", 
                       "CREATED DATE", "L1", "L2", "L3", "L4", "P1", "P2", "P3", 
                       "P4", "CAM1", "CAM2", "RESULT","EMPLOYEE CODE"]

        table_frame = tk.Frame(self.root, padx=10, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True)

        scroll_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)

        self.result_table = ttk.Treeview(table_frame, columns=self.columns, 
                                       xscrollcommand=scroll_x.set, 
                                       yscrollcommand=scroll_y.set, 
                                       show="headings")

        scroll_x.config(command=self.result_table.xview)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        scroll_y.config(command=self.result_table.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.result_table.pack(fill=tk.BOTH, expand=True)

        # Define column headings
        for col in self.columns:
            self.result_table.heading(col, text=col)
            self.result_table.column(col, width=100, anchor="center")

    def create_footer(self):
        footer_frame = tk.Frame(self.root, bg="pink")
        footer_frame.pack(fill=tk.X)

        footer_label = tk.Label(footer_frame, 
                              text="Designed and developed by Nice Computers & Industrial Solutions", 
                              font=("Arial", 10), bg="pink")
        footer_label.pack(pady=5)

    def search_records(self):
        # Clear existing table
        for item in self.result_table.get_children():
            self.result_table.delete(item)
            
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Convert dates to datetime format
            start_date = self.start_date_entry.get_date().strftime('%Y-%m-%d 00:00:00')
            end_date = self.end_date_entry.get_date().strftime('%Y-%m-%d 23:59:59')
            part_number = self.part_combobox.get()
            
            query = """
                SELECT 
                    ID, TD_MACHINE_ID, TD_PART_NUMBER, TD_TRACEABILITY_CODE,
                    TD_LOT_NUMBER, TD_RECORD_DATE, L1, L2, L3, L4, P1, P2, P3, P4,
                    CAM1, CAM2, TD_OVERALL_STATUS, TD_EMP_CODE
                FROM TBL_TEST_DATA
                WHERE TD_RECORD_DATE BETWEEN %s AND %s
                AND TD_PART_NUMBER = %s
                ORDER BY TD_RECORD_DATE DESC
            """
            
            cursor.execute(query, (start_date, end_date, part_number))
            records = cursor.fetchall()
            
            # Insert records into table
            for i, record in enumerate(records, 1):
                values = [i] + list(record)[1:]  # Add row number
                self.result_table.insert('', 'end', values=values)
                
        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
    
                

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = DataConsole()
    app.run()

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import mysql.connector

import db
import ui
from datetime import datetime
import csv
import os

class DataConsole:
    def __init__(self, root):
        # Accept parent window instead of creating new one
        self.root = root
        ui.apply(root)
        self.root.title("EOL (END OF LINE) TESTER")
        
        # Database configuration
        self.db_config = db.get_config()
        
        self.create_header()
        self.create_input_section()
        self.create_table()
        self.create_footer()
        
        # Load part numbers after UI is created
        self.load_part_numbers()

    def create_header(self):
        ui.page_header(self.root, "Work Data", compact=True, icon='bars')

    def create_input_section(self):
        self.page_scroller = ui.scrollable(self.root, horizontal=True)
        self.page_scroller.pack(fill=tk.BOTH, expand=True)
        page = self.page_scroller.body

        filters = ui.ctk_card(page)
        filters.pack(fill=tk.X, padx=ui.PAD_LARGE, pady=(ui.PAD_LARGE, 0))
        ui.ctk_card_header(filters, "SEARCH FILTERS", icon='clipboard')

        input_frame = tk.Frame(filters, bg=ui.SURFACE, padx=10, pady=10)
        input_frame.pack(fill=tk.X)

        # Part Number
        part_label = tk.Label(input_frame, text="PART NUMBER:", bg=ui.SURFACE,
                              fg=ui.TEXT_MUTED, font=ui.FONT_BODY_BOLD)
        part_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.part_combobox = ttk.Combobox(input_frame, state="readonly", width=20)
        self.part_combobox.grid(row=0, column=1, padx=5, pady=5)

        # Start Date Label
        start_date_label = tk.Label(input_frame, text="START DATE:", bg=ui.SURFACE,
                                    fg=ui.TEXT_MUTED, font=ui.FONT_BODY_BOLD)
        start_date_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")

        # Set start date to beginning of current month and end date to current date
        current_date = datetime.now()
        start_of_month = current_date.replace(day=1)

        # Calendar widget for start date with enhanced styling
        self.start_date_entry = DateEntry(input_frame, 
                                        width=18, 
                                        date_pattern='dd-mm-yyyy',
                                        background=ui.ACCENT_FILL,
                                        foreground=ui.TEXT_ON_ACCENT,
                                        borderwidth=0,
                                        font=ui.FONT_BODY,
                                        showweeknumbers=False,
                                        showothermonthdays=True,
                                        firstweekday='sunday',
                                        maxdate=current_date,
                                        selectmode='day',
                                        cursor='hand2')
        self.start_date_entry.grid(row=0, column=3, padx=5, pady=5)
        self.start_date_entry.set_date(start_of_month)

        # End Date Label
        end_date_label = tk.Label(input_frame, text="END DATE:", bg=ui.SURFACE,
                                  fg=ui.TEXT_MUTED, font=ui.FONT_BODY_BOLD)
        end_date_label.grid(row=0, column=4, padx=5, pady=5, sticky="e")

        # Calendar widget for end date with enhanced styling
        self.end_date_entry = DateEntry(input_frame, 
                                      width=18, 
                                      date_pattern='dd-mm-yyyy',
                                      background=ui.ACCENT_FILL,
                                      foreground=ui.TEXT_ON_ACCENT,
                                      borderwidth=0,
                                      font=ui.FONT_BODY,
                                      showweeknumbers=False,
                                      showothermonthdays=True,
                                      firstweekday='sunday',
                                      maxdate=current_date,
                                      selectmode='day',
                                      cursor='hand2')
        self.end_date_entry.grid(row=0, column=5, padx=5, pady=5)
        self.end_date_entry.set_date(current_date)

        # Result
        result_label = tk.Label(input_frame, text="RESULT:", bg=ui.SURFACE,
                                fg=ui.TEXT_MUTED, font=ui.FONT_BODY_BOLD)
        result_label.grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.result_combobox = ttk.Combobox(input_frame, state="readonly", width=20, 
                                          values=["ALL", "PASS", "NG"])
        self.result_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.result_combobox.set("ALL")  # Set default value

        # Part Status
        status_label = tk.Label(input_frame, text="PART STATUS:", bg=ui.SURFACE,
                                fg=ui.TEXT_MUTED, font=ui.FONT_BODY_BOLD)
        status_label.grid(row=2, column=2, padx=5, pady=5, sticky="e")
        self.status_combobox = ttk.Combobox(input_frame, state="readonly", width=20,
                                          values=["ACTIVE", "INACTIVE"])
        self.status_combobox.grid(row=2, column=3, padx=5, pady=5)
        self.status_combobox.set("ACTIVE")  # Set default value

        # Buttons
        self.search_button = ui.ctk_button(input_frame, text="Search", icon='clipboard',
                                           kind='primary', width=120,
                                           command=self.search_records)
        self.search_button.grid(row=0, column=10, padx=10, pady=5)

        self.export_button = ui.ctk_button(input_frame, text="Export", icon='download',
                                           kind='success', width=120,
                                           command=self.export_to_csv)
        self.export_button.grid(row=0, column=11, padx=10, pady=5)

    def create_table(self):
        self.columns = ["NO", "LOT NUMBER", "PART NUMBER", "L1", "L2", "L3", "L4", 
                       "P1", "P2", "P3", "P4", "RESULT", "SCAN RESULT", 
                       "EMPLOYEE CODE", "SPEC DATA", "CREATED DATE"]

        table_card = ui.ctk_card(self.page_scroller.body)
        table_card.pack(fill=tk.BOTH, expand=True, padx=ui.PAD_LARGE,
                        pady=ui.PAD_LARGE)
        ui.ctk_card_header(table_card, "RESULTS", icon='list')

        table_frame = tk.Frame(table_card, bg=ui.SURFACE, padx=10, pady=10)
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
        tk.Frame(self.root, bg=ui.BORDER, height=1).pack(fill=tk.X)
        footer_frame = tk.Frame(self.root, bg=ui.SURFACE)
        footer_frame.pack(fill=tk.X)

        footer_label = tk.Label(footer_frame,
                              text="Designed and developed by Nice Computers & Industrial Solutions",
                              font=ui.FONT_SMALL, bg=ui.SURFACE, fg=ui.TEXT_MUTED)
        footer_label.pack(pady=5)

    def load_part_numbers(self):
        """Load part numbers from TBL_MODEL_MASTER into combobox"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("SELECT MM_PART_NUMBER FROM TBL_MODEL_MASTER ORDER BY MM_PART_NUMBER")
            part_numbers = [row[0] for row in cursor.fetchall()]
            
            # Add "ALL" option at the beginning
            part_numbers.insert(0, "ALL")
            self.part_combobox['values'] = part_numbers
            
            # Set default to ALL
            if part_numbers:
                self.part_combobox.set("ALL")
            
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to load part numbers: {err}")
    
    def search_records(self):
        """Search records based on filters"""
        # Clear existing table
        for item in self.result_table.get_children():
            self.result_table.delete(item)
            
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Get filter values - convert date objects to proper format for MySQL
            start_date = self.start_date_entry.get_date().strftime('%Y-%m-%d')
            end_date = self.end_date_entry.get_date().strftime('%Y-%m-%d')
            part_number = self.part_combobox.get()
            result_filter = self.result_combobox.get()
            
            # Build query with dynamic filters for TBL_TEST_RESULTS
            query = """
                SELECT 
                    ID, LOT_NUMBER, PART_NUMBER, L1, L2, L3, L4, P1, P2, P3, P4,
                    RESULT, SCAN_RESULT, EMP_CODE, SPEC_DATA, CREATED_DATE
                FROM TBL_TEST_RESULTS
                WHERE DATE(CREATED_DATE) BETWEEN %s AND %s
            """
            params = [start_date, end_date]
            
            # Add part number filter if not ALL
            if part_number and part_number != "ALL":
                query += " AND PART_NUMBER = %s"
                params.append(part_number)
            
            # Add result filter if not ALL
            if result_filter and result_filter != "ALL":
                query += " AND RESULT = %s"
                params.append(result_filter)
            
            query += " ORDER BY CREATED_DATE DESC"
            
            cursor.execute(query, tuple(params))
            records = cursor.fetchall()
            
            # Insert records into table
            for i, record in enumerate(records, 1):
                values = [i] + list(record)[1:]  # Add row number, skip ID
                self.result_table.insert('', 'end', values=values)
            
            # Show count
            messagebox.showinfo("Search Complete", f"Found {len(records)} records")
                
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Search failed: {err}")
            
        finally:
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
    
    def export_to_csv(self):
        """Export table data to CSV file"""
        try:
            # Check if there's data to export
            if not self.result_table.get_children():
                messagebox.showwarning("No Data", "No data to export. Please search first.")
                return
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"EOL_Data_Export_{timestamp}.csv"
            
            # Get desktop path
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
            filepath = os.path.join(desktop, filename)
            
            # Write to CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Write headers
                writer.writerow(self.columns)
                
                # Write data
                for item in self.result_table.get_children():
                    values = self.result_table.item(item)['values']
                    writer.writerow(values)
            
            messagebox.showinfo("Export Successful", f"Data exported to:\n{filepath}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {e}")
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = DataConsole(root)
    root.mainloop()

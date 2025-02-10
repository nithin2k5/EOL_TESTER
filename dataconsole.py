import tkinter as tk
from tkinter import ttk

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

        # Start Date
        start_date_label = tk.Label(input_frame, text="START DATE:", font=("Arial", 12))
        start_date_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.start_date_entry = tk.Entry(input_frame, width=20)
        self.start_date_entry.grid(row=0, column=3, padx=5, pady=5)

        # End Date
        end_date_label = tk.Label(input_frame, text="END DATE:", font=("Arial", 12))
        end_date_label.grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.end_date_entry = ttk.Entry(input_frame, width=20)
        self.end_date_entry.grid(row=0, column=5, padx=5, pady=5)

        # Result
        result_label = tk.Label(input_frame, text="RESULT:", font=("Arial", 12))
        result_label.grid(row=0, column=6, padx=5, pady=5, sticky="e")
        self.result_combobox = ttk.Combobox(input_frame, state="readonly", width=20)
        self.result_combobox.grid(row=0, column=7, padx=5, pady=5)

        # Part Status
        status_label = tk.Label(input_frame, text="PART STATUS:", font=("Arial", 12))
        status_label.grid(row=0, column=8, padx=5, pady=5, sticky="e")
        self.status_combobox = ttk.Combobox(input_frame, state="readonly", width=20)
        self.status_combobox.grid(row=0, column=9, padx=5, pady=5)

        # Buttons
        self.search_button = tk.Button(input_frame, text="Search", bg="red", 
                                     fg="white", font=("Arial", 12))
        self.search_button.grid(row=0, column=10, padx=10, pady=5)

        self.export_button = tk.Button(input_frame, text="Export", bg="green", 
                                     fg="white", font=("Arial", 12))
        self.export_button.grid(row=0, column=11, padx=10, pady=5)

    def create_table(self):
        self.columns = ["NO", "MACHINE ID", "PART NUMBER", "ALC", "LOT NUMBER", 
                       "CREATED DATE", "L1", "L2", "L3", "L4", "P1", "P2", "P3", 
                       "P4", "CAM1", "CAM2", "RESULT"]

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

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = DataConsole()
    app.run()

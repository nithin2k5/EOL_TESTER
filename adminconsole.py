import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import mysql.connector
from tkcalendar import DateEntry

class AdminConsole:
    def __init__(self, root):
        self.root = root
        self.root.title("ADMIN CONSOLE")
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'nk446420',
            'database': 'EOL'
        }
        
        # Initialize database
        self.init_database()
        
        # Make it full screen
        self.root.attributes('-fullscreen', True)  # Changed to true fullscreen
        
        # Configure the main background color
        self.root.configure(bg='pink')
        
        # Add escape key binding to exit fullscreen
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        
        # Create and setup the UI
        self.setup_ui()
        
        # Load existing records
        self.load_records()

    def init_database(self):
        """Initialize the database table"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS EMPLOYEE_INFO (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    EMPLOYEE_FULL_NAME VARCHAR(255),
                    EMPLOYEE_NUMBER VARCHAR(50) UNIQUE,
                    PASSWORD VARCHAR(255),
                    DESIGNATION VARCHAR(100),
                    DEPARTMENT VARCHAR(100),
                    MOBILE_NUMBER VARCHAR(20),
                    IS_ACTIVE BOOLEAN DEFAULT TRUE
                )
            ''')
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to initialize database: {err}")

    def load_records(self):
        """Load existing records into the treeview"""
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT EMPLOYEE_FULL_NAME, EMPLOYEE_NUMBER, DESIGNATION, 
                       DEPARTMENT, MOBILE_NUMBER, IS_ACTIVE 
                FROM EMPLOYEE_INFO 
                ORDER BY ID DESC
            """)
            
            for i, row in enumerate(cursor.fetchall(), 1):
                status = "Active" if row[5] else "Inactive"
                self.tree.insert('', 'end', values=(i,) + row[:-1] + (status,))
            
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to load records: {err}")

    def add_record(self):
        """Add a new employee record"""
        try:
            # Get values from entries, ignoring placeholder text
            values = {}
            for field, entry in self.entries.items():
                value = entry.get().strip()
                if value == self.get_placeholder(field):
                    messagebox.showwarning("Warning", f"Please enter {field.lower().strip(':')}")
                    return
                values[field] = value
            
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = """
                INSERT INTO EMPLOYEE_INFO (
                    EMPLOYEE_FULL_NAME, EMPLOYEE_NUMBER, PASSWORD,
                    DESIGNATION, DEPARTMENT, MOBILE_NUMBER, IS_ACTIVE
                ) VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            """
            
            cursor.execute(query, (
                values["EMPLOYEE FULL NAME :"],
                values["EMPLOYEE NUMBER :"],
                values["PASSWORD :"],
                values["DESIGNATION :"],
                values["DEPARTMENT :"],
                values["MOBILE NUMBER :"]
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messagebox.showinfo("Success", "Employee added successfully!")
            self.load_records()
            self.clear_entries()
            
        except mysql.connector.Error as err:
            if err.errno == 1062:  # Duplicate entry error
                messagebox.showerror("Error", "Employee number already exists!")
            else:
                messagebox.showerror("Database Error", f"Failed to add employee: {err}")

    def get_placeholder(self, field):
        """Get placeholder text for a field"""
        placeholders = {
            "EMPLOYEE FULL NAME :": "Enter Full Name",
            "EMPLOYEE NUMBER :": "Enter Employee Number",
            "PASSWORD :": "Enter Password",
            "DESIGNATION :": "Enter Designation",
            "DEPARTMENT :": "Enter Department",
            "MOBILE NUMBER :": "Enter Mobile Number"
        }
        return placeholders.get(field, "")

    def clear_entries(self):
        """Clear all entry fields and reset to default state with placeholders"""
        default_values = {
            "EMPLOYEE FULL NAME :": "Enter Full Name",
            "EMPLOYEE NUMBER :": "Enter Employee Number",
            "PASSWORD :": "Enter Password",
            "DESIGNATION :": "Enter Designation",
            "DEPARTMENT :": "Enter Department",
            "MOBILE NUMBER :": "Enter Mobile Number"
        }
        
        for field, entry in self.entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, default_values.get(field, ""))
            entry.config(fg='gray')
            
            # Rebind placeholder events
            placeholder = default_values.get(field, "")
            entry.bind('<FocusIn>', lambda e, entry=entry, placeholder=placeholder: 
                self.on_entry_focus_in(entry, placeholder))
            entry.bind('<FocusOut>', lambda e, entry=entry, placeholder=placeholder: 
                self.on_entry_focus_out(entry, placeholder))
        
        # Clear treeview selection
        if hasattr(self, 'tree'):
            self.tree.selection_remove(self.tree.selection())

    def on_entry_focus_in(self, entry, placeholder):
        """Handle entry field focus in"""
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg='black')

    def on_entry_focus_out(self, entry, placeholder):
        """Handle entry field focus out"""
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg='gray')

    def delete_record(self):
        """Delete selected employee record"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a record to delete!")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this record?"):
            try:
                item = self.tree.item(selected[0])
                emp_number = item['values'][2]  # Employee number is at index 2
                
                conn = mysql.connector.connect(**self.db_config)
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM EMPLOYEE_INFO WHERE EMPLOYEE_NUMBER = %s", (emp_number,))
                conn.commit()
                cursor.close()
                conn.close()
                
                messagebox.showinfo("Success", "Record deleted successfully!")
                self.load_records()
                
            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", f"Failed to delete record: {err}")

    def save_record(self):
        """Save/Update employee record"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a record to save!")
            return
        
        try:
            values = {field: entry.get().strip() for field, entry in self.entries.items()}
            item = self.tree.item(selected[0])
            emp_number = item['values'][2]  # Original employee number
            
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = """
                UPDATE EMPLOYEE_INFO SET 
                    EMPLOYEE_FULL_NAME = %s,
                    EMPLOYEE_NUMBER = %s,
                    PASSWORD = %s,
                    DESIGNATION = %s,
                    DEPARTMENT = %s,
                    MOBILE_NUMBER = %s
                WHERE EMPLOYEE_NUMBER = %s
            """
            
            cursor.execute(query, (
                values["EMPLOYEE FULL NAME :"],
                values["EMPLOYEE NUMBER :"],
                values["PASSWORD :"],
                values["DESIGNATION :"],
                values["DEPARTMENT :"],
                values["MOBILE NUMBER :"],
                emp_number
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messagebox.showinfo("Success", "Record updated successfully!")
            self.load_records()
            self.clear_entries()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to update record: {err}")

    def edit_record(self):
        """Load selected record into entry fields"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a record to edit!")
            return
        
        # Get values from selected item
        item = self.tree.item(selected[0])
        values = item['values']
        
        # Clear and populate entry fields
        self.clear_entries()
        fields = ["EMPLOYEE FULL NAME :", "EMPLOYEE NUMBER :", "DESIGNATION :", 
                 "DEPARTMENT :", "MOBILE NUMBER :"]
        for field, value in zip(fields, values[1:]):  # Skip the NO column
            if field in self.entries:
                self.entries[field].insert(0, value)

    def setup_ui(self):
        # Load icons
        try:
            self.add_icon = ImageTk.PhotoImage(Image.open("icons/add_icon.png").resize((20, 20)))
            self.edit_icon = ImageTk.PhotoImage(Image.open("icons/edit_icon.png").resize((20, 20)))
            self.save_icon = ImageTk.PhotoImage(Image.open("icons/save_icon.png").resize((20, 20)))
            self.delete_icon = ImageTk.PhotoImage(Image.open("icons/delete_icon.png").resize((20, 20)))
            self.clear_icon = ImageTk.PhotoImage(Image.open("icons/clear_icon.png").resize((20, 20)))
        except Exception as e:
            print(f"Error loading icons: {e}")
            # Fallback to text-only buttons if icons fail to load
            self.add_icon = self.edit_icon = self.save_icon = self.delete_icon = self.clear_icon = None

        # Header
        header_frame = tk.Frame(self.root, bg='pink', height=80)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # INFAC INDIA logo placeholder (left side)
        logo_label = tk.Label(header_frame, text="INFAC\nINDIA", bg='pink', font=('Arial', 12, 'bold'))
        logo_label.pack(side=tk.LEFT, padx=20)
        
        # EOL TESTER title (center)
        title_label = tk.Label(
            header_frame, 
            text="EOL (END OF LINE) TESTER",
            bg='pink',
            font=('Arial', 24, 'bold')
        )
        title_label.pack(expand=True)

        # Main content frame
        content_frame = tk.Frame(self.root, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Top section container
        top_container = tk.Frame(content_frame, bg='white')
        top_container.pack(fill=tk.X, padx=10, pady=10)

        # Left side - Entry fields (70% of width)
        left_frame = tk.Frame(top_container, bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Fields configuration
        fields = [
            "EMPLOYEE FULL NAME :",
            "EMPLOYEE NUMBER :",
            "PASSWORD :",
            "DESIGNATION :",
            "DEPARTMENT :",
            "MOBILE NUMBER :"
        ]

        # Create a frame for organizing entry fields in a grid layout
        entries_frame = tk.Frame(left_frame, bg='white')
        entries_frame.pack(anchor='w', padx=20)

        self.entries = {}
        for i, field in enumerate(fields):
            # Create frame for each row
            row_frame = tk.Frame(entries_frame, bg='white')
            row_frame.pack(fill=tk.X, pady=5)
            
            # Label with fixed width
            label = tk.Label(
                row_frame, 
                text=field,
                bg='white',
                fg='black',
                font=('Arial', 10, 'bold'),
                width=20,
                anchor='e'
            )
            label.pack(side=tk.LEFT, padx=5)
            
            # Entry with specified width
            entry = tk.Entry(
                row_frame,
                font=('Arial', 10),
                width=40,
                bg='black',
                fg='white',
                relief='solid',
                bd=1
            )
            entry.pack(side=tk.LEFT, padx=5)
            self.entries[field] = entry

        # Right side - Buttons frame (30% of width)
        right_frame = tk.Frame(top_container, bg='white')
        right_frame.pack(side=tk.RIGHT, padx=20)

        # Configure treeview style
        style = ttk.Style()
        style.configure(
            "Custom.Treeview",
            background="black",
            foreground="white",
            fieldbackground="black",  # Color of empty rows
            rowheight=25,
            font=('Arial', 9)
        )
        
        style.configure(
            "Custom.Treeview.Heading",
            background="navy",
            foreground="white",
            relief="flat",
            font=('Arial', 10, 'bold')
        )
        
        # Map selected row colors
        style.map('Custom.Treeview',
            background=[('selected', '#303030')],
            foreground=[('selected', '#ffffff')]
        )

        # Updated buttons configuration with distinct colors
        buttons = [
            ("ADD", "#2ecc71", self.add_record, self.add_icon),      # Green
            ("EDIT", "#e67e22", self.edit_record, self.edit_icon),   # Orange
            ("SAVE", "#3498db", self.save_record, self.save_icon),   # Blue
            ("DELETE", "#e74c3c", self.delete_record, self.delete_icon),  # Red
            ("CLEAR", "#95a5a6", self.clear_entries, self.clear_icon)     # Gray
        ]

        # Create buttons vertically with spacing and updated hover colors
        for text, color, command, icon in buttons:
            btn_frame = tk.Frame(right_frame, bg='white')
            btn_frame.pack(pady=5)
            
            btn = tk.Button(
                btn_frame,
                text=" " + text,
                command=command,
                bg=color,
                fg='white',
                font=('Arial', 10, 'bold'),
                width=15,
                height=2,
                relief='raised',
                bd=2,
                cursor='hand2',
                compound='left'
            )
            if icon:
                btn.config(image=icon)
            btn.pack()
            
            # Custom hover colors for each button
            hover_colors = {
                "#2ecc71": "#27ae60",  # Darker green
                "#e67e22": "#d35400",  # Darker orange
                "#3498db": "#2980b9",  # Darker blue
                "#e74c3c": "#c0392b",  # Darker red
                "#95a5a6": "#7f8c8d"   # Darker gray
            }
            
            btn.bind('<Enter>', lambda e, b=btn, c=hover_colors[color]: b.configure(bg=c))
            btn.bind('<Leave>', lambda e, b=btn, c=color: b.configure(bg=c))

        # Treeview section
        tree_frame = tk.Frame(content_frame, bg='white')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(20, 10))

        # Configure columns
        columns = ('NO', 'EMPLOYEE FULL NAME', 'EMPLOYEE NUMBER', 
                  'DESIGNATION', 'DEPARTMENT', 'MOBILE NUMBER', 'STATUS')
        
        self.tree = ttk.Treeview(
            tree_frame, 
            columns=columns, 
            show='headings', 
            height=15,
            style="Custom.Treeview"
        )
        
        # Column widths
        widths = {
            'NO': 50,
            'EMPLOYEE FULL NAME': 200,
            'EMPLOYEE NUMBER': 150,
            'DESIGNATION': 150,
            'DEPARTMENT': 150,
            'MOBILE NUMBER': 150,
            'STATUS': 100
        }
        
        # Configure columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], anchor='center')

        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Footer
        footer_text = "Powered By: IRACRAT TECHNOLOGIES. Contact: INFO@IRACRAT.COM, (+91) 99623 44614."
        footer = tk.Label(
            self.root,
            text=footer_text,
            bg='pink',
            font=('Arial', 8)
        )
        footer.pack(side=tk.BOTTOM, pady=5)

        # Bind treeview selection event
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

    def lighten_color(self, color):
        """Helper function for hover effects - Not used anymore as we have specific hover colors"""
        pass  # This function is kept for compatibility but no longer needed

    def on_tree_select(self, event):
        """Handle treeview selection with improved entry handling"""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            values = item['values']
            
            # Clear entries without setting placeholders
            for entry in self.entries.values():
                entry.delete(0, tk.END)
                entry.config(fg='black')  # Set text color to black for actual data
            
            # Populate entries with selected record data
            fields = ["EMPLOYEE FULL NAME :", "EMPLOYEE NUMBER :", "DESIGNATION :", 
                     "DEPARTMENT :", "MOBILE NUMBER :"]
            for field, value in zip(fields, values[1:6]):  # Skip NO and STATUS
                if field in self.entries:
                    self.entries[field].insert(0, value)
                    self.entries[field].config(fg='black')  # Ensure text is black
                    # Unbind placeholder events temporarily
                    self.entries[field].unbind('<FocusIn>')
                    self.entries[field].unbind('<FocusOut>')

    def add_image_to_frame(self, image_path):
        try:
            # Open and resize image
            image = Image.open(image_path)
            image = image.resize((140, 170), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # Create label and display image
            image_label = tk.Label(self.image_frame, image=photo, bg='white')
            image_label.image = photo  # Keep a reference
            image_label.pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            print(f"Error loading image: {e}")

def main():
    root = tk.Tk()
    app = AdminConsole(root)
    root.mainloop()

if __name__ == "__main__":
    main()
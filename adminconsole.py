import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import mysql.connector
from tkcalendar import DateEntry
import os
import json
from datetime import datetime, timedelta
import csv
import shutil
import auth
import config
import db
import ui

class AdminConsole:
    # A stored password is a hash, so it is never shown. This stands in
    # its place and means "leave the password as it is".
    KEEP_PASSWORD = "(unchanged - type to replace)"

    def __init__(self, root):
        self.root = root
        ui.apply(root)
        
        # Initialize backup paths and machine ID from environment variables
        self.backup_paths = {
            'primary': config.get('PRIMARY_BACKUP_PATH', ''),
            'secondary': config.get('SECONDARY_BACKUP_PATH', '')
        }
        self.machine_id = config.get('MACHINE_ID', '')  # Get machine ID from settings
        
        # Set title with machine ID
        title = "ADMIN CONSOLE"
        if self.machine_id:
            title += f" - Machine ID: {self.machine_id}"
        self.root.title(title)
        
        # Database configuration
        self.db_config = db.get_config()
        
        # Initialize database
        self.init_database()
        
        # Configure the main background color
        self.root.configure(bg=ui.APP_BG)
        
        # Create and setup the UI
        self.setup_ui()
        
        # Load existing records
        self.load_records()

    def init_database(self):
        """Create the database and any missing tables."""
        if not db.init_database():
            messagebox.showerror("Database Error", "Failed to initialize database")

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
            # Get values from entries
            values = {}
            for field, entry in self.entries.items():
                value = entry.get().strip()
                placeholder = self.get_placeholder(field)
                # Check if value is empty or is placeholder text
                if not value or value == placeholder:
                    messagebox.showwarning("Warning", f"Please enter {field.lower().replace(':', '').strip()}")
                    entry.focus_set()  # Set focus to the empty field
                    return
                values[field] = value
            
            # A new employee needs a real password, not the "unchanged" marker
            # left behind by selecting an existing record.
            if values["PASSWORD :"] == self.KEEP_PASSWORD:
                messagebox.showwarning("Warning", "Please enter a password for the new employee")
                self.entries["PASSWORD :"].focus_set()
                return
            
            # Add machine ID to the record
            machine_id = self.machine_id_var.get().strip()
            if not machine_id:
                messagebox.showwarning("Warning", "Please set Machine ID first")
                return
            
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = """
                INSERT INTO EMPLOYEE_INFO (
                    EMPLOYEE_FULL_NAME, EMPLOYEE_NUMBER, PASSWORD,
                    DESIGNATION, DEPARTMENT, MOBILE_NUMBER, MACHINE_ID, IS_ACTIVE
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
            """
            
            cursor.execute(query, (
                values["EMPLOYEE FULL NAME :"],
                values["EMPLOYEE NUMBER :"],
                auth.compute_hash(values["PASSWORD :"]),
                values["DESIGNATION :"],
                values["DEPARTMENT :"],
                values["MOBILE NUMBER :"],
                machine_id
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

    def show_password_placeholder(self):
        """Mark the password box as carrying the stored password, not a new one."""
        entry = self.entries.get("PASSWORD :")
        if entry is None:
            return

        entry.delete(0, tk.END)
        entry.insert(0, self.KEEP_PASSWORD)
        entry.config(fg='#999999')

        # Clear the marker as soon as the operator starts typing a new one.
        def clear_marker(event, entry=entry):
            if entry.get() == self.KEEP_PASSWORD:
                entry.delete(0, tk.END)
                entry.config(fg='black')

        def restore_marker(event, entry=entry):
            if not entry.get():
                entry.insert(0, self.KEEP_PASSWORD)
                entry.config(fg='#999999')

        entry.bind('<FocusIn>', clear_marker)
        entry.bind('<FocusOut>', restore_marker)

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
            entry.config(fg='#999999')  # Gray color for placeholder
            
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
            entry.config(fg='#999999')  # Gray color for placeholder

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
                self.clear_entries()  # Clear entries after deletion
                
            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", f"Failed to delete record: {err}")

    def save_record(self):
        """Save/Update employee record"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a record to save!")
            return
        
        try:
            # Get and validate values from entries
            values = {}
            for field, entry in self.entries.items():
                value = entry.get().strip()
                placeholder = self.get_placeholder(field)
                # Check if value is empty or is placeholder text
                if not value or value == placeholder:
                    messagebox.showwarning("Warning", f"Please enter {field.lower().replace(':', '').strip()}")
                    entry.focus_set()
                    return
                values[field] = value
            
            item = self.tree.item(selected[0])
            emp_number = item['values'][2]  # Original employee number
            
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # The password column is only touched when a new one was typed.
            typed_password = values["PASSWORD :"]
            replace_password = typed_password != self.KEEP_PASSWORD
            
            if replace_password:
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
                parameters = (
                    values["EMPLOYEE FULL NAME :"],
                    values["EMPLOYEE NUMBER :"],
                    auth.compute_hash(typed_password),
                    values["DESIGNATION :"],
                    values["DEPARTMENT :"],
                    values["MOBILE NUMBER :"],
                    emp_number
                )
            else:
                query = """
                    UPDATE EMPLOYEE_INFO SET 
                        EMPLOYEE_FULL_NAME = %s,
                        EMPLOYEE_NUMBER = %s,
                        DESIGNATION = %s,
                        DEPARTMENT = %s,
                        MOBILE_NUMBER = %s
                    WHERE EMPLOYEE_NUMBER = %s
                """
                parameters = (
                    values["EMPLOYEE FULL NAME :"],
                    values["EMPLOYEE NUMBER :"],
                    values["DESIGNATION :"],
                    values["DEPARTMENT :"],
                    values["MOBILE NUMBER :"],
                    emp_number
                )
            
            cursor.execute(query, parameters)
            
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
        
        try:
            # Get values from selected item
            item = self.tree.item(selected[0])
            values = item['values']
            emp_number = values[2]  # Employee number
            
            # Fetch full record including password from database
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EMPLOYEE_FULL_NAME, EMPLOYEE_NUMBER, 
                       DESIGNATION, DEPARTMENT, MOBILE_NUMBER
                FROM EMPLOYEE_INFO
                WHERE EMPLOYEE_NUMBER = %s
            """, (emp_number,))
            
            record = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not record:
                messagebox.showerror("Error", "Could not load employee record")
                return
            
            # Clear all entries first
            for entry in self.entries.values():
                entry.delete(0, tk.END)
                entry.config(fg='black')
                # Unbind placeholder events
                entry.unbind('<FocusIn>')
                entry.unbind('<FocusOut>')
            
            # Populate entry fields with actual data
            fields = ["EMPLOYEE FULL NAME :", "EMPLOYEE NUMBER :",
                     "DESIGNATION :", "DEPARTMENT :", "MOBILE NUMBER :"]
            
            for field, value in zip(fields, record):
                if field in self.entries:
                    self.entries[field].delete(0, tk.END)
                    self.entries[field].insert(0, value)
                    self.entries[field].config(fg='black')
            
            self.show_password_placeholder()
                    
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to load record: {err}")

    def setup_ui(self):
        # Load icons with fallback text
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icons")
            self.add_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_path, "add_icon.png")).resize((20, 20)))
            self.edit_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_path, "edit_icon.png")).resize((20, 20)))
            self.save_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_path, "save_icon.png")).resize((20, 20)))
            self.delete_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_path, "delete_icon.png")).resize((20, 20)))
            self.clear_icon = ImageTk.PhotoImage(Image.open(os.path.join(icon_path, "clear_icon.png")).resize((20, 20)))
        except Exception as e:
            print(f"Error loading icons: {e}")
            # Set icons to None for fallback to text-only buttons
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

        # Main content frame, inside a scroller so nothing falls off a
        # shorter screen.
        self.page_scroller = ui.scrollable(self.root)
        self.page_scroller.pack(fill=tk.BOTH, expand=True)
        
        content_frame = tk.Frame(self.page_scroller.body, bg='white')
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
        placeholders = {
            "EMPLOYEE FULL NAME :": "Enter Full Name",
            "EMPLOYEE NUMBER :": "Enter Employee Number",
            "PASSWORD :": "Enter Password",
            "DESIGNATION :": "Enter Designation",
            "DEPARTMENT :": "Enter Department",
            "MOBILE NUMBER :": "Enter Mobile Number"
        }
        
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
                bg='white',
                fg='#999999',  # Start with gray placeholder color
                relief='solid',
                bd=1,
                insertbackground='black'
            )
            entry.pack(side=tk.LEFT, padx=5)
            self.entries[field] = entry
            
            # Insert placeholder text
            placeholder = placeholders.get(field, "")
            entry.insert(0, placeholder)
            
            # Bind focus events for placeholder behavior
            entry.bind('<FocusIn>', lambda e, entry=entry, placeholder=placeholder: 
                self.on_entry_focus_in(entry, placeholder))
            entry.bind('<FocusOut>', lambda e, entry=entry, placeholder=placeholder: 
                self.on_entry_focus_out(entry, placeholder))

        # Add Backup Path Selection frames after Machine ID
        self.create_backup_path_section(entries_frame)

        # Right side - Buttons frame (30% of width)
        right_frame = tk.Frame(top_container, bg='white')
        right_frame.pack(side=tk.RIGHT, padx=20)

        # Configure treeview style
        style = ttk.Style()
        style.configure(
            "Custom.Treeview",
            background=ui.SURFACE,
            foreground=ui.TEXT,
            fieldbackground=ui.SURFACE,  # Color of empty rows
            rowheight=26,
            font=ui.FONT_BODY
        )
        
        style.configure(
            "Custom.Treeview.Heading",
            background=ui.SUBTLE,
            foreground=ui.TEXT,
            relief="flat",
            font=ui.FONT_BODY_BOLD
        )
        
        # Map selected row colors
        style.map('Custom.Treeview',
            background=[('selected', ui.ACCENT)],
            foreground=[('selected', ui.TEXT_ON_ACCENT)]
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
            try:
                item = self.tree.item(selected[0])
                values = item['values']
                emp_number = values[2]  # Employee number
                
                # Fetch full record including password from database
                conn = mysql.connector.connect(**self.db_config)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT EMPLOYEE_FULL_NAME, EMPLOYEE_NUMBER, 
                           DESIGNATION, DEPARTMENT, MOBILE_NUMBER
                    FROM EMPLOYEE_INFO
                    WHERE EMPLOYEE_NUMBER = %s
                """, (emp_number,))
                
                record = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if not record:
                    return
                
                # Clear entries without setting placeholders
                for entry in self.entries.values():
                    entry.delete(0, tk.END)
                    entry.config(fg='black')  # Set text color to black for actual data
                    # Unbind placeholder events temporarily
                    entry.unbind('<FocusIn>')
                    entry.unbind('<FocusOut>')
                
                # Populate entries with selected record data
                fields = ["EMPLOYEE FULL NAME :", "EMPLOYEE NUMBER :",
                         "DESIGNATION :", "DEPARTMENT :", "MOBILE NUMBER :"]
                
                for field, value in zip(fields, record):
                    if field in self.entries:
                        self.entries[field].delete(0, tk.END)
                        self.entries[field].insert(0, value)
                        self.entries[field].config(fg='black')
                
                self.show_password_placeholder()
                        
            except mysql.connector.Error as err:
                print(f"Error loading record: {err}")

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

    def create_backup_path_section(self, parent):
        """Create backup path section with machine ID"""
        # Create a frame with a border and title
        backup_frame = ttk.LabelFrame(parent, text="Backup Configuration", padding=(10, 5))
        backup_frame.pack(fill=tk.X, pady=10, padx=5)
        
        # Machine ID
        row_frame = tk.Frame(backup_frame, bg='white')
        row_frame.pack(fill=tk.X, pady=5)
        
        label = tk.Label(
            row_frame, 
            text="MACHINE ID :",
            bg='white',
            fg='black',
            font=('Arial', 10, 'bold'),
            width=20,
            anchor='e'
        )
        label.pack(side=tk.LEFT, padx=5)
        
        # Text entry for Machine ID
        self.machine_id_var = tk.StringVar(value=self.machine_id)
        self.machine_id_entry = tk.Entry(
            row_frame,
            textvariable=self.machine_id_var,
            width=40,
            bg='white',
            fg='black',
            font=('Arial', 9)
        )
        self.machine_id_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Save Machine ID button
        save_machine_id_btn = tk.Button(
            row_frame,
            text="Save ID",
            command=self.save_machine_id,
            bg='#3498db',
            fg='white',
            font=('Arial', 9, 'bold'),
            relief='raised',
            bd=2,
            padx=10
        )
        save_machine_id_btn.pack(side=tk.LEFT, padx=5)
        
        # Add hover effect for save button
        save_machine_id_btn.bind('<Enter>', lambda e: save_machine_id_btn.configure(bg='#2980b9'))
        save_machine_id_btn.bind('<Leave>', lambda e: save_machine_id_btn.configure(bg='#3498db'))

        # Primary Backup Path
        row_frame = tk.Frame(backup_frame, bg='white')
        row_frame.pack(fill=tk.X, pady=5)
        
        label = tk.Label(
            row_frame, 
            text="PRIMARY BACKUP PATH :",
            bg='white',
            fg='black',
            font=('Arial', 10, 'bold'),
            width=20,
            anchor='e'
        )
        label.pack(side=tk.LEFT, padx=5)
        
        # Text entry for primary path
        primary_default = self.backup_paths.get('primary', '')
        if not primary_default or primary_default == '':
            primary_default = 'Click to select primary backup path...'
        self.primary_path_var = tk.StringVar(value=primary_default)
        self.primary_path_entry = tk.Entry(
            row_frame,
            textvariable=self.primary_path_var,
            width=40,
            bg='#f0f0f0',  # Light gray background
            fg='#666666' if primary_default.startswith('Click') else '#000000',  # Gray for placeholder, black for path
            font=('Arial', 9),
            state='readonly'  # Make read-only, only clickable
        )
        self.primary_path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Bind click event to primary path entry
        self.primary_path_entry.bind('<Button-1>', lambda e: self.browse_backup_path('primary'))
        
        # Secondary Backup Path
        row_frame = tk.Frame(backup_frame, bg='white')
        row_frame.pack(fill=tk.X, pady=5)
        
        label = tk.Label(
            row_frame, 
            text="SECONDARY BACKUP PATH :",
            bg='white',
            fg='black',
            font=('Arial', 10, 'bold'),
            width=20,
            anchor='e'
        )
        label.pack(side=tk.LEFT, padx=5)
        
        # Text entry for secondary path
        secondary_default = self.backup_paths.get('secondary', '')
        if not secondary_default or secondary_default == '':
            secondary_default = 'Click to select secondary backup path...'
        self.secondary_path_var = tk.StringVar(value=secondary_default)
        self.secondary_path_entry = tk.Entry(
            row_frame,
            textvariable=self.secondary_path_var,
            width=40,
            bg='#f0f0f0',  # Light gray background
            fg='#666666' if secondary_default.startswith('Click') else '#000000',  # Gray for placeholder, black for path
            font=('Arial', 9),
            state='readonly'  # Make read-only, only clickable
        )
        self.secondary_path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Bind click event to secondary path entry
        self.secondary_path_entry.bind('<Button-1>', lambda e: self.browse_backup_path('secondary'))

        # Backup Now button with improved styling
        backup_btn = tk.Button(
            backup_frame,
            text="Backup Now",
            command=self.create_backup,
            bg='#2ecc71',
            fg='white',
            font=('Arial', 10, 'bold'),
            relief='raised',
            bd=2,
            padx=20,
            pady=5
        )
        backup_btn.pack(pady=10)
        
        # Add hover effects for backup button
        backup_btn.bind('<Enter>', lambda e: backup_btn.configure(bg='#27ae60'))
        backup_btn.bind('<Leave>', lambda e: backup_btn.configure(bg='#2ecc71'))

        # Add hover effects for text entries
        def on_enter(event):
            event.widget.config(bg='#e8e8e8')  # Slightly darker on hover

        def on_leave(event):
            event.widget.config(bg='#f0f0f0')  # Back to normal color

        for entry in [self.primary_path_entry, self.secondary_path_entry]:
            entry.bind('<Enter>', on_enter)
            entry.bind('<Leave>', on_leave)

    def browse_backup_path(self, path_type):
        """Open folder selection dialog and update backup path"""
        try:
            # Get current path or default to home directory
            current_path = self.backup_paths.get(path_type, '')
            if not current_path or current_path.startswith('Click to select'):
                initial_dir = os.path.expanduser('~')
            else:
                initial_dir = current_path
                
            # Open folder selection dialog
            folder_path = filedialog.askdirectory(
                title=f"Select {path_type.title()} Backup Location",
                initialdir=initial_dir
            )
            
            if folder_path:
                # Update the path in the interface and storage
                if path_type == 'primary':
                    self.primary_path_entry.config(state='normal')  # Temporarily enable
                    self.primary_path_var.set(folder_path)
                    self.primary_path_entry.config(fg='#000000', state='readonly')  # Black text for selected path
                else:
                    self.secondary_path_entry.config(state='normal')  # Temporarily enable
                    self.secondary_path_var.set(folder_path)
                    self.secondary_path_entry.config(fg='#000000', state='readonly')  # Black text for selected path
                
                # Store in backup_paths dictionary
                self.backup_paths[path_type] = folder_path
                
                # Save to the settings file
                config.set(f'{path_type.upper()}_BACKUP_PATH', folder_path)
                
                messagebox.showinfo("Success", f"{path_type.title()} backup path set successfully!")
                
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Failed to set {path_type} backup path:\n{str(e)}"
            )

    def create_backup(self):
        """Create backup of last 3 months data"""
        try:
            # Validate backup paths
            primary_path = self.primary_path_var.get()
            secondary_path = self.secondary_path_var.get()
            
            # Check for placeholder text or empty paths
            if primary_path.startswith('Click to select') or not primary_path.strip():
                primary_path = None
            if secondary_path.startswith('Click to select') or not secondary_path.strip():
                secondary_path = None
            
            if not primary_path and not secondary_path:
                messagebox.showerror("Error", "Please select at least one valid backup location!")
                return
            
            # Validate that paths exist
            if primary_path and not os.path.exists(primary_path):
                messagebox.showerror("Error", f"Primary backup path does not exist: {primary_path}")
                return
            if secondary_path and not os.path.exists(secondary_path):
                messagebox.showerror("Error", f"Secondary backup path does not exist: {secondary_path}")
                return
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)  # 3 months
            
            # Connect to database
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Get data for last 3 months
            query = """
                SELECT 
                    EMPLOYEE_FULL_NAME, 
                    EMPLOYEE_NUMBER, 
                    DESIGNATION, 
                    DEPARTMENT, 
                    MOBILE_NUMBER, 
                    MACHINE_ID,
                    IS_ACTIVE,
                    CREATED_DATE
                FROM EMPLOYEE_INFO 
                WHERE CREATED_DATE BETWEEN %s AND %s
            """
            
            cursor.execute(query, (start_date, end_date))
            data = cursor.fetchall()
            
            if not data:
                messagebox.showinfo("Info", "No data found for the last 3 months")
                return
            
            # Create backup files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"employee_backup_{timestamp}.csv"
            
            # Headers for CSV file
            headers = [
                "Employee Name", 
                "Employee Number", 
                "Designation", 
                "Department", 
                "Mobile Number", 
                "Machine ID",
                "Status",
                "Created Date"
            ]
            
            def save_backup(path):
                if path:
                    full_path = os.path.join(path, filename)
                    with open(full_path, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        for row in data:
                            writer.writerow(row)
                    return full_path
                return None
            
            # Create primary backup
            primary_file = save_backup(primary_path)
            
            # Create secondary backup
            secondary_file = save_backup(secondary_path)
            
            # Create backup info file
            backup_info = {
                'timestamp': timestamp,
                'date_range': {
                    'start': start_date.strftime("%Y-%m-%d"),
                    'end': end_date.strftime("%Y-%m-%d")
                },
                'record_count': len(data),
                'primary_location': primary_file,
                'secondary_location': secondary_file
            }
            
            if primary_path:
                info_file = os.path.join(primary_path, f"backup_info_{timestamp}.json")
                with open(info_file, 'w') as f:
                    json.dump(backup_info, f, indent=4)
            
            messagebox.showinfo("Success", 
                              f"Backup created successfully!\n"
                              f"Records backed up: {len(data)}\n"
                              f"Date range: {start_date.date()} to {end_date.date()}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup: {str(e)}")
        finally:
            if 'conn' in locals():
                cursor.close()
                conn.close()

    def save_machine_id(self):
        """Save Machine ID to environment variable and update database"""
        try:
            machine_id = self.machine_id_var.get().strip()
            if not machine_id:
                messagebox.showwarning("Warning", "Please enter a Machine ID")
                return
            
            # Save to the settings file
            config.set('MACHINE_ID', machine_id)
            self.machine_id = machine_id
            
            # Update database with machine ID for all records
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Update all records with the new machine ID where it's NULL or empty
            cursor.execute("""
                UPDATE EMPLOYEE_INFO 
                SET MACHINE_ID = %s 
                WHERE MACHINE_ID IS NULL OR MACHINE_ID = ''
            """, (machine_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messagebox.showinfo("Success", f"Machine ID saved: {machine_id}")
            
            # Update window title with new machine ID
            title = "ADMIN CONSOLE"
            if self.machine_id:
                title += f" - Machine ID: {self.machine_id}"
            self.root.title(title)
            
            # Refresh the display
            self.load_records()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save Machine ID: {str(e)}")

    def cleanup(self):
        """Cleanup function called when closing the application"""
        try:
            # Save backup paths and machine ID to the settings file
            if self.backup_paths.get('primary') and not self.backup_paths['primary'].startswith('Click to select'):
                config.set('PRIMARY_BACKUP_PATH', self.backup_paths['primary'])
            if self.backup_paths.get('secondary') and not self.backup_paths['secondary'].startswith('Click to select'):
                config.set('SECONDARY_BACKUP_PATH', self.backup_paths['secondary'])
            if self.machine_id_var.get().strip():
                config.set('MACHINE_ID', self.machine_id_var.get().strip())
            
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

def main():
    root = tk.Tk()
    app = AdminConsole(root)
    root.mainloop()

if __name__ == "__main__":
    main()
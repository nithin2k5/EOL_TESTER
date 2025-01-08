import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import json
import mysql.connector
from datetime import datetime
from mysql.connector import Error
import threading

class WorkspaceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EOL Tester - Model Settings")
        
        # Make it full screen
        self.root.state('zoomed')
        
        # Track placed labels
        self.placed_labels = {}
        self.original_positions = {}
        
        # Initialize variables
        self.current_label = None
        self.moving_label = None
        self.image_label = None
        self.workspace_image = None
        self.textboxes = {}
        self.spec_entries = {}
        
        # Set minimum size for quadrants
        self.min_quadrant_size = (500, 400)

        # Style configuration
        self.style = ttk.Style()
        self.style.configure("Header.TLabel", font=('Arial', 12, 'bold'), background='navy', foreground='white')
        self.style.configure("Custom.TEntry", padding=5)
        
        self.image_uploaded = False  # Flag to track image upload
        
        # Initialize label tracking dictionaries
        self.label_status = {str(i+1): {'status': 'OFF'} for i in range(16)}
        self.label_details = {str(i+1): {'details': ''} for i in range(16)}
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'nk446420',
            'database': 'EOL'
        }
        
        # Initialize database connection and create table if not exists
        self.init_database()
        
        self.setup_ui()

    def setup_ui(self):
        # Create main container
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create top navigation frame
        self.create_navigation()
        
        # Create header with labels
        self.create_header()
        
        # Create main workspace
        self.create_workspace()

    def create_navigation(self):
        nav_frame = tk.Frame(self.main_container, bg="lightgray", height=40)
        nav_frame.pack(fill=tk.X)

        buttons = ["PORT SETTINGS", "LABEL MAKER", "MODEL SETTINGS", 
                  "TEST", "WORK DATA", "ADMIN", "HELP", "EXIT"]
        
        for btn_text in buttons:
            btn = tk.Button(nav_frame, text=btn_text, bg="white", 
                          relief=tk.FLAT, padx=10, pady=5)
            btn.pack(side=tk.LEFT, padx=2, pady=2)

    def create_header(self):
        # Header frame
        header_frame = tk.Frame(self.main_container, height=100)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Labels frame
        self.labels_frame = tk.Frame(header_frame)
        self.labels_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Create moveable labels
        self.create_moveable_labels()
        
        # Buttons frame
        self.buttons_frame = tk.Frame(header_frame)
        self.buttons_frame.pack(side=tk.RIGHT)
        
        # Create buttons
        self.create_buttons()

    def create_workspace(self):
        # Create workspace frame
        self.workspace_frame = tk.Frame(self.main_container)
        self.workspace_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create quadrants
        self.create_quadrants()

    def create_quadrants(self):
        self.quadrants = []
        
        # Create first quadrant (image quadrant)
        self.image_quadrant = tk.Frame(self.workspace_frame,
                                     relief="groove",
                                     borderwidth=1,
                                     bg='white',
                                     width=self.min_quadrant_size[0],
                                     height=self.min_quadrant_size[1])
        self.image_quadrant.grid(row=0, column=0, sticky="nsew")
        self.image_quadrant.grid_propagate(False)
        
        # Create second quadrant
        self.second_quadrant = tk.Frame(self.workspace_frame,
                                      relief="groove",
                                      borderwidth=1,
                                      bg='white',
                                      width=self.min_quadrant_size[0],
                                      height=self.min_quadrant_size[1])
        self.second_quadrant.grid(row=0, column=1, sticky="nsew")
        self.second_quadrant.grid_propagate(False)
        
        # Add both quadrants to the list
        self.quadrants.append(self.image_quadrant)
        self.quadrants.append(self.second_quadrant)
        
        # Create coordinate display label
        self.coord_label = tk.Label(self.image_quadrant, 
                                  text="Coordinates: ", 
                                  bg='white',
                                  font=('Arial', 10))
        self.coord_label.place(relx=0.02, rely=0.95)
        
        # Create bottom row container
        bottom_container = tk.Frame(self.workspace_frame)
        bottom_container.grid(row=1, column=0, columnspan=2, sticky="nsew")
        
        # Configure main grid weights
        self.workspace_frame.grid_rowconfigure(0, weight=1)
        self.workspace_frame.grid_rowconfigure(1, weight=1)
        self.workspace_frame.grid_columnconfigure(0, weight=1)
        self.workspace_frame.grid_columnconfigure(1, weight=1)
        
        # Create three sections in the bottom row with headers
        self.create_bottom_sections(bottom_container)
        
        # Add content to second quadrant
        self.create_second_quadrant_content()

    def create_bottom_sections(self, container):
        # Headers
        headers = ["SPECIFICATIONS", "LABEL DETAILS", "PARTS LIST"]
        sections = []
        
        for i, header in enumerate(headers):
            section_frame = tk.Frame(container, relief="groove", borderwidth=1)
            section_frame.grid(row=0, column=i, sticky="nsew", padx=1, pady=1)
            container.grid_columnconfigure(i, weight=1)
            
            # Header
            header_label = tk.Label(section_frame, 
                                  text=header,
                                  bg="navy",
                                  fg="white",
                                  font=("Arial", 12, "bold"))
            header_label.pack(fill=tk.X)
            
            # Content frame
            content_frame = tk.Frame(section_frame)
            content_frame.pack(fill=tk.BOTH, expand=True)
            
            if i == 0:
                self.create_specifications_section(content_frame)
            elif i == 1:
                self.create_label_details_section(content_frame)
            else:
                self.create_parts_list_section(content_frame)
                
            sections.append(section_frame)

    def create_specifications_section(self, frame):
        # Input fields frame
        input_frame = tk.Frame(frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create input fields
        entries = [
            ("Description", 0, 0, 2),  # spans 2 columns
            ("Device", 1, 0, 1),
            ("Unit", 1, 1, 1),
            ("Master Min", 0, 2, 1),
            ("Master Max", 0, 3, 1),
            ("Normal Min", 1, 2, 1),
            ("Normal Max", 1, 3, 1)
        ]
        
        self.spec_entries = {}
        for label_text, row, col, span in entries:
            label = tk.Label(input_frame, text=label_text, anchor='w')
            label.grid(row=row*2, column=col, columnspan=span, sticky='w', padx=5)
            
            entry = tk.Entry(input_frame)
            entry.grid(row=row*2+1, column=col, columnspan=span, sticky='ew', padx=5, pady=2)
            self.spec_entries[label_text] = entry

        # Buttons frame
        button_frame = tk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(button_frame, text="ADD", bg="green", fg="white", width=10,
                 command=lambda: self.on_add_button_click(self.spec_entries.values(), self.spec_tree)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="REMOVE", bg="red", fg="white", width=10,
                 command=lambda: self.on_remove_button_click(self.spec_tree)).pack(side=tk.LEFT, padx=5)

        # Specifications Treeview
        columns = ('description', 'device', 'unit', 'master_min', 'master_max', 'normal_min', 'normal_max')
        self.spec_tree = ttk.Treeview(frame, columns=columns, show='headings', height=10)
        
        # Define headings
        headings = {
            'description': 'DESCRIPTION',
            'device': 'DEVICE',
            'unit': 'UNIT',
            'master_min': 'MASTER\nMIN',
            'master_max': 'MASTER\nMAX',
            'normal_min': 'NORMAL\nMIN',
            'normal_max': 'NORMAL\nMAX'
        }
        
        for col, heading in headings.items():
            self.spec_tree.heading(col, text=heading)
            self.spec_tree.column(col, width=100, anchor='center')

        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.spec_tree.yview)
        self.spec_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.spec_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

    def create_label_details_section(self, frame):
        # Label Details Treeview
        columns = ('label', 'on_status', 'off_status')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings', height=10)
        
        # Define headings
        headings = {
            'label': 'LABEL',
            'on_status': 'ON STATUS',
            'off_status': 'OFF STATUS'
        }
        
        for col, heading in headings.items():
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=100, anchor='center')

        # Create initial entries for all labels (1-16)
        for i in range(1, 17):
            label_text = f'L{i}'
            self.tree.insert('', 'end', values=(label_text, '', ''))
        
        # Enable editing on double click
        self.tree.bind('<Double-1>', self.on_double_click)
        
        # Add tooltip to show editing instructions
        tooltip_text = "Double-click ON/OFF status to edit (only for placed labels)"
        tooltip = tk.Label(frame, text=tooltip_text, bg='lightyellow')
        tooltip.pack(pady=(0, 5))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

    def create_parts_list_section(self, frame):
        # Create Part List section
        part_list_frame = ttk.LabelFrame(frame, text="Part List")
        part_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create Treeview
        columns = ('part_number', 'model_name', 'created_date')
        self.part_list_tree = ttk.Treeview(part_list_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        self.part_list_tree.heading('part_number', text='Part Number')
        self.part_list_tree.heading('model_name', text='Model Name')
        self.part_list_tree.heading('created_date', text='Created Date')
        
        # Set column widths
        self.part_list_tree.column('part_number', width=100)
        self.part_list_tree.column('model_name', width=150)
        self.part_list_tree.column('created_date', width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(part_list_frame, orient=tk.VERTICAL, command=self.part_list_tree.yview)
        self.part_list_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.part_list_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load existing records
        self.update_part_list_view()

    def create_second_quadrant_content(self):
        second_quadrant = self.quadrants[1]
        
        # Header
        header_frame = tk.Frame(second_quadrant, bg='#00BFFF')  # Light blue background
        header_frame.pack(fill=tk.X)
        
        header_label = tk.Label(header_frame, 
                              text="PART DETAILS",
                              font=('Arial', 14, 'bold'),
                              bg='#00BFFF',
                              fg='navy')
        header_label.pack(pady=5)

        # Main content frame
        content_frame = tk.Frame(second_quadrant, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left side frame for input fields
        left_frame = tk.Frame(content_frame, bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Right side frame for buttons
        right_frame = tk.Frame(content_frame, bg='white')
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        # Input fields configuration with placeholders
        fields = [
            ("Vendor Code", "Enter vendor code", 0, 0),
            ("EO Number", "Enter EO number", 0, 1),
            ("Special Data", "Enter special data", 1, 0),
            ("Initial ID", "Enter initial ID", 1, 1),
            ("Part Number", "Enter part number", 2, 0, 2),  # spans 2 columns
            ("Model & Part Name", "Enter model & part name", 3, 0, 2),  # spans 2 columns
            ("Image File Path", "No image selected", 4, 0, 2),  # spans 2 columns
            ("ALC Code", "Enter ALC code", 5, 0),
            ("Supplier Section", "Enter supplier section", 5, 1)
        ]

        self.textboxes = {}
        
        # Create and arrange input fields
        for field in fields:
            label_text = field[0]
            placeholder = field[1]
            row = field[2]
            col = field[3]
            colspan = field[4] if len(field) > 4 else 1

            # Label
            label = tk.Label(left_frame, 
                           text=label_text,
                           bg='white',
                           anchor='w')
            label.grid(row=row*2, column=col, 
                      columnspan=colspan,
                      sticky='w', 
                      padx=5, 
                      pady=(5,0))

            # Entry with placeholder
            entry = tk.Entry(left_frame, bg='black',fg='gray',width=30 if colspan > 1 else 20)
            entry.insert(0, placeholder)
            entry.config(fg='gray')
            
            # Bind focus events for placeholder behavior
            entry.bind('<FocusIn>', lambda e, entry=entry, placeholder=placeholder: 
                      self.on_entry_focus_in(e, entry, placeholder))
            entry.bind('<FocusOut>', lambda e, entry=entry, placeholder=placeholder: 
                      self.on_entry_focus_out(e, entry, placeholder))

            entry.grid(row=row*2+1, column=col,
                      columnspan=colspan,
                      sticky='ew',
                      padx=5,
                      pady=(0,5))

            # Store reference to entry widget
            self.textboxes[label_text] = entry

            # Special handling for Image File Path
            if label_text == "Image File Path":
                entry.config(state='readonly')
                browse_btn = tk.Button(left_frame,fg="white",background="black" ,
                                     text="📂",
                                     command=self.upload_image)
                browse_btn.grid(row=row*2+1, column=col+colspan, padx=(0,5))

        # Configure grid
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_columnconfigure(1, weight=1)

        # Create buttons in right frame
        buttons = [
            ("NEW", "red", None),  # Add None for buttons without a command
            ("EDIT", "navy", None),
            ("SAVE", "green", self.save_specifications_to_db),  # Add command to SAVE button
            ("CLEAR", "gray", None),
            ("DELETE", "red", None)
        ]

        for text, color, command in buttons:
            btn = tk.Button(right_frame,
                           text=text,
                           bg="white",
                           fg='black',
                           width=10,
                           height=2,
                           command=command)  # Assign command to button
            btn.pack(pady=5)

    def on_entry_focus_in(self, event, entry, placeholder):
        """Handle entry field focus in - remove placeholder text"""
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg='black')

    def on_entry_focus_out(self, event, entry, placeholder):
        """Handle entry field focus out - restore placeholder if empty"""
        if entry.get() == '':
            entry.insert(0, placeholder)
            entry.config(fg='grey')

    def create_moveable_labels(self):
        # Create 16 moveable labels
        self.moveable_labels = []
        for i in range(16):
            label = tk.Label(self.labels_frame, 
                           text=f"L{i+1}", 
                           width=4, 
                           relief="raised",
                           bg="lightgray")
            label.pack(side=tk.LEFT, padx=2)
            label.bind("<Button-1>", self.start_move)
            label.bind("<B1-Motion>", self.on_motion)  # Bind motion event
            label.bind("<ButtonRelease-1>", self.stop_move)  # Bind release event
            self.original_positions[f"L{i+1}"] = label
            self.moveable_labels.append(label)

    def create_buttons(self):
        # Reset button
        self.reset_btn = tk.Button(self.buttons_frame, 
                                 text="RESET",
                                 bg="red",
                                 fg="black",
                                 width=10,
                                 height=2,
                                 command=self.reset_labels)
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Update button
        self.update_btn = tk.Button(self.buttons_frame,
                                  text="UPDATE",
                                  bg="green",
                                  fg="black",
                                  width=10,
                                  height=2,
                                  command=self.update_positions)
        self.update_btn.pack(side=tk.LEFT, padx=5)
        
        # Upload image button
        self.upload_btn = tk.Button(self.buttons_frame,
                                  text="Upload Image",
                                  width=10,
                                  height=2,
                                  command=self.upload_image)
        self.upload_btn.pack(side=tk.LEFT, padx=5)

    def start_move(self, event):
        if not self.image_uploaded:
            messagebox.showwarning("Warning", "Please upload an image first!")
            return
        
        widget = event.widget
        
        if widget.winfo_parent() == str(self.labels_frame):
            label_text = widget.cget("text")
            
            # Check if this label is already placed
            if label_text in self.placed_labels:
                return
            
            # Create new label in the image quadrant
            new_label = tk.Label(self.image_quadrant, 
                               text=label_text,
                               width=4,
                               relief="raised",
                               bg="lightblue")
            
            # Get the cursor position relative to the image quadrant
            x = event.x_root - self.image_quadrant.winfo_rootx() - (new_label.winfo_reqwidth() // 2)
            y = event.y_root - self.image_quadrant.winfo_rooty() - (new_label.winfo_reqheight() // 2)
            
            # Ensure the label stays within the quadrant boundaries
            x = max(0, min(x, self.image_quadrant.winfo_width() - new_label.winfo_reqwidth()))
            y = max(0, min(y, self.image_quadrant.winfo_height() - new_label.winfo_reqheight()))
            
            new_label.place(x=x, y=y)
            
            # Bind motion and release events to the new label
            new_label.bind("<Button-1>", self.start_move)
            new_label.bind("<B1-Motion>", self.on_motion)
            new_label.bind("<ButtonRelease-1>", self.stop_move)
            
            # Store initial coordinates
            self.original_positions[label_text] = (x, y)
            
            # Store the new label
            self.placed_labels[label_text] = new_label
            
            # Change original label color to indicate it's been placed
            widget.config(bg="lightgray")
            
            # Set current label and drag start position
            self.current_label = new_label
            self.drag_start_x = event.x
            self.drag_start_y = event.y
            
            self.update_coordinate_display(label_text, x, y)
            
            # Update only the status of the specific label
            self.update_label_status(label_text)
            
            # After placing the label, update the label details treeview
            self.label_tree.insert('', tk.END, values=(
                label_text,
                self.label_status[label_text[1:]]['status'],
                self.label_details[label_text[1:]]['details']
            ))
            
            # Update the label details treeview for the placed label
            for item in self.label_tree.get_children():
                if self.label_tree.item(item)['values'][0] == label_text:
                    self.label_tree.item(item, values=(label_text, 'OFF', 'ON'))
                    break
        else:
            self.current_label = widget
            self.drag_start_x = event.x
            self.drag_start_y = event.y

        # Update the treeview after placing the label
        self.update_treeview()

    def on_motion(self, event):
        if not self.current_label:
            return
        
        # Get the current cursor position relative to the image quadrant
        x = event.x_root - self.image_quadrant.winfo_rootx() - (self.current_label.winfo_reqwidth() // 2)
        y = event.y_root - self.image_quadrant.winfo_rooty() - (self.current_label.winfo_reqheight() // 2)
        
        # Ensure the label stays within the quadrant boundaries
        x = max(0, min(x, self.image_quadrant.winfo_width() - self.current_label.winfo_reqwidth()))
        y = max(0, min(y, self.image_quadrant.winfo_height() - self.current_label.winfo_reqheight()))
        
        # Update label position
        self.current_label.place(x=x, y=y)
        
        # Update coordinates in the display
        self.update_coordinate_display(self.current_label.cget("text"), x, y)

    def stop_move(self, event):
        if self.current_label:
            label_text = self.current_label.cget("text")
            x = self.current_label.winfo_x()
            y = self.current_label.winfo_y()
            self.update_coordinate_display(label_text, x, y)
        self.current_label = None
        self.drag_start_x = None
        self.drag_start_y = None

    def update_coordinate_display(self, label_text, x, y):
        """Update the coordinate display label with current position"""
        self.coord_label.config(text=f"Label {label_text}: ({x}, {y})")
        print(f"Label {label_text} position: ({x}, {y})")

    def on_double_click(self, event):
        item = self.tree.selection()[0]
        column = self.tree.identify_column(event.x)
        
        # Get label text from the selected item
        label_text = self.tree.item(item)['values'][0]
        
        # Handle OFF status name editing (column #3)
        if label_text in self.placed_labels and column == '#3':
            x, y, w, h = self.tree.bbox(item, column)
            
            # Create entry widget for name editing
            entry = tk.Entry(self.tree)
            entry.place(x=x, y=y, width=w, height=h)
            
            # Get current value
            current_values = self.tree.item(item)['values']
            current_name = current_values[2] if len(current_values) > 2 else ''
            entry.insert(0, current_name)
            
            def update_label_name(event=None):
                new_name = entry.get()
                
                # Update the label text and size on the image
                if label_text in self.placed_labels:
                    label_widget = self.placed_labels[label_text]
                    if new_name:
                        # Update label with just the new name
                        label_widget.config(text=new_name)
                        # Adjust label size
                        label_widget.config(width=len(new_name) + 2)
                        
                        # Update tree view with the new name
                        values = list(self.tree.item(item)['values'])
                        values[2] = new_name  # Update OFF status column
                        self.tree.item(item, values=tuple(values))
                    else:
                        # If no name entered, revert to original label number
                        label_widget.config(text=label_text)
                        label_widget.config(width=len(label_text) + 2)
                
                entry.destroy()
            
            entry.bind('<Return>', update_label_name)
            entry.bind('<FocusOut>', update_label_name)
            entry.focus()
        
        # Handle ON/OFF status editing (columns #2 and #3)
        elif label_text in self.placed_labels and column in ('#2', '#3'):
            x, y, w, h = self.tree.bbox(item, column)
            
            # Create combobox for status selection
            combo = ttk.Combobox(self.tree, values=['ON', 'OFF'], width=8)
            combo.place(x=x, y=y, width=w, height=h)
            
            # Get current value
            current_value = self.tree.item(item)['values'][int(column[1])-1]
            combo.set(current_value if current_value else 'OFF')
            
            def on_combo_select(event):
                selected_value = combo.get()
                values = list(self.tree.item(item)['values'])
                
                # Update the selected column
                col_idx = int(column[1])-1
                values[col_idx] = selected_value
                
                # Update opposite column
                other_col = 2 if col_idx == 1 else 1
                values[other_col] = 'OFF' if selected_value == 'ON' else 'ON'
                
                # Update the tree
                self.tree.item(item, values=tuple(values))
                combo.destroy()
            
            combo.bind('<<ComboboxSelected>>', on_combo_select)
            combo.bind('<FocusOut>', lambda e: combo.destroy())
            combo.focus()

    def edit_cell(self, item, column):
        current_value = self.label_tree.item(item, 'values')
        edit_window = tk.Toplevel(self.root)
        edit_window.title('Edit Status')
        
        x = self.root.winfo_x() + self.label_tree.winfo_x() + 50
        y = self.root.winfo_y() + self.label_tree.winfo_y() + 50
        edit_window.geometry(f'+{x}+{y}')
        
        entry = tk.Entry(edit_window)
        entry.insert(0, current_value[int(column[1])-1])
        entry.pack(padx=10, pady=5)
        
        def save_changes():
            new_value = entry.get()
            values = list(current_value)
            values[int(column[1])-1] = new_value
            self.label_tree.item(item, values=values)
            edit_window.destroy()
        
        save_btn = tk.Button(edit_window, text='Save', command=save_changes)
        save_btn.pack(pady=5)
        entry.focus_set()

    def on_add_button_click(self, entries, tree):
        def add_specification():
            data = tuple(entry.get() for entry in entries)
            self.insert_specification(data)
            tree.insert('', 'end', values=data)

        # Run the add_specification function in a separate thread
        threading.Thread(target=add_specification).start()

    def on_remove_button_click(self, tree):
        def remove_specification():
            selected_item = tree.selection()
            if selected_item:
                part_number = tree.item(selected_item, 'values')[0]
                self.remove_specification(part_number)
                tree.delete(selected_item)

        # Run the remove_specification function in a separate thread
        threading.Thread(target=remove_specification).start()

    def reset_labels(self):
        if messagebox.askyesno("Reset", "Are you sure you want to reset all labels?"):
            # Remove all placed labels
            for label in self.placed_labels.values():
                label.destroy()
            self.placed_labels.clear()
            
            # Reset original labels' appearance
            for label in self.original_positions.values():
                if isinstance(label, tk.Label):
                    label.config(bg="lightgray")
            
            # Reset all label statuses in treeview
            for item in self.tree.get_children():
                label_text = self.tree.item(item)['values'][0]
                self.tree.item(item, values=(label_text, '', ''))
            
            # Reset stored positions
            self.original_positions = {key: label for key, label in self.original_positions.items() 
                                    if isinstance(label, tk.Label)}
            
            # Reset coordinate display
            self.coord_label.config(text="Coordinates: ")
            print("All labels reset and positions cleared")

    def update_positions(self):
        positions = {}
        for label_text, label_widget in self.placed_labels.items():
            positions[label_text] = {
                'x': label_widget.winfo_x(),
                'y': label_widget.winfo_y()
            }
        print("Label positions updated:", positions)
        messagebox.showinfo("Success", "Label positions updated successfully!")

    def update_image_path(self, path):
        if "Image File Path" in self.textboxes:
            entry = self.textboxes["Image File Path"]
            entry.config(state='normal')
            entry.delete(0, tk.END)
            entry.insert(0, path)
            entry.config(state='readonly')

    def upload_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.ico")]
        )
        
        if file_path:
            try:
                first_quadrant = self.quadrants[0]
                
                # Create a frame to hold the image and labels
                if not hasattr(self, 'image_frame'):
                    self.image_frame = tk.Frame(first_quadrant, bg='white')
                    self.image_frame.place(relwidth=1, relheight=1)
                
                image = Image.open(file_path)
                
                quad_width = first_quadrant.winfo_width()
                quad_height = first_quadrant.winfo_height()
                
                width_ratio = quad_width / image.size[0]
                height_ratio = quad_height / image.size[1]
                scale_factor = min(width_ratio, height_ratio)
                
                new_width = int(image.size[0] * scale_factor)
                new_height = int(image.size[1] * scale_factor)
                
                resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(resized_image)
                
                if self.image_label:
                    self.image_label.destroy()
                
                self.image_label = tk.Label(self.image_frame, image=photo, bg='white')
                self.image_label.image = photo
                
                x_pos = (quad_width - new_width) // 2
                y_pos = (quad_height - new_height) // 2
                self.image_label.place(x=x_pos, y=y_pos)
                
                self.update_image_path(file_path)
                self.image_uploaded = True  # Set flag to True after image upload
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading image: {str(e)}")

    def update_coordinates(self):
        if not self.placed_labels:
            messagebox.showwarning("Warning", "No labels have been placed!")
            return
        
        # Update the original_positions dictionary with current positions
        for label_text, label_widget in self.placed_labels.items():
            x = label_widget.winfo_x()
            y = label_widget.winfo_y()
            self.original_positions[label_text] = (x, y)
            
            # Update the coordinates display
            self.update_coordinate_display(label_text, x, y)
        
        # Save to JSON file
        coordinates_data = {
            'image_path': self.current_image_path,
            'coordinates': self.original_positions
        }
        
        try:
            with open('coordinates.json', 'w') as f:
                json.dump(coordinates_data, f, indent=4)
            messagebox.showinfo("Success", "Coordinates saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save coordinates: {str(e)}")

    def reset_positions(self):
        # Remove all placed labels from the image quadrant
        for label in self.placed_labels.values():
            label.destroy()
        
        # Reset the placed_labels dictionary
        self.placed_labels.clear()
        
        # Reset the original_positions dictionary
        self.original_positions.clear()
        
        # Reset the colors of all labels in the labels_frame back to original
        for child in self.labels_frame.winfo_children():
            if isinstance(child, tk.Label):
                child.config(bg="lightblue")  # Reset to original color
        
        # Clear the coordinates display
        self.coordinates_text.delete(1.0, tk.END)
        
        # Clear the treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Reset label details
        for label_num in self.label_details:
            self.label_details[label_num]['details'] = ''
        
        messagebox.showinfo("Reset", "All labels have been reset!")

    def create_treeview(self):
        # Create Treeview frame
        self.tree_frame = ttk.Frame(self.parts_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

        # Create Treeview
        self.tree = ttk.Treeview(self.tree_frame, columns=('Label', 'Status', 'Details'), show='headings')
        self.tree.heading('Label', text='Label')  
        self.tree.heading('Status', text='Status')
        self.tree.heading('Details', text='Details')
        
        # Bind double-click event for editing
        self.tree.bind('<Double-1>', self.on_double_click)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Add Clear Details button
        self.clear_button = tk.Button(self.tree_frame, text="Clear Details", command=self.clear_label_details)
        self.clear_button.pack(side=tk.BOTTOM, pady=5)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def update_treeview(self):
        existing_labels = set()
        
        # Get existing labels from treeview
        for item in self.tree.get_children():
            label_text = self.tree.item(item)['values'][0]
            existing_labels.add(label_text)
        
        # Update or add entries
        for i in range(1, 17):
            label_text = f'L{i}'
            if label_text in self.placed_labels:
                on_status = 'OFF'
                off_status = 'ON'
            else:
                on_status = ''
                off_status = ''
            
            # If label exists, update it. If not, create new entry
            if label_text in existing_labels:
                # Find and update existing item
                for item in self.tree.get_children():
                    if self.tree.item(item)['values'][0] == label_text:
                        self.tree.item(item, values=(label_text, on_status, off_status))
                        break
            else:
                # Create new entry only if it doesn't exist
                self.tree.insert('', 'end', values=(label_text, on_status, off_status))

    def create_edit_popup(self, item, label_num):
        popup = tk.Toplevel(self)
        popup.title(f"Edit Label {label_num} Details")
        popup.geometry("300x150")
        
        # Add entry widget
        label = tk.Label(popup, text="Enter details:")
        label.pack(pady=5)
        
        entry = tk.Entry(popup, width=40)
        current_details = self.label_details[label_num]['details']
        entry.insert(0, current_details)
        entry.pack(pady=5)
        
        # Add status toggle
        status_var = tk.StringVar(value=self.label_status[label_num]['status'])
        status_frame = tk.Frame(popup)
        status_frame.pack(pady=5)
        
        tk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        on_radio = tk.Radiobutton(status_frame, text="ON", variable=status_var, value='on')
        off_radio = tk.Radiobutton(status_frame, text="OFF", variable=status_var, value='off')
        on_radio.pack(side=tk.LEFT, padx=5)
        off_radio.pack(side=tk.LEFT)
        
        def save_details():
            new_details = entry.get()
            new_status = status_var.get()
            
            # Update details and status
            self.label_details[label_num]['details'] = new_details
            self.label_status[label_num]['status'] = new_status
            
            # Update treeview
            current_values = list(self.tree.item(item)['values'])
            current_values[1] = "ON" if new_status == 'on' else "OFF"
            current_values[2] = new_details
            self.tree.item(item, values=current_values)
            
            # Update status display
            self.update_status_display()
            
            popup.destroy()
        
        # Add save button
        save_button = tk.Button(popup, text="Save", command=save_details)
        save_button.pack(pady=10)

    def clear_label_details(self):
        # Clear details for all labels
        for label_num in self.label_details:
            self.label_details[label_num]['details'] = ''
        
        # Update the treeview to reflect the changes
        self.update_treeview()
        
        messagebox.showinfo("Success", "All label details have been cleared!")

    def update_label_status(self, label_text):
        # Find the item for this label
        for item in self.tree.get_children():
            if self.tree.item(item)['values'][0] == label_text:
                current_values = self.tree.item(item)['values']
                # Preserve any existing OFF status name when updating status
                off_status_name = current_values[2] if len(current_values) > 2 else 'ON'
                self.tree.item(item, values=(label_text, 'OFF', off_status_name))
                
                # Update label on image with just the OFF status name if it exists
                if label_text in self.placed_labels:
                    if off_status_name and off_status_name != 'ON':
                        self.placed_labels[label_text].config(text=off_status_name)
                    else:
                        self.placed_labels[label_text].config(text=label_text)
                break

    def init_database(self):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS part_list (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    part_number VARCHAR(50),
                    model_name VARCHAR(100),
                    created_date DATETIME,
                    label_data JSON
                )
            ''')
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to initialize database: {err}")

    def save_to_database(self):
        try:
            # Get model name and part number
            model_name = self.model_name_var.get().strip()
            part_number = self.part_number_var.get().strip()
            
            # Validate inputs
            if not model_name or not part_number:
                messagebox.showwarning("Warning", "Please enter both Model Name and Part Number!")
                return
            
            # Collect label data
            label_data = {}
            for item in self.tree.get_children():
                values = self.tree.item(item)['values']
                label_num = values[0]
                if label_num in self.placed_labels:
                    label_widget = self.placed_labels[label_num]
                    label_data[label_num] = {
                        'name': label_widget.cget('text'),  # Get current label text
                        'position': {
                            'x': label_widget.winfo_x(),
                            'y': label_widget.winfo_y()
                        },
                        'on_status': values[1],
                        'off_status': values[2]
                    }
            
            # Connect to database
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="label_db"
            )
            cursor = conn.cursor()
            
            # Insert data
            query = """
                INSERT INTO part_list 
                (part_number, model_name, created_date, label_data) 
                VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                part_number,
                model_name,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                json.dumps(label_data)
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Clear input fields
            self.model_name_var.set('')
            self.part_number_var.set('')
            
            # Update the part list view
            self.update_part_list_view()
            
            messagebox.showinfo("Success", "Data saved successfully!")
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to save data: {err}")

    def update_part_list_view(self):
        try:
            # Clear existing items
            for item in self.part_list_tree.get_children():
                self.part_list_tree.delete(item)
            
            # Connect to database
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="nk446420",
                database="label_db"
            )
            cursor = conn.cursor()
            
            # Fetch all records
            cursor.execute("""
                SELECT id, part_number, model_name, created_date 
                FROM part_list 
                ORDER BY created_date DESC
            """)
            
            # Insert records into treeview
            for row in cursor.fetchall():
                formatted_date = row[3].strftime('%Y-%m-%d %H:%M:%S')
                self.part_list_tree.insert('', 'end', values=(row[1], row[2], formatted_date))
            
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to fetch records: {err}")

    def create_part_list_section(self, frame):
        # Create Part List section
        part_list_frame = ttk.LabelFrame(frame, text="Part List")
        part_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create Treeview
        columns = ('part_number', 'model_name', 'created_date')
        self.part_list_tree = ttk.Treeview(part_list_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        self.part_list_tree.heading('part_number', text='Part Number')
        self.part_list_tree.heading('model_name', text='Model Name')
        self.part_list_tree.heading('created_date', text='Created Date')
        
        # Set column widths
        self.part_list_tree.column('part_number', width=100)
        self.part_list_tree.column('model_name', width=150)
        self.part_list_tree.column('created_date', width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(part_list_frame, orient=tk.VERTICAL, command=self.part_list_tree.yview)
        self.part_list_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.part_list_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load existing records
        self.update_part_list_view()

    def insert_specification(self, data):
        try:
            # Debugging: Print the data being inserted
            print("Inserting data:", data)
            
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="nk446420",
                database="EOL"
            )
            cursor = conn.cursor()
            
            # Ensure the number of placeholders matches the number of data elements
            query = """
            INSERT INTO TBL_MODEL_SPECIFICATION 
            (MS_DESCRIPTION, MS_DEVICE, MS_UNIT, MS_MASTER_MIN, MS_MASTER_MAX, MS_NORMAL_MIN, MS_NORMAL_MAX)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, data)
            conn.commit()
            cursor.close()
            conn.close()
            print("Data inserted successfully!")
            
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            messagebox.showerror("Database Error", f"Failed to insert data: {err}")
        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def remove_specification(self, part_number):
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="nk446420",
                database="EOL"
            )
            cursor = conn.cursor()
            query = "DELETE FROM TBL_MODEL_SPECIFICATION WHERE MS_PART_NUMBER = %s"
            cursor.execute(query, (part_number,))
            conn.commit()
            cursor.close()
            conn.close()
            print("Specification data removed successfully!")
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    def save_specifications_to_db(self):
        """Save specifications data to the database."""
        try:
            # Collect data from spec_entries
            data = tuple(entry.get() for entry in self.spec_entries.values())
            
            # Debugging: Print the collected data
            print("Collected data for saving:", data)
            
            # Insert data into the database
            self.insert_specification(data)
            
            messagebox.showinfo("Success", "Specifications saved successfully!")
        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"Failed to save specifications: {str(e)}")

def main():
    root = tk.Tk()
    app = WorkspaceApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()        
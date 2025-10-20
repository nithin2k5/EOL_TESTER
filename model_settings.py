import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import json
import mysql.connector
from datetime import datetime
from mysql.connector import Error
import threading
import os

class WorkspaceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EOL Tester - Model Settings")
        
        # Set window state to zoomed instead of fullscreen
        self.root.state('zoomed')  # Change from fullscreen to maximized
        
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
        
        # Track edit mode for CRUD operations
        self.edit_mode = False
        self.current_selected_part = None
        
        # Database configuration
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '12345',
            'database': 'EOL'
        }
        
        # Initialize database connection and create table if not exists
        self.init_database()
        
        self.setup_ui()

    def setup_ui(self):
        # Create main container
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create header with labels
        self.create_header()
        
        # Create main workspace
        self.create_workspace()

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
        
        # First quadrant (Image Display)
        first_quadrant = tk.Frame(self.workspace_frame, bg='white')
        first_quadrant.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        first_quadrant.grid_propagate(False)
        first_quadrant.config(width=800, height=600)  # This sets the overall quadrant size

        # Image frame within first quadrant - MATCH test_console.py EXACTLY
        self.image_frame = tk.Frame(first_quadrant, bg='white')
        self.image_frame.pack(fill="both", expand=True, padx=2, pady=2)  # Match test_console.py
        self.image_frame.pack_propagate(False)  # Match test_console.py
        self.image_frame.config(width=750, height=450)  # Match test_console.py image dimensions
        
        # Create coordinate display label - positioned in first_quadrant, not image_frame
        self.coord_label = tk.Label(first_quadrant, 
                                  text="Coordinates: ", 
                                  bg='white',
                                  font=('Arial', 10))
        self.coord_label.place(relx=0.02, rely=0.95)
        
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
        self.quadrants.append(first_quadrant)
        self.quadrants.append(self.second_quadrant)
        
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
        
        # Updated button styling
        add_btn = tk.Button(
            button_frame, 
            text="ADD",
            bg="#2ecc71",
            fg="white",
            width=10,
            relief=tk.RAISED,
            activebackground="#27ae60",
            activeforeground="white",
            highlightbackground="#2ecc71",
            command=lambda: self.on_add_button_click(self.spec_entries.values(), self.spec_tree)
        )
        add_btn.pack(side=tk.LEFT, padx=5)

        remove_btn = tk.Button(
            button_frame, 
            text="REMOVE",
            bg="#ff4d4d",
            fg="white",
            width=10,
            relief=tk.RAISED,
            activebackground="#ff3333",
            activeforeground="white",
            highlightbackground="#ff4d4d",
            command=lambda: self.on_remove_button_click(self.spec_tree)
        )
        remove_btn.pack(side=tk.LEFT, padx=5)

        # Specifications Treeview
        columns = ('description', 'device', 'unit', 'master_min', 'master_max', 'normal_min', 'normal_max')
        self.spec_tree = ttk.Treeview(frame, columns=columns, show='headings', height=10)
        

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

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.spec_tree.yview)
        self.spec_tree.configure(yscrollcommand=scrollbar.set)
        

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
        part_list_frame = ttk.LabelFrame(frame)
        part_list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=0)
        
        # Create Treeview
        columns = ('part_number', 'model_name', 'created_date')
        self.part_list_tree = ttk.Treeview(part_list_frame, columns=columns, show='headings',height=10)
        
        # Configure columns
        self.part_list_tree.heading('part_number', text='Part Number')
        self.part_list_tree.heading('model_name', text='Model Name')
        self.part_list_tree.heading('created_date', text='Created Date')
        
        # Set column widths
        self.part_list_tree.column('part_number', width=70)
        self.part_list_tree.column('model_name', width=100)
        self.part_list_tree.column('created_date', width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(part_list_frame, orient=tk.VERTICAL, command=self.part_list_tree.yview)
        self.part_list_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.part_list_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load existing records
        self.update_part_list_view()

        # Add binding for tree item selection
        self.part_list_tree.bind('<<TreeviewSelect>>', self.on_tree_select)

    def create_second_quadrant_content(self):
        second_quadrant = self.quadrants[1]
        
        # Create main container with padding
        main_container = tk.Frame(second_quadrant, bg='white')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Load combobox options from files
        plc_options = self.load_plc_options()
        barcode_options = self.load_barcode_options()
        
        # Create header label "PART DETAILS"
        header_label = tk.Label(main_container, 
                              text="PART DETAILS",
                              font=('Arial', 12, 'bold'),
                              bg='deepskyblue',
                              fg='navy',
                              anchor='w',
                              padx=10,
                              pady=5)
        header_label.pack(fill=tk.X, pady=(0, 5))
        
        # Create left frame for input fields
        left_frame = tk.Frame(main_container, bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Create right frame for buttons
        button_frame = tk.Frame(main_container, bg='white')
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Create textboxes for each field
        fields = [
            ("Vendor Code", "Enter vendor code", 0, 0),
            ("EO Number", "Enter EO number", 0, 1),
            ("Special Data", "Enter special data", 1, 0),
            ("Initial ID", "Enter initial ID", 1, 1),
            ("Part Number", "Enter part number", 2, 0, 2),
            ("Supplier Section", "Enter supplier details", 3, 0, 2),
            ("Model & Part Name", "Enter model & part name", 4, 0, 2),
            ("Image File Path", "No image selected", 5, 0, 2),
            ("ALC Code", "Enter ALC code", 6, 0),
            ("PLC Address", plc_options, 7, 0),  # Using loaded PLC options
            ("Barcode Type", barcode_options, 7, 1),  # Using loaded barcode options
        ]
        
        self.textboxes = {}
        self.second_quad_combos = {}  # Dictionary to store comboboxes
        
        # Create textboxes and comboboxes for each field
        for field in fields:
            label_text, placeholder, row, col = field[:4]
            colspan = field[4] if len(field) > 4 else 1
            
            if isinstance(placeholder, list):  # If placeholder is a list, create combobox
                combo = ttk.Combobox(left_frame, width=20, values=placeholder)
                combo.set(f"Select {label_text}")
                combo.grid(row=row, column=col, columnspan=colspan, sticky='ew', padx=5, pady=5)
                self.second_quad_combos[label_text] = combo
                
                # Bind selection events for specific comboboxes
                if label_text == "PLC Address":
                    combo.bind('<<ComboboxSelected>>', self.on_plc_address_select)
                elif label_text == "Barcode Type":
                    combo.bind('<<ComboboxSelected>>', self.on_barcode_type_select)
            else:  # Create regular entry
                entry = tk.Entry(left_frame, width=20)
                entry.insert(0, placeholder)
                entry.config(fg='gray')
                entry.grid(row=row, column=col, columnspan=colspan, sticky='ew', padx=5, pady=5)
                
                # Bind focus events for entries
                entry.bind('<FocusIn>', lambda e, entry=entry, ph=placeholder: self.on_entry_focus_in(e, entry, ph))
                entry.bind('<FocusOut>', lambda e, entry=entry, ph=placeholder: self.on_entry_focus_out(e, entry, ph))
                
                # Make Image File Path read-only
                if label_text == "Image File Path":
                    entry.config(state='readonly')
                
                self.textboxes[label_text] = entry

        # Configure grid weights
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_columnconfigure(1, weight=1)
        
        # Create buttons with vibrant colors
        buttons = [
            ("NEW", "#3498db", "#2980b9", "white"),     # Bright Blue
            ("EDIT", "#9b59b6", "#8e44ad", "white"),    # Vibrant Purple
            ("SAVE", "#2ecc71", "#27ae60", "white"),    # Bright Green
            ("CLEAR", "#95a5a6", "#7f8c8d", "white"),   # Light Gray
            ("DELETE", "#e74c3c", "#c0392b", "white")   # Bright Red
        ]
        
        for text, bg_color, active_bg, fg_color in buttons:
            btn = tk.Button(
                button_frame,
                text=text,
                bg=bg_color,
                fg=fg_color,
                width=10,
                height=2,
                relief=tk.RAISED,
                activebackground=active_bg,
                activeforeground=fg_color,
                highlightbackground=bg_color,
                font=('Arial', 10, 'bold')  # Make text bold
            )
            btn.pack(pady=5)
            
            # Update the button commands
            if text == "SAVE":
                btn.config(command=self.save_specifications_to_db)
            elif text == "CLEAR":
                btn.config(command=self.clear_all_data)
            elif text == "DELETE":
                btn.config(command=self.delete_record)
            elif text == "NEW":
                btn.config(command=self.reset_form)
            elif text == "EDIT":
                btn.config(command=self.edit_record)

    def on_entry_focus_in(self, event, entry, placeholder):
        """Handle entry field focus in - remove placeholder text"""
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg='black')  # Set text color to black when typing

    def on_entry_focus_out(self, event, entry, placeholder):
        """Handle entry field focus out - restore placeholder if empty"""
        if entry.get() == '':
            entry.insert(0, placeholder)
            entry.config(fg='gray')  # Set placeholder text color to gray
        else:
            entry.config(fg='black')  # Keep actual text black

    def on_text_focus_in(self, event, text_widget, placeholder):
        """Handle text widget focus in - remove placeholder text"""
        if text_widget.get("1.0", "end-1c") == placeholder:
            text_widget.delete("1.0", tk.END)
            text_widget.config(fg='white')

    def on_text_focus_out(self, event, text_widget, placeholder):
        """Handle text widget focus out - restore placeholder if empty"""
        if text_widget.get("1.0", "end-1c").strip() == '':
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", placeholder)
            text_widget.config(fg='white')

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
        # Modern button styles with gradients and hover effects - only for image operations
        button_styles = [
            {
                'text': "RESET IMAGE LABELS",  # Clarified purpose
                'main_color': "#ff4757",      
                'hover_color': "#ff6b81",      
                'width': 15,
                'icon': "��",                 
                'command': self.reset_labels   # Only resets the image labels
            },
            {
                'text': "SAVE LABEL POSITIONS",  # Clarified purpose
                'main_color': "#2ed573",      
                'hover_color': "#7bed9f",      
                'width': 15,
                'icon': "💾",                 
                'command': lambda: self.update_positions()  # Only saves label positions
            },
            {
                'text': "UPLOAD NEW IMAGE",    # Clarified purpose
                'main_color': "#1e90ff",      
                'hover_color': "#70a1ff",      
                'width': 15,
                'icon': "📁",                 
                'command': self.upload_image   # Only handles image upload
            }
        ]

        # Create a frame for image-related buttons with a label
        image_buttons_frame = tk.Frame(self.buttons_frame)
        image_buttons_frame.pack(side=tk.LEFT, padx=10)

        
        # Create buttons container
        buttons_container = tk.Frame(image_buttons_frame)
        buttons_container.pack()

        for style in button_styles:
            # Create button frame for gradient effect
            btn_frame = tk.Frame(buttons_container, padx=2, pady=2)
            btn_frame.pack(side=tk.LEFT, padx=5, pady=2)

            # Create the actual button
            btn = tk.Button(btn_frame,
                          text=f"{style['icon']} {style['text']}",
                          width=style['width'],
                          bg=style['main_color'],
                          fg="white",
                          font=('Arial', 9, 'bold'),
                          relief="flat",
                          bd=0,
                          padx=10,
                          pady=5,
                          cursor="hand2",
                          command=style['command'])
            btn.pack()

            # Add tooltip
            self.create_tooltip(btn, f"Click to {style['text'].lower()}")

            # Bind hover effects
            btn.bind('<Enter>', lambda e, b=btn, c=style['hover_color']: 
                    self.on_button_hover(b, c))
            btn.bind('<Leave>', lambda e, b=btn, c=style['main_color']: 
                    self.on_button_hover(b, c))

    def create_tooltip(self, widget, text):
        """Create a tooltip for a given widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")

            label = tk.Label(tooltip, text=text, bg="lightyellow", 
                            padx=5, pady=2, relief="solid", borderwidth=1)
            label.pack()

            def hide_tooltip():
                tooltip.destroy()

            widget.tooltip = tooltip
            widget.bind('<Leave>', lambda e: hide_tooltip())

        widget.bind('<Enter>', show_tooltip)

    def on_button_hover(self, button, color):
        """Handle button hover effect"""
        button.configure(bg=color)

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
            
            # Create new label in the image quadrant - MATCH test_console.py style
            new_label = tk.Label(self.image_frame, 
                               text=label_text,
                               bg="yellow",  # Match test_console.py
                               fg="black",
                               font=("Arial", 12, "bold"),  # Match test_console.py
                               width=4,
                               relief="raised",
                               borderwidth=2)  # Match test_console.py
            
            # Get the cursor position relative to the image quadrant
            x = event.x_root - self.image_frame.winfo_rootx() - (new_label.winfo_reqwidth() // 2)
            y = event.y_root - self.image_frame.winfo_rooty() - (new_label.winfo_reqheight() // 2)
            
            # Ensure the label stays within the quadrant boundaries
            x = max(0, min(x, self.image_frame.winfo_width() - new_label.winfo_reqwidth()))
            y = max(0, min(y, self.image_frame.winfo_height() - new_label.winfo_reqheight()))
            
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
            
            # Update the treeview after placing the label
            self.update_treeview()
        else:
            self.current_label = widget
            self.drag_start_x = event.x
            self.drag_start_y = event.y

    def on_motion(self, event):
        if not self.current_label:
            return
        
        # Get the current cursor position relative to the image quadrant
        x = event.x_root - self.image_frame.winfo_rootx() - (self.current_label.winfo_reqwidth() // 2)
        y = event.y_root - self.image_frame.winfo_rooty() - (self.current_label.winfo_reqheight() // 2)
        
        # Ensure the label stays within the quadrant boundaries
        x = max(0, min(x, self.image_frame.winfo_width() - self.current_label.winfo_reqwidth()))
        y = max(0, min(y, self.image_frame.winfo_height() - self.current_label.winfo_reqheight()))
        
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
        """Add specification to the tree (not database yet - saved when SAVE is clicked)"""
        # Get entries in the correct order to match database columns
        spec_field_order = ['Description', 'Device', 'Unit', 'Master Min', 'Master Max', 'Normal Min', 'Normal Max']
        data = tuple(self.spec_entries[field].get().upper() for field in spec_field_order)
        
        # Check if all fields have values
        if not all(data):
            messagebox.showwarning("Input Error", "Please fill in all specification fields!")
            return
        
        # Add to tree view only (will be saved to database when SAVE is clicked)
        tree.insert('', 'end', values=data)
        
        # Clear all specification entries after adding to tree
        for entry in self.spec_entries.values():
            entry.delete(0, tk.END)
        
        print(f"Added specification to tree: {data}")

    def on_remove_button_click(self, tree):
        """Remove specification from tree (database will be updated when SAVE is clicked)"""
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a specification to remove!")
            return
        
        # Remove from tree view only (database will be updated when SAVE is clicked)
        tree.delete(selected_item)
        print("Removed specification from tree")

    def reset_labels(self):
        """Reset all labels to their original positions."""
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

    def update_positions(self):
        """Update and save label positions to database"""
        positions = {}
        for label_text, label_widget in self.placed_labels.items():
            positions[label_text] = {
                'x': label_widget.winfo_x(),
                'y': label_widget.winfo_y(),
                'text': label_widget.cget('text')  # Store the label text as well
            }
        
        try:
            # Convert positions to JSON string
            positions_json = json.dumps(positions)
            
            # Get current part number
            part_number = self.textboxes["Part Number"].get()
            
            # Update database
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = """
            UPDATE TBL_MODEL_MASTER 
            SET MM_LABEL_COORDINATES = %s,
                MM_MODIFIED_BY = %s,
                MM_MODIFIED_DATE = %s
            WHERE MM_PART_NUMBER = %s
            """
            
            cursor.execute(query, (positions_json, 'User', datetime.now(), part_number))
            conn.commit()
            cursor.close()
            conn.close()
            
            print("Label positions updated:", positions)
            messagebox.showinfo("Success", "Label positions updated successfully!")
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            messagebox.showerror("Database Error", f"Failed to update label positions: {err}")

    def update_image_path(self, path):
        if "Image File Path" in self.textboxes:
            entry = self.textboxes["Image File Path"]
            entry.config(state='normal')
            entry.delete(0, tk.END)
            entry.insert(0, path)
            entry.config(state='readonly')

    def upload_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Part Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.ico")]
        )
        
        if file_path:
            try:
                # Load the image
                image = Image.open(file_path)
                
                # Use exact same dimensions as test_console.py: 750x450
                target_width = 750
                target_height = 450
                
                # Resize image to exactly match test_console.py dimensions
                resized_image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(resized_image)
                
                # Remove old image label if it exists
                if hasattr(self, 'image_label') and self.image_label:
                    self.image_label.destroy()
                
                # Create new image label - MATCH test_console.py EXACTLY
                self.image_label = tk.Label(self.image_frame, image=photo, bg='white')
                self.image_label.image = photo  # Keep a reference
                self.image_label.place(x=0, y=0, relwidth=1, relheight=1)  # Match test_console.py line 3661
                
                # Store image dimensions to match test_console.py exactly
                self.image_dimensions = {
                    'width': target_width,
                    'height': target_height,
                    'x_offset': 0,
                    'y_offset': 0
                }
                
                # Update the image path and set flag
                self.update_image_path(file_path)
                self.image_uploaded = True
                
                # Provide feedback
                print(f"Image uploaded successfully: {file_path}")
                messagebox.showinfo(
                    "Image Uploaded", 
                    f"✓ Image uploaded successfully!\n\n" +
                    f"File: {os.path.basename(file_path)}\n" +
                    f"Size: {target_width}x{target_height} pixels\n\n" +
                    "You can now place labels on the image."
                )
                
            except Exception as e:
                messagebox.showerror("Image Upload Error", f"Failed to load image: {str(e)}")

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
            cursor = conn.cursor(buffered=True)  # Use buffered cursor to prevent "Unread result" errors
            
            # Create TBL_MODEL_MASTER table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS TBL_MODEL_MASTER (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    MM_PART_NUMBER VARCHAR(255) UNIQUE,
                    MM_MODEL_NAME VARCHAR(255),
                    MM_ALC_CODE VARCHAR(255),
                    MM_PLC_ADDRESS VARCHAR(255),
                    MM_BARCODE_LABEL_CODE VARCHAR(255),
                    MM_IMAGE_PATH VARCHAR(255),
                    MM_VENDOR_CODE VARCHAR(255),
                    MM_EO_NUMBER VARCHAR(255),
                    MM_SPECIAL_DATA VARCHAR(255),
                    MM_INITIAL_ID VARCHAR(255),
                    MM_SUPPLIER_SECTION VARCHAR(255),
                    MM_CREATED_BY VARCHAR(255),
                    MM_CREATED_DATE DATETIME,
                    MM_STATUS TINYINT(1),
                    MM_MODIFIED_BY VARCHAR(255),
                    MM_MODIFIED_DATE DATETIME,
                    MM_LABEL_POSITIONS JSON,
                    MM_LABEL_COORDINATES JSON
                )
            ''')
            
            # Create TBL_MODEL_SPECIFICATION table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS TBL_MODEL_SPECIFICATION (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    MS_PART_NUMBER VARCHAR(255),
                    MS_DESCRIPTION VARCHAR(255),
                    MS_DEVICE VARCHAR(255),
                    MS_UNIT VARCHAR(255),
                    MS_MASTER_MIN VARCHAR(255),
                    MS_MASTER_MAX VARCHAR(255),
                    MS_NORMAL_MIN VARCHAR(255),
                    MS_NORMAL_MAX VARCHAR(255),
                    FOREIGN KEY (MS_PART_NUMBER) REFERENCES TBL_MODEL_MASTER(MM_PART_NUMBER) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            print(f"Database initialization error: {err}")
            messagebox.showerror("Database Error", f"Failed to initialize database: {err}")

    def save_to_database(self):
        try:
            # Get values from textboxes
            part_number = self.textboxes["Part Number"].get().strip()
            model_name = self.textboxes["Model & Part Name"].get().strip()
            
            # Validate inputs
            if not model_name or not part_number:
                messagebox.showwarning("Warning", "Please enter both Model Name and Part Number!")
                return
            
            # The rest of the data will be saved through save_specifications_to_db method
            # which already handles saving to TBL_MODEL_MASTER
            self.save_specifications_to_db()
            
            # Update the part list view
            self.update_part_list_view()
            
        except Exception as err:
            messagebox.showerror("Error", f"Failed to save data: {err}")

    def update_part_list_view(self):
        try:
            # Clear existing items
            for item in self.part_list_tree.get_children():
                self.part_list_tree.delete(item)
            
            # Connect to database using existing config
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Fetch all records from TBL_MODEL_MASTER
            cursor.execute("""
                SELECT MM_PART_NUMBER, MM_MODEL_NAME, MM_CREATED_DATE 
                FROM TBL_MODEL_MASTER 
                ORDER BY MM_CREATED_DATE DESC
            """)
            
            # Insert records into treeview
            for row in cursor.fetchall():
                formatted_date = row[2].strftime('%Y-%m-%d %H:%M:%S') if row[2] else ''
                self.part_list_tree.insert('', 'end', values=(row[0], row[1], formatted_date))
            
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to fetch records: {err}")

    def insert_specification(self, data):
        try:
            # Debugging: Print the data being inserted
            print("Inserting data:", data)
            
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="12345",
                database="EOL"
            )
            cursor = conn.cursor()
            
            # Add part number to the data tuple
            part_number = self.textboxes["Part Number"].get()
            data_with_part_number = (part_number,) + data
            
 
            query = """
            INSERT INTO TBL_MODEL_SPECIFICATION 
            (MS_PART_NUMBER, MS_DESCRIPTION, MS_DEVICE, MS_UNIT, MS_MASTER_MIN, MS_MASTER_MAX, MS_NORMAL_MIN, MS_NORMAL_MAX)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, data_with_part_number)
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
                password="12345",
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
        try:
            # Only validate required part list fields
            required_fields = [
                "Part Number",
                "Model & Part Name",
                "ALC Code",
                "Vendor Code",
                "EO Number",
                "Special Data",
                "Initial ID",
                "Supplier Section"
            ]
            
            # Check if required fields are filled
            empty_fields = [field for field in required_fields 
                           if not self.textboxes[field].get() or 
                           self.textboxes[field].get() == f"Enter {field.lower()}"]
            
            if empty_fields:
                messagebox.showwarning(
                    "Input Error", 
                    f"Please fill in the following required fields:\n{', '.join(empty_fields)}"
                )
                return
            
            # Enhanced image validation - check both for new uploads and existing paths
            image_path = self.textboxes["Image File Path"].get()
            
            # Check if image path is empty or placeholder
            if not image_path or image_path == "No image selected":
                messagebox.showwarning(
                    "Image Required", 
                    "Please upload an image before saving the part!\n\n" +
                    "Click 'UPLOAD NEW IMAGE' button to attach an image."
                )
                return
            
            # Check if the image file actually exists
            if not os.path.exists(image_path):
                messagebox.showerror(
                    "Image Not Found", 
                    f"The image file does not exist:\n{image_path}\n\n" +
                    "Please upload a valid image before saving."
                )
                return
            
            # Collect other data
            part_number = self.textboxes["Part Number"].get()
            model_name = self.textboxes["Model & Part Name"].get()
            alc_code = self.textboxes["ALC Code"].get()
            
            # Enhanced duplicate check and edit mode validation
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT MM_PART_NUMBER FROM TBL_MODEL_MASTER WHERE MM_PART_NUMBER = %s", (part_number,))
            existing = cursor.fetchone()
            cursor.close()
            conn.close()
            
            # Logic to prevent duplication and ensure proper update flow
            if not self.edit_mode:
                # CREATE mode - check for duplicates
                if existing:
                    messagebox.showerror(
                        "Duplicate Part Number",
                        f"Part Number '{part_number}' already exists in the database!\n\n" +
                        "To update this part:\n" +
                        "1. Select it from the Parts List\n" +
                        "2. Click the EDIT button\n" +
                        "3. Make your changes\n" +
                        "4. Click SAVE to update\n\n" +
                        "Please use a different Part Number for new entries."
                    )
                    return
            else:
                # EDIT mode - ensure we're updating the correct record
                if self.current_selected_part != part_number:
                    messagebox.showerror(
                        "Update Error",
                        f"Part Number cannot be changed during edit!\n\n" +
                        "Original Part Number: {self.current_selected_part}\n" +
                        "Current Part Number: {part_number}\n\n" +
                        "The Part Number is locked during editing to maintain data integrity."
                    )
                    return
                
                # Verify the record exists before updating
                if not existing:
                    messagebox.showerror(
                        "Update Error",
                        f"Cannot update - Part Number '{part_number}' not found in database!\n\n" +
                        "The record may have been deleted. Please refresh and try again."
                    )
                    return
            
            # Collect data from second quadrant with safe defaults
            plc_address = self.second_quad_combos.get("PLC Address", ttk.Combobox()).get()
            barcode_type = self.second_quad_combos.get("Barcode Type", ttk.Combobox()).get()
            
            # Get supplier section from textboxes
            supplier_section = self.textboxes.get("Supplier Section", tk.Entry()).get()
            if supplier_section == "Enter supplier details":
                supplier_section = ""
            
            # Collect other data
            vendor_code = self.textboxes["Vendor Code"].get()
            eo_number = self.textboxes["EO Number"].get()
            special_data = self.textboxes["Special Data"].get()
            initial_id = self.textboxes["Initial ID"].get()
            image_path = self.textboxes["Image File Path"].get()
            
            master_data = (
                part_number, model_name, alc_code, plc_address, barcode_type, 
                image_path, vendor_code, eo_number, special_data, 
                initial_id, supplier_section, 'User', datetime.now(), True, 'User', datetime.now()
            )
            
            # Save specifications from the spec_tree (not from entry fields)
            specifications_to_save = []
            for item in self.spec_tree.get_children():
                spec_values = self.spec_tree.item(item)['values']
                if spec_values and len(spec_values) >= 7:
                    specifications_to_save.append(spec_values)
            
            print(f"=== SAVE OPERATION ===")
            print(f"Edit Mode: {self.edit_mode}")
            print(f"Part Number: {part_number}")
            print(f"Current Selected Part: {self.current_selected_part}")
            print(f"Specifications count: {len(specifications_to_save)}")
            
            # Insert or Update based on edit mode
            if self.edit_mode:
                # UPDATE existing record
                print(f"UPDATING existing record: {part_number}")
                self.update_model_master(master_data, specifications_to_save)
                messagebox.showinfo(
                    "Update Successful", 
                    f"✓ Part '{part_number}' has been updated successfully!\n\n" +
                    f"Model: {model_name}\n" +
                    f"Specifications: {len(specifications_to_save)} items\n" +
                    f"Image: Validated\n\n" +
                    "The form has been cleared and is ready for new entries."
                )
            else:
                # INSERT new record
                print(f"INSERTING new record: {part_number}")
                self.insert_model_master(master_data, specifications_to_save)
                messagebox.showinfo(
                    "Creation Successful", 
                    f"✓ New part '{part_number}' has been created successfully!\n\n" +
                    f"Model: {model_name}\n" +
                    f"Specifications: {len(specifications_to_save)} items\n" +
                    f"Image: Attached\n\n" +
                    "The form has been cleared and is ready for new entries."
                )
            
            # Clear everything after successful save
            self.clear_all_data()
            
            # Reset edit mode
            self.edit_mode = False
            self.current_selected_part = None
            
            # Update part list view
            self.update_part_list_view()
            
        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"Failed to save data: {str(e)}")

    def insert_model_master(self, data, specifications=None):
        """Insert new model master record with specifications"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            part_number = data[0]
            
            # Format label positions and coordinates as separate JSON objects
            label_positions = {}
            label_coordinates = {}
            
            for label_text, label_widget in self.placed_labels.items():
                label_num = label_text.lstrip('L')
                
                # Label positions JSON
                label_positions[label_num] = {
                    'position': 'placed',
                    'status': 'active'
                }
                
                # Label coordinates JSON
                label_coordinates[label_num] = {
                    'x': float(label_widget.winfo_x()),
                    'y': float(label_widget.winfo_y()),
                    'text': str(label_widget.cget('text'))
                }
            
            positions_json = json.dumps(label_positions, ensure_ascii=False)
            coordinates_json = json.dumps(label_coordinates, ensure_ascii=False)
            
            query = """
            INSERT INTO TBL_MODEL_MASTER (
                MM_PART_NUMBER, MM_MODEL_NAME, MM_ALC_CODE, MM_PLC_ADDRESS, 
                MM_BARCODE_LABEL_CODE, MM_IMAGE_PATH, MM_VENDOR_CODE, MM_EO_NUMBER,
                MM_SPECIAL_DATA, MM_INITIAL_ID, MM_SUPPLIER_SECTION, MM_CREATED_BY,
                MM_CREATED_DATE, MM_STATUS, MM_MODIFIED_BY, MM_MODIFIED_DATE,
                MM_LABEL_POSITIONS, MM_LABEL_COORDINATES
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            final_data = (
                data[0],  # MM_PART_NUMBER
                data[1],  # MM_MODEL_NAME
                data[2],  # MM_ALC_CODE
                data[3],  # MM_PLC_ADDRESS
                data[4],  # MM_BARCODE_LABEL_CODE
                data[5],  # MM_IMAGE_PATH
                data[6],  # MM_VENDOR_CODE
                data[7],  # MM_EO_NUMBER
                data[8],  # MM_SPECIAL_DATA
                data[9],  # MM_INITIAL_ID
                data[10], # MM_SUPPLIER_SECTION
                'User',   # MM_CREATED_BY
                datetime.now(), # MM_CREATED_DATE
                1,       # MM_STATUS (TINYINT)
                'User',  # MM_MODIFIED_BY
                datetime.now(), # MM_MODIFIED_DATE
                positions_json,    # MM_LABEL_POSITIONS
                coordinates_json   # MM_LABEL_COORDINATES
            )
            
            cursor.execute(query, final_data)
            
            # Insert specifications if provided
            if specifications:
                spec_query = """
                INSERT INTO TBL_MODEL_SPECIFICATION 
                (MS_PART_NUMBER, MS_DESCRIPTION, MS_DEVICE, MS_UNIT, 
                 MS_MASTER_MIN, MS_MASTER_MAX, MS_NORMAL_MIN, MS_NORMAL_MAX)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                for spec in specifications:
                    cursor.execute(spec_query, (part_number,) + tuple(spec))
            
            conn.commit()
            cursor.close()
            conn.close()
            print("Model master data inserted successfully!")
            
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            messagebox.showerror("Database Error", f"Failed to insert model master data: {err}")

    def update_model_master(self, data, specifications=None):
        """Update existing model master record with specifications"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            part_number = data[0]
            
            # Format label positions and coordinates as separate JSON objects
            label_positions = {}
            label_coordinates = {}
            
            for label_text, label_widget in self.placed_labels.items():
                label_num = label_text.lstrip('L')
                
                # Label positions JSON
                label_positions[label_num] = {
                    'position': 'placed',
                    'status': 'active'
                }
                
                # Label coordinates JSON
                label_coordinates[label_num] = {
                    'x': float(label_widget.winfo_x()),
                    'y': float(label_widget.winfo_y()),
                    'text': str(label_widget.cget('text'))
                }
            
            positions_json = json.dumps(label_positions, ensure_ascii=False)
            coordinates_json = json.dumps(label_coordinates, ensure_ascii=False)
            
            # Update query for existing record
            query = """
            UPDATE TBL_MODEL_MASTER SET
                MM_MODEL_NAME = %s,
                MM_ALC_CODE = %s,
                MM_PLC_ADDRESS = %s,
                MM_BARCODE_LABEL_CODE = %s,
                MM_IMAGE_PATH = %s,
                MM_VENDOR_CODE = %s,
                MM_EO_NUMBER = %s,
                MM_SPECIAL_DATA = %s,
                MM_INITIAL_ID = %s,
                MM_SUPPLIER_SECTION = %s,
                MM_MODIFIED_BY = %s,
                MM_MODIFIED_DATE = %s,
                MM_LABEL_POSITIONS = %s,
                MM_LABEL_COORDINATES = %s
            WHERE MM_PART_NUMBER = %s
            """
            
            update_data = (
                data[1],  # MM_MODEL_NAME
                data[2],  # MM_ALC_CODE
                data[3],  # MM_PLC_ADDRESS
                data[4],  # MM_BARCODE_LABEL_CODE
                data[5],  # MM_IMAGE_PATH
                data[6],  # MM_VENDOR_CODE
                data[7],  # MM_EO_NUMBER
                data[8],  # MM_SPECIAL_DATA
                data[9],  # MM_INITIAL_ID
                data[10], # MM_SUPPLIER_SECTION
                'User',   # MM_MODIFIED_BY
                datetime.now(), # MM_MODIFIED_DATE
                positions_json,    # MM_LABEL_POSITIONS
                coordinates_json,   # MM_LABEL_COORDINATES
                data[0]   # MM_PART_NUMBER (WHERE clause)
            )
            
            cursor.execute(query, update_data)
            print(f"Updated master record for part number: {part_number}")
            
            # Delete old specifications and insert new ones
            cursor.execute("DELETE FROM TBL_MODEL_SPECIFICATION WHERE MS_PART_NUMBER = %s", (part_number,))
            print(f"Deleted old specifications for part number: {part_number}")
            
            # Insert new specifications if provided
            if specifications:
                spec_query = """
                INSERT INTO TBL_MODEL_SPECIFICATION 
                (MS_PART_NUMBER, MS_DESCRIPTION, MS_DEVICE, MS_UNIT, 
                 MS_MASTER_MIN, MS_MASTER_MAX, MS_NORMAL_MIN, MS_NORMAL_MAX)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                for spec in specifications:
                    cursor.execute(spec_query, (part_number,) + tuple(spec))
                print(f"Inserted {len(specifications)} new specifications")
            
            conn.commit()
            cursor.close()
            conn.close()
            print("Model master data updated successfully!")
            
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            messagebox.showerror("Database Error", f"Failed to update model master data: {err}")

    def check_part_exists(self, part_number):
        """Check if a part number already exists in the database"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT MM_PART_NUMBER FROM TBL_MODEL_MASTER WHERE MM_PART_NUMBER = %s", (part_number,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result is not None
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            return False

    def delete_specifications(self, part_number):
        """Delete all specifications for a given part number"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM TBL_MODEL_SPECIFICATION WHERE MS_PART_NUMBER = %s", (part_number,))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"Specifications deleted for part: {part_number}")
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            messagebox.showerror("Database Error", f"Failed to delete specifications: {err}")

    def clear_all_data(self):
        """Clear all data fields, image, and restore labels."""
        # Reset edit mode
        self.edit_mode = False
        self.current_selected_part = None
        
        # Clear specification entries and enable them
        for entry in self.spec_entries.values():
            entry.config(state='normal')
            entry.delete(0, 'end')
        
        # Clear second quadrant comboboxes and enable them
        for combo in self.second_quad_combos.values():
            combo.config(state='normal')
            combo.set('')
        
        # Clear textboxes and restore to editable state
        for key, entry in self.textboxes.items():
            entry.config(state='normal', bg='white')
            entry.delete(0, 'end')
            
            # Set appropriate placeholder based on field
            if key == "Part Number":
                entry.insert(0, "Enter part number")
            elif key == "Model & Part Name":
                entry.insert(0, "Enter model & part name")
            elif key == "Image File Path":
                entry.insert(0, "No image selected")
                entry.config(state='readonly')
            else:
                entry.insert(0, f"Enter {key.lower()}")
            
            entry.config(fg='gray')
        
        # Clear image
        if self.image_label:
            self.image_label.destroy()
            self.image_label = None
        self.image_uploaded = False
        
        # Reset labels
        self.reset_labels()
        
        # Clear specifications tree
        for item in self.spec_tree.get_children():
            self.spec_tree.delete(item)
        
        # Clear tree selection
        self.part_list_tree.selection_remove(self.part_list_tree.selection())
        
        # Update the part list view
        self.update_part_list_view()
        
        print("Form cleared - Ready for new entry")

    def load_label_positions(self, part_number):
        """Load and place labels on the image"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            query = """
            SELECT MM_LABEL_COORDINATES 
            FROM TBL_MODEL_MASTER 
            WHERE MM_PART_NUMBER = %s
            """
            
            cursor.execute(query, (part_number,))
            result = cursor.fetchone()
            
            if result and result[0]:
                try:
                    coordinates = json.loads(result[0])
                    print(f"Loading {len(coordinates)} label positions for part: {part_number}")
                except json.JSONDecodeError as je:
                    print(f"JSON decode error for label coordinates: {je}")
                    messagebox.showwarning("Warning", "Invalid label coordinates data")
                    cursor.close()
                    conn.close()
                    return
                
                # Clear existing labels
                self.reset_labels()
                
                # Place labels using coordinates - MATCH test_console.py style
                labels_placed = 0
                for label_num, coord_data in coordinates.items():
                    try:
                        label_text = f'L{label_num}'
                        display_text = coord_data.get('text', label_text)
                        
                        new_label = tk.Label(
                            self.image_frame,
                            text=display_text,
                            bg="yellow",  # Match test_console.py
                            fg="black",
                            font=("Arial", 12, "bold"),  # Match test_console.py
                            width=4,  # Fixed width like test_console.py
                            relief="raised",
                            borderwidth=2  # Match test_console.py
                        )
                        
                        # Place label at exact coordinates
                        x = float(coord_data.get('x', 0))
                        y = float(coord_data.get('y', 0))
                        new_label.place(x=x, y=y)
                        new_label.bind("<Button-1>", self.start_move)
                        new_label.bind("<B1-Motion>", self.on_motion)
                        new_label.bind("<ButtonRelease-1>", self.stop_move)
                        
                        self.placed_labels[label_text] = new_label
                        labels_placed += 1
                        
                        # Update original label appearance
                        if label_text in self.original_positions and isinstance(self.original_positions[label_text], tk.Label):
                            self.original_positions[label_text].config(bg="lightgray")
                    
                    except Exception as label_error:
                        print(f"Error placing label L{label_num}: {label_error}")
                        continue
                
                # Update the treeview to reflect label positions
                self.update_treeview()
                print(f"Successfully placed {labels_placed} labels")
            else:
                print(f"No label coordinates found for part: {part_number}")
            
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            print(f"Database Error in load_label_positions: {err}")
            messagebox.showerror("Database Error", f"Failed to load label positions: {err}")
        except Exception as e:
            print(f"Error in load_label_positions: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")

    def on_combo_focus_in(self, event, combo, placeholder):
        """Handle combobox focus in - remove placeholder text"""
        if combo.get() == placeholder:
            combo.set('')
            combo.config(style='Custom.TCombobox')

    def on_combo_focus_out(self, event, combo, placeholder):
        """Handle combobox focus out - restore placeholder if empty"""
        if combo.get() == '':
            combo.set(placeholder)
            combo.config(style='Custom.TCombobox')

    def on_text_focus_in(self, event, text_widget, placeholder):
        """Handle text widget focus in - remove placeholder text"""
        if text_widget.get("1.0", "end-1c") == placeholder:
            text_widget.delete("1.0", tk.END)
            text_widget.config(fg='black')

    def on_text_focus_out(self, event, text_widget, placeholder):
        """Handle text widget focus out - restore placeholder if empty"""
        if text_widget.get("1.0", "end-1c").strip() == '':
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", placeholder)
            text_widget.config(fg='gray')

    def on_plc_address_select(self, event):
        """Handle PLC Address combobox selection"""
        # No popup needed, options are already loaded in combobox
        pass

    def on_barcode_type_select(self, event):
        """Handle Barcode Type combobox selection"""
        # No popup needed, options are already loaded in combobox
        pass

    def load_plc_options(self):
        """Load PLC address options from txt_files/ProgramSelectionInPLC.txt"""
        try:
            # Use file in txt_files directory
            file_path = "txt_files/ProgramSelectionInPLC.txt"
            with open(file_path, 'r') as file:
                content = file.read().strip()
                options = [opt.strip() for opt in content.split(',') if opt.strip()]
                print(f"Loaded PLC options: {options}")
                return options
        except FileNotFoundError:
            print(f"Warning: ProgramSelectionInPLC.txt not found at {file_path}")
            return []
        except Exception as e:
            print(f"Error reading PLC options: {str(e)}")
            return []

    def load_barcode_options(self):
        """Load barcode options from txt_files/barcodeprintfilenames.txt"""
        try:
            # Use file in txt_files directory
            file_path = "txt_files/barcodeprintfilenames.txt"
            with open(file_path, 'r') as file:
                content = file.read().strip()
                options = [opt.strip() for opt in content.split(',') if opt.strip()]
                print(f"Loaded barcode options: {options}")
                return options
        except FileNotFoundError:
            print(f"Warning: barcodeprintfilenames.txt not found at {file_path}")
            return []
        except Exception as e:
            print(f"Error reading barcode options: {str(e)}")
            return []

    def on_tree_select(self, event):
        """Handle tree item selection - Load in VIEW mode (readonly)"""
        selected_items = self.part_list_tree.selection()
        if not selected_items:
            return
        
        # Get the selected item
        item = selected_items[0]
        part_number = self.part_list_tree.item(item)['values'][0]
        
        # Store the currently selected part number (but don't enter edit mode)
        self.current_selected_part = part_number
        self.edit_mode = False  # Explicitly set to view mode
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)  # Use dictionary cursor for easier access
            
            # Fetch record from database with explicit column names
            query = """
            SELECT 
                MM_PART_NUMBER, MM_MODEL_NAME, MM_ALC_CODE, MM_PLC_ADDRESS,
                MM_BARCODE_LABEL_CODE, MM_IMAGE_PATH, MM_VENDOR_CODE, MM_EO_NUMBER,
                MM_SPECIAL_DATA, MM_INITIAL_ID, MM_SUPPLIER_SECTION,
                MM_LABEL_POSITIONS, MM_LABEL_COORDINATES
            FROM TBL_MODEL_MASTER 
            WHERE MM_PART_NUMBER = %s
            """
            cursor.execute(query, (part_number,))
            
            record = cursor.fetchone()
            
            if record:
                print(f"Loading record for part number: {part_number}")
                
                # Clear form fields manually without resetting selection
                for entry in self.spec_entries.values():
                    entry.delete(0, tk.END)
                
                for combo in self.second_quad_combos.values():
                    combo.set('')
                
                # Clear and reset labels
                self.reset_labels()
                
                # Clear specifications tree
                for item in self.spec_tree.get_children():
                    self.spec_tree.delete(item)
                
                # Populate textboxes with data using dictionary keys
                field_mappings = {
                    "Part Number": record.get('MM_PART_NUMBER', ''),
                    "Model & Part Name": record.get('MM_MODEL_NAME', ''),
                    "ALC Code": record.get('MM_ALC_CODE', ''),
                    "Vendor Code": record.get('MM_VENDOR_CODE', ''),
                    "EO Number": record.get('MM_EO_NUMBER', ''),
                    "Special Data": record.get('MM_SPECIAL_DATA', ''),
                    "Initial ID": record.get('MM_INITIAL_ID', ''),
                    "Supplier Section": record.get('MM_SUPPLIER_SECTION', '')
                }
                
                # Make readonly in view mode with visual indication
                for key, value in field_mappings.items():
                    self.textboxes[key].config(state='normal')
                    self.textboxes[key].delete(0, tk.END)
                    if value:  # Only update if value exists
                        self.textboxes[key].insert(0, value)
                        self.textboxes[key].config(fg='black')
                    else:
                        self.textboxes[key].insert(0, f"Enter {key.lower()}")
                        self.textboxes[key].config(fg='gray')
                    # Make readonly in view mode with light gray background
                    self.textboxes[key].config(state='readonly', bg='#f5f5f5')
                
                # Set combobox values and make readonly
                plc_addr = record.get('MM_PLC_ADDRESS', '')
                if "PLC Address" in self.second_quad_combos:
                    if plc_addr:
                        self.second_quad_combos["PLC Address"].set(plc_addr)
                    else:
                        self.second_quad_combos["PLC Address"].set("Select PLC Address")
                    self.second_quad_combos["PLC Address"].config(state='disabled')
                
                barcode = record.get('MM_BARCODE_LABEL_CODE', '')
                if "Barcode Type" in self.second_quad_combos:
                    if barcode:
                        self.second_quad_combos["Barcode Type"].set(barcode)
                    else:
                        self.second_quad_combos["Barcode Type"].set("Select Barcode Type")
                    self.second_quad_combos["Barcode Type"].config(state='disabled')
                
                # Update image path
                image_path = record.get('MM_IMAGE_PATH', '')
                if image_path:
                    self.textboxes["Image File Path"].config(state='normal')
                    self.textboxes["Image File Path"].delete(0, tk.END)
                    self.textboxes["Image File Path"].insert(0, image_path)
                    self.textboxes["Image File Path"].config(state='readonly')
                    
                    # Load the image first
                    self.load_image(image_path)
                    
                    # Then load label positions after image is loaded
                    label_coords = record.get('MM_LABEL_COORDINATES', None)
                    if label_coords:
                        self.root.after(100, lambda: self.load_label_positions(part_number))
                
                # Load specifications
                self.load_specifications(part_number)
                
                # Make specification entries readonly in view mode
                for entry in self.spec_entries.values():
                    entry.config(state='readonly')
                
                # Restore selection state
                self.current_selected_part = part_number
                
                print(f"Successfully loaded part: {part_number} in VIEW MODE")
                
                # Show view mode notification
                model_name = record.get('MM_MODEL_NAME', '')
                has_image = "✓ Yes" if image_path and os.path.exists(image_path) else "✗ No"
                messagebox.showinfo(
                    "Part Loaded - View Mode",
                    f"📋 Part loaded in VIEW mode\n\n" +
                    f"Part Number: {part_number}\n" +
                    f"Model: {model_name}\n" +
                    f"Image Available: {has_image}\n\n" +
                    "• All fields are READ-ONLY\n" +
                    "• Click EDIT to modify this part\n" +
                    "• Click NEW for a fresh entry\n" +
                    "• Click DELETE to remove this part"
                )
            else:
                messagebox.showwarning("Not Found", f"Record not found for part number: {part_number}")
            
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            print(f"Database Error in on_tree_select: {err}")
            messagebox.showerror("Database Error", f"Failed to load record: {err}")
        except Exception as e:
            print(f"Error in on_tree_select: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")

    def load_image(self, image_path):
        """Load image from path with exact same dimensions as test_console.py"""
        try:
            if os.path.exists(image_path):
                # Load and resize the image using exact same dimensions as test_console.py
                image = Image.open(image_path)
                target_width = 750
                target_height = 450
                resized_image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(resized_image)
                
                # Remove old image label if it exists
                if hasattr(self, 'image_label') and self.image_label:
                    self.image_label.destroy()
                
                # Create new image label - MATCH test_console.py EXACTLY
                self.image_label = tk.Label(self.image_frame, image=photo, bg='white')
                self.image_label.image = photo  # Keep a reference
                self.image_label.place(x=0, y=0, relwidth=1, relheight=1)  # Match test_console.py line 3661
                
                # Store image dimensions to match test_console.py exactly
                self.image_dimensions = {
                    'width': target_width,
                    'height': target_height,
                    'x_offset': 0,
                    'y_offset': 0
                }
                
                # Update image path and flag
                self.update_image_path(image_path)
                self.image_uploaded = True
                
            else:
                messagebox.showwarning("Warning", f"Image file not found: {image_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def load_specifications(self, part_number):
        """Load specifications for the selected part"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)  # Use dictionary cursor
            
            # Query with explicit column names
            query = """
            SELECT 
                MS_DESCRIPTION, MS_DEVICE, MS_UNIT, 
                MS_MASTER_MIN, MS_MASTER_MAX, MS_NORMAL_MIN, MS_NORMAL_MAX
            FROM TBL_MODEL_SPECIFICATION 
            WHERE MS_PART_NUMBER = %s
            ORDER BY MS_DEVICE
            """
            cursor.execute(query, (part_number,))
            specs = cursor.fetchall()
            
            print(f"Loading {len(specs)} specifications for part: {part_number}")
            
            # Clear existing specs from tree
            for item in self.spec_tree.get_children():
                self.spec_tree.delete(item)
            
            # Insert specifications into tree
            if specs:
                for spec in specs:
                    spec_values = (
                        spec.get('MS_DESCRIPTION', ''),
                        spec.get('MS_DEVICE', ''),
                        spec.get('MS_UNIT', ''),
                        spec.get('MS_MASTER_MIN', ''),
                        spec.get('MS_MASTER_MAX', ''),
                        spec.get('MS_NORMAL_MIN', ''),
                        spec.get('MS_NORMAL_MAX', '')
                    )
                    self.spec_tree.insert('', 'end', values=spec_values)
                
                print(f"Loaded {len(specs)} specifications into tree")
            else:
                print(f"No specifications found for part: {part_number}")
            
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            print(f"Database Error in load_specifications: {err}")
            messagebox.showerror("Database Error", f"Failed to load specifications: {err}")
        except Exception as e:
            print(f"Error in load_specifications: {e}")
            messagebox.showerror("Error", f"An error occurred: {e}")

    def reset_form(self):
        """Reset all form fields to their default state and enable for NEW entry"""
        # Reset edit mode flag - entering CREATE mode
        self.edit_mode = False
        self.current_selected_part = None
        
        # Clear all textboxes and restore default placeholders - ENABLE for new entry
        for key, entry in self.textboxes.items():
            entry.config(state='normal')  # Enable all fields
            entry.delete(0, 'end')
            
            # Set appropriate placeholder based on field
            if key == "Part Number":
                entry.insert(0, "Enter part number")
            elif key == "Model & Part Name":
                entry.insert(0, "Enter model name")
            elif key == "Image File Path":
                entry.insert(0, "No image selected")
                entry.config(state='readonly')
            else:
                entry.insert(0, f"Enter {key.lower()}")
            
            entry.config(fg='gray')
        
        # Enable and clear comboboxes
        for combo in self.second_quad_combos.values():
            combo.config(state='normal')  # Enable comboboxes
            combo.set('')
        
        # Enable and clear specification entries
        for entry in self.spec_entries.values():
            entry.config(state='normal')  # Enable specification fields
            entry.delete(0, tk.END)
        
        # Clear specification tree
        for item in self.spec_tree.get_children():
            self.spec_tree.delete(item)
        
        # Clear the image
        if hasattr(self, 'image_label') and self.image_label:
            self.image_label.destroy()
            self.image_label = None
        self.image_uploaded = False
        
        # Reset labels
        self.reset_labels()
        
        # Clear tree selection
        self.part_list_tree.selection_remove(self.part_list_tree.selection())
        
        print("Form reset - Ready for NEW entry (CREATE mode)")

    def delete_record(self):
        """Delete the selected record and clear all textboxes"""
        if not hasattr(self, 'current_selected_part') or not self.current_selected_part:
            messagebox.showwarning("Warning", "Please select a record to delete!")
            return
        
        # Get the part details from textboxes for confirmation
        part_number = self.current_selected_part
        model_name = self.textboxes["Model & Part Name"].get()
        
        # Show confirmation dialog with record details
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete:\nPart Number: {part_number}\nModel Name: {model_name}?"
        )
        
        if not confirm:
            return
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Delete from TBL_MODEL_SPECIFICATION
            cursor.execute("DELETE FROM TBL_MODEL_SPECIFICATION WHERE MS_PART_NUMBER = %s", (part_number,))
            
            # Delete from TBL_MODEL_MASTER
            cursor.execute("DELETE FROM TBL_MODEL_MASTER WHERE MM_PART_NUMBER = %s", (part_number,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            messagebox.showinfo("Success", "Record deleted successfully!")
            
            # Reset all form fields
            self.reset_form()
            
            # Update the part list view
            self.update_part_list_view()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to delete record: {err}")

    def on_reset_button_click(self):
        """Handle reset button click"""
        self.reset_form()

    def edit_record(self):
        """Enable editing of the selected record"""
        if not hasattr(self, 'current_selected_part') or not self.current_selected_part:
            messagebox.showwarning(
                "No Record Selected", 
                "Please select a record from the Parts List to edit!\n\n" +
                "1. Click on a part in the Parts List\n" +
                "2. Click the EDIT button\n" +
                "3. Make your changes\n" +
                "4. Click SAVE to update"
            )
            return
        
        # Verify the image exists before allowing edit
        image_path = self.textboxes["Image File Path"].get()
        if not image_path or image_path == "No image selected":
            response = messagebox.askyesno(
                "Missing Image", 
                f"Part '{self.current_selected_part}' does not have an image attached.\n\n" +
                "Do you want to continue editing?\n\n" +
                "Note: You must upload an image before you can save changes."
            )
            if not response:
                return
        
        # Set edit mode flag
        self.edit_mode = True
        print(f"Edit mode enabled for part number: {self.current_selected_part}")
        
        # Enable all textboxes for editing (except Part Number and Image File Path)
        for key, entry in self.textboxes.items():
            if key == "Part Number":
                # Part Number cannot be changed (it's the primary key)
                entry.config(state='readonly', bg='#ffe6e6')  # Light red to indicate locked
                print(f"Part Number field locked: {entry.get()}")
            elif key != "Image File Path":  # Keep Image File Path readonly
                entry.config(state='normal', bg='white')
                if entry.get() in ["Enter " + key.lower(), "No image selected"]:
                    entry.delete(0, tk.END)
                entry.config(fg='black')
        
        # Enable comboboxes
        for combo in self.second_quad_combos.values():
            combo.config(state='normal')
        
        # Enable specification entries
        for entry in self.spec_entries.values():
            entry.config(state='normal')
        
        # Get current part info for display
        part_number = self.current_selected_part
        model_name = self.textboxes["Model & Part Name"].get()
        
        messagebox.showinfo(
            "Edit Mode Enabled", 
            f"✎ Edit Mode Active\n\n" +
            f"Part Number: {part_number} (locked)\n" +
            f"Model: {model_name}\n\n" +
            "• You can now modify all fields except Part Number\n" +
            "• Upload a new image if needed (optional)\n" +
            "• An image MUST be present before saving\n" +
            "• Click SAVE to update this part\n" +
            "• Click CLEAR to cancel and start fresh"
        )

def main():
    root = tk.Tk()
    app = WorkspaceApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()        
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

        # Image frame within first quadrant
        self.image_frame = tk.Frame(first_quadrant, bg='white')
        self.image_frame.place(relx=0.5, rely=0.5, anchor='center')
        self.image_frame.config(width=750, height=550)  # These are the actual image frame dimensions
        
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
        
        # Create coordinate display label
        self.coord_label = tk.Label(first_quadrant, 
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
            
            # Create new label in the image quadrant
            new_label = tk.Label(self.image_frame, 
                               text=label_text,
                               width=4,
                               relief="raised",
                               bg="lightblue")
            
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
        def add_specification():
            # Convert all entry values to uppercase
            data = tuple(entry.get().upper() for entry in entries)
            self.insert_specification(data)
            tree.insert('', 'end', values=data)
            
            # Reset all specification entries after successful insertion
            for entry in entries:
                entry.delete(0, tk.END)

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
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.ico")]
        )
        
        if file_path:
            try:
                # Get the first quadrant
                first_quadrant = self.quadrants[0]
                
                # Create a frame to hold the image
                if not hasattr(self, 'image_frame'):
                    self.image_frame = tk.Frame(first_quadrant, bg='white')
                    self.image_frame.place(relwidth=1, relheight=1)  # Use place with relative dimensions
                
                # Load the image
                image = Image.open(file_path)
                
                # Get the exact quadrant dimensions
                quad_width = first_quadrant.winfo_width()
                quad_height = first_quadrant.winfo_height()
                
                # Resize image to exactly match quadrant dimensions
                resized_image = image.resize((quad_width, quad_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(resized_image)
                
                # Remove old image label if it exists
                if hasattr(self, 'image_label') and self.image_label:
                    self.image_label.destroy()
                
                # Create new image label that fills the entire frame
                self.image_label = tk.Label(self.image_frame, image=photo, bg='white')
                self.image_label.image = photo  # Keep a reference
                self.image_label.place(x=0, y=0, relwidth=1, relheight=1)  # Fill entire frame
                
                # Store image dimensions
                self.image_dimensions = {
                    'width': quad_width,
                    'height': quad_height,
                    'x_offset': 0,
                    'y_offset': 0
                }
                
                # Update the image path and set flag
                self.update_image_path(file_path)
                self.image_uploaded = True
                
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
            
            # Create table with exact column structure
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS TBL_MODEL_MASTER (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    MM_PART_NUMBER VARCHAR(255),
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
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
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
                password="nk446420",
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
        try:
            # Validate that all required fields are filled
            if not all(entry.get() for entry in self.spec_entries.values()) or \
               not all(self.textboxes[key].get() for key in self.textboxes):
                messagebox.showwarning("Input Error", "Please fill in all the fields before saving.")
                return
            
            # Collect data from spec_entries
            spec_data = tuple(entry.get() for entry in self.spec_entries.values())
            
            # Collect data from second quadrant with safe defaults
            plc_address = self.second_quad_combos.get("PLC Address", ttk.Combobox()).get()
            barcode_type = self.second_quad_combos.get("Barcode Type", ttk.Combobox()).get()
            
            # Get supplier section from textboxes instead of text widget
            supplier_section = self.textboxes.get("Supplier Section", tk.Entry()).get()
            if supplier_section == "Enter supplier details":
                supplier_section = ""
            
            # Collect other data
            part_number = self.textboxes["Part Number"].get()
            model_name = self.textboxes["Model & Part Name"].get()
            alc_code = self.textboxes["ALC Code"].get()
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
            
            # Insert data into the database
            self.insert_model_master(master_data)
            self.insert_specification(spec_data)
            
            # Clear everything after successful save
            self.clear_all_data()
            
            messagebox.showinfo("Success", "Specifications and part list details saved successfully!")
            
        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"Failed to save specifications: {str(e)}")

    def insert_model_master(self, data):
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
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
            conn.commit()
            cursor.close()
            conn.close()
            print("Model master data inserted successfully!")
            
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            messagebox.showerror("Database Error", f"Failed to insert model master data: {err}")

    def clear_all_data(self):
        """Clear all data fields, image, and restore labels."""
        # Clear specification entries
        for entry in self.spec_entries.values():
            entry.delete(0, 'end')
        
        # Clear second quadrant comboboxes
        for combo in self.second_quad_combos.values():
            combo.set('')
        
        # Clear textboxes
        for key, entry in self.textboxes.items():
            entry.config(state='normal')
            entry.delete(0, 'end')
            placeholder = "Enter " + key.lower()
            if key == "Image File Path":
                placeholder = "No image selected"
            entry.insert(0, placeholder)
            entry.config(fg='gray')
            if key == "Image File Path":
                entry.config(state='readonly')
        
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
        
        # Update the part list view
        self.update_part_list_view()

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
                coordinates = json.loads(result[0])
                
                # Clear existing labels
                self.reset_labels()
                
                # Place labels using coordinates
                for label_num, coord_data in coordinates.items():
                    label_text = f'L{label_num}'
                    display_text = coord_data['text'] if coord_data['text'] else label_text
                    
                    new_label = tk.Label(
                        self.image_frame,
                        text=display_text,
                        width=len(display_text) + 2,
                        relief="raised",
                        bg="lightblue"
                    )
                    
                    new_label.place(x=coord_data['x'], y=coord_data['y'])
                    new_label.bind("<Button-1>", self.start_move)
                    new_label.bind("<B1-Motion>", self.on_motion)
                    new_label.bind("<ButtonRelease-1>", self.stop_move)
                    
                    self.placed_labels[label_text] = new_label
                    
                    # Update original label appearance
                    if label_text in self.original_positions and isinstance(self.original_positions[label_text], tk.Label):
                        self.original_positions[label_text].config(bg="lightgray")
                
                # Update the treeview to reflect label positions
                self.update_treeview()
            
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            messagebox.showerror("Database Error", f"Failed to load label positions: {err}")

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
        try:
            # Read PLC register data from file
            with open('/Users/nithink/Developer/python/EOL_TESTER/plc_register.txt', 'r') as file:
                plc_data = file.read()
            
            # Create popup window to display data
            popup = tk.Toplevel(self.root)
            popup.title("PLC Register Data")
            popup.geometry("400x300")
            
            # Add text widget to display data
            text_widget = tk.Text(popup, wrap=tk.WORD)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Insert the data
            text_widget.insert('1.0', plc_data)
            text_widget.config(state='disabled')  # Make read-only
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(popup, orient='vertical', command=text_widget.yview)
            scrollbar.pack(side='right', fill='y')
            text_widget.config(yscrollcommand=scrollbar.set)
            
        except FileNotFoundError:
            messagebox.showerror("Error", "plc_register.txt file not found!")
        except Exception as e:
            messagebox.showerror("Error", f"Error reading PLC register data: {str(e)}")

    def on_barcode_type_select(self, event):
        """Handle Barcode Type combobox selection"""
        try:
            # Read barcode filename data from file
            with open('/Users/nithink/Developer/python/EOL_TESTER/barcodeprintfilename.txt', 'r') as file:
                barcode_data = file.read().strip()
            
            # Split data by commas
            barcode_options = [opt.strip() for opt in barcode_data.split(',')]
            
            # Create popup window to display data
            popup = tk.Toplevel(self.root)
            popup.title("Barcode Print Filenames")
            popup.geometry("400x300")
            
            # Add listbox to display data
            listbox = tk.Listbox(popup)
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Insert the options
            for option in barcode_options:
                listbox.insert(tk.END, option)
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(popup, orient='vertical', command=listbox.yview)
            scrollbar.pack(side='right', fill='y')
            listbox.config(yscrollcommand=scrollbar.set)
            
        except FileNotFoundError:
            messagebox.showerror("Error", "barcodeprintfilename.txt file not found!")
        except Exception as e:
            messagebox.showerror("Error", f"Error reading barcode filename data: {str(e)}")

    def load_plc_options(self):
        """Load PLC address options from plc_register.txt"""
        try:
            # Use absolute path to the file
            file_path = "/Users/nithink/Developer/python/EOL_TESTER/PLC_on_register.txt"
            with open(file_path, 'r') as file:
                # Read content and split by commas
                content = file.read().strip()
                options = [opt.strip() for opt in content.split(',') if opt.strip()]
                print(f"Loaded PLC options: {options}")  # Debug print
                return options
        except FileNotFoundError:
            print(f"Warning: plc_register.txt not found at {file_path}")
            return []
        except Exception as e:
            print(f"Error reading PLC options: {str(e)}")
            return []

    def load_barcode_options(self):
        """Load barcode options from barcodeprintfilename.txt"""
        try:
            # Use absolute path to the file
            file_path = "/Users/nithink/Developer/python/EOL_TESTER/barcodeprintfilenames.txt"
            with open(file_path, 'r') as file:
                # Read content and split by commas
                content = file.read().strip()
                options = [opt.strip() for opt in content.split(',') if opt.strip()]
                print(f"Loaded barcode options: {options}")  # Debug print
                return options
        except FileNotFoundError:
            print(f"Warning: barcodeprintfilename.txt not found at {file_path}")
            return []
        except Exception as e:
            print(f"Error reading barcode options: {str(e)}")
            return []

    def on_tree_select(self, event):
        """Handle tree item selection"""
        selected_items = self.part_list_tree.selection()
        if not selected_items:
            return
        
        # Get the selected item
        item = selected_items[0]
        part_number = self.part_list_tree.item(item)['values'][0]
        
        # Store the currently selected part number
        self.current_selected_part = part_number
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Fetch record from database
            query = """
            SELECT * FROM TBL_MODEL_MASTER 
            WHERE MM_PART_NUMBER = %s
            """
            cursor.execute(query, (part_number,))
            
            record = cursor.fetchone()
            
            if record:
                # Clear existing data
                self.clear_all_data()
                
                # Populate textboxes with data - set as real values, not placeholders
                field_mappings = {
                    "Part Number": record[1],
                    "Model & Part Name": record[2],
                    "ALC Code": record[3],
                    "Vendor Code": record[7],
                    "EO Number": record[8],
                    "Special Data": record[9],
                    "Initial ID": record[10],
                    "Supplier Section": record[11]
                }
                
                for key, value in field_mappings.items():
                    if value:  # Only update if value exists
                        self.textboxes[key].delete(0, tk.END)
                        self.textboxes[key].insert(0, value)
                        self.textboxes[key].config(fg='black')  # Set text color to black for real values
                
                # Set combobox values
                if "PLC Address" in self.second_quad_combos and record[4]:
                    self.second_quad_combos["PLC Address"].set(record[4])
                
                if "Barcode Type" in self.second_quad_combos and record[5]:
                    self.second_quad_combos["Barcode Type"].set(record[5])
                
                # Update image path
                if record[6]:
                    self.textboxes["Image File Path"].config(state='normal')
                    self.textboxes["Image File Path"].delete(0, tk.END)
                    self.textboxes["Image File Path"].insert(0, record[6])
                    self.textboxes["Image File Path"].config(state='readonly')
                    
                    # Load the image first
                    self.load_image(record[6])
                    
                    # Then load label positions after image is loaded
                    if record[17]:  # MM_LABEL_COORDINATES
                        self.root.after(100, lambda: self.load_label_positions(part_number))
                
                # Load specifications
                self.load_specifications(part_number)
            
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to load record: {err}")

    def load_image(self, image_path):
        """Load image from path"""
        try:
            if os.path.exists(image_path):
                # Get the first quadrant
                first_quadrant = self.quadrants[0]
                
                # Create a frame to hold the image if it doesn't exist
                if not hasattr(self, 'image_frame'):
                    self.image_frame = tk.Frame(first_quadrant, bg='white')
                    self.image_frame.place(relwidth=1, relheight=1)
                
                # Load and resize the image
                image = Image.open(image_path)
                quad_width = first_quadrant.winfo_width()
                quad_height = first_quadrant.winfo_height()
                resized_image = image.resize((quad_width, quad_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(resized_image)
                
                # Remove old image label if it exists
                if hasattr(self, 'image_label') and self.image_label:
                    self.image_label.destroy()
                
                # Create new image label
                self.image_label = tk.Label(self.image_frame, image=photo, bg='white')
                self.image_label.image = photo  # Keep a reference
                self.image_label.place(x=0, y=0, relwidth=1, relheight=1)
                
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
            cursor = conn.cursor()
            
            query = """
            SELECT * FROM TBL_MODEL_SPECIFICATION 
            WHERE MS_PART_NUMBER = %s
            """
            cursor.execute(query, (part_number,))
            specs = cursor.fetchall()
            
            # Clear existing specs from tree
            for item in self.spec_tree.get_children():
                self.spec_tree.delete(item)
            
            # Insert specifications into tree and populate the first spec into entry fields
            if specs:
                for spec in specs:
                    self.spec_tree.insert('', 'end', values=spec[1:])  # Skip part number column
                
                # Populate the first specification into entry fields
                first_spec = specs[0]
                spec_fields = ['Description', 'Device', 'Unit', 'Master Min', 'Master Max', 'Normal Min', 'Normal Max']
                for i, field in enumerate(spec_fields):
                    if field in self.spec_entries:
                        self.spec_entries[field].delete(0, tk.END)
                        self.spec_entries[field].insert(0, first_spec[i+1])  # +1 to skip part number
            
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to load specifications: {err}")

    def reset_form(self):
        """Reset all form fields to their default state"""
        # Clear all textboxes and restore default placeholders
        for key, entry in self.textboxes.items():
            entry.config(state='normal')
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
        
        # Clear comboboxes
        for combo in self.second_quad_combos.values():
            combo.set('')
        
        # Clear specification entries
        for entry in self.spec_entries.values():
            entry.delete(0, tk.END)
        
        # Clear the image
        if hasattr(self, 'image_label') and self.image_label:
            self.image_label.destroy()
            self.image_label = None
        self.image_uploaded = False
        
        # Reset current selection
        if hasattr(self, 'current_selected_part'):
            self.current_selected_part = None
        
        # Clear tree selection
        self.part_list_tree.selection_remove(self.part_list_tree.selection())

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
            
            # Reset all form fields
            self.reset_form()
            
            # Update the part list view
            self.update_part_list_view()
            
            messagebox.showinfo("Success", "Record deleted successfully!")
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to delete record: {err}")

    def on_reset_button_click(self):
        """Handle reset button click"""
        self.reset_form()

    def edit_record(self):
        """Enable editing of the selected record"""
        if not hasattr(self, 'current_selected_part') or not self.current_selected_part:
            messagebox.showwarning("Warning", "Please select a record to edit!")
            return
        
        # Enable all textboxes for editing
        for key, entry in self.textboxes.items():
            if key != "Image File Path":  # Keep Image File Path readonly
                entry.config(state='normal')
                if entry.get() in ["Enter " + key.lower(), "No image selected"]:
                    entry.delete(0, tk.END)
                entry.config(fg='black')
        
        # Enable comboboxes
        for combo in self.second_quad_combos.values():
            combo.config(state='normal')
        
        # Enable specification entries
        for entry in self.spec_entries.values():
            entry.config(state='normal')
        
        messagebox.showinfo("Edit Mode", "You can now edit the record.\nClick SAVE when done to update the changes.")

def main():
    root = tk.Tk()
    app = WorkspaceApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()        
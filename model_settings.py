import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import json

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
                 command=self.add_specification).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="REMOVE", bg="red", fg="white", width=10,
                 command=self.remove_specification).pack(side=tk.LEFT, padx=5)

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
        self.label_tree = ttk.Treeview(frame, columns=columns, show='headings', height=10)
        
        # Define headings
        headings = {
            'label': 'LABEL',
            'on_status': 'ON STATUS',
            'off_status': 'OFF STATUS'
        }
        
        for col, heading in headings.items():
            self.label_tree.heading(col, text=heading)
            self.label_tree.column(col, width=100, anchor='center')

        # Enable editing on double click
        self.label_tree.bind('<Double-1>', self.on_double_click)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.label_tree.yview)
        self.label_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.label_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

        # Add sample data
        for i in range(1, 17):
            self.label_tree.insert('', tk.END, values=(f'L{i}', 'OFF', 'ON'))         
    def create_parts_list_section(self, frame):
        # Parts List Treeview
        columns = ('sl_no', 'alc', 'part_number', 'model_part_name')
        self.parts_tree = ttk.Treeview(frame, columns=columns, show='headings', height=10)
        
        # Define headings
        headings = {
            'sl_no': 'Sl. No.',
            'alc': 'ALC',
            'part_number': 'PART NUMBER',
            'model_part_name': 'MODEL & PART NAME'
        }
        
        # Set column widths
        widths = {
            'sl_no': 60,
            'alc': 100,
            'part_number': 150,
            'model_part_name': 200
        }
        
        for col, heading in headings.items():
            self.parts_tree.heading(col, text=heading)
            self.parts_tree.column(col, width=widths[col], anchor='center')

        # Add scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.parts_tree.yview)
        self.parts_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.parts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

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
            entry = tk.Entry(left_frame, width=30 if colspan > 1 else 20)
            entry.insert(0, placeholder)
            entry.config(fg='white')
            
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
            ("NEW", "red"),
            ("EDIT", "navy"),
            ("SAVE", "green"),
            ("CLEAR", "gray"),
            ("DELETE", "red")
        ]

        for text, color in buttons:
            btn = tk.Button(right_frame,
                           text=text,
                           bg="white",
                           fg='black',
                           width=10,
                           height=2)
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
        
        # Create a copy of the label in the first quadrant if it's from the header
        if widget.winfo_parent() == str(self.labels_frame):
            # Get the original label text
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
            
            # After placing the label, update the treeview
            self.update_treeview()
        else:
            self.current_label = widget
            self.drag_start_x = event.x
            self.drag_start_y = event.y

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
        # Get the item that was clicked
        item = self.tree.selection()[0]
        column = self.tree.identify_column(event.x)
        values = self.tree.item(item)['values']
        label_text = values[0]  # "Label X"
        label_num = label_text.split()[1]  # Extract number from "Label X"
        
        # Handle Status column (column #2)
        if column == '#2' and label_num in self.placed_labels:
            current_status = self.label_status[label_num]['status']
            # Toggle status
            new_status = 'off' if current_status == 'on' else 'on'
            self.label_status[label_num]['status'] = new_status
            
            # Update treeview
            current_values = list(values)
            current_values[1] = "ON" if new_status == 'on' else "OFF"
            self.tree.item(item, values=current_values)
            
            # Update status display
            self.update_status_display()
        
        # Handle Details column (column #3)
        elif column == '#3' and label_num in self.placed_labels:
            self.create_edit_popup(item, label_num)

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

    def add_specification(self):
        values = []
        for label in ['Description', 'Device', 'Unit', 'Master Min', 'Master Max', 'Normal Min', 'Normal Max']:
            value = self.spec_entries[label].get()
            if not value:
                messagebox.showerror("Error", f"{label} cannot be empty!")
                return
            values.append(value)
        self.spec_tree.insert('', tk.END, values=values)
        for entry in self.spec_entries.values():
            entry.delete(0, tk.END)

    def remove_specification(self):
        selected_items = self.spec_tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select an item to remove!")
            return
        if messagebox.askyesno("Confirm", "Are you sure you want to remove the selected item(s)?"):
            for item in selected_items:
                self.spec_tree.delete(item)

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
            
            # Clear stored positions
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
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add current labels and their status
        for label_num, status in self.label_status.items():
            # Only show labels that are placed on the image
            if label_num in self.placed_labels:
                status_str = "ON" if status['status'] == 'on' else "OFF"
                details = self.label_details[label_num]['details']
                self.tree.insert('', 'end', values=(f"Label {label_num}", status_str, details))

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

def main():
    root = tk.Tk()
    app = WorkspaceApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()        
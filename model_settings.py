import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

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
        
        # Create first two quadrants normally (top row)
        for i in range(2):
            frame = tk.Frame(self.workspace_frame,
                           relief="groove",
                           borderwidth=1,
                           bg='white',
                           width=self.min_quadrant_size[0],
                           height=self.min_quadrant_size[1])
            frame.grid(row=0, column=i, sticky="nsew")
            frame.grid_propagate(False)
            self.quadrants.append(frame)
        
        # Create bottom row container
        bottom_container = tk.Frame(self.workspace_frame)
        bottom_container.grid(row=1, column=0, columnspan=2, sticky="nsew")
        
        # Create three sections in the bottom row with headers
        self.create_bottom_sections(bottom_container)
        
        # Configure main grid weights
        self.workspace_frame.grid_rowconfigure(0, weight=1)
        self.workspace_frame.grid_rowconfigure(1, weight=1)
        self.workspace_frame.grid_columnconfigure(0, weight=1)
        self.workspace_frame.grid_columnconfigure(1, weight=1)

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

        # Input fields configuration
        fields = [
            ("Vendor Code", 0, 0),
            ("EO Number", 0, 1),
            ("Special Data", 1, 0),
            ("Initial ID", 1, 1),
            ("Part Number", 2, 0, 2),  # spans 2 columns
            ("Model & Part Name", 3, 0, 2),  # spans 2 columns
            ("Image File Path", 4, 0, 2),  # spans 2 columns
            ("ALC Code", 5, 0),
            ("Supplier Section", 2, 1)
        ]

        self.textboxes = {}
        
        # Create and arrange input fields
        for field in fields:
            label_text = field[0]
            row = field[1]
            col = field[2]
            colspan = field[3] if len(field) > 3 else 1

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

            # Entry
            entry = tk.Entry(left_frame, width=30 if colspan > 1 else 20)
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
                browse_btn = tk.Button(left_frame, 
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
                           bg=color,
                           fg='white',
                           width=10,
                           height=2)
            btn.pack(pady=5)              

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
            self.original_positions[f"L{i+1}"] = label
            self.moveable_labels.append(label)

    def create_buttons(self):
        # Reset button
        self.reset_btn = tk.Button(self.buttons_frame, 
                                 text="RESET",
                                 bg="red",
                                 fg="white",
                                 width=10,
                                 height=2,
                                 command=self.reset_labels)
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Update button
        self.update_btn = tk.Button(self.buttons_frame,
                                  text="UPDATE",
                                  bg="green",
                                  fg="white",
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
        widget = event.widget
        widget.startX = event.x
        widget.startY = event.y
        self.current_label = widget

    def on_motion(self, event):
        if self.current_label:
            x = self.current_label.winfo_x() + event.x - self.current_label.startX
            y = self.current_label.winfo_y() + event.y - self.current_label.startY
            self.current_label.place(x=x, y=y)

    def stop_move(self, event):
        self.current_label = None

    def on_double_click(self, event):
        try:
            item = self.label_tree.selection()[0]
            column = self.label_tree.identify_column(event.x)
            if column in ('#2', '#3'):
                self.edit_cell(item, column)
        except IndexError:
            pass

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
            for label in self.placed_labels.values():
                label.destroy()
            self.placed_labels.clear()
            for label in self.original_positions.values():
                label.config(bg="lightgray")

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
                
                self.image_label = tk.Label(first_quadrant, image=photo, bg='white')
                self.image_label.image = photo
                
                x_pos = (quad_width - new_width) // 2
                y_pos = (quad_height - new_height) // 2
                self.image_label.place(x=x_pos, y=y_pos)
                
                self.update_image_path(file_path)
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading image: {str(e)}")

def main():
    root = tk.Tk()
    app = WorkspaceApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()        
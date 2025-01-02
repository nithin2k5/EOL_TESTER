import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import mysql.connector
import os
import re
from datetime import datetime
import logging
import configparser

class ModelSettings:
    def __init__(self, root):
        self.root = root
        self.root.title("EOL Tester - Model Settings")
        self.root.state('zoomed')
        
        # Initialize variables
        self.part_labels_list = []
        self.used_plc_addresses = []
        self.program_selection_array = []
        self.barcode_print_files_array = []
        self.action = None
        self.selected_part_number = None
        self.user = ""
        self.label_positions = {}
        self.selected_label = None
        self.image_loaded = False
        
        # Setup logging
        logging.basicConfig(
            filename='model_settings.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Database connection
        self.db = self.setup_database_connection()
        
        # Load configuration
        self.config = self.load_config()
        
        # Setup UI components
        self.setup_ui()
        
        # Show login dialog
        self.show_login_dialog()

    def setup_database_connection(self):
        try:
            return mysql.connector.connect(
                host='localhost',
                database='eol_tester_db',
                user='root',
                password='password'
            )
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to connect to database: {err}")
            return None

    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists('config.ini'):
            config.read('config.ini')
        return config

    def setup_ui(self):
        # Create main container
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create navigation bar
        self.create_navigation()
        
        # Create main content area with quadrants
        self.create_quadrants()
        
        # Create status bar
        self.create_status_bar()
        
        # Load initial data
        self.load_part_labels()
        self.load_plc_addresses()
        self.load_barcode_print_files()

    def create_navigation(self):
        nav_frame = tk.Frame(self.main_container, bg="lightgray", height=40)
        nav_frame.pack(fill=tk.X)
        
        buttons = [
            ("PORT SETTINGS", self.port_settings),
            ("LABEL MAKER", self.label_maker),
            ("MODEL SETTINGS", self.model_settings),
            ("TEST", self.test),
            ("WORK DATA", self.work_data),
            ("ADMIN", self.admin),
            ("HELP", self.help),
            ("EXIT", self.exit_app)
        ]
        
        for btn_text, command in buttons:
            btn = tk.Button(nav_frame, text=btn_text, bg="white",
                          relief=tk.FLAT, padx=10, pady=5,
                          command=command)
            btn.pack(side=tk.LEFT, padx=2, pady=2)

    def create_quadrants(self):
        # Create frame for quadrants
        self.workspace = tk.Frame(self.main_container)
        self.workspace.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure grid
        self.workspace.grid_columnconfigure(0, weight=1)
        self.workspace.grid_columnconfigure(1, weight=1)
        self.workspace.grid_rowconfigure(0, weight=1)
        self.workspace.grid_rowconfigure(1, weight=1)
        
        # Create quadrants
        self.q1 = self.create_first_quadrant()
        self.q2 = self.create_second_quadrant()
        self.q3 = self.create_third_quadrant()
        self.q4 = self.create_fourth_quadrant()
        
        # Place quadrants in grid
        self.q1.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self.q2.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
        self.q3.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)
        self.q4.grid(row=1, column=1, sticky="nsew", padx=1, pady=1)

    def create_first_quadrant(self):
        frame = tk.Frame(self.workspace, relief="groove", borderwidth=1)
        
        # Header
        header = tk.Label(frame, text="MODEL NAME / PART NAME - PART NUMBER",
                         bg="navy", fg="white", font=("Arial", 12, "bold"))
        header.pack(fill=tk.X)
        
        # Label strip (L0-L15)
        label_frame = tk.Frame(frame)
        label_frame.pack(fill=tk.X, pady=5)
        
        self.label_widgets = {}
        for i in range(16):
            label = tk.Label(label_frame, text=f"L{i}", width=4,
                           relief="raised", bg="lightgray")
            label.pack(side=tk.LEFT, padx=2)
            self.label_widgets[f"L{i}"] = label
            
            # Bind drag events
            label.bind("<Button-1>", self.start_label_drag)
            label.bind("<B1-Motion>", self.on_label_drag)
            label.bind("<ButtonRelease-1>", self.stop_label_drag)
        
        # Image area
        self.image_area = tk.Frame(frame, bg="white")
        self.image_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Image label
        self.image_label = tk.Label(self.image_area, bg="white")
        self.image_label.pack(fill=tk.BOTH, expand=True)
        
        # Browse button
        self.browse_btn = tk.Button(frame, text="Browse Image",
                                  command=self.browse_image)
        self.browse_btn.pack(side=tk.BOTTOM, pady=5)
        
        return frame

    def create_second_quadrant(self):
        frame = tk.Frame(self.workspace, relief="groove", borderwidth=1)
        
        # Header
        header = tk.Label(frame, text="PART DETAILS",
                         bg="#00BFFF", fg="black", 
                         font=("Arial", 12, "bold"))
        header.pack(fill=tk.X)
        
        # Part details form
        form_frame = tk.Frame(frame)
        form_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create form fields
        fields = [
            ("Part Number:", "part_number"),
            ("Model Name:", "model_name"),
            ("ALC Code:", "alc_code"),
            ("PLC Address:", "plc_address"),
            ("Barcode Print File:", "barcode_file"),
            ("Vendor Code:", "vendor_code"),
            ("EO Number:", "eo_number"),
            ("Special Data:", "special_data"),
            ("Initial ID:", "initial_id"),
            ("Supplier Section:", "supplier_section")
        ]
        
        self.entries = {}
        for i, (text, key) in enumerate(fields):
            label = tk.Label(form_frame, text=text)
            label.grid(row=i, column=0, sticky="e", padx=5, pady=2)
            
            if key in ["plc_address", "barcode_file"]:
                entry = ttk.Combobox(form_frame)
            else:
                entry = tk.Entry(form_frame)
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=2)
            self.entries[key] = entry
        
        return frame

    def create_third_quadrant(self):
        frame = tk.Frame(self.workspace, relief="groove", borderwidth=1)
        
        # Create sections
        sections = [
            ("SPECIFICATIONS", self.create_specifications_section),
            ("LABEL DETAILS", self.create_label_details_section),
            ("PARTS LIST", self.create_parts_list_section)
        ]
        
        for title, create_func in sections:
            section_frame = tk.LabelFrame(frame, text=title,
                                        font=("Arial", 10, "bold"))
            section_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            create_func(section_frame)
        
        return frame

    def create_fourth_quadrant(self):
        frame = tk.Frame(self.workspace, relief="groove", borderwidth=1)
        
        # Header
        columns = ["LOT NUMBER", "L1", "P1", "P2", "RESULT"]
        header_frame = tk.Frame(frame, bg="#00BFFF")
        header_frame.pack(fill=tk.X)
        
        for col in columns:
            label = tk.Label(header_frame, text=col, bg="#00BFFF",
                           font=("Arial", 10, "bold"))
            label.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        
        # Grid view
        self.results_tree = ttk.Treeview(frame, columns=columns,
                                       show="headings", height=10)
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=100)
        
        self.results_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bottom frame
        bottom_frame = tk.Frame(frame)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
        
        # Next model button
        next_btn = tk.Button(bottom_frame, 
                           text="CLICK HERE TO MOVE TO NEXT MODEL",
                           bg="yellow")
        next_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 1))
        
        # ALC CODE entry
        self.alc_entry = tk.Entry(bottom_frame, bg="yellow",
                                justify="center")
        self.alc_entry.insert(0, "ALC CODE")
        self.alc_entry.pack(side=tk.RIGHT, padx=(1, 2), ipady=1)
        
        return frame

    def create_specifications_section(self, parent):
        # Input fields
        input_frame = tk.Frame(parent)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        fields = [
            ("Description", 0, 0, 2),
            ("Device", 1, 0, 1),
            ("Unit", 1, 1, 1),
            ("Master Min", 2, 0, 1),
            ("Master Max", 2, 1, 1),
            ("Normal Min", 3, 0, 1),
            ("Normal Max", 3, 1, 1)
        ]
        
        self.spec_entries = {}
        for label_text, row, col, span in fields:
            label = tk.Label(input_frame, text=label_text)
            label.grid(row=row*2, column=col, columnspan=span, sticky="w")
            
            entry = tk.Entry(input_frame)
            entry.grid(row=row*2+1, column=col, columnspan=span, sticky="ew")
            self.spec_entries[label_text] = entry
        
        # Buttons
        btn_frame = tk.Frame(input_frame)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=5)
        
        tk.Button(btn_frame, text="ADD", bg="green", fg="white",
                 command=self.add_specification).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="REMOVE", bg="red", fg="white",
                 command=self.remove_specification).pack(side=tk.LEFT, padx=5)
        
        # Specifications table
        self.spec_tree = ttk.Treeview(parent, height=6)
        self.spec_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_label_details_section(self, parent):
        columns = ("Label", "ON Status", "OFF Status")
        self.label_tree = ttk.Treeview(parent, columns=columns,
                                     show="headings", height=6)
        
        for col in columns:
            self.label_tree.heading(col, text=col)
            self.label_tree.column(col, width=100)
        
        self.label_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL,
                                command=self.label_tree.yview)
        self.label_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_parts_list_section(self, parent):
        columns = ("Sl.No", "ALC", "Part Number", "Model & Part Name")
        self.parts_tree = ttk.Treeview(parent, columns=columns,
                                     show="headings", height=6)
        
        for col in columns:
            self.parts_tree.heading(col, text=col)
        
        self.parts_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL,
                                command=self.parts_tree.yview)
        self.parts_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_status_bar(self):
        self.status_bar = tk.Label(self.root, text="Ready",
                                 bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # Event handlers and utility methods
    def start_label_drag(self, event):
        if not self.image_loaded:
            return
        self.selected_label = event.widget
        self.selected_label._drag_start_x = event.x
        self.selected_label._drag_start_y = event.y

    def on_label_drag(self, event):
        if not self.selected_label or not self.image_loaded:
            return
        
        x = self.selected_label.winfo_x() + event.x - self.selected_label._drag_start_x
        y = self.selected_label.winfo_y() + event.y - self.selected_label._drag_start_y
        
        # Keep within image area bounds
        x = max(0, min(x, self.image_area.winfo_width() - self.selected_label.winfo_width()))
        y = max(0, min(y, self.image_area.winfo_height() - self.selected_label.winfo_height()))
        
        self.selected_label.place(x=x, y=y)

    def stop_label_drag(self, event):
        if self.selected_label and self.image_loaded:
            self.label_positions[self.selected_label.cget("text")] = (
                self.selected_label.winfo_x(),
                self.selected_label.winfo_y()
            )
        self.selected_label = None

    def browse_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            try:
                image = Image.open(file_path)
                # Calculate scaling to fit
                image_width, image_height = image.size
                area_width = self.image_area.winfo_width()
                area_height = self.image_area.winfo_height()
                
                scale = min(area_width/image_width, area_height/image_height)
                new_width = int(image_width * scale)
                new_height = int(image_height * scale)
                
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                self.image_label.configure(image=photo)
                self.image_label.image = photo
                self.image_loaded = True
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading image: {str(e)}")

    def add_specification(self):
        # Get values from entries
        values = [self.spec_entries[key].get() for key in self.spec_entries]
        if all(values):
            self.spec_tree.insert("", tk.END, values=values)
            # Clear entries
            for entry in self.spec_entries.values():
                entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Warning", "Please fill all specification fields")

    def remove_specification(self):
        selected_item = self.spec_tree.selection()
        if selected_item:
            self.spec_tree.delete(selected_item)

    def show_login_dialog(self):
        # Implement login dialog
        pass

    # Navigation button commands
    def port_settings(self):
        pass

    def label_maker(self):
        pass

    def model_settings(self):
        pass

    def test(self):
        pass

    def work_data(self):
        pass

    def admin(self):
        pass

    def help(self):
        pass

    def exit_app(self):
        if messagebox.askokcancel("Exit", "Do you want to exit?"):
            self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = ModelSettings(root)
    root.mainloop()        
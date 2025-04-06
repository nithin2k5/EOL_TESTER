import tkinter as tk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import mysql.connector
from pynput import keyboard
import threading
import json
from pymodbus.client import ModbusSerialClient
import serial
from dotenv import load_dotenv
import time

class EOLTesterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EOL (END OF LINE) TESTER")
        
        # Initialize variables before setting up the window
        self.initialize_variables()
        
        # Set up the window after initialization
        self.root.after(100, self.setup_window)  # Delay window setup slightly
        
        # Continue with the rest of your initialization...

    def initialize_variables(self):
        """Initialize all variables before window setup"""
        self.image_label = None
        self.current_image = None
        self.label_positions = {}
        self.selected_label = None
        self.barcode_data = ""
        self.label_widgets = {}
        
        # Get machine ID from environment variable and store it
        self.machineid = os.getenv('MACHINE_ID', 'Not Set')
        
        # Initialize arrays for different data types
        self.process_status_array = []
        self.program_selection_array = []
        self.input_sensors_array = []
        self.employee_codes = []
        
        # Initialize additional variables
        self.keepWriting = False
        self.breakLoop = False
        self.failCounter = 0
        self.startingNGCableValidation = False
        self.endingNGCableValidation = False
        self.noOfValues = 0
        self.resetPLCOnFormClosing = True
        
        # Initialize timers
        self.alc_timer = None
        self.alcInput_TimeInterval = 200  # milliseconds

    def setup_window(self):
        """Set up the window after initialization"""
        # Change from fullscreen to maximized state
        self.root.state('zoomed')  # Replace fullscreen with maximized state
        self.root.lift()  # Bring window to front
        self.root.focus_force()  # Force focus
        
        # Remove escape key binding since we're not using fullscreen
        # self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        
        # Load data and connect to devices
        self.load_configuration_data()
        load_dotenv()
        self.connect_to_devices()
        
        # Set up GUI components
        self.setup_gui()
        self.setup_barcode_listener()
        
        # Start monitoring
        self.monitor_p0000_state()
        self.start_check_async()
        
        # Ensure window stays on top during initialization
        self.root.after(500, lambda: self.root.attributes('-topmost', False))

    def setup_gui(self):
        # Main container
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)

        # Add message label for status updates with empty initial text
        self.message_label = tk.Label(self.main_container, text="Ready", font=("Arial", 10))
        self.message_label.pack(fill="x", pady=2)
        
        # Title bar with INFAC logo
        self.create_title_bar()
        
        # Main workspace
        self.workspace = tk.Frame(self.main_container)
        self.workspace.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Force the workspace to update its geometry
        self.root.update_idletasks()
        
        # Create quadrants
        self.create_quadrants()
        
        # Footer
        self.create_footer()

    def create_title_bar(self):
        title_frame = tk.Frame(self.main_container, bg="#FFB6C1", height=40)
        title_frame.pack(fill="x")
        
        # INFAC Logo (left side)
        logo_label = tk.Label(
            title_frame, 
            text="INFAC\nINDIA", 
            bg="#FFB6C1", 
            font=("Arial", 10, "bold")
        )
        logo_label.pack(side="left", padx=10)
        
        # Add Test PLC Button (left side, after logo)
        self.test_plc_button = tk.Button(
            title_frame,
            text="P0000: LOW",  # Initial state
            bg="#4CAF50",  # Green background
            fg="white",
            font=("Arial", 10, "bold"),
            relief="raised",
            command=self.test_plc_communication,
            width=12,
            height=1
        )
        self.test_plc_button.pack(side="left", padx=10)
        
        # Add status indicator
        self.status_label = tk.Label(
            title_frame,
            text="●",  # Dot indicator
            font=("Arial", 16, "bold"),
            bg="#FFB6C1",
            fg="gray"  # Initial color
        )
        self.status_label.pack(side="left")
        
        # Title (center)
        title_label = tk.Label(
            title_frame, 
            text="EOL (END OF LINE) TESTER",
            font=("Arial", 16, "bold"), 
            bg="#FFB6C1"
        )
        title_label.pack(pady=5)
        
        # Machine ID (right side)
        machine_id = os.getenv('MACHINE_ID', 'Not Set')  # Get from environment variable
        machine_label = tk.Label(
            title_frame, 
            text=f"Machine ID: {machine_id}",
            bg="#FFB6C1", 
            font=("Arial", 12, "bold")
        )
        machine_label.pack(side="right", padx=20)

        # Add hover effect for the test button
        self.test_plc_button.bind('<Enter>', lambda e: self.test_plc_button.config(bg="#45a049"))
        self.test_plc_button.bind('<Leave>', lambda e: self.test_plc_button.config(bg="#4CAF50"))

    def create_quadrants(self):
        """Update the create_quadrants method to remove borders"""
        # Configure grid weights for equal space
        self.workspace.grid_columnconfigure(0, weight=1)  # First column
        self.workspace.grid_columnconfigure(1, weight=1)  # Second column
        self.workspace.grid_rowconfigure(0, weight=1)     # First row
        self.workspace.grid_rowconfigure(1, weight=1)     # Second row
        
        # Create quadrants without borders
        self.q1 = self.create_first_quadrant()
        self.q2 = self.create_second_quadrant()
        self.q3 = self.create_third_quadrant()
        self.q4 = self.create_fourth_quadrant()
        
        # Place quadrants with minimal spacing
        self.q1.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self.q2.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
        self.q3.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)
        self.q4.grid(row=1, column=1, sticky="nsew", padx=1, pady=1)
        
        # Prevent resizing
        for quadrant in [self.q1, self.q2, self.q3, self.q4]:
            quadrant.grid_propagate(False)

    def create_first_quadrant(self):
        """Create the image display quadrant with correct dimensions."""
        q1 = tk.Frame(self.workspace, bg='white')
        q1.grid_propagate(False)  # Prevent frame from resizing
        q1.config(width=800, height=600)  # Match model_settings.py quadrant size
        
        # Create header frame at the top
        header_frame = tk.Frame(q1, bg="#00BFFF", height=30)
        header_frame.pack(fill="x", side="top", pady=(0, 5))
        
        # Add header label
        self.model_header = tk.Label(header_frame, 
                                    text="MODEL - PART NUMBER",
                                    bg="#00BFFF",
                                    font=("Arial", 12, "bold"))
        self.model_header.pack(pady=2)
        
        # Create a frame to hold the image with exact dimensions
        self.image_frame = tk.Frame(q1, bg='white')
        self.image_frame.pack(fill="both", expand=True, padx=2, pady=2)
        self.image_frame.pack_propagate(False)
        
        # Set exact size to match model_settings.py image dimensions
        self.image_frame.config(width=750, height=450)  # Further reduced height to ensure space for labels
        
        # Create initial placeholder
        self.image_label = tk.Label(self.image_frame, 
                                   text="No image loaded",
                                   bg='white',
                                   font=('Arial', 12))
        self.image_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Create status labels frame with fixed height
        status_frame = tk.Frame(q1, bg='white', height=60)  # Increased height
        status_frame.pack(fill="x", side="bottom", pady=10, before=self.image_frame)
        status_frame.pack_propagate(False)  # Prevent frame from shrinking
        
        # Configure grid for equal spacing
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=1)
        status_frame.grid_columnconfigure(2, weight=1)
        status_frame.grid_columnconfigure(3, weight=1)
        status_frame.grid_columnconfigure(4, weight=1)
        
        # Define status labels with their properties
        status_labels = [
            {'text': 'AUTO', 'bg': '#00BFFF'},
            {'text': 'HOME', 'bg': '#00BFFF'},
            {'text': '1st PULL\n(Load Test)', 'bg': '#00BFFF'},
            {'text': '2nd PULL\n(Length Test)', 'bg': '#00BFFF'},
            {'text': 'TEST\nRESULT', 'bg': '#00BFFF'}
        ]
        
        # Create and pack status labels using grid
        for i, label_info in enumerate(status_labels):
            label = tk.Label(
                status_frame,
                text=label_info['text'],
                bg=label_info['bg'],
                fg="black",
                font=("Arial", 10, "bold"),
                relief="raised",
                borderwidth=1,
                width=15,  # Fixed width
                height=5   # Fixed height
            )
            label.grid(row=0, column=i, padx=2, pady=2, sticky="nsew")
            
            # Store reference to the label
            setattr(self, f"{label_info['text'].split()[0].lower()}_label", label)
        
        # Create bottom frame for label info
        bottom_frame = tk.Frame(q1, height=30, bg='white')
        bottom_frame.pack(fill="x", side="bottom", pady=5)
        bottom_frame.pack_propagate(False)
        
        # Add label info text
        self.label_info = tk.Label(bottom_frame,
                                  text="Placed Labels: None",
                                  bg='white',
                                  font=('Arial', 10))
        self.label_info.pack(pady=2)
        
        return q1

    def create_second_quadrant(self):
        """Create the specifications display quadrant."""
        q2 = tk.Frame(self.workspace, relief="groove", borderwidth=1)
        
        # Define camera frame dimensions
        cam_width = 120  # Width for camera frames
        cam_height = 90  # Height for camera frames
        
        # Add header
        header = tk.Label(q2, text="TEST SPECIFICATIONS",
                         bg="#00BFFF", fg="black",
                         font=("Arial", 12, "bold"))
        header.pack(fill="x")
        
        # Create specifications table frame (70% of height)
        spec_frame = tk.Frame(q2, relief="solid", borderwidth=1)  # Add border to spec frame
        spec_frame.pack(fill="x", expand=True, padx=2, pady=2)  # Add padding
        
        # Create specifications table with numbered ID
        columns = (
            "Description",
            "Device",
            "Unit",
            "Min",
            "Max",
            "Actual",
            "Result"
        )
        
        # Configure style for Treeview
        style = ttk.Style()
        style.configure("Custom.Treeview",
                       borderwidth=1,  # Border width
                       relief="solid",  # Border style
                       fieldbackground="white",  # Background color
                       background="white",  # Row background color
                       foreground="black")  # Text color
        
        style.configure("Custom.Treeview.Heading",
                       borderwidth=1,
                       relief="solid",
                       background="#e0e0e0",  # Light gray header background
                       foreground="black",  # Header text color
                       font=("Arial", 9, "bold"))  # Header font
        
        # Configure selection colors
        style.map("Custom.Treeview",
                 background=[("selected", "#cce5ff")],  # Light blue for selected row
                 foreground=[("selected", "black")])  # Selected row text color
        
        # Create Treeview with custom style
        self.spec_tree = ttk.Treeview(spec_frame, 
                                     columns=columns, 
                                     show="headings", 
                                     height=15,
                                     style="Custom.Treeview")
        
        # Configure columns with specific widths
        column_widths = {
            "Description": 200,
            "Device": 100,
            "Unit": 80,
            "Min": 50,
            "Max": 50,
            "Actual": 50,
            "Result": 50
        }
        
        # Set up each column with borders
        for col in columns:
            self.spec_tree.heading(col, text=col)
            self.spec_tree.column(col, width=column_widths.get(col, 100), anchor='center')
        
        # Add scrollbars
        scrollbar = ttk.Scrollbar(spec_frame, orient="vertical", command=self.spec_tree.yview)
        self.spec_tree.configure(yscrollcommand=scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(spec_frame, orient="horizontal", command=self.spec_tree.xview)
        self.spec_tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Pack the treeview and scrollbars
        self.spec_tree.pack(side="top", fill="both", expand=True, padx=0, pady=0)
        scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        # Create camera frame container (30% of height)
        camera_container = tk.Frame(q2, bg='#f0f0f0')
        camera_container.pack(fill="both", expand=True, padx=1, pady=1)
        
        # Configure grid for equal spacing
        camera_container.grid_columnconfigure(0, weight=1)  # First camera
        camera_container.grid_columnconfigure(1, weight=1)  # Second camera
        camera_container.grid_columnconfigure(2, weight=1)  # Spacing
        camera_container.grid_columnconfigure(3, weight=1)  # Text box
        
        # Camera 1 section
        cam1_label = tk.Label(camera_container, text="CAM 1", fg='black', bg='white', font=("Arial", 10, "bold"))
        cam1_label.grid(row=0, column=0, pady=(0, 5))
        
        self.cam1_frame = tk.Frame(camera_container, width=cam_width, height=cam_height, 
                                  bg='white', relief='solid', borderwidth=1)
        self.cam1_frame.grid(row=1, column=0, padx=10)
        self.cam1_frame.grid_propagate(False)
        
        # Camera 2 section
        cam2_label = tk.Label(camera_container, text="CAM 2", bg='white', fg='black', font=("Arial", 10, "bold"))
        cam2_label.grid(row=0, column=1, pady=(0, 5))
        
        self.cam2_frame = tk.Frame(camera_container, width=cam_width, height=cam_height, 
                                  bg='white', relief='solid', borderwidth=1)
        self.cam2_frame.grid(row=1, column=1, padx=10)
        self.cam2_frame.grid_propagate(False)

        # Text box (moved to column 3 for equal spacing)

        textbox_label = tk.Label(camera_container, text="LABEL SCAN RESULT", bg='white', fg='black', font=("Arial", 10, "bold"))
        textbox_label.grid(row=0, column=3, pady=(0, 5))
        self.cam_textbox = tk.Text(camera_container, width=40, height=7)
        self.cam_textbox.grid(row=1, column=3, padx=10, pady=1)
        return q2

    def create_third_quadrant(self):
        q3 = tk.Frame(self.workspace, relief="groove", borderwidth=1)
        
        # Add graph area directly without the labels
        self.create_graph_area(q3)
        
        return q3

    def create_fourth_quadrant(self):
        q4 = tk.Frame(self.workspace)
        
        # Header with gradient effect - reduced height to 30
        header_frame = tk.Frame(q4, bg="#1e88e5", height=30)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        columns = ["LOT NUMBER", "L1", "P1", "P2", "RESULT"]
        for col in columns:
            label = tk.Label(header_frame, 
                           text=col, 
                           bg="#1e88e5",     
                           fg="white",        
                           font=("Arial", 9, "bold"))
            label.pack(side="left", expand=True, fill="x", padx=2, pady=3)
        
        # Grid view area
        grid_frame = tk.Frame(q4, bg="#f5f5f5")
        grid_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        grid_label = tk.Label(grid_frame, 
                            text="Grid view", 
                            font=("Arial", 20),
                            bg="#f5f5f5",
                            fg="#757575")
        grid_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Bottom frame with equal spacing
        bottom_frame = tk.Frame(q4, bg="#f5f5f5", height=40)
        bottom_frame.pack(fill="x", side="bottom", pady=2)
        bottom_frame.pack_propagate(False)
        
        # Configure equal column weights
        bottom_frame.columnconfigure(0, weight=1)  # EMP CODE
        bottom_frame.columnconfigure(1, weight=1)  # NEXT LABEL button
        bottom_frame.columnconfigure(2, weight=1)  # ALC CODE
        
        # Employee Code Entry
        self.emp_entry = tk.Entry(bottom_frame,
                                 bg="white",
                                 fg="#424242",
                                 font=("Arial", 9, "bold"),
                                 justify="center",
                                 relief="flat",
                                 width=12)
        self.emp_entry.grid(row=0, column=0, padx=5, sticky="ew")
        self.emp_entry.insert(0, "EMP CODE")
        self.emp_entry.configure(highlightthickness=1,
                               highlightbackground="#e0e0e0",
                               highlightcolor="#1e88e5")
        
        # Next Label Button (centered)
        next_btn = tk.Button(bottom_frame,
                            text="NEXT LABEL ➜",
                            bg="#ffd700",
                            fg="#000000",
                            relief="flat",
                            font=("Arial", 9, "bold"),
                            cursor="hand2",
                            pady=2)
        next_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Add hover effect
        next_btn.bind('<Enter>', lambda e: next_btn.configure(bg="#ffeb3b"))
        next_btn.bind('<Leave>', lambda e: next_btn.configure(bg="#ffd700"))
        
        # ALC Code Entry (initially disabled)
        self.alc_entry = tk.Entry(bottom_frame,
                                 bg="white",
                                 fg="black",
                                 font=("Arial", 9, "bold"),
                                 justify="center",
                                 relief="flat",
                                 width=12,
                                 state='disabled')  # Initially disabled
        self.alc_entry.grid(row=0, column=2, padx=5, sticky="ew")
        self.alc_entry.insert(0, "ALC CODE")
        self.alc_entry.configure(highlightthickness=1,
                               highlightbackground="#e0e0e0",
                               highlightcolor="#ffd700")
        
        # Bind events
        self.emp_entry.bind("<FocusIn>", lambda e: self.on_emp_entry_focus(True))
        self.emp_entry.bind("<FocusOut>", lambda e: self.on_emp_entry_focus(False))
        self.emp_entry.bind("<Return>", self.validate_employee_code)
        
        self.alc_entry.bind("<FocusIn>", lambda e: self.on_alc_entry_focus(True))
        self.alc_entry.bind("<FocusOut>", lambda e: self.on_alc_entry_focus(False))
        self.alc_entry.bind("<Return>", self.process_alc_code)
        
        return q4

    def create_graph_area(self, parent):
        # Create main graph container with black background
        graph_container = tk.Frame(parent, bg="black")
        graph_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure grid weights for reduced height
        graph_container.grid_rowconfigure(0, weight=0)  # Title row for Load graph
        graph_container.grid_rowconfigure(1, weight=1)  # Load graph
        graph_container.grid_rowconfigure(2, weight=0)  # Title row for Length graph
        graph_container.grid_rowconfigure(3, weight=1)  # Length graph
        graph_container.grid_columnconfigure(0, weight=1)  # Ensure full width
        
        # Load Graph Title
        tk.Label(graph_container, text="LOAD GRAPH", 
                 bg="black", fg="white", anchor="w",
                 font=("Arial", 10)).grid(row=0, column=0, sticky="w", padx=5)
        
        # Load Graph Canvas with reduced height
        self.load_canvas = tk.Canvas(graph_container, bg="black", 
                                   highlightthickness=0, height=100)  # Reduced height
        self.load_canvas.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 10))
        
        # Length Graph Title
        tk.Label(graph_container, text="LENGTH GRAPH", 
                 bg="black", fg="white", anchor="w",
                 font=("Arial", 10)).grid(row=2, column=0, sticky="w", padx=5)
        
        # Length Graph Canvas with reduced height
        self.length_canvas = tk.Canvas(graph_container, bg="black", 
                                     highlightthickness=0, height=100)  # Reduced height
        self.length_canvas.grid(row=3, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        # Bind resize events
        self.load_canvas.bind('<Configure>', lambda e: self.draw_load_graph())
        self.length_canvas.bind('<Configure>', lambda e: self.draw_length_graph())

    def draw_load_graph(self):
        canvas = self.load_canvas
        canvas.delete("all")
        
        # Get dimensions
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        # Set margins
        left_margin = 40
        right_margin = 100  # Extra space for legend
        top_margin = 20
        bottom_margin = 30
        
        # Drawing area
        graph_width = width - (left_margin + right_margin)
        graph_height = height - (top_margin + bottom_margin)
        
        # Draw grid
        # Vertical lines
        for i in range(9):  # 8 divisions
            x = left_margin + (i * graph_width / 8)
            canvas.create_line(x, top_margin, x, height-bottom_margin, 
                             fill="gray", dash=(1,2))
            # X-axis labels
            canvas.create_text(x, height-bottom_margin+10, 
                             text=str(i+1), fill="white")
        
        # Horizontal lines
        for i in range(6):  # 5 divisions (0, 20, 40, 60, 80, 100)
            y = height - (bottom_margin + (i * graph_height / 5))
            canvas.create_line(left_margin, y, width-right_margin, y, 
                             fill="gray", dash=(1,2))
            # Y-axis labels
            canvas.create_text(left_margin-15, y, 
                             text=str(i*20), fill="white")
        
        # Draw legend
        legend_items = [
            ("L1", "cyan"),
            ("L2", "orange"),
            ("L3", "red"),
            ("L4", "blue")
        ]
        
        legend_x = width - right_margin + 20
        legend_y = top_margin + 20
        
        for text, color in legend_items:
            canvas.create_line(legend_x, legend_y, legend_x+20, legend_y, 
                             fill=color, width=2)
            canvas.create_text(legend_x+30, legend_y, 
                             text=text, fill="white", anchor="w")
            legend_y += 20

    def draw_length_graph(self):
        canvas = self.length_canvas
        canvas.delete("all")
        
        # Get dimensions
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        # Set margins
        left_margin = 40
        right_margin = 100
        top_margin = 20
        bottom_margin = 30
        
        # Drawing area
        graph_width = width - (left_margin + right_margin)
        graph_height = height - (top_margin + bottom_margin)
        
        # Draw grid
        # Vertical lines
        for i in range(9):  # 8 divisions
            x = left_margin + (i * graph_width / 8)
            canvas.create_line(x, top_margin, x, height-bottom_margin, 
                             fill="gray", dash=(1,2))
            # X-axis labels
            canvas.create_text(x, height-bottom_margin+10, 
                             text=str(i+1), fill="white")
        
        # Horizontal lines and labels
        y_labels = [-5, -3, -1, 1, 3, 5]
        for i, label in enumerate(y_labels):
            y = top_margin + (i * graph_height / (len(y_labels)-1))
            canvas.create_line(left_margin, y, width-right_margin, y, 
                             fill="gray", dash=(1,2))
            canvas.create_text(left_margin-15, y, 
                             text=str(label), fill="white")
        
        # Draw legend
        legend_items = [
            ("P1", "blue"),
            ("P2", "orange"),
            ("P3", "red"),
            ("P4", "white")
        ]
        
        legend_x = width - right_margin + 20
        legend_y = top_margin + 20
        
        for text, color in legend_items:
            canvas.create_line(legend_x, legend_y, legend_x+20, legend_y, 
                             fill=color, width=2)
            canvas.create_text(legend_x+30, legend_y, 
                             text=text, fill="white", anchor="w")
            legend_y += 20

    def create_footer(self):
        footer = tk.Label(self.main_container,
                        text="Powered By: NICE COMPUTERS AND SOFTWARE SOLUTIONS, Kavali, A.P",
                        bg="#FFB6C1", height=2)
        footer.pack(fill="x", side="bottom")

    # Label drag and drop functionality
    def enable_label_dragging(self):
        """Enable drag and drop for all labels"""
        for label in self.label_widgets.values():
            label.bind("<Button-1>", self.start_label_drag)
            label.bind("<B1-Motion>", self.on_label_drag)
            label.bind("<ButtonRelease-1>", self.stop_label_drag)
            label.configure(cursor="hand2")  # Change cursor to indicate draggable

    def disable_label_dragging(self):
        """Disable drag and drop for all labels"""
        for label in self.label_widgets.values():
            label.unbind("<Button-1>")
            label.unbind("<B1-Motion>")
            label.unbind("<ButtonRelease-1>")
            label.configure(cursor="")  # Reset cursor
            # Reset label position if it was placed on image
            if label in self.label_positions:
                label.place_forget()
                label.pack(side="left", padx=2)

    def start_label_drag(self, event):
        """Start dragging a label."""
        label = event.widget
        label._drag_start_x = event.x
        label._drag_start_y = event.y
        # Raise the label to the top of the stacking order
        label.lift()
        # Store original position
        label._original_position = (label.winfo_x(), label.winfo_y())

    def on_label_drag(self, event):
        """Handle label dragging."""
        label = event.widget
        # Calculate new position
        x = label.winfo_x() + event.x - label._drag_start_x
        y = label.winfo_y() + event.y - label._drag_start_y
        
        # Get image frame boundaries
        image_frame = self.image_frame
        frame_width = image_frame.winfo_width()
        frame_height = image_frame.winfo_height()
        
        # Keep label within image frame boundaries
        x = max(0, min(x, frame_width - label.winfo_width()))
        y = max(0, min(y, frame_height - label.winfo_height()))
        
        # Move the label
        label.place(in_=image_frame, x=x, y=y)

    def stop_label_drag(self, event):
        """Handle end of label drag."""
        label = event.widget
        
        # Get label position relative to image frame
        x = label.winfo_x()
        y = label.winfo_y()
        
        # Check if label is within image frame bounds
        if (0 <= x <= self.image_frame.winfo_width() and 
            0 <= y <= self.image_frame.winfo_height()):
            # Save the new position
            self.label_positions[label.cget('text')] = (x, y)
            print(f"Label {label.cget('text')} dropped at x={x}, y={y}")
        else:
            # Return label to label frame if dropped outside image
            label.place_forget()
            label.pack(in_=self.label_info_frame, side="left", padx=1)
            if label.cget('text') in self.label_positions:
                del self.label_positions[label.cget('text')]

    # Button command methods
    def auto_command(self):
        """Example of using the communication methods"""
        try:
            # Read PLC status
            plc_status = self.read_plc_data()
            
            # Read both loadcells
            lc1_value = self.read_loadcell(1)
            lc2_value = self.read_loadcell(2)
            
            # Update your UI with the values
            self.update_display(plc_status, lc1_value, lc2_value)
            
        except Exception as e:
            messagebox.showerror("Communication Error", str(e))

    def home_command(self):
        messagebox.showinfo("Home", "Returning to home position")

    def first_pull_command(self):
        messagebox.showinfo("1st Pull", "Performing load test")

    def second_pull_command(self):
        messagebox.showinfo("2nd Pull", "Performing length test")

    def test_result_command(self):
        messagebox.showinfo("Test Result", "Generating test results")

    def next_model_command(self):
        messagebox.showinfo("Next Model", "Moving to next model")

    def alc_code_command(self):
        messagebox.showinfo("ALC Code", "Opening ALC Code dialog")

    def load_image(self, image_path):
        try:
            # Open and resize the image to match frame dimensions
            image = Image.open(image_path)
            image = image.resize((750, 450), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(image)
            
            # Create or update the image label
            if hasattr(self, 'image_label'):
                self.image_label.configure(image=self.photo)
            else:
                self.image_label = tk.Label(self.image_frame, image=self.photo, bg='white')
                self.image_label.pack(expand=True, fill='both')
            
            # Update status
            self.status_label.config(text=f"Image loaded: {os.path.basename(image_path)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {str(e)}")
            self.status_label.config(text="Failed to load image")

    def setup_barcode_listener(self):
        """Alternative approach using tkinter bindings"""
        self.root.bind('<Key>', self.on_key_press)
        self.root.bind('<Return>', self.on_enter_press)

    def on_key_press(self, event):
        if event.char:
            self.barcode_data += event.char

    def on_enter_press(self, event):
        self.process_barcode_data()
        self.barcode_data = ""

    def process_barcode_data(self):
        """Process the captured barcode data."""
        barcode = self.barcode_data.strip()
        if not barcode:
            return
            
        # Check if we're waiting for employee code
        if not self.emp_entry.get() or self.emp_entry.get() == "EMP CODE":
            self.emp_entry.delete(0, tk.END)
            self.emp_entry.insert(0, barcode)
            self.validate_employee_code()
            
        # If ALC code is enabled and a barcode is scanned, process it
        elif self.alc_entry.cget('state') == 'normal':
            self.alc_entry.delete(0, tk.END)
            self.alc_entry.insert(0, barcode)
            self.process_alc_code()

    def load_configuration_data(self):
        """Load configuration data from txt_files subdirectory"""
        try:
            # Define the subdirectory path
            txt_files_dir = os.path.join(os.path.dirname(__file__), 'txt_files')
            
            # Ensure the directory exists
            if not os.path.exists(txt_files_dir):
                raise FileNotFoundError(f"Directory not found: {txt_files_dir}")
            
            # Load ProcessStatus
            process_status_path = os.path.join(txt_files_dir, 'ProcessStatus.txt')
            with open(process_status_path, 'r') as file:
                self.process_status_array = [line.strip() for line in file.readlines()]
            
            # Load ProgramSelectionInPLC
            program_selection_path = os.path.join(txt_files_dir, 'ProgramSelectionInPLC.txt')
            with open(program_selection_path, 'r') as file:
                self.program_selection_array = [line.strip() for line in file.readlines()]
            
            # Load InputSensors
            input_sensors_path = os.path.join(txt_files_dir, 'InputSensors.txt')
            with open(input_sensors_path, 'r') as file:
                self.input_sensors_array = [line.strip() for line in file.readlines()]
            
            # Load EmployeeCodes
            employee_codes_path = os.path.join(txt_files_dir, 'EmployeeCodes.txt')
            with open(employee_codes_path, 'r') as file:
                self.employee_codes = [line.strip() for line in file.readlines()]
            
            # Check if any array is empty
            if not all([self.process_status_array, self.program_selection_array, 
                       self.input_sensors_array, self.employee_codes]):
                messagebox.showwarning("Empty File", "One or more configuration files are empty.")
            
        except FileNotFoundError as e:
            messagebox.showerror("File Not Found", 
                               f"Configuration file not found in txt_files directory:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Error loading configuration data:\n{str(e)}")

    def connect_to_devices(self):
        """Connect to PLC and loadcells with improved error handling"""
        try:
            # Initialize clients as None first
            self.plc_client = None
            self.loadcell1_client = None
            self.loadcell2_client = None
            
            # Connect to PLC
            plc_port = os.getenv('PLC_COM_PORT')
            plc_baud = os.getenv('PLC_BAUD_RATE')
            plc_station_id = os.getenv('PLC_STATION_ID')
            
            if all([plc_port, plc_baud, plc_station_id]):
                try:
                    # Close any existing connection first
                    if hasattr(self, 'plc_client') and self.plc_client:
                        try:
                            if self.plc_client.is_socket_open():
                                self.plc_client.close()
                        except:
                            pass
                    
                    # Create new PLC client
                    self.plc_client = ModbusSerialClient(
                        port=plc_port,
                        baudrate=int(plc_baud),
                        timeout=1,
                        stopbits=1,
                        bytesize=8,
                        parity='N'
                    )
                    
                    # Attempt to connect with retries
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            if self.plc_client.connect():
                                # Test connection by reading a coil
                                test_response = self.plc_client.read_coils(
                                    address=0,
                                    count=1,
                                    slave=int(plc_station_id)
                                )
                                
                                if not test_response.isError():
                                    print(f"Successfully connected to PLC on {plc_port}")
                                    break
                        except Exception as e:
                            print(f"Attempt {attempt + 1} failed: {e}")
                            if attempt < max_retries - 1:
                                time.sleep(1)  # Wait before retrying
                            else:
                                raise Exception("Failed to establish PLC connection after multiple attempts")
                    
                except Exception as e:
                    print(f"PLC connection error: {e}")
                    messagebox.showwarning("Warning", f"Failed to connect to PLC: {str(e)}")
                    self.plc_client = None
            else:
                print("Missing PLC configuration in environment variables")
                messagebox.showwarning("Warning", "Missing PLC configuration in environment variables")

            # Connect to Loadcell 1
            lc1_port = os.getenv('LOADCELL_01_COM_PORT')
            lc1_baud = os.getenv('LOADCELL_01_BAUD_RATE')
            
            if all([lc1_port, lc1_baud]):
                try:
                    self.loadcell1_client = serial.Serial(
                        port=lc1_port,
                        baudrate=int(lc1_baud),
                        bytesize=8,
                        parity='N',
                        stopbits=1,
                        timeout=0.5
                    )
                except serial.SerialException as e:
                    print(f"Failed to connect to Loadcell 1: {e}")
                    messagebox.showwarning("Warning", f"Failed to connect to Loadcell 1 on {lc1_port}")
            
            # Connect to Loadcell 2
            lc2_port = os.getenv('LOADCELL_02_COM_PORT')
            lc2_baud = os.getenv('LOADCELL_02_BAUD_RATE')
            
            if all([lc2_port, lc2_baud]):
                try:
                    self.loadcell2_client = serial.Serial(
                        port=lc2_port,
                        baudrate=int(lc2_baud),
                        bytesize=8,
                        parity='N',
                        stopbits=1,
                        timeout=0.5
                    )
                except serial.SerialException as e:
                    print(f"Failed to connect to Loadcell 2: {e}")
                    messagebox.showwarning("Warning", f"Failed to connect to Loadcell 2 on {lc2_port}")
                    
        except Exception as e:
            print(f"Error connecting to devices: {str(e)}")
            messagebox.showerror("Connection Error", f"Failed to connect to devices: {str(e)}")

    def read_plc_data(self):
        """Read data from PLC with improved error handling"""
        try:
            if not self.plc_client:
                raise Exception("PLC client not initialized")
                
            if not self.plc_client.is_socket_open():
                # Attempt to reconnect
                if not self.plc_client.connect():
                    raise Exception("PLC not connected and reconnection failed")
                
            station_id = int(os.getenv('PLC_STATION_ID'))
            
            # Read process status
            response = self.plc_client.read_coils(
                address=0,
                count=1,
                slave=station_id
            )
            
            if response is None or response.isError():
                raise Exception("Error reading PLC data")
                
            return response.bits[0]
                
        except Exception as e:
            print(f"Error reading PLC: {str(e)}")
            return None

    def read_loadcell(self, loadcell_num):
        """Read data from specified loadcell"""
        try:
            client = self.loadcell1_client if loadcell_num == 1 else self.loadcell2_client
            
            if not client or not client.is_open:
                raise Exception(f"Loadcell {loadcell_num} not connected")
            
            # Clear buffers
            client.reset_input_buffer()
            client.reset_output_buffer()
            
            # Send command
            command = f"ID{loadcell_num:02d}P".encode()
            client.write(command)
            
            # Read response
            response = client.readline()
            if response:
                decoded = response.decode('utf-8', errors='replace').strip()
                parts = decoded.split(',')
                if len(parts) > 1:
                    return parts[1]  # Return the value part
            
            return None
            
        except Exception as e:
            print(f"Error reading Loadcell {loadcell_num}: {str(e)}")
            return None

    def cleanup(self):
        """Enhanced cleanup method with improved error handling"""
        try:
            # Stop all monitoring first
            self.keepWriting = False
            self.breakLoop = True
            
            # Stop all blinking labels
            if hasattr(self, 'blinking_labels'):
                for label in self.blinking_labels.values():
                    if hasattr(label, 'blink_job'):
                        self.root.after_cancel(label.blink_job)
                self.blinking_labels.clear()
            
            # Only close loadcell connections, keep PLC connection alive
            if hasattr(self, 'loadcell1_client') and self.loadcell1_client:
                try:
                    if self.loadcell1_client.is_open:
                        self.loadcell1_client.close()
                    print("Loadcell 1 connection closed successfully")
                except Exception as e:
                    print(f"Error closing Loadcell 1 connection: {e}")
                finally:
                    self.loadcell1_client = None
            
            if hasattr(self, 'loadcell2_client') and self.loadcell2_client:
                try:
                    if self.loadcell2_client.is_open:
                        self.loadcell2_client.close()
                    print("Loadcell 2 connection closed successfully")
                except Exception as e:
                    print(f"Error closing Loadcell 2 connection: {e}")
                finally:
                    self.loadcell2_client = None
                
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

    def retrieve_part_specifications(self, part_number):
        """Retrieve specifications and label coordinates from database."""
        try:
            # Connect to database with error handling
            try:
                conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="12345",
                    database="EOL"
                )
            except mysql.connector.Error as err:
                print(f"Database connection failed: {err}")
                messagebox.showerror("Database Error", "Failed to connect to database. Please check your database connection.")
                return

            cursor = conn.cursor(dictionary=True)  # Use dictionary cursor for clearer data access
            
            # Get image path and label coordinates
            master_query = """
            SELECT MM_IMAGE_PATH, MM_LABEL_COORDINATES, MM_MODEL_NAME, MM_PART_NUMBER
            FROM TBL_MODEL_MASTER 
            WHERE MM_PART_NUMBER = %s
            """
            cursor.execute(master_query, (part_number,))
            result = cursor.fetchone()
            
            if not result:
                messagebox.showwarning("Warning", f"No data found for part number: {part_number}")
                return
            
            # Store current part number
            self.current_part_number = result['MM_PART_NUMBER']
            
            # Update model header
            if result['MM_MODEL_NAME']:
                self.model_header.config(text=f"{result['MM_MODEL_NAME']} - {part_number}")
            
            # Load image if path exists
            if result['MM_IMAGE_PATH']:
                image_path = self.get_absolute_image_path(result['MM_IMAGE_PATH'])
                if not image_path or not os.path.exists(image_path):
                    messagebox.showwarning("Warning", f"Image file not found: {result['MM_IMAGE_PATH']}")
                else:
                    if self.load_image_with_path(image_path):
                        # After successful image load, place labels if coordinates exist
                        if result['MM_LABEL_COORDINATES']:
                            try:
                                coordinates_data = json.loads(result['MM_LABEL_COORDINATES'])
                                self.place_labels_from_positions(coordinates_data)
                            except json.JSONDecodeError as e:
                                print(f"Warning: Invalid label coordinate data: {e}")
                                messagebox.showwarning("Warning", "Invalid label coordinate data in database")
            
            # Get specifications
            spec_query = """
            SELECT 
                MS_DESCRIPTION,
                MS_DEVICE,
                MS_UNIT,
                CAST(MS_NORMAL_MIN AS DECIMAL(10,2)) as MIN_VAL,
                CAST(MS_NORMAL_MAX AS DECIMAL(10,2)) as MAX_VAL
            FROM TBL_MODEL_SPECIFICATION 
            WHERE MS_PART_NUMBER = %s
            ORDER BY MS_DEVICE
            """
            cursor.execute(spec_query, (part_number,))
            specs = cursor.fetchall()
            
            # Update specifications tree
            self.spec_tree.delete(*self.spec_tree.get_children())
            for spec in specs:
                values = (
                    spec['MS_DESCRIPTION'],
                    spec['MS_DEVICE'],
                    spec['MS_UNIT'],
                    f"{float(spec['MIN_VAL']):.2f}" if spec['MIN_VAL'] is not None else "N/A",
                    f"{float(spec['MAX_VAL']):.2f}" if spec['MAX_VAL'] is not None else "N/A",
                    "",  # Empty Actual column
                    ""   # Empty Result column
                )
                self.spec_tree.insert('', 'end', values=values)
            
            # Update status message
            self.message_label.config(
                text=f"Loaded specifications for {result['MM_MODEL_NAME']} - {part_number}",
                fg="green"
            )
            
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            messagebox.showerror("Database Error", f"Failed to retrieve data: {err}")
        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()

    def get_absolute_image_path(self, db_image_path):
        """Convert database image path to absolute path if needed"""
        if not db_image_path:
            return None
        
        # If path is already absolute, return it
        if os.path.isabs(db_image_path):
            return db_image_path
        
        # Otherwise, assume it's relative to the application directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, db_image_path)

    def load_image_with_path(self, image_path):
        """Load and fit image to match the exact dimensions of model_settings.py"""
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Get the frame dimensions
            frame_width = self.image_frame.winfo_width()
            frame_height = self.image_frame.winfo_height()
            
            print(f"Loading image with frame dimensions: {frame_width}x{frame_height}")
            
            # Load and resize image to exactly match model_settings.py dimensions
            original_image = Image.open(image_path)
            resized_image = original_image.resize((frame_width, frame_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(resized_image)
            
            # Remove old image label if it exists
            if hasattr(self, 'image_label'):
                self.image_label.destroy()
            
            # Create new image label with exact same dimensions
            self.image_label = tk.Label(self.image_frame, image=photo, bg='white')
            self.image_label.image = photo  # Keep a reference
            self.image_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Store image dimensions for label positioning
            self.image_dimensions = {
                'width': frame_width,
                'height': frame_height,
                'x_offset': 0,
                'y_offset': 0
            }
            
            # Force update of the display
            self.image_frame.update_idletasks()
            
            self.current_image_path = image_path
            print(f"Successfully loaded image: {image_path}")
            return True
            
        except Exception as e:
            print(f"Error loading image: {str(e)}")
            messagebox.showerror("Error", f"Error loading image: {str(e)}")
            return False

    def place_labels_from_positions(self, coordinates_data):
        """Place labels exactly according to database coordinates."""
        try:
            # Clear any existing placed labels
            for label in getattr(self, 'placed_labels', {}).values():
                label.destroy()
            self.placed_labels = {}
            
            print(f"Placing labels with coordinates: {coordinates_data}")
            
            # Get image frame dimensions for validation
            frame_width = self.image_frame.winfo_width()
            frame_height = self.image_frame.winfo_height()
            
            print(f"Image frame dimensions: {frame_width}x{frame_height}")
            
            # Create labels based on coordinates data
            for label_num, coord_data in coordinates_data.items():
                try:
                    # Get coordinates from database
                    x = float(coord_data.get('x', 0))
                    y = float(coord_data.get('y', 0))
                    
                    print(f"Processing label {label_num} at coordinates ({x}, {y})")
                    
                    # Validate coordinates are within frame bounds with margin
                    x = max(10, min(x, frame_width - 50))  # Leave margin on edges
                    y = max(10, min(y, frame_height - 30))  # Leave margin on edges
                    
                    # Create label with exact specifications
                    label_text = f'L{label_num}'
                    new_label = tk.Label(self.image_frame,
                                       text=label_text,
                                       bg="yellow",
                                       fg="black",
                                       font=("Arial", 10, "bold"),
                                       width=4,
                                       relief="raised",
                                       borderwidth=2)
                    
                    # Place label at exact coordinates
                    new_label.place(x=x, y=y)
                    new_label.lift()  # Ensure label is on top of image
                    
                    # Store the label and its position
                    self.placed_labels[label_text] = new_label
                    self.label_positions[label_text] = (x, y)
                    
                    print(f"Successfully placed {label_text} at coordinates x={x}, y={y}")
                    
                except Exception as e:
                    print(f"Error placing label {label_num}: {str(e)}")
                    continue
            
            # Update label info
            if self.placed_labels:
                sorted_labels = sorted(self.placed_labels.keys(), key=lambda x: int(x[1:]))
                self.label_info.config(text=f"Placed Labels: {', '.join(sorted_labels)}")
            else:
                self.label_info.config(text="Placed Labels: None")
                
            # Force update of the display
            self.image_frame.update_idletasks()
            
        except Exception as e:
            print(f"Error placing labels: {e}")
            messagebox.showerror("Error", f"Failed to place labels: {str(e)}")

    def get_status_label_color(self, label_text):
        """Return the color for each status label."""
        colors = {
            'HOME': '#4169E1',  # Royal Blue
            'AUTO': '#228B22',  # Forest Green
            'SEMI': '#DAA520',  # Goldenrod
            'MANU': '#B8860B',  # Dark Goldenrod
            'STOP': '#DC143C'   # Crimson
        }
        return colors.get(label_text, 'gray')

    def reset_labels(self):
        """Reset all labels to their original state"""
        # Clear any placed labels
        for label in getattr(self, 'placed_labels', {}).values():
            label.destroy()
        self.placed_labels = {}
        
        # Ensure original labels are visible in their container
        for label in self.label_widgets.values():
            label.pack(in_=self.label_info_frame, side="left", padx=2, expand=True)
        
        self.label_positions.clear()
        
        # Save the cleared positions to database
        if hasattr(self, 'current_part_number'):
            self.save_label_positions()

    # Example button command methods
    def button1_command(self):
        messagebox.showinfo("Button 1", "Button 1 pressed")

    def button2_command(self):
        messagebox.showinfo("Button 2", "Button 2 pressed")

    def button3_command(self):
        messagebox.showinfo("Button 3", "Button 3 pressed")

    def button4_command(self):
        messagebox.showinfo("Button 4", "Button 4 pressed")

    def button5_command(self):
        messagebox.showinfo("Button 5", "Button 5 pressed")

    def button6_command(self):
        messagebox.showinfo("Button 6", "Button 6 pressed")

    def save_label_positions(self):
        """Save current label positions to database."""
        if not hasattr(self, 'current_part_number') or not self.placed_labels:
            return

        positions = {}
        for label_text, label in self.placed_labels.items():
            if label_text.startswith('L'):
                label_num = label_text[1:]  # Extract number from "L1", "L2", etc.
                positions[label_num] = {
                    'x': label.winfo_x(),
                    'y': label.winfo_y(),
                    'text': label_text
                }

        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="12345",
                database="EOL"
            )
            cursor = conn.cursor()

            # Update the database with new positions
            positions_json = json.dumps(positions)
            update_query = """
            UPDATE TBL_MODEL_MASTER 
            SET MM_LABEL_COORDINATES = %s 
            WHERE MM_PART_NUMBER = %s
            """
            cursor.execute(update_query, (positions_json, self.current_part_number))
            conn.commit()

            cursor.close()
            conn.close()

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            messagebox.showerror("Database Error", f"Failed to save label positions: {err}")
        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def start_monitoring(self):
        """Start monitoring sensors and PLC status"""
        self.message_label.configure(text="Please Validate NG Cable...")
        self.startingNGCableValidation = True
        # Start your monitoring threads/processes here

    def on_emp_entry_focus(self, is_focused):
        """Handle employee code entry focus"""
        if is_focused:
            if self.emp_entry.get() == "EMP CODE":
                self.emp_entry.delete(0, tk.END)
            self.emp_entry.configure(bg="white")
        else:
            if not self.emp_entry.get():
                self.emp_entry.insert(0, "EMP CODE")
                self.emp_entry.configure(bg="white")

    def validate_employee_code(self, event=None):
        """Validate employee code against employecode.txt"""
        emp_code = self.emp_entry.get().strip()
        if emp_code == "EMP CODE" or not emp_code:
            messagebox.showwarning("Warning", "Please enter an employee code")
            return
        
        try:
            # Use the correct path in txt_files subdirectory
            employee_codes_path = os.path.join(os.path.dirname(__file__), 'txt_files', 'EmployeeCodes.txt')
            
            # Check if file exists
            if not os.path.exists(employee_codes_path):
                messagebox.showerror("Error", "Employee codes file not found in txt_files directory")
                return
            
            # Read from the correct file path
            with open(employee_codes_path, 'r') as file:
                valid_codes = [code.strip() for code in file.readlines()]
            
            if emp_code in valid_codes:
                messagebox.showinfo("Success", "Employee code validated successfully")
                self.alc_entry.configure(state='normal')  # Enable ALC entry
                self.emp_entry.configure(bg="lightgreen")
                self.alc_entry.focus_set()  # Set focus to ALC entry
            else:
                messagebox.showerror("Error", "Employee code unauthorized")
                self.alc_entry.configure(state='disabled')
                self.emp_entry.configure(bg="pink")
                
        except FileNotFoundError:
            messagebox.showerror("Error", "Employee codes file not found in txt_files directory")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def on_alc_entry_focus(self, is_focused):
        """Handle ALC entry focus with visual feedback"""
        if is_focused:
            if self.alc_entry.get() == "ALC CODE":
                self.alc_entry.delete(0, tk.END)
            self.alc_entry.configure(bg="white")
        else:
            if not self.alc_entry.get():
                self.alc_entry.insert(0, "ALC CODE")
                self.alc_entry.configure(bg="#fff9c4")

    def process_alc_code(self, event=None):
        """Process the entered ALC code and retrieve specifications"""
        alc_code = self.alc_entry.get().strip()
        if not alc_code or alc_code == "ALC CODE":
            messagebox.showwarning("Warning", "Please enter a valid ALC code")
            return

        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="12345",
                database="EOL"
            )
            cursor = conn.cursor(dictionary=True)

            # Get model information using ALC code
            model_query = """
            SELECT 
                MM_PART_NUMBER,
                MM_MODEL_NAME,
                MM_IMAGE_PATH,
                MM_LABEL_COORDINATES
            FROM TBL_MODEL_MASTER 
            WHERE MM_ALC_CODE = %s
            """
            cursor.execute(model_query, (alc_code,))
            model_result = cursor.fetchone()

            if not model_result:
                messagebox.showwarning("Warning", f"No data found for ALC code: {alc_code}")
                cursor.close()
                conn.close()
                return

            # Store current part number and update UI
            self.current_part_number = model_result['MM_PART_NUMBER']
            self.model_header.config(text=f"{model_result['MM_MODEL_NAME']} - {self.current_part_number}")
            
            # Get specifications using the part number
            spec_query = """
            SELECT 
                MS_DESCRIPTION as Description,
                MS_DEVICE as Device,
                MS_UNIT as Unit,
                CAST(MS_NORMAL_MIN AS DECIMAL(10,2)) as Min,
                CAST(MS_NORMAL_MAX AS DECIMAL(10,2)) as Max
            FROM TBL_MODEL_SPECIFICATION 
            WHERE MS_PART_NUMBER = %s
            ORDER BY MS_DEVICE
            """
            cursor.execute(spec_query, (self.current_part_number,))
            specs = cursor.fetchall()

            # Clear and update specifications tree
            self.spec_tree.delete(*self.spec_tree.get_children())
            for spec in specs:
                values = (
                    spec['Description'],
                    spec['Device'],
                    spec['Unit'],
                    f"{float(spec['Min']):.2f}" if spec['Min'] is not None else "N/A",
                    f"{float(spec['Max']):.2f}" if spec['Max'] is not None else "N/A",
                    "",  # Empty Actual column
                    ""   # Empty Result column
                )
                self.spec_tree.insert('', 'end', values=values)

            # Handle image loading and label placement
            if model_result['MM_IMAGE_PATH']:
                abs_image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), model_result['MM_IMAGE_PATH']))
                if os.path.exists(abs_image_path):
                    if self.load_image(abs_image_path):
                        if model_result['MM_LABEL_COORDINATES']:
                            try:
                                coordinates_data = json.loads(model_result['MM_LABEL_COORDINATES'])
                                self.place_labels_from_positions(coordinates_data)
                            except json.JSONDecodeError:
                                messagebox.showwarning("Warning", "Invalid label coordinate data")
                else:
                    messagebox.showwarning("Warning", f"Image not found: {abs_image_path}")

            # Update status message
            self.message_label.config(
                text=f"Model: {model_result['MM_MODEL_NAME']} | Part Number: {self.current_part_number}",
                fg="green"
            )

            cursor.close()
            conn.close()

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to retrieve data: {err}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def load_and_monitor_sensors(self):
        """Load and monitor input sensors and process status"""
        try:
            # Read input sensors file
            sensors_path = os.path.join(os.path.dirname(__file__), 'txt_files', 'InputSensors.txt')
            with open(sensors_path, 'r') as f:
                sensor_data = f.read().strip().split(',')
            
            # Read process status file
            status_path = os.path.join(os.path.dirname(__file__), 'txt_files', 'ProcessStatus.txt')
            with open(status_path, 'r') as f:
                process_data = f.read().strip().split(',')
            
            # Start monitoring sensors
            self.start_sensor_monitoring(sensor_data)
            
        except FileNotFoundError as e:
            messagebox.showerror("Error", f"Configuration file not found: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading configuration: {str(e)}")

    def start_sensor_monitoring(self, sensor_data):
        """Start monitoring sensors and update labels accordingly"""
        self.sensor_data = sensor_data
        self.blinking_labels = {}  # Store blinking label references
        
        # Map sensors to placed labels
        for i, (label_text, label_widget) in enumerate(self.placed_labels.items()):
            if i < len(sensor_data):
                self.setup_label_blinking(label_widget, i)
        
        # Start the monitoring loop
        self.monitor_sensors()

    def setup_label_blinking(self, label_widget, sensor_index):
        """Setup blinking for a label"""
        label_widget.blink_state = False
        label_widget.sensor_index = sensor_index
        label_widget.original_bg = label_widget.cget('bg')
        self.blinking_labels[id(label_widget)] = label_widget

    def monitor_sensors(self):
        """Monitor sensors and update label states"""
        try:
            # Read current sensor states
            with open(os.path.join(os.path.dirname(__file__), 'txt_files', 'InputSensors.txt'), 'r') as f:
                current_states = f.read().strip().split(',')
            
            # Update each label based on sensor state
            for label_widget in self.blinking_labels.values():
                sensor_index = label_widget.sensor_index
                if sensor_index < len(current_states):
                    if current_states[sensor_index].strip().upper() == 'HIGH':
                        # Stop blinking, set normal background
                        if hasattr(label_widget, 'blink_job'):
                            self.root.after_cancel(label_widget.blink_job)
                            delattr(label_widget, 'blink_job')
                        label_widget.configure(bg=label_widget.original_bg)
                    else:
                        # Start/continue blinking if not already blinking
                        if not hasattr(label_widget, 'blink_job'):
                            self.blink_label(label_widget)
            
            # Schedule next monitoring cycle
            self.root.after(100, self.monitor_sensors)  # Check every 100ms
            
        except Exception as e:
            print(f"Error monitoring sensors: {e}")

    def blink_label(self, label):
        """Make a label blink red"""
        if not hasattr(label, 'blink_state'):
            label.blink_state = False
        
        label.blink_state = not label.blink_state
        label.configure(bg='red' if label.blink_state else 'white')
        label.blink_job = self.root.after(500, lambda: self.blink_label(label))  # Blink every 500ms

    def test_plc_communication(self):
        """Test PLC communication by toggling P0000 input address"""
        try:
            if not self.plc_client or not self.plc_client.is_socket_open():
                messagebox.showerror("Error", "PLC not connected. Please check COM port settings.")
                return

            # Get the station ID from environment variable
            station_id = int(os.getenv('PLC_STATION_ID', '1'))

            # First read the current state of P0000
            read_response = self.plc_client.read_coils(
                address=0x0000,  # Change to your desired address
                count=1,
                slave=station_id
            )

            if read_response.isError():
                raise Exception(f"Failed to read P0000 state: {read_response}")

            current_state = read_response.bits[0]
            new_state = not current_state  # Toggle the state

            # Write the new state to P0000
            write_response = self.plc_client.write_coil(
                address=0x0000,  # Change to your desired address
                value=new_state,
                slave=station_id
            )

            if write_response.isError():
                raise Exception(f"Failed to write to P0000: {write_response}")

            # Read back to confirm the change
            verify_response = self.plc_client.read_coils(
                address=0x0000,
                count=1,
                slave=station_id
            )

            if verify_response.isError():
                raise Exception(f"Failed to verify P0000 state: {verify_response}")

            verified_state = verify_response.bits[0]

            # Show success message with state change
            messagebox.showinfo("Success", 
                f"P0000 state changed successfully!\n"
                f"Previous state: {'HIGH' if current_state else 'LOW'}\n"
                f"Current state: {'HIGH' if verified_state else 'LOW'}"
            )

            # Update button text to show current state
            self.test_plc_button.config(
                text=f"P0000: {'HIGH' if verified_state else 'LOW'}"
            )

            # Flash the button to indicate success
            self.flash_button_success()

        except Exception as e:
            messagebox.showerror("Communication Error", f"Failed to communicate with PLC:\n{str(e)}")
            self.flash_button_failure()

    def flash_button_success(self):
        """Visual feedback for successful communication"""
        def reset_colors():
            self.test_plc_button.config(bg="#4CAF50")  # Reset button color
            self.status_label.config(fg="green")  # Keep status indicator green
        
        self.test_plc_button.config(bg="#00FF00")  # Bright green for success
        self.status_label.config(fg="#00FF00")  # Bright green for status
        self.root.after(200, reset_colors)

    def flash_button_failure(self):
        """Visual feedback for failed communication"""
        def reset_colors():
            self.test_plc_button.config(bg="#4CAF50")  # Reset button color
            self.status_label.config(fg="red")  # Keep status indicator red
        
        self.test_plc_button.config(bg="#FF0000")  # Red for failure
        self.status_label.config(fg="#FF0000")  # Red for status
        self.root.after(200, reset_colors)

    def monitor_p0000_state(self):
        """Continuously monitor P0000 state"""
        try:
            if self.plc_client and self.plc_client.is_socket_open():
                station_id = int(os.getenv('PLC_STATION_ID', '1'))
                
                response = self.plc_client.read_coils(
                    address=0x0000,
                    count=1,
                    slave=station_id
                )
                
                if not response.isError():
                    state = response.bits[0]
                    self.test_plc_button.config(
                        text=f"P0000: {'HIGH' if state else 'LOW'}"
                    )
                    self.status_label.config(
                        fg="green" if state else "gray"
                    )
            
        except Exception as e:
            print(f"Monitoring error: {e}")
            self.status_label.config(fg="red")
        
        # Schedule next update
        self.root.after(1000, self.monitor_p0000_state)  # Update every second

    def start_check_async(self):
        """Main monitoring and test sequence"""
        try:
            # Reset message label
            self.message_label.config(text="")
            
            # Initial readings
            self.read_plc_coils()
            self.read_sensor_inputs()
            
            # Start continuous monitoring loop
            self.keepWriting = True
            self.monitor_serial_ports()
            
            # Handle NG validation
            if self.startingNGCableValidation:
                self.root.after(2000, self.validate_ng_cable)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error in monitoring sequence: {str(e)}")

    def monitor_serial_ports(self):
        """Continuous monitoring of serial ports"""
        try:
            if self.keepWriting and not self.breakLoop:
                # Send commands to loadcells
                if self.loadcell1_client and self.loadcell1_client.is_open:
                    self.loadcell1_client.write(b"ID01P")
                if self.loadcell2_client and self.loadcell2_client.is_open:
                    self.loadcell2_client.write(b"ID02P")
                
                # Read responses
                self.read_loadcell_data()
                
                # Schedule next check
                if not self.breakLoop and self.noOfValues == 0:
                    self.root.after(50, self.monitor_serial_ports)
                
        except Exception as e:
            print(f"Error monitoring ports: {e}")

    def process_test_results(self):
        """Process and validate test results"""
        try:
            # Only process if we have actual values
            if self.noOfValues == 0:
                return
            
            self.failCounter = 0
            has_actual_values = False
            
            # Process each specification
            for item in self.spec_tree.get_children():
                values = self.spec_tree.item(item)['values']
                device = values[1]
                actual = values[5]
                
                if actual:  # Only process if there's an actual value
                    has_actual_values = True
                    min_val = float(values[3]) if values[3] != "N/A" else None
                    max_val = float(values[4]) if values[4] != "N/A" else None
                    
                    if min_val is not None and max_val is not None:
                        actual_val = float(actual)
                        if min_val <= actual_val <= max_val:
                            self.update_specification_result(device, actual, "PASS")
                else:
                            self.update_specification_result(device, actual, "NG")
                            self.failCounter += 1
            
            # Update UI based on results only if we have processed values
            if has_actual_values:
                if self.failCounter > 0:
                    self.message_label.config(text="Test Failed - NG", fg="red")
                else:
                    self.message_label.config(text="Test Passed - OK", fg="green")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error processing results: {str(e)}")

    def validate_ng_cable(self):
        """Handle NG cable validation"""
        try:
            if self.startingNGCableValidation:
                if self.failCounter > 0:
                    messagebox.showinfo("Validation", "NG Validation successful")
                    self.startingNGCableValidation = False
                else:
                    if messagebox.askyesno("Validation", "No failures detected. Repeat validation?"):
                        self.start_check_async()
                    else:
                        self.startingNGCableValidation = False
                    
            elif self.endingNGCableValidation:
                if self.failCounter > 0:
                    self.reset_plc()
                else:
                    if messagebox.askyesno("Validation", "No failures detected. Repeat validation?"):
                        self.start_check_async()
                    else:
                        self.endingNGCableValidation = False
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error in validation: {str(e)}")

    def reset_plc(self):
        """Reset PLC to initial state"""
        try:
            if self.plc_client and self.plc_client.is_socket_open():
                station_id = int(os.getenv('PLC_STATION_ID', '1'))
                
                # Write 0 to all relevant coils
                for address in range(10):  # Adjust range as needed
                    self.plc_client.write_coil(
                        address=address,
                        value=False,
                        slave=station_id
                    )
                
                messagebox.showinfo("PLC Reset", "PLC has been reset successfully")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to reset PLC: {str(e)}")

    def read_loadcell_data(self):
        """Read and process loadcell data"""
        try:
            for i, client in enumerate([self.loadcell1_client, self.loadcell2_client], 1):
                if client and client.is_open:
                    response = client.readline()
                    if response:
                        decoded = response.decode('utf-8', errors='replace').strip()
                        parts = decoded.split(',')
                        if len(parts) > 1:
                            value = float(parts[1])
                            # Update specification tree with actual value
                            self.update_specification_result(f"L{i}", value, "")
                            self.noOfValues += 1
                            
        except Exception as e:
            print(f"Error reading loadcell data: {e}")

    def read_plc_coils(self):
        """Read all configured coils from PLC"""
        try:
            if not self.plc_client or not self.plc_client.is_socket_open():
                raise Exception("PLC not connected")
            
            station_id = int(os.getenv('PLC_STATION_ID', '1'))
            
            # Read process status addresses
            for address_str in self.process_status_array:
                try:
                    # Split if comma-separated
                    addresses = [addr.strip() for addr in address_str.split(',')]
                    
                    for address in addresses:
                        if not address:
                            continue
                            
                        # Extract hex part based on prefix
                        if address.startswith('M'):
                            hex_part = address[1:]  # Remove 'M'
                        else:
                            print(f"Invalid address format: {address}")
                            continue
                        
                        try:
                            coil_address = int(hex_part, 16)
                        except ValueError:
                            print(f"Invalid hex value: {hex_part}")
                            continue
                        
                        response = self.plc_client.read_coils(
                            address=coil_address,
                            count=1,
                            slave=station_id
                        )
                        
                        if not response.isError():
                            status = response.bits[0]
                            print(f"Address {address}: {'ON' if status else 'OFF'}")
                        else:
                            print(f"Error reading coil {address}")
                    
                except Exception as e:
                    print(f"Error reading coil {address_str}: {str(e)}")
                
            return True
            
        except Exception as e:
            print(f"Error reading PLC coils: {str(e)}")
            return False

    def read_sensor_inputs(self):
        """Read all configured sensor inputs"""
        try:
            if not self.plc_client or not self.plc_client.is_socket_open():
                raise Exception("PLC not connected")
            
            station_id = int(os.getenv('PLC_STATION_ID', '1'))
            
            # Read input sensor addresses
            for address_str in self.input_sensors_array:
                try:
                    # Split if comma-separated
                    addresses = [addr.strip() for addr in address_str.split(',')]
                    
                    for address in addresses:
                        if not address:
                            continue
                            
                        # Extract hex part based on prefix
                        if address.startswith('P'):
                            hex_part = address[1:]  # Remove 'P'
                        else:
                            print(f"Invalid address format: {address}")
                            continue
                        
                        try:
                            input_address = int(hex_part, 16)
                        except ValueError:
                            print(f"Invalid hex value: {hex_part}")
                            continue
                        
                        response = self.plc_client.read_discrete_inputs(
                            address=input_address,
                            count=1,
                            slave=station_id
                        )
                        
                        if not response.isError():
                            status = response.bits[0]
                            print(f"Sensor {address}: {'ON' if status else 'OFF'}")
                        else:
                            print(f"Error reading sensor {address}")
                    
                except Exception as e:
                    print(f"Error reading sensor {address_str}: {str(e)}")
                
            return True
            
        except Exception as e:
            print(f"Error reading sensor inputs: {str(e)}")
            return False

    def reconnect_plc(self):
        """Attempt to reconnect to PLC"""
        try:
            if self.plc_client:
                if self.plc_client.is_socket_open():
                    self.plc_client.close()
                
                if self.plc_client.connect():
                    # Test connection
                    station_id = int(os.getenv('PLC_STATION_ID', '1'))
                    test_response = self.plc_client.read_coils(
                        address=0,
                        count=1,
                        slave=station_id
                    )
                    
                    if not test_response.isError():
                        print("Successfully reconnected to PLC")
                        return True
            
            # If reconnection failed or no client exists, try full connection
            self.connect_to_devices()
            return self.plc_client and self.plc_client.is_socket_open()
            
        except Exception as e:
            print(f"Error reconnecting to PLC: {e}")
            return False

def main():
    root = tk.Tk()
    app = EOLTesterGUI(root)
    # Add this line to ensure cleanup on window close
    root.protocol("WM_DELETE_WINDOW", lambda: [app.cleanup(), root.destroy()])
    root.mainloop()

if __name__ == "__main__":
    main()


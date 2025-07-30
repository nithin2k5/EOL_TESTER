import tkinter as tk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
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
import traceback
from datetime import datetime
import random
import sys

class EOLTesterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EOL (END OF LINE) TESTER")
        
        # Initialize variables before setting up the window
        self.initialize_variables()
        
        # Set up the window after initialization
        self.root.after(100, self.setup_window)  # Delay window setup slightly
        
        # Set up window closing handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Continue with the rest of your initialization...

    def check_serial_module(self):
        """Check if PySerial is properly installed and functioning"""
        try:
            import serial
            import serial.tools.list_ports
            print(f"PySerial version: {serial.VERSION}")
            return True
        except ImportError as e:
            print(f"PySerial not properly installed: {e}")
            print("Please install PySerial with: pip install pyserial")
            messagebox.showerror("Error", "PySerial module not properly installed. Please install it with: pip install pyserial")
            return False
        except Exception as e:
            print(f"Error checking PySerial: {e}")
            return False
            
    def get_available_ports(self):
        """Get a list of available serial ports on the current platform"""
        if not self.check_serial_module():
            return []
            
        try:
            available_ports = []
            # Use serial.tools.list_ports to get available ports
            import serial.tools.list_ports
            ports = list(serial.tools.list_ports.comports())
            for port in ports:
                available_ports.append(port.device)
            
            if not available_ports:
                print("No serial ports found")
                return []
                
            print(f"Available ports: {available_ports}")
            return available_ports
        except Exception as e:
            print(f"Error getting available ports: {e}")
            return []

    def ensure_env_file_exists(self):
        """Ensure that the .env file exists and create it if it doesn't"""
        env_file = '.env'
        if not os.path.exists(env_file):
            print(f"Creating new {env_file} file")
            
            # Get available ports
            available_ports = self.get_available_ports()
            default_port = available_ports[0] if available_ports else ""
            
            with open(env_file, 'w') as f:
                f.write('# PLC Connection Settings\n')
                f.write(f'PLC_COM_PORT={default_port}\n')
                f.write('PLC_BAUD_RATE=38400\n')
                f.write('PLC_STATION_ID=1\n')
                f.write('# Loadcell Settings\n')
                f.write('LOADCELL_01_COM_PORT=\n')
                f.write('LOADCELL_01_BAUD_RATE=\n')
                f.write('LOADCELL_02_COM_PORT=\n')
                f.write('LOADCELL_02_BAUD_RATE=\n')
                f.write('# Machine Settings\n')
                f.write('MACHINE_ID=\n')
        return env_file

    def reload_env_settings(self):
        """Force reload environment settings from .env file"""
        try:
            env_file = '.env'
            if os.path.exists(env_file):
                # Clear existing environment variables
                for key in ['PLC_COM_PORT', 'PLC_BAUD_RATE', 'PLC_STATION_ID']:
                    if key in os.environ:
                        del os.environ[key]
                
                # Force reload from file
                load_dotenv(dotenv_path=env_file, override=True)
                print("Environment variables reloaded from .env file")
                
                # Print current settings for debugging
                plc_port = os.getenv('PLC_COM_PORT', '')
                plc_baud = os.getenv('PLC_BAUD_RATE', '')
                plc_station_id = os.getenv('PLC_STATION_ID', '')
                print(f"Reloaded settings: Port={plc_port}, Baud={plc_baud}, Station ID={plc_station_id}")
                
                return True
            else:
                print("No .env file found to reload")
                return False
        except Exception as e:
            print(f"Error reloading environment settings: {str(e)}")
            return False

    def initialize_variables(self):
        """Initialize all variables before window setup and ensure clean COM ports"""
        # Initialize UI-related variables
        self.image_label = None
        self.current_image = None
        self.label_positions = {}
        self.selected_label = None
        self.barcode_data = ""
        self.label_widgets = {}
        
        # Initialize container references (will be properly created in setup_window)
        self.main_container = None
        self.message_label = None
        self.workspace = None
        
        # Clear any previous connections
        self.plc_client = None
        self.loadcell1_client = None
        self.loadcell2_client = None
        
        # Ensure .env file exists and load environment variables
        env_file = self.ensure_env_file_exists()
        load_dotenv(dotenv_path=env_file, override=True)
        
        # Attempt to force-clean COM ports at startup
        try:
            plc_port = os.getenv('PLC_COM_PORT')
            if plc_port:
                try:
                    # Try direct port open/close to force release
                    test_serial = serial.Serial(plc_port)
                    test_serial.close()
                    print(f"Startup: Successfully released {plc_port}")
                except:
                    print(f"Startup: COM port {plc_port} may be in use by another application")
        except:
            pass
        
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
        
        # Initialize blinking jobs tracking
        self.blinking_jobs = {}
        
        # Initialize timers
        self.alc_timer = None
        self.alcInput_TimeInterval = 200  # milliseconds
        
        # Track test result states to prevent duplicate saves
        self.last_test_result_pass_state = False
        self.last_test_result_ng_state = False
        self.test_result_saved = False

    def setup_window(self):
        """Set up the window after initialization"""
        # Change from fullscreen to maximized state
        self.root.state('zoomed')  # Replace fullscreen with maximized state
        self.root.lift()  # Bring window to front
        self.root.focus_force()  # Force focus
        
        # Create the main_container first to ensure it exists before other operations
        # Create main container
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)

        # Add message label for status updates
        self.message_label = tk.Label(self.main_container, text="Initializing...", font=("Arial", 10))
        self.message_label.pack(fill="x", pady=2)
        
        # Ensure .env file exists and load environment variables
        env_file = self.ensure_env_file_exists()
        load_dotenv(dotenv_path=env_file, override=True)
        
        # Load data after environment variables are loaded
        self.load_configuration_data()
        
        # Set up GUI components before connecting to devices
        self.setup_gui()
        self.setup_barcode_listener()
        
        # Connect to devices after GUI is set up
        self.connect_to_devices()
        
        # Start monitoring only if PLC is connected
        if hasattr(self, 'plc_client') and self.plc_client and self.plc_client.is_socket_open():
            self.monitor_p0000_state()
            self.start_check_async()
            print("Started monitoring - PLC is connected")
        else:
            print("Monitoring not started - PLC is not connected")
            # Start monitoring anyway to show disconnected state
            self.monitor_p0000_state()
        
        # Ensure window stays on top during initialization
        self.root.after(500, lambda: self.root.attributes('-topmost', False))

    def setup_gui(self):
        # Main container and message label are already created in setup_window
        # Do not recreate them here
        
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
        
        # Add PLC Control Button (left side, after logo)
        self.plc_control_button = tk.Button(
            title_frame,
            text="SET HIGH",  # Initial state
            bg="#4CAF50",  # Green background
            fg="white",
            font=("Arial", 10, "bold"),
            relief="raised",
            command=self.toggle_plc_state,
            width=12,
            height=1
        )
        self.plc_control_button.pack(side="left", padx=5)
        
        # Add Reconnect PLC Button
        self.reconnect_button = tk.Button(
            title_frame,
            text="RECONNECT",
            bg="#FF9800",  # Orange background
            fg="white",
            font=("Arial", 9, "bold"),
            relief="raised",
            command=self.manual_reconnect_plc,
            width=10,
            height=1
        )
        self.reconnect_button.pack(side="left", padx=5)
        
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

        # Add hover effects for buttons
        def plc_button_enter(e):
            current_bg = self.plc_control_button.cget('bg')
            if current_bg == "#4CAF50":  # Green (LOW state)
                self.plc_control_button.config(bg="#45a049")
            elif current_bg == "#FF5722":  # Red (HIGH state)
                self.plc_control_button.config(bg="#E64A19")
            
        def plc_button_leave(e):
            # Only reset if PLC is connected, otherwise let monitor update it
            if hasattr(self, 'plc_client') and self.plc_client and self.plc_client.is_socket_open():
                try:
                    # Don't change color on leave, let the monitor handle it
                    pass
                except:
                    pass
        
        self.plc_control_button.bind('<Enter>', plc_button_enter)
        self.plc_control_button.bind('<Leave>', plc_button_leave)
        
        self.reconnect_button.bind('<Enter>', lambda e: self.reconnect_button.config(bg="#F57C00"))
        self.reconnect_button.bind('<Leave>', lambda e: self.reconnect_button.config(bg="#FF9800"))

    def manual_reconnect_plc(self):
        """Manual PLC reconnection triggered by user"""
        try:
            self.safe_update_message("Reloading settings and reconnecting to PLC...", "blue")
            self.reconnect_button.config(bg="#FFC107", text="CONNECTING...")
            self.root.update()  # Force UI update
            
            # Force reload environment settings first
            reload_success = self.reload_env_settings()
            if not reload_success:
                self.safe_update_message("Failed to reload settings", "red")
                self.reconnect_button.config(bg="#F44336", text="FAILED")
                self.root.after(2000, lambda: self.reconnect_button.config(bg="#FF9800", text="RECONNECT"))
                messagebox.showerror("Error", "Failed to reload settings from .env file")
                return
            
            # Attempt reconnection with fresh settings
            success = self.auto_connect_plc()
            
            if success:
                self.safe_update_message("PLC reconnected successfully with saved settings", "green")
                self.reconnect_button.config(bg="#4CAF50", text="CONNECTED")
                self.root.after(2000, lambda: self.reconnect_button.config(bg="#FF9800", text="RECONNECT"))
                messagebox.showinfo("Success", "PLC reconnected successfully with saved settings!")
            else:
                self.safe_update_message("PLC reconnection failed", "red") 
                self.reconnect_button.config(bg="#F44336", text="FAILED")
                self.root.after(2000, lambda: self.reconnect_button.config(bg="#FF9800", text="RECONNECT"))
                messagebox.showerror("Error", "Failed to reconnect to PLC. Please check COM port settings.")
                
        except Exception as e:
            print(f"Error in manual reconnect: {str(e)}")
            self.safe_update_message(f"Reconnection error: {str(e)}", "red")
            self.reconnect_button.config(bg="#F44336", text="ERROR")
            self.root.after(2000, lambda: self.reconnect_button.config(bg="#FF9800", text="RECONNECT"))
            messagebox.showerror("Error", f"Reconnection failed: {str(e)}")

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
        spec_frame.pack(fill="both", expand=True, padx=2, pady=2)  # Add padding
        
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
                       foreground="black",  # Text color
                       rowheight=30)  # Increase row height to fill space better
        
        style.configure("Custom.Treeview.Heading",
                       borderwidth=1,
                       relief="solid",
                       background="#e0e0e0",  # Light gray header background
                       foreground="black",  # Header text color
                       font=("Arial", 9, "bold"))  # Header font
        
        # Configure selection colors
        style.map("Custom.Treeview",
                 background=[("selected", "#cce5ff")],  # Light blue for selected row
                 foreground=[("selected", "black")])
        
        # Create Treeview with custom style - LIMIT TO 8 ROWS as requested
        self.spec_tree = ttk.Treeview(spec_frame, 
                                     columns=columns, 
                                     show="headings", 
                                     height=8,  # Fixed at 8 rows as requested
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
        
        # Pack the treeview to fill the available space without scrollbars
        self.spec_tree.pack(fill="both", expand=True)
        
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
        self.cam_textbox = tk.Text(camera_container, width=40, height=5.5)
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
        
        # Default columns: LOT NUMBER, L1, L2, P1, P2, RESULT, SCAN RESULT
        self.default_columns = ["LOT NUMBER", "L1", "L2", "P1", "P2", "RESULT", "SR"]
        self.current_columns = self.default_columns.copy()
        
        # Store references to header labels so we can update them later
        self.header_labels = {}
        for col in self.current_columns:
            label = tk.Label(header_frame, 
                           text=col, 
                           bg="#1e88e5",     
                           fg="white",        
                           font=("Arial", 9, "bold"))
            label.pack(side="left", expand=True, fill="x", padx=2, pady=3)
            self.header_labels[col] = label
        
        # Main content frame to hold grid and entry fields
        content_frame = tk.Frame(q4, bg="#f5f5f5")
        content_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Configure grid for main content
        content_frame.grid_rowconfigure(0, weight=1)  # Treeview gets most space
        content_frame.grid_rowconfigure(1, weight=0)  # Entry frame gets fixed space
        content_frame.grid_columnconfigure(0, weight=1)  # Single column takes full width
        
        # Create lot number tree view with frame - in the first row
        # Set a fixed width for the grid frame to prevent expansion
        self.grid_frame = tk.Frame(content_frame, bg="#f5f5f5", width=800)
        self.grid_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 5))
        self.grid_frame.grid_propagate(False)  # Prevent the frame from resizing
        
        # Configure style for the lot number tree view
        style = ttk.Style()
        style.configure("LotTree.Treeview",
                       borderwidth=1,
                       relief="solid",
                       fieldbackground="#ffffff", 
                       background="#ffffff",
                       rowheight=25,  # Increase row height
                       font=("Arial", 10))
                       
        style.configure("LotTree.Treeview.Heading",
                       borderwidth=1,
                       relief="solid",
                       background="#f0f0f0",
                       foreground="#000000",
                       font=("Arial", 9, "bold"))
                       
        # Configure selection colors
        style.map("LotTree.Treeview",
                 background=[("selected", "#e6f2ff")],
                 foreground=[("selected", "#000000")])
        
        # Store the fixed width we want for our tree
        self.tree_fixed_width = 780  # Slightly less than frame width to account for padding
        
        # Create Treeview with default columns
        self.create_lot_tree(self.grid_frame, self.current_columns)
        
        # Bottom frame for entry fields - in the second row
        entry_frame = tk.Frame(content_frame, bg="#f5f5f5", height=50)  # Reduced height
        entry_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        entry_frame.grid_propagate(False)  # Prevent shrinking
        
        # Simplified layout with just the entry fields
        input_frame = tk.Frame(entry_frame, bg="#f5f5f5") 
        input_frame.pack(fill="both", expand=True, pady=5)
        
        # Configure equal column weights
        input_frame.columnconfigure(0, weight=1)  # EMP CODE
        input_frame.columnconfigure(1, weight=1)  # NEXT LABEL button
        input_frame.columnconfigure(2, weight=1)  # ALC CODE
        
        # Employee Code Entry
        self.emp_entry = tk.Entry(input_frame,
                                 bg="white",
                                 fg="#424242",
                                 font=("Arial", 9, "bold"),
                                 justify="center",
                                 relief="flat",
                                 width=15)
        self.emp_entry.grid(row=0, column=0, padx=5, sticky="ew")
        self.emp_entry.insert(0, "EMP CODE")
        self.emp_entry.configure(highlightthickness=1,
                               highlightbackground="#e0e0e0",
                               highlightcolor="#1e88e5")
        
        # Next Label Button (centered)
        next_btn = tk.Button(input_frame,
                            text="NEXT LABEL ➜",
                            bg="#ffd700",
                            fg="#000000",
                            relief="flat",
                            font=("Arial", 9, "bold"),
                            cursor="hand2",
                            command=self.next_label_command,
                            pady=2)
        next_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Add hover effect
        next_btn.bind('<Enter>', lambda e: next_btn.configure(bg="#ffeb3b"))
        next_btn.bind('<Leave>', lambda e: next_btn.configure(bg="#ffd700"))
        
        # ALC Code Entry (initially disabled)
        self.alc_entry = tk.Entry(input_frame,
                                 bg="white",
                                 fg="black",
                                 font=("Arial", 9, "bold"),
                                 justify="center",
                                 relief="flat",
                                 width=15,
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
        
    def create_lot_tree(self, parent_frame, columns):
        """Create the lot tree with specified columns"""
        # Configure base column widths
        self.base_column_widths = {
            "LOT NUMBER": 150,
            "L1": 60,
            "L2": 60,
            "L3": 60,
            "L4": 60,
            "P1": 60,
            "P2": 60,
            "P3": 60,
            "P4": 60,
            "RESULT": 80,
            "SCAN RESULT": 100
        }
        
        # Get the fixed width we established
        tree_width = self.tree_fixed_width
        
        # Calculate how to distribute widths
        column_widths = self.adjust_column_widths(columns, tree_width)
        
        # Create Treeview with the specified columns
        self.tree = ttk.Treeview(parent_frame, 
                                columns=columns,
                                show="headings",
                                height=10,
                                style="LotTree.Treeview")
        
        # Set up columns with strict widths
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 60), anchor="center", stretch=False)
        
        # Pack tree without scrollbar
        self.tree.pack(side="left", fill="both", expand=True)
        
        # Configure scrolling using only the mouse wheel
        def on_mousewheel(event):
            # For Windows
            self.tree.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def on_mousewheel_linux(event):
            # For Linux
            if event.num == 4:
                self.tree.yview_scroll(-1, "units")
            elif event.num == 5:
                self.tree.yview_scroll(1, "units")
        
        # Add keyboard-based scrolling
        def on_up_arrow(event):
            self.tree.yview_scroll(-1, "units")
            return "break"  # Prevent default behavior
            
        def on_down_arrow(event):
            self.tree.yview_scroll(1, "units")
            return "break"  # Prevent default behavior
            
        def on_page_up(event):
            self.tree.yview_scroll(-10, "units")
            return "break"
            
        def on_page_down(event):
            self.tree.yview_scroll(10, "units")
            return "break"
        
        # Bind wheel events based on platform
        if sys.platform == "win32":
            self.tree.bind("<MouseWheel>", on_mousewheel)
        else:
            self.tree.bind("<Button-4>", on_mousewheel_linux)
            self.tree.bind("<Button-5>", on_mousewheel_linux)
            
        # Add keyboard navigation
        self.tree.bind("<Up>", on_up_arrow)
        self.tree.bind("<Down>", on_down_arrow)
        self.tree.bind("<Prior>", on_page_up)  # Page Up
        self.tree.bind("<Next>", on_page_down)  # Page Down
        
        # Bind double-click event to view details
        self.tree.bind("<Double-1>", self.on_tree_double_click)

    def adjust_column_widths(self, columns, available_width=800):
        """Adjust column widths proportionally to fit within available space"""
        # We're not accounting for scrollbar width since it's invisible now
        adjusted_available_width = available_width
        
        # Calculate total width of all columns using base widths
        total_base_width = sum(self.base_column_widths.get(col, 60) for col in columns)
        
        # Always adjust columns to fit the available width exactly
        scale_factor = adjusted_available_width / total_base_width
        adjusted_widths = {
            col: max(40, int(self.base_column_widths.get(col, 60) * scale_factor)) 
            for col in columns
        }
        
        # Ensure the total width is exactly equal to the available width
        total_adjusted = sum(adjusted_widths.values())
        diff = adjusted_available_width - total_adjusted
        
        # Distribute any remaining pixels to priority columns
        if diff != 0:
            # Priority order for adjustment
            priority_cols = ["LOT NUMBER", "RESULT", "SCAN RESULT", "L1", "P1", "L2", "P2", "L3", "L4", "P3", "P4"]
            # Filter to only include columns that exist in our current set
            priority_cols = [col for col in priority_cols if col in columns]
            
            # Add or subtract pixels one by one following priority
            idx = 0
            while diff != 0 and priority_cols:
                col = priority_cols[idx % len(priority_cols)]
                if diff > 0:
                    adjusted_widths[col] += 1
                    diff -= 1
                else:
                    if adjusted_widths[col] > 40:  # Don't go below minimum width
                        adjusted_widths[col] -= 1
                        diff += 1
                idx += 1
        
        return adjusted_widths

    def update_tree_columns(self, devices):
        """Update tree columns based on available devices"""
        # Determine which columns to show based on available devices
        new_columns = ["LOT NUMBER"]
        
        # Always include L1, L2, P1, P2
        for device in ["L1", "L2", "P1", "P2"]:
            new_columns.append(device)
        
        # Add L3, L4, P3, P4 if they exist in devices
        for device in ["L3", "L4", "P3", "P4"]:
            if device in devices:
                new_columns.append(device)
        
        # Always include RESULT and SCAN RESULT
        new_columns.extend(["RESULT", "SCAN RESULT"])
        
        # Check if columns are different from current ones
        if set(new_columns) != set(self.current_columns):
            print(f"Updating columns from {self.current_columns} to {new_columns}")
            
            # Save current data
            current_data = []
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                current_data.append((item, values))
            
            # Destroy and recreate tree with new columns
            self.tree.destroy()
            self.create_lot_tree(self.grid_frame, new_columns)
            
            # Update header frame labels
            # First hide all labels
            for label in self.header_labels.values():
                label.pack_forget()
            
            # Then show only the labels for current columns
            for col in new_columns:
                if col in self.header_labels:
                    self.header_labels[col].pack(side="left", expand=True, fill="x")
            
            # Store new columns
            self.current_columns = new_columns
            
            # Try to restore data with mapping to new columns
            self.load_history_to_treeview()
            
            print(f"Tree columns updated to: {new_columns}")
            
            # Force the frame to maintain its fixed size
            self.grid_frame.config(width=800)
            self.grid_frame.grid_propagate(False)
            
            # Make sure the tree uses the whole fixed width
            total_width = sum(int(self.tree.column(col, "width")) for col in new_columns)
            if total_width != self.tree_fixed_width:  # No need to adjust for scrollbar width
                # Recalculate column widths to match exactly
                new_widths = self.adjust_column_widths(new_columns, self.tree_fixed_width)
                # Apply the exact widths to prevent width creep
                for col, width in new_widths.items():
                    self.tree.column(col, width=width, stretch=False)
            
            # Force layout update
            self.grid_frame.update_idletasks()

    def on_tree_double_click(self, event):
        """Handle double-click on treeview item"""
        try:
            item = self.tree.selection()[0]
            values = self.tree.item(item, "values")
            lot_number = values[0]
            
            # Build message based on current columns
            message = f"Lot: {lot_number}"
            
            # Add values for each column except LOT NUMBER
            for i, col in enumerate(self.current_columns[1:], 1):
                if i < len(values):
                    message += f", {col}: {values[i]}"
            
            self.safe_update_message(message, "blue")
        except IndexError:
            # No item selected
            pass
        except Exception as e:
            print(f"Error on tree double-click: {str(e)}")
            self.safe_update_message(f"Error displaying details: {str(e)}", "red")

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
        frame_width = self.image_frame.winfo_width()
        frame_height = self.image_frame.winfo_height()
        
        # Keep label within image frame boundaries
        x = max(0, min(x, frame_width - label.winfo_width()))
        y = max(0, min(y, frame_height - label.winfo_height()))
        
        # Move the label
        label.place(x=x, y=y)

    def stop_label_drag(self, event):
        """Handle end of label drag."""
        label = event.widget
        
        # Get label position relative to image frame
        x = label.winfo_x()
        y = label.winfo_y()
        
        # Update position in the positions dictionary
        self.label_positions[label.cget('text')] = (x, y)
        print(f"Label {label.cget('text')} dropped at x={x}, y={y}")
        
        # Save the updated positions to database
        self.save_label_positions()

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
        """Process test results and save to database automatically"""
        try:
            print("Test Result command triggered - Processing test results")
            
            # Check if we have a valid lot number (from barcode scanning)
            lot_number = getattr(self, 'current_lot_number', None)
            
            if not lot_number:
                self.safe_update_message("No LOT number available for test result saving", "orange")
                print("Warning: No LOT number available - cannot save test results")
                return
                
            # Get test results from spec tree
            values_dict = {}
            values_dict["LOT NUMBER"] = lot_number
            
            has_result = False
            all_devices_pass = True
            
            # If we have specifications available, collect them
            if hasattr(self, 'spec_tree') and self.spec_tree:
                available_devices = set()
                
                # First, collect all device values and check if any are NG
                for item in self.spec_tree.get_children():
                    values = self.spec_tree.item(item, "values")
                    if len(values) > 1 and values[1]:  # If device column has a value
                        device = values[1]
                        result_value = values[-1] if len(values) > 5 else None
                        actual_value = values[-2] if len(values) > 5 else None
                        
                        # Store device in available devices set
                        available_devices.add(device)
                        
                        # Store both the result and actual value
                        if result_value:
                            has_result = True
                            # Store the actual value (not the result) for L1-L4 and P1-P4
                            if device in ["L1", "L2", "L3", "L4", "P1", "P2", "P3", "P4"] and actual_value:
                                values_dict[device] = actual_value
                            else:
                                values_dict[device] = result_value
                            
                            # Check if this result is NG
                            if result_value == "NG":
                                all_devices_pass = False
                
                # If there are any device results, set an overall RESULT value
                if has_result:
                    values_dict["RESULT"] = "PASS" if all_devices_pass else "NG"
                
                # Check if all existing devices have values and all are passing
                all_existing_devices_pass = True
                if has_result:
                    # Loop through specifications to see if any with values are NG
                    for item in self.spec_tree.get_children():
                        values = self.spec_tree.item(item, "values")
                        if len(values) > 5:
                            device = values[1] if len(values) > 1 else ""
                            result = values[-1]
                            actual = values[-2]
                            
                            # Only check devices that have actual values
                            if actual and actual != "N/A":
                                if result == "NG":
                                    all_existing_devices_pass = False
                                    break
            
            # Save test results to database if we have results
            if has_result:
                print("Test results found - saving to database")
                success = self.save_lot_data_to_database(values_dict)
                
                if success:
                    if all_existing_devices_pass:
                        self.safe_update_message(f"Test Results: LOT {lot_number} - PASS result saved automatically", "green")
                        print(f"Test Result: LOT {lot_number} - PASS result automatically saved to database")
                    else:
                        self.safe_update_message(f"Test Results: LOT {lot_number} - FAIL result saved automatically", "orange")
                        print(f"Test Result: LOT {lot_number} - FAIL result automatically saved to database")
                    
                    # Optional: Add to tree view display for PASS results
                    if all_existing_devices_pass and hasattr(self, 'tree') and hasattr(self, 'current_columns'):
                        # Create values list with PASS/NG for display in treeview
                        display_values = []
                        for col in self.current_columns:
                            if col in ["L1", "L2", "L3", "L4", "P1", "P2", "P3", "P4"]:
                                # For device columns, display PASS/NG in the tree view
                                if col in values_dict and values_dict[col]:
                                    # If we have a numeric value, determine if it's PASS or NG
                                    device_item = None
                                    for tree_item in self.spec_tree.get_children():
                                        tree_values = self.spec_tree.item(tree_item, "values")
                                        if len(tree_values) > 1 and tree_values[1] == col:
                                            device_item = tree_item
                                            break
                                    
                                    if device_item:
                                        result = self.spec_tree.item(device_item, "values")[-1]
                                        display_values.append(result)
                                    else:
                                        display_values.append("N/A")
                                else:
                                    display_values.append("N/A")
                            else:
                                # For non-device columns, use the value directly
                                display_values.append(values_dict.get(col, "N/A"))
                        
                        # Insert new row at the top for PASS results
                        self.tree.insert('', 0, values=tuple(display_values))
                        print("PASS result added to tree view display")
                        
                else:
                    self.safe_update_message("Failed to save test results to database", "red")
                    print("Error: Failed to save test results to database")
            else:
                self.safe_update_message("No test results found - nothing to save", "orange")
                print("Warning: No test results found - nothing to save")
                
        except Exception as e:
            print(f"Error in test_result_command: {e}")
            traceback.print_exc()
            self.safe_update_message(f"Error processing test results: {e}", "red")

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
        self.barcode_data = ""  # Initialize empty barcode data

    def on_key_press(self, event):
        """Handle key press events for barcode scanning"""
        if event.char and event.char.isprintable():
            # Only accumulate data if we're not directly focused on an entry widget
            focused_widget = self.root.focus_get()
            if not isinstance(focused_widget, tk.Entry):
                self.barcode_data += event.char
            # If focused on an entry, let the default behavior happen

    def on_enter_press(self, event):
        """Handle Enter key for barcode scanning"""
        # Process barcode if not in an entry widget
        focused_widget = self.root.focus_get()
        if not isinstance(focused_widget, tk.Entry) and self.barcode_data:
            self.process_barcode_data()
        # If Enter is pressed in an entry, let the default behavior happen
        # Barcode data is cleared in process_barcode_data when used

    def process_barcode_data(self):
        """Process the captured barcode data."""
        barcode = ''.join(c for c in self.barcode_data if c.isprintable()).strip()
        if not barcode:
            return
            
        # Check if we're waiting for employee code
        if not self.emp_entry.get() or self.emp_entry.get() == "EMP CODE":
            self.emp_entry.delete(0, tk.END)
            self.emp_entry.insert(0, barcode)
            self.validate_employee_code()
            # Reset barcode data after processing
            self.barcode_data = ""
            return
            
        # If ALC code is enabled and a barcode is scanned, process it
        elif self.alc_entry.cget('state') == 'normal':
            self.alc_entry.delete(0, tk.END)
            self.alc_entry.insert(0, barcode)
            self.process_alc_code()
            # Reset barcode data after processing
            self.barcode_data = ""
            return
            
        # If we have ALC code and employee code, treat this as a LOT number
        elif (hasattr(self, 'current_part_number') and self.current_part_number and 
              self.emp_entry.get() and self.emp_entry.get() != "EMP CODE" and
              self.alc_entry.get() and self.alc_entry.get() != "ALC CODE"):
            # Store as current lot number
            self.current_lot_number = barcode
            
            # Reset test result saved flag for new test cycle
            self.test_result_saved = False
            self.last_test_result_pass_state = False
            self.last_test_result_ng_state = False
            
            # Display in camera textbox
            if hasattr(self, 'cam_textbox'):
                self.cam_textbox.delete("1.0", tk.END)
                self.cam_textbox.insert("1.0", f"LOT NUMBER: {barcode}\nReady for testing...")
            
            self.safe_update_message(f"LOT {barcode} scanned - Ready for testing", "green")
            print(f"LOT number {barcode} stored")
            
            # Reset barcode data after processing
            self.barcode_data = ""
            return
            
        # Reset barcode data if not used
        self.barcode_data = ""

    def load_configuration_data(self):
        """Load configuration data from txt_files subdirectory"""
        try:
            # Define the subdirectory path
            txt_files_dir = os.path.join(os.path.dirname(__file__), 'txt_files')
            
            # Ensure the directory exists
            if not os.path.exists(txt_files_dir):
                os.makedirs(txt_files_dir, exist_ok=True)
                print(f"Created txt_files directory at: {txt_files_dir}")
            
            # Load ProcessStatus
            process_status_path = os.path.join(txt_files_dir, 'ProcessStatus.txt')
            if os.path.exists(process_status_path):
                with open(process_status_path, 'r') as file:
                    self.process_status_array = [line.strip() for line in file.readlines()]
            else:
                print(f"Warning: ProcessStatus.txt not found at {process_status_path}")
                self.process_status_array = []
            
            # Load ProgramSelectionInPLC
            program_selection_path = os.path.join(txt_files_dir, 'ProgramSelectionInPLC.txt')
            if os.path.exists(program_selection_path):
                with open(program_selection_path, 'r') as file:
                    self.program_selection_array = [line.strip() for line in file.readlines()]
            else:
                print(f"Warning: ProgramSelectionInPLC.txt not found at {program_selection_path}")
                self.program_selection_array = []
            
            # Load InputSensors
            input_sensors_path = os.path.join(txt_files_dir, 'InputSensors.txt')
            if os.path.exists(input_sensors_path):
                with open(input_sensors_path, 'r') as file:
                    self.input_sensors_array = [line.strip() for line in file.readlines()]
            else:
                print(f"Warning: InputSensors.txt not found at {input_sensors_path}")
                self.input_sensors_array = []
            
            # Load EmployeeCodes
            employee_codes_path = os.path.join(txt_files_dir, 'EmployeeCodes.txt')
            if os.path.exists(employee_codes_path):
                with open(employee_codes_path, 'r') as file:
                    self.employee_codes = [line.strip() for line in file.readlines()]
            else:
                print(f"Warning: EmployeeCodes.txt not found at {employee_codes_path}")
                self.employee_codes = []
            
            # Load PLC On Register file - updated to txt_files directory
            plc_register_path = os.path.join(txt_files_dir, 'PLC_on_register.txt')
            if os.path.exists(plc_register_path):
                with open(plc_register_path, 'r') as file:
                    # Process the file content as needed
                    print(f"Loaded PLC register file from: {plc_register_path}")
            else:
                print(f"Warning: PLC_on_register.txt not found at {plc_register_path}")
            
            # Load barcode print filenames - updated to txt_files directory
            barcode_print_path = os.path.join(txt_files_dir, 'barcodeprintfilenames.txt')
            if os.path.exists(barcode_print_path):
                with open(barcode_print_path, 'r') as file:
                    # Process the file content as needed
                    print(f"Loaded barcode print filenames from: {barcode_print_path}")
            else:
                print(f"Warning: barcodeprintfilenames.txt not found at {barcode_print_path}")
            
            # Check if any array is empty
            if not all([self.process_status_array, self.program_selection_array, 
                       self.input_sensors_array, self.employee_codes]):
                print("Warning: One or more configuration files are empty or not found.")
                # Only try to update message_label if it exists and the window is valid
                self.safe_update_message("Warning: Some configuration files not found. Check txt_files directory.", "orange")
            
        except FileNotFoundError as e:
            print(f"File Not Found: {str(e)}")
            self.safe_update_message(f"File Not Found: {str(e)}", "red")
        except Exception as e:
            print(f"Error loading configuration data: {str(e)}")
            self.safe_update_message(f"Error loading configuration data: {str(e)}", "red")
            
    def update_status_labels(self, status_values=None):
        """
        Update the status labels based on the PLC input states
        
        Args:
            status_values: Dictionary of register addresses and their HIGH/LOW states
                          If None, the method will read the values from the PLC
        """
        try:
            # If status_values not provided, read from PLC
            if status_values is None:
                status_values = self.read_process_status_values()
                
            if not status_values:
                print("No status values available to update labels")
                return
                
            # Define address indices from ProcessStatus.txt
            # Make sure we have the addresses loaded
            if not hasattr(self, 'process_addresses'):
                # First time initialization - read from ProcessStatus.txt
                process_status_line = self.process_status_array[0] if self.process_status_array else ""
                self.process_addresses = [addr.strip() for addr in process_status_line.split(',')]
            
            # Get the addresses by index (or use defaults if not found)
            # Index assignments from your specification
            auto_index = 0       # AUTO - first address in the file
            home_index = 1       # HOME - second address in the file
            first_pull_index = 2  # 1st PULL PASS - third address
            first_pull_ng_index = 3  # 1st PULL NG - fourth address
            second_pull_index = 4  # 2nd PULL PASS - fifth address
            second_pull_ng_index = 5  # 2nd PULL NG - sixth address
            test_result_index = 6  # TEST RESULT PASS - seventh address
            test_result_ng_index = 7  # TEST RESULT NG - eighth address
            
            # Get addresses safely with bounds checking
            def get_address_safe(index):
                if 0 <= index < len(self.process_addresses):
                    return self.process_addresses[index]
                print(f"Warning: Address index {index} out of range")
                return None
                
            # Map the indices to actual addresses
            auto_addr = get_address_safe(auto_index)
            home_addr = get_address_safe(home_index)
            first_pull_addr = get_address_safe(first_pull_index)
            first_pull_ng_addr = get_address_safe(first_pull_ng_index)
            second_pull_addr = get_address_safe(second_pull_index)
            second_pull_ng_addr = get_address_safe(second_pull_ng_index)
            test_result_addr = get_address_safe(test_result_index)
            test_result_ng_addr = get_address_safe(test_result_ng_index)
            
            # Now define the status mapping using the dynamic addresses
            status_mapping = {
                'auto': {'address': auto_addr, 
                         'color': 'GREEN' if status_values.get(auto_addr, False) else 'BLUE'},
                'home': {'address': home_addr, 
                         'color': 'GREEN' if status_values.get(home_addr, False) else 'BLUE'},
                '1st': {
                    'address': first_pull_addr,  # 1st PULL input
                    'ok_address': first_pull_addr,  # 1st PULL PASS
                    'ng_address': first_pull_ng_addr,  # 1st PULL NG
                    'color': self.determine_pull_color(first_pull_addr, first_pull_addr, first_pull_ng_addr, status_values)
                },
                '2nd': {
                    'address': second_pull_addr,  # 2nd PULL input
                    'ok_address': second_pull_addr,  # 2nd PULL PASS
                    'ng_address': second_pull_ng_addr,  # 2nd PULL NG
                    'color': self.determine_pull_color(second_pull_addr, second_pull_addr, second_pull_ng_addr, status_values)
                },
                'test': {
                    'address': test_result_addr,  # TEST RESULT input
                    'ok_address': test_result_addr,  # TEST RESULT PASS
                    'ng_address': test_result_ng_addr,  # TEST RESULT NG
                    'color': self.determine_pull_color(test_result_addr, test_result_addr, test_result_ng_addr, status_values)
                }
            }
            
            # Update label colors and stop blinking if HIGH
            for label_name, status_info in status_mapping.items():
                if not status_info['address']:  # Skip if address is None
                    continue
                    
                label_obj = getattr(self, f"{label_name}_label", None)
                if label_obj:
                    color = status_info['color']
                    if color == 'GREEN':
                        label_obj.config(bg="#00FF00")  # Bright green
                    elif color == 'RED':
                        label_obj.config(bg="#FF0000")  # Bright red
                    else:
                        label_obj.config(bg="#00BFFF")  # Default blue
                        
                    print(f"Updated {label_name} label to {color}")
                else:
                    print(f"Label {label_name}_label not found")
            
            # Update the specification table with values from loadcells if needed
            if hasattr(self, 'spec_tree') and self.spec_tree:
                if first_pull_addr and status_values.get(first_pull_addr, False):  # 1st PULL PASS
                    print("1st Pull PASS detected - Reading load test registers")
                    
                    # Read first 4 hold registers when 1st pull passes
                    register_values = self.read_hold_registers(0, 4)
                    if register_values:
                        print(f"Successfully read 1st Pull register values: {register_values}")
                        self.safe_update_message(f"1st Pull Passed - Load Test Values Read", "green")
                        
                        # Update specification tree with L1-L4 values from registers
                        self.update_spec_tree_with_register_values(register_values, "L")
                    else:
                        print("Failed to read register values for 1st Pull - Using default PASS")
                        # If no register values, use the basic update method
                        self.update_specification_values('L1', 'L2', 'L3', 'L4', result_color='GREEN')
                        self.safe_update_message("1st Pull Passed - No Register Values Available", "orange")
                elif first_pull_ng_addr and status_values.get(first_pull_ng_addr, False):  # 1st PULL NG
                    print("1st Pull FAIL detected")
                    self.update_specification_values('L1', 'L2', 'L3', 'L4', result_color='RED')
                    self.safe_update_message("1st Pull Failed", "red")
                    
                if second_pull_addr and status_values.get(second_pull_addr, False):  # 2nd PULL PASS
                    print("2nd Pull PASS detected - Reading length test registers")
                    
                    # Read next 4 hold registers when 2nd pull passes
                    register_values = self.read_hold_registers(4, 4)
                    if register_values:
                        print(f"Successfully read 2nd Pull register values: {register_values}")
                        self.safe_update_message(f"2nd Pull Passed - Length Test Values Read", "green")
                        
                        # Update specification tree with P1-P4 values from registers
                        self.update_spec_tree_with_register_values(register_values, "P")
                    else:
                        print("Failed to read register values for 2nd Pull - Using default PASS")
                        # If no register values, use the basic update method
                        self.update_specification_values('P1', 'P2', 'P3', 'P4', result_color='GREEN')
                        self.safe_update_message("2nd Pull Passed - No Register Values Available", "orange")
                elif second_pull_ng_addr and status_values.get(second_pull_ng_addr, False):  # 2nd PULL NG
                    print("2nd Pull FAIL detected")
                    self.update_specification_values('P1', 'P2', 'P3', 'P4', result_color='RED')
                    self.safe_update_message("2nd Pull Failed", "red")
                
                # Check for TEST RESULT completion and automatically save to database
                test_result_pass_current = test_result_addr and status_values.get(test_result_addr, False)
                test_result_ng_current = test_result_ng_addr and status_values.get(test_result_ng_addr, False)
                
                # Check for state change from LOW to HIGH (rising edge) to prevent duplicate saves
                if test_result_pass_current and not self.last_test_result_pass_state and not self.test_result_saved:
                    print("Test Result PASS detected (rising edge) - Auto-saving to database")
                    self.safe_update_message("Test Result PASS - Auto-saving to database", "green")
                    
                    # Automatically trigger test result processing and database saving
                    # Use a small delay to ensure all values are updated
                    self.root.after(500, self.test_result_command)
                    self.test_result_saved = True
                    
                elif test_result_ng_current and not self.last_test_result_ng_state and not self.test_result_saved:
                    print("Test Result FAIL detected (rising edge) - Auto-saving to database")
                    self.safe_update_message("Test Result FAIL - Auto-saving to database", "orange")
                    
                    # Automatically trigger test result processing and database saving
                    # Use a small delay to ensure all values are updated
                    self.root.after(500, self.test_result_command)
                    self.test_result_saved = True
                
                # Update the last states for next cycle
                self.last_test_result_pass_state = test_result_pass_current
                self.last_test_result_ng_state = test_result_ng_current
        
        except Exception as e:
            print(f"Error updating status labels: {e}")
            traceback.print_exc()
            
    def determine_pull_color(self, input_address, ok_address, ng_address, status_values):
        """Determine the color for a pull status label based on input, OK and NG states"""
        # Handle None addresses
        if not input_address or not ok_address or not ng_address:
            return 'BLUE'  # Default color
            
        if status_values.get(input_address, False):  # If input is HIGH
            if status_values.get(ok_address, False):  # If OK is HIGH
                return 'GREEN'
            elif status_values.get(ng_address, False):  # If NG is HIGH
                return 'RED'
        return 'BLUE'  # Default color
        
    def read_process_status_values(self):
        """Read all process status registers and return a dictionary of their states"""
        status_values = {}
        
        try:
            if not self.plc_client or not self.plc_client.is_socket_open():
                print("PLC not connected")
                return status_values
                
            station_id = int(os.getenv('PLC_STATION_ID', '1'))
            
            # Process the content of ProcessStatus.txt
            if not self.process_status_array:
                print("Process status array is empty")
                return status_values
                
            # First element contains all comma-separated addresses
            process_status_line = self.process_status_array[0] if self.process_status_array else ""
            addresses = [addr.strip() for addr in process_status_line.split(',')]
            
            # Store addresses for index-based access
            self.process_addresses = addresses
            
            # Read state for each address
            for i, address in enumerate(addresses):
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
                    status_values[address] = status
                    # Also store by index for easier access
                    status_values[f"index_{i}"] = status
                    print(f"Address {address} (index {i}): {'HIGH' if status else 'LOW'}")
                else:
                    print(f"Error reading coil {address}")
                    
            return status_values
                
        except Exception as e:
            print(f"Error reading process status values: {e}")
            return status_values
            
    def update_specification_values(self, *devices, result_color):
        """Update specification table with result values and colors"""
        try:
            if not hasattr(self, 'spec_tree') or not self.spec_tree:
                return
                
            # Iterate through all rows in the tree
            for item in self.spec_tree.get_children():
                values = list(self.spec_tree.item(item, "values"))
                device = values[1] if len(values) > 1 else ""
                
                # If this device should be updated
                if device in devices:
                    # Set result column color/value
                    if result_color == 'GREEN':
                        values[-1] = "PASS"  # Last column is Result
                    elif result_color == 'RED':
                        values[-1] = "NG"
                        
                    # Update the row
                    self.spec_tree.item(item, values=values)
        except Exception as e:
            print(f"Error updating specification values: {e}")
            
    def safe_update_message(self, message, color="black"):
        """Safely update message label with proper error handling"""
        try:
            if hasattr(self, 'root') and self.root.winfo_exists():
                if hasattr(self, 'message_label') and self.message_label and self.message_label.winfo_exists():
                    self.message_label.config(text=message, fg=color)
                else:
                    print(f"Cannot display message '{message}' - message_label not ready")
            else:
                print(f"Cannot display message '{message}' - root window not ready")
        except Exception as e:
            print(f"Error updating message: {e}")
            print(f"Original message was: {message}")

    def connect_to_devices(self):
        """Connect to PLC and loadcells with improved error handling and port validation"""
        try:
            # Check if main_container exists
            if not hasattr(self, 'main_container'):
                print("Error: main_container does not exist. Creating it now.")
                self.main_container = tk.Frame(self.root)
                self.main_container.pack(fill="both", expand=True)
            
            # Check if message_label exists
            if not hasattr(self, 'message_label'):
                print("Error: message_label does not exist. Creating it now.")
                self.message_label = tk.Label(self.main_container, text="Ready", font=("Arial", 10))
                self.message_label.pack(fill="x", pady=2)
                
            # Check if PySerial is properly installed
            if not self.check_serial_module():
                self.safe_update_message("PySerial module not properly installed. Please install it with: pip install pyserial", "red")
                return
                
            # Initialize clients as None first
            self.plc_client = None
            self.loadcell1_client = None
            self.loadcell2_client = None
            
            # Ensure .env file exists and load environment variables
            env_file = self.ensure_env_file_exists()
            load_dotenv(dotenv_path=env_file, override=True)
            
            self.safe_update_message("Connecting to devices...", "blue")
            
            # Connect to PLC automatically
            success = self.auto_connect_plc()
            
            if success:
                self.safe_update_message("PLC connected successfully. Ready for operation.", "green")
                # Update status indicator
                if hasattr(self, 'status_label'):
                    self.status_label.config(fg="green")
            else:
                self.safe_update_message("PLC connection failed. Check COM port settings.", "red")
                if hasattr(self, 'status_label'):
                    self.status_label.config(fg="red")
            
        except Exception as e:
            print(f"Error connecting to devices: {str(e)}")
            self.safe_update_message(f"Error connecting to devices: {str(e)}", "red")

    def auto_connect_plc(self):
        """Automatically connect to PLC using saved settings from .env file"""
        try:
            # Get PLC settings from environment variables
            plc_port = os.getenv('PLC_COM_PORT', '').strip()
            plc_baud = os.getenv('PLC_BAUD_RATE', '').strip()
            plc_station_id = os.getenv('PLC_STATION_ID', '').strip()
            
            print(f"Auto-connecting to PLC with settings: Port={plc_port}, Baud={plc_baud}, Station ID={plc_station_id}")
            
            # Validate that we have all required settings
            if not all([plc_port, plc_baud, plc_station_id]):
                print("Missing PLC configuration in .env file")
                missing_items = []
                if not plc_port: missing_items.append("PLC_COM_PORT")
                if not plc_baud: missing_items.append("PLC_BAUD_RATE")
                if not plc_station_id: missing_items.append("PLC_STATION_ID")
                
                self.safe_update_message(f"Missing PLC config: {', '.join(missing_items)}. Please configure in COM Port Settings.", "orange")
                return False
            
            # Validate station ID is numeric
            try:
                station_id = int(plc_station_id)
                baud_rate = int(plc_baud)
            except ValueError:
                print(f"Invalid PLC configuration: Station ID or Baud Rate not numeric")
                self.safe_update_message("Invalid PLC configuration: Station ID or Baud Rate must be numeric", "red")
                return False
            
            # Check if port is available
            available_ports = self.get_available_ports()
            if plc_port not in available_ports:
                print(f"PLC port {plc_port} not available. Available ports: {available_ports}")
                self.safe_update_message(f"PLC port {plc_port} not available. Check COM port settings.", "red")
                return False
            
            # Close any existing connection
            if self.plc_client:
                try:
                    if self.plc_client.is_socket_open():
                        self.plc_client.close()
                        print("Closed existing PLC connection")
                except:
                    pass
                self.plc_client = None
            
            # Create new PLC client
            print(f"Creating ModbusSerialClient for port {plc_port} at {baud_rate} baud")
            self.plc_client = ModbusSerialClient(
                port=plc_port,
                baudrate=baud_rate,
                timeout=2,  # Increased timeout for reliability
                stopbits=1,
                bytesize=8,
                parity='N'
            )
            
            # Attempt connection with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"PLC connection attempt {attempt + 1}/{max_retries}")
                    
                    # Ensure any previous connection is closed
                    if self.plc_client.is_socket_open():
                        self.plc_client.close()
                        time.sleep(0.5)
                    
                    # Attempt to connect
                    if self.plc_client.connect():
                        print("PLC client connected, testing communication...")
                        
                        # Test communication by reading a coil
                        test_response = self.plc_client.read_coils(
                            address=0,
                            count=1,
                            slave=station_id
                        )
                        
                        if not test_response.isError():
                            print("PLC communication test successful")
                            self.safe_update_message(f"Connected to PLC on {plc_port}", "green")
                            
                            # Update control button to show current P0000 state
                            if hasattr(self, 'plc_control_button'):
                                state = test_response.bits[0]
                                if state:  # PLC is HIGH
                                    self.plc_control_button.config(
                                        text="SET LOW",
                                        bg="#FF5722"  # Red for HIGH state
                                    )
                                else:  # PLC is LOW
                                    self.plc_control_button.config(
                                        text="SET HIGH",
                                        bg="#4CAF50"  # Green for LOW state
                                    )
                            
                            return True
                        else:
                            print(f"PLC communication test failed: {test_response}")
                            if self.plc_client.is_socket_open():
                                self.plc_client.close()
                    else:
                        print("Failed to establish PLC connection")
                        
                except Exception as e:
                    print(f"Connection attempt {attempt + 1} failed: {str(e)}")
                    try:
                        if self.plc_client and self.plc_client.is_socket_open():
                            self.plc_client.close()
                    except:
                        pass
                
                # Wait before retry (except on last attempt)
                if attempt < max_retries - 1:
                    print("Waiting before retry...")
                    time.sleep(1)
            
            # All attempts failed
            print("Failed to connect to PLC after all attempts")
            self.plc_client = None
            self.safe_update_message(f"Failed to connect to PLC on {plc_port} after {max_retries} attempts", "red")
            return False
            
        except Exception as e:
            print(f"Error in auto_connect_plc: {str(e)}")
            self.safe_update_message(f"PLC connection error: {str(e)}", "red")
            if self.plc_client:
                try:
                    if self.plc_client.is_socket_open():
                        self.plc_client.close()
                except:
                    pass
                self.plc_client = None
            return False

    def start_status_monitoring(self):
        """Start periodic monitoring of PLC status registers and update the UI"""
        # Check if PLC client exists and is connected
        if not hasattr(self, 'plc_client') or not self.plc_client or not self.plc_client.is_socket_open():
            print("Cannot start status monitoring - PLC not connected")
            self.safe_update_message("Cannot start monitoring - PLC not connected", "red")
            return False
        
        # Initialize status_monitoring_active if not already set
        if not hasattr(self, 'status_monitoring_active'):
            self.status_monitoring_active = False
            
        # If monitoring is already active, don't start again
        if self.status_monitoring_active:
            print("Status monitoring already active")
            return True
            
        # Set monitoring as active
        self.status_monitoring_active = True
        print("Starting status monitoring")
        
        # Try to read status values immediately to update UI on start
        try:
            status_values = self.read_process_status_values()
            if status_values:
                self.update_status_labels(status_values)
                print(f"Initial status values read: {len(status_values)} values")
            else:
                print("Warning: No initial status values read from PLC")
        except Exception as e:
            print(f"Warning: Error reading initial status values: {e}")
        
        # Start the monitoring loop
        self.update_status_from_plc()
        return True

    def update_status_from_plc(self):
        """Periodic update of status from PLC with process halting control"""
        try:
            # Only update if client is still connected
            if self.plc_client and self.plc_client.is_socket_open() and self.status_monitoring_active:
                # Check PLC control state first
                plc_control_state = self.check_plc_control_state()
                
                if plc_control_state is False:  # PLC is LOW - halt process
                    self.halt_process()
                elif plc_control_state is True:  # PLC is HIGH - allow process
                    # Read all process status values
                    status_values = self.read_process_status_values()
                    
                    # Update the labels with the values
                    if status_values:
                        self.update_status_labels(status_values)
                
                # Schedule next update (every 500ms)
                self.root.after(500, self.update_status_from_plc)
            else:
                print("PLC client not connected or monitoring stopped - stopping status updates")
                self.status_monitoring_active = False
        except Exception as e:
            print(f"Error in status update loop: {e}")
            self.status_monitoring_active = False

    def check_plc_control_state(self):
        """Check the PLC control state (P0000) to determine if process should run"""
        try:
            if not self.plc_client or not self.plc_client.is_socket_open():
                return None
                
            station_id = int(os.getenv('PLC_STATION_ID', '1'))
            
            response = self.plc_client.read_coils(
                address=0x0000,  # P0000 address
                count=1,
                slave=station_id
            )
            
            if not response.isError():
                return response.bits[0]  # True for HIGH, False for LOW
            else:
                print(f"Error reading PLC control state: {response}")
                return None
                
        except Exception as e:
            print(f"Error checking PLC control state: {e}")
            return None

    def halt_process(self):
        """Halt the process when PLC control is LOW"""
        try:
            # Reset process status labels to default
            self.reset_process_status_labels()
            
            # Clear specification tree results but keep the structure
            if hasattr(self, 'spec_tree') and self.spec_tree:
                for item in self.spec_tree.get_children():
                    values = list(self.spec_tree.item(item, "values"))
                    if len(values) >= 7:
                        values[-2] = ""  # Clear Actual column
                        values[-1] = ""  # Clear Result column
                        self.spec_tree.item(item, values=values, tags=('neutral',))
            
            # Reset any placed labels to default state
            if hasattr(self, 'placed_labels'):
                for label in self.placed_labels.values():
                    label.configure(bg="yellow")  # Reset to default color
            
            # Stop all label blinking
            self.stop_all_label_blinking()
            
            # Update status message
            self.safe_update_message("Process halted - PLC control is LOW", "red")
            
            print("Process halted - waiting for PLC control to go HIGH")
            
        except Exception as e:
            print(f"Error halting process: {e}")

    def is_port_available(self, port):
        """Check if a COM port is available for connection"""
        if not port:
            print("No port specified")
            return False
            
        try:
            # Try to open the port
            ser = serial.Serial(port)
            ser.close()
            print(f"Port {port} is available")
            return True
        except Exception as e:
            print(f"Port {port} is not available: {e}")
            return False

    def reconnect_plc(self):
        """Attempt to reconnect to PLC with forced resource release"""
        try:
            # Force close any existing connections
            if hasattr(self, 'plc_client') and self.plc_client:
                try:
                    if self.plc_client.is_socket_open():
                        self.plc_client.close()
                        
                    # Access the underlying serial object to ensure it's closed
                    if hasattr(self.plc_client, 'socket') and self.plc_client.socket:
                        if hasattr(self.plc_client.socket, 'close'):
                            self.plc_client.socket.close()
                except Exception as e:
                    print(f"Error closing existing PLC connection: {e}")
                
                # Set to None to ensure garbage collection
                self.plc_client = None
            
            # Force close COM ports
            self.force_close_com_ports()
            
            # Allow time for COM port to release
            time.sleep(1)
            
            # Ensure .env file exists and load environment variables
            env_file = self.ensure_env_file_exists()
            load_dotenv(dotenv_path=env_file, override=True)
            
            # Get configuration from environment
            plc_port = os.getenv('PLC_COM_PORT')
            plc_baud = os.getenv('PLC_BAUD_RATE')
            plc_station_id = os.getenv('PLC_STATION_ID')
            
            print(f"PLC reconnection settings from env: Port={plc_port}, Baud={plc_baud}, ID={plc_station_id}")
            
            if not all([plc_port, plc_baud, plc_station_id]):
                print("Missing PLC configuration in environment variables")
                return False
            
            # Check if port is available
            if not self.is_port_available(plc_port):
                print(f"Port {plc_port} is still not available after force release")
                return False
            
            # Create a fresh PLC client
            self.plc_client = ModbusSerialClient(
                port=plc_port,
                baudrate=int(plc_baud),
                timeout=1,
                stopbits=1,
                bytesize=8,
                parity='N'
            )
            
            # Attempt connection
            if not self.plc_client.connect():
                print("Failed to reconnect to PLC")
                self.plc_client = None
                return False
            
            # Test connection
            test_response = self.plc_client.read_coils(
                address=0,
                count=1,
                slave=int(plc_station_id)
            )
            
            if test_response.isError():
                print("PLC connection test failed")
                self.plc_client.close()
                self.plc_client = None
                return False
            
            print("Successfully reconnected to PLC")
            return True
            
        except Exception as e:
            print(f"Error reconnecting to PLC: {e}")
            if hasattr(self, 'plc_client') and self.plc_client:
                try:
                    if self.plc_client.is_socket_open():
                        self.plc_client.close()
                except:
                    pass
                self.plc_client = None
            return False

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
        """Enhanced cleanup method with forced resource release for PLC connection"""
        try:
            # Stop all monitoring first
            self.keepWriting = False
            self.breakLoop = True
            
            # Stop PLC status monitoring
            if hasattr(self, 'status_monitoring_active'):
                self.status_monitoring_active = False
                print("Status monitoring stopped")
            
            # Stop all blinking labels
            self.stop_all_label_blinking()
            
            # Clean up loadcell connections
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
            
            # Force release PLC connection
            if hasattr(self, 'plc_client') and self.plc_client:
                try:
                    # Double-ensure the socket is closed
                    if self.plc_client.is_socket_open():
                        self.plc_client.close()
                        print("PLC connection closed")
                    
                    # Access the underlying serial object to ensure it's closed
                    if hasattr(self.plc_client, 'socket') and self.plc_client.socket:
                        if hasattr(self.plc_client.socket, 'close'):
                            self.plc_client.socket.close()
                            print("PLC socket forcefully closed")
                    
                    print("PLC connection cleanup completed")
                except Exception as e:
                    print(f"Error closing PLC connection: {e}")
                finally:
                    # Ensure the reference is removed
                    self.plc_client = None
            
            # Give time for ports to be released
            time.sleep(0.5)
            
            # Additional force close to ensure COM ports are released
            self.force_close_com_ports()
            
            print("All connections cleaned up successfully")
                
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
    
    def force_close_com_ports(self):
        """Force close COM ports that might be in use"""
        try:
            # Get PLC COM port from environment
            plc_port = os.getenv('PLC_COM_PORT')
            if not plc_port:
                print("No PLC port configured in environment variables")
                return
                
            try:
                # Try to open and immediately close the port to force release
                test_serial = serial.Serial(plc_port)
                test_serial.close()
                print(f"Successfully force-closed {plc_port}")
            except AttributeError:
                print(f"Serial module issue: Make sure pyserial is installed properly")
            except Exception as e:
                print(f"Could not force-close {plc_port}: {e}")
                
            # Also check if any loadcell ports need to be closed
            loadcell1_port = os.getenv('LOADCELL_01_COM_PORT')
            if loadcell1_port:
                try:
                    test_serial = serial.Serial(loadcell1_port)
                    test_serial.close()
                    print(f"Successfully force-closed {loadcell1_port}")
                except Exception as e:
                    print(f"Could not force-close {loadcell1_port}: {e}")
                    
            loadcell2_port = os.getenv('LOADCELL_02_COM_PORT')
            if loadcell2_port:
                try:
                    test_serial = serial.Serial(loadcell2_port)
                    test_serial.close()
                    print(f"Successfully force-closed {loadcell2_port}")
                except Exception as e:
                    print(f"Could not force-close {loadcell2_port}: {e}")
        except Exception as e:
            print(f"Error force-closing COM ports: {e}")

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
            
            # Load and resize image to exactly match frame dimensions
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
            
            # Force update of the display before returning
            self.root.update_idletasks()
            
            self.current_image_path = image_path
            print(f"Successfully loaded image: {image_path}")
            return True
            
        except Exception as e:
            print(f"Error loading image: {str(e)}")
            messagebox.showerror("Error", f"Error loading image: {str(e)}")
            return False

    def place_labels_from_positions(self, coordinates_data):
        """Place labels L1-L15 according to database coordinates with improved visibility and blinking effect."""
        try:
            # Clear any existing placed labels and stop any blinking
            self.stop_all_label_blinking()
            for label in getattr(self, 'placed_labels', {}).values():
                label.destroy()
            self.placed_labels = {}
            self.label_positions = {}  # Reset positions dictionary
            
            # Get image frame dimensions for validation
            frame_width = self.image_frame.winfo_width()
            frame_height = self.image_frame.winfo_height()
            
            print(f"Image frame dimensions: {frame_width}x{frame_height}")
            print(f"Placing labels with coordinates: {coordinates_data}")
            
            # Make sure image is fully loaded before placing labels
            self.root.update_idletasks()
            
            # Create all labels L1-L15 if they exist in coordinates_data
            for i in range(1, 16):  # 1 to 15
                label_num = str(i)
                if label_num in coordinates_data:
                    try:
                        coord_data = coordinates_data[label_num]
                        # Get coordinates from database
                        x = float(coord_data.get('x', 0))
                        y = float(coord_data.get('y', 0))
                        
                        print(f"Processing label L{label_num} at coordinates ({x}, {y})")
                        
                        # Create label with enhanced visibility
                        label_text = f'L{label_num}'
                        new_label = tk.Label(self.image_frame,
                                           text=label_text,
                                           bg="yellow",  # Initial background color
                                           fg="black",
                                           font=("Arial", 12, "bold"),
                                           width=4,
                                           relief="raised",
                                           borderwidth=2)
                        
                        # Place label at exact coordinates
                        new_label.place(x=x, y=y)
                        
                        # Ensure label is on top of all other widgets
                        new_label.lift()
                        
                        # Enable dragging for the label
                        new_label.bind("<Button-1>", self.start_label_drag)
                        new_label.bind("<B1-Motion>", self.on_label_drag)
                        new_label.bind("<ButtonRelease-1>", self.stop_label_drag)
                        new_label.configure(cursor="hand2")
                        
                        # Store the label and its position
                        self.placed_labels[label_text] = new_label
                        self.label_positions[label_text] = (x, y)
                        
                        # Store original color for blinking
                        new_label.original_bg = "yellow"
                        
                        print(f"Successfully placed {label_text} at coordinates x={x}, y={y}")
                        
                    except Exception as e:
                        print(f"Error placing label L{label_num}: {str(e)}")
                        continue
            
            # Start blinking effect for all placed labels
            self.start_label_blinking()
            
            # Update label info
            if self.placed_labels:
                sorted_labels = sorted(self.placed_labels.keys(), key=lambda x: int(x[1:]))
                self.label_info.config(text=f"Placed Labels: {', '.join(sorted_labels)}")
            else:
                self.label_info.config(text="Placed Labels: None")
                
        except Exception as e:
            print(f"Error placing labels: {e}")
            messagebox.showerror("Error", f"Failed to place labels: {str(e)}")

    def start_label_blinking(self):
        """Start blinking effect for all placed labels."""
        if not hasattr(self, 'blinking_jobs'):
            self.blinking_jobs = {}
        
        # Start blinking for each label
        for label_text, label in self.placed_labels.items():
            if label_text not in self.blinking_jobs:
                self.blink_label(label, label_text)
    
    def blink_label(self, label, label_text):
        """Create blinking effect for a label, alternating between red and original color."""
        if not hasattr(label, 'blink_state'):
            label.blink_state = False
        
        # Toggle blink state
        label.blink_state = not label.blink_state
        
        # Set background color based on blink state
        if label.blink_state:
            label.configure(bg="red")
        else:
            label.configure(bg=label.original_bg)
        
        # Store the job ID to be able to cancel it later
        self.blinking_jobs[label_text] = self.root.after(500, lambda: self.blink_label(label, label_text))
    
    def stop_all_label_blinking(self):
        """Stop blinking effect for all labels."""
        if hasattr(self, 'blinking_jobs'):
            for job_id in self.blinking_jobs.values():
                self.root.after_cancel(job_id)
            self.blinking_jobs = {}
    
    def stop_label_blinking(self, label_text):
        """Stop blinking effect for a specific label."""
        if hasattr(self, 'blinking_jobs') and label_text in self.blinking_jobs:
            self.root.after_cancel(self.blinking_jobs[label_text])
            del self.blinking_jobs[label_text]

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
                    'y': label.winfo_y()
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

            print(f"Saved label positions to database for part number {self.current_part_number}")
            print(f"Positions: {positions_json}")

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
            txt_files_dir = os.path.join(os.path.dirname(__file__), 'txt_files')
            
            # Ensure the directory exists
            if not os.path.exists(txt_files_dir):
                os.makedirs(txt_files_dir, exist_ok=True)
                print(f"Created txt_files directory at: {txt_files_dir}")
            
            # Check for employee codes file
            employee_codes_path = os.path.join(txt_files_dir, 'EmployeeCodes.txt')
            
            # Check if file exists
            if not os.path.exists(employee_codes_path):
                print(f"Warning: EmployeeCodes.txt not found at {employee_codes_path}")
                self.safe_update_message(f"Warning: EmployeeCodes.txt not found - auto-approving", "orange")
                # Auto-approve employee code if file is missing
                self.alc_entry.configure(state='normal')  # Enable ALC entry
                self.emp_entry.configure(bg="lightgreen")
                self.alc_entry.focus_set()  # Set focus to ALC entry
                return
            
            # Read from the correct file path
            with open(employee_codes_path, 'r') as file:
                valid_codes = [code.strip() for code in file.readlines()]
            
            if emp_code in valid_codes:
                self.safe_update_message("Employee code validated", "green")
                self.alc_entry.configure(state='normal')  # Enable ALC entry
                self.emp_entry.configure(bg="lightgreen")
                self.alc_entry.focus_set()  # Set focus to ALC entry
            else:
                self.safe_update_message("Error: Employee code unauthorized", "red")
                messagebox.showerror("Error", "Employee code unauthorized")
                self.alc_entry.configure(state='disabled')
                self.emp_entry.configure(bg="pink")
                
        except FileNotFoundError:
            print(f"Error: Employee codes file not found in txt_files directory")
            self.safe_update_message("Error: Employee codes file not found - auto-approving", "orange")
            # Auto-approve employee code if file cannot be read
            self.alc_entry.configure(state='normal')  # Enable ALC entry
            self.emp_entry.configure(bg="lightgreen")
            self.alc_entry.focus_set()  # Set focus to ALC entry
        except Exception as e:
            print(f"Error during employee code validation: {str(e)}")
            self.safe_update_message(f"Error validating employee code: {str(e)}", "red")

    def on_alc_entry_focus(self, is_focused):
        """Handle ALC entry focus with visual feedback"""
        if is_focused:
            if self.alc_entry.get() == "ALC CODE":
                self.alc_entry.delete(0, tk.END)
            self.alc_entry.configure(bg="white")
            
            # Remove the selection dialog trigger
            # When the entry gets focus, don't show selection dialog anymore
        else:
            if not self.alc_entry.get():
                self.alc_entry.insert(0, "ALC CODE")
                self.alc_entry.configure(bg="#fff9c4")

    def process_alc_code(self, event=None):
        """Process the entered ALC code and retrieve specifications"""
        # Use the value from the entry field
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
            
            # Collect all device names to update tree columns
            available_devices = set()
            
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
                
                # Add device to the set of available devices
                if spec['Device']:
                    available_devices.add(spec['Device'])

            # Update tree columns based on available devices
            self.update_tree_columns(available_devices)

            # Handle image loading and label placement
            if model_result['MM_IMAGE_PATH']:
                abs_image_path = os.path.abspath(os.path.join(os.path.dirname(__file__), model_result['MM_IMAGE_PATH']))
                if os.path.exists(abs_image_path):
                    if self.load_image_with_path(abs_image_path):
                        # Force update to ensure image is loaded before placing labels
                        self.root.update_idletasks()
                        
                        if model_result['MM_LABEL_COORDINATES']:
                            try:
                                coordinates_data = json.loads(model_result['MM_LABEL_COORDINATES'])
                                # Ensure we place labels after the image is fully loaded
                                self.root.after(100, lambda: self.place_labels_from_positions(coordinates_data))
                            except json.JSONDecodeError:
                                messagebox.showwarning("Warning", "Invalid label coordinate data")
                else:
                    messagebox.showwarning("Warning", f"Image not found: {abs_image_path}")

            # Update status message
            self.safe_update_message(
                f"Model: {model_result['MM_MODEL_NAME']} | Part Number: {self.current_part_number}",
                "green"
            )

            cursor.close()
            conn.close()
            
            # Load lot history for this part number
            self.load_history_to_treeview()
            
            # Start monitoring PLC status now that we have the ALC code and specifications
            if hasattr(self, 'plc_client') and self.plc_client and self.plc_client.is_socket_open():
                print("Starting process status monitoring after ALC code entry")
                self.start_status_monitoring()
                self.safe_update_message(
                    f"Process monitoring started for Part: {self.current_part_number} - Scan LOT number to begin",
                    "green"
                )
            else:
                print("PLC not connected - attempting to reconnect for monitoring")
                # Try to reconnect before starting monitoring
                success = self.auto_connect_plc()
                if success:
                    print("Successfully reconnected PLC - starting monitoring")
                    self.start_status_monitoring()
                    self.safe_update_message(
                        f"PLC reconnected and monitoring started for Part: {self.current_part_number} - Scan LOT number to begin",
                        "green"
                    )
                else:
                    print("Cannot start monitoring - PLC connection failed")
                    self.safe_update_message("Cannot start monitoring - PLC connection failed. Check COM port settings.", "red")

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

    def toggle_plc_state(self):
        """Toggle PLC P0000 between HIGH and LOW"""
        try:
            # Check if PLC is connected, if not try to reconnect
            if not self.plc_client or not self.plc_client.is_socket_open():
                print("PLC not connected, attempting to reconnect...")
                success = self.auto_connect_plc()
                if not success:
                    messagebox.showerror("Error", "PLC not connected. Please check COM port settings and ensure configuration is saved.")
                    return

            # Get the station ID from environment variable
            station_id = int(os.getenv('PLC_STATION_ID', '1'))

            # First read the current state of P0000
            read_response = self.plc_client.read_coils(
                address=0x0000,  # P0000 address
                count=1,
                slave=station_id
            )

            if read_response.isError():
                raise Exception(f"Failed to read P0000 state: {read_response}")

            current_state = read_response.bits[0]
            new_state = not current_state  # Toggle the state

            # Write the new state to P0000
            write_response = self.plc_client.write_coil(
                address=0x0000,  # P0000 address
                value=new_state,
                slave=station_id
            )

            if write_response.isError():
                raise Exception(f"Failed to write to P0000: {write_response}")

            # Update button text and color based on new state
            if new_state:
                self.plc_control_button.config(
                    text="SET LOW",
                    bg="#FF5722"  # Red for HIGH state (button shows opposite action)
                )
                status_msg = "PLC P0000 set to HIGH"
            else:
                self.plc_control_button.config(
                    text="SET HIGH", 
                    bg="#4CAF50"  # Green for LOW state (button shows opposite action)
                )
                status_msg = "PLC P0000 set to LOW"

            # Flash the button to indicate success
            self.flash_plc_button_success()
            
            # Update status message
            self.safe_update_message(status_msg, "green")

        except Exception as e:
            print(f"PLC toggle failed: {str(e)}")
            messagebox.showerror("PLC Error", f"Failed to toggle PLC state:\n{str(e)}")
            self.flash_plc_button_failure()
            self.safe_update_message(f"PLC toggle failed: {str(e)}", "red")

    def flash_plc_button_success(self):
        """Visual feedback for successful PLC operation"""
        def reset_colors():
            # Don't reset the button color as it should stay based on the PLC state
            self.status_label.config(fg="green")  # Keep status indicator green
        
        # Brief flash to indicate success
        original_bg = self.plc_control_button.cget('bg')
        self.plc_control_button.config(bg="#00FF00")  # Bright green flash for success
        self.status_label.config(fg="#00FF00")  # Bright green for status
        self.root.after(200, lambda: self.plc_control_button.config(bg=original_bg))
        self.root.after(200, reset_colors)

    def flash_plc_button_failure(self):
        """Visual feedback for failed PLC operation"""
        def reset_colors():
            # Reset to default green for failed operations
            self.plc_control_button.config(bg="#4CAF50", text="SET HIGH")
            self.status_label.config(fg="red")  # Keep status indicator red
        
        self.plc_control_button.config(bg="#FF0000")  # Red for failure
        self.status_label.config(fg="#FF0000")  # Red for status
        self.root.after(200, reset_colors)

    def monitor_p0000_state(self):
        """Continuously monitor P0000 state and update button/status accordingly"""
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
                    
                    # Update control button based on current PLC state
                    if state:  # PLC is HIGH
                        self.plc_control_button.config(
                            text="SET LOW",
                            bg="#FF5722"  # Red background for HIGH state
                        )
                    else:  # PLC is LOW
                        self.plc_control_button.config(
                            text="SET HIGH",
                            bg="#4CAF50"  # Green background for LOW state
                        )
                    
                    # Update status indicator
                    self.status_label.config(
                        fg="green" if state else "gray"
                    )
                else:
                    print(f"P0000 read error: {response}")
                    self.plc_control_button.config(
                        text="ERROR",
                        bg="#9E9E9E"  # Gray for error
                    )
                    self.status_label.config(fg="red")
            else:
                # PLC not connected
                self.plc_control_button.config(
                    text="DISCONNECTED",
                    bg="#9E9E9E"  # Gray for disconnected
                )
                self.status_label.config(fg="red")
            
        except Exception as e:
            print(f"P0000 monitoring error: {e}")
            self.plc_control_button.config(
                text="ERROR",
                bg="#9E9E9E"  # Gray for error
            )
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

    def on_closing(self):
        """Handle window closing event"""
        try:
            # Perform cleanup operations
            self.cleanup()
            
            # Destroy the window
            self.root.destroy()
            
            print("Test console closed properly")
        except Exception as e:
            print(f"Error during window closing: {e}")
            # Ensure window is destroyed even if cleanup fails
            self.root.destroy()

    def next_label_command(self):
        """Process test results, save to database, reset page, and prepare for next test"""
        try:
            # Check if we have a valid lot number (from barcode scanning)
            lot_number = getattr(self, 'current_lot_number', None)
            
            if not lot_number:
                messagebox.showwarning("Warning", "Please scan a barcode first to get LOT number")
                return
                
            # Get test results from spec tree
            values_dict = {}
            values_dict["LOT NUMBER"] = lot_number
            
            has_result = False
            all_devices_pass = True
            
            # If we have specifications available, collect them
            if hasattr(self, 'spec_tree') and self.spec_tree:
                available_devices = set()
                
                # First, collect all device values and check if any are NG
                for item in self.spec_tree.get_children():
                    values = self.spec_tree.item(item, "values")
                    if len(values) > 1 and values[1]:  # If device column has a value
                        device = values[1]
                        result_value = values[-1] if len(values) > 5 else None
                        actual_value = values[-2] if len(values) > 5 else None
                        
                        # Store device in available devices set
                        available_devices.add(device)
                        
                        # Store both the result and actual value
                        if result_value:
                            has_result = True
                            # Store the actual value (not the result) for L1-L4 and P1-P4
                            if device in ["L1", "L2", "L3", "L4", "P1", "P2", "P3", "P4"] and actual_value:
                                values_dict[device] = actual_value
                            else:
                                values_dict[device] = result_value
                            
                            # Check if this result is NG
                            if result_value == "NG":
                                all_devices_pass = False
                
                # If there are any device results, set an overall RESULT value
                if has_result:
                    values_dict["RESULT"] = "PASS" if all_devices_pass else "NG"
                
                # Check if all existing devices have values and all are passing
                all_existing_devices_pass = True
                if has_result:
                    # Loop through specifications to see if any with values are NG
                    for item in self.spec_tree.get_children():
                        values = self.spec_tree.item(item, "values")
                        if len(values) > 5:
                            device = values[1] if len(values) > 1 else ""
                            result = values[-1]
                            actual = values[-2]
                            
                            # Only check devices that have actual values
                            if actual and actual != "N/A":
                                if result == "NG":
                                    all_existing_devices_pass = False
                                    break
            
            # Always add to tree view and database if we have results
            if has_result:
                # Create values list with PASS/NG for display in treeview
                display_values = []
                for col in self.current_columns:
                    if col in ["L1", "L2", "L3", "L4", "P1", "P2", "P3", "P4"]:
                        # For device columns, display PASS/NG in the tree view
                        if col in values_dict and values_dict[col]:
                            # If we have a numeric value, determine if it's PASS or NG
                            device_item = None
                            for tree_item in self.spec_tree.get_children():
                                tree_values = self.spec_tree.item(tree_item, "values")
                                if len(tree_values) > 1 and tree_values[1] == col:
                                    device_item = tree_item
                                    break
                            
                            if device_item:
                                result = self.spec_tree.item(device_item, "values")[-1]
                                display_values.append(result)
                            else:
                                display_values.append("N/A")
                        else:
                            display_values.append("N/A")
                    else:
                        # For non-device columns, use the value directly
                        display_values.append(values_dict.get(col, "N/A"))
                
                # Only add PASS results to tree view (but save all to database)
                should_display_in_tree = all_existing_devices_pass
                if should_display_in_tree:
                    # Insert new row at the top for PASS results only
                    self.tree.insert('', 0, values=tuple(display_values))
                
                # Save lot data to database (always save both PASS and FAIL)
                print("Saving test result to database")
                success = self.save_lot_data_to_database(values_dict)
                
                if success:
                    if all_existing_devices_pass:
                        self.safe_update_message(f"LOT {lot_number} - PASS result saved and displayed", "green")
                    else:
                        self.safe_update_message(f"LOT {lot_number} - FAIL result saved (not displayed in tree)", "orange")
                    
                    # Start 3-second timer for automatic reset
                    self.safe_update_message("Resetting in 3 seconds...", "blue")
                    self.root.after(3000, self.reset_page_for_next_test)
                else:
                    self.safe_update_message("Failed to save to database", "red")
            else:
                self.safe_update_message("No test results found - nothing to save", "orange")
            
        except Exception as e:
            print(f"Error in next_label_command: {e}")
            traceback.print_exc()
            self.safe_update_message(f"Error: {e}", "red")

    def reset_page_for_next_test(self):
        """Reset the page for next test while keeping PLC connection active and maintaining PLC high state"""
        try:
            print("Resetting page for next test...")
            
            # Clear current lot number
            if hasattr(self, 'current_lot_number'):
                delattr(self, 'current_lot_number')
            
            # Clear and reset entries
            self.alc_entry.delete(0, tk.END)
            self.alc_entry.insert(0, "ALC CODE")
            self.alc_entry.configure(state='disabled')
            
            self.emp_entry.delete(0, tk.END)
            self.emp_entry.insert(0, "EMP CODE")
            self.emp_entry.configure(bg="white")
            self.emp_entry.focus_set()
            
            # Clear barcode data
            self.barcode_data = ""
            
            # Reset test result saved flag for next test cycle
            self.test_result_saved = False
            self.last_test_result_pass_state = False
            self.last_test_result_ng_state = False
            
            # Clear camera textbox
            if hasattr(self, 'cam_textbox'):
                self.cam_textbox.delete("1.0", tk.END)
            
            # Reset specification tree - clear actual values and results
            if hasattr(self, 'spec_tree') and self.spec_tree:
                for item in self.spec_tree.get_children():
                    values = list(self.spec_tree.item(item, "values"))
                    if len(values) >= 7:
                        values[-2] = ""  # Clear Actual column
                        values[-1] = ""  # Clear Result column
                        self.spec_tree.item(item, values=values, tags=('neutral',))
            
            # Reset process status labels to default but keep PLC in high state
            self.reset_process_status_labels_keep_plc_high()
            
            # Clear any placed labels (keep the image but remove test indicators)
            if hasattr(self, 'placed_labels'):
                for label in self.placed_labels.values():
                    label.configure(bg="yellow")  # Reset to default color
            
            # Stop all label blinking
            self.stop_all_label_blinking()
            
            # Reset model header
            if hasattr(self, 'model_header'):
                self.model_header.config(text="MODEL - PART NUMBER")
            
            # Keep PLC connection active and maintain high state - DO NOT reset PLC
            # Continue monitoring without interruption
            print("Page reset complete - PLC connection and high state maintained")
            self.safe_update_message("Ready for next test - Scan employee code", "blue")
            
            # Restart monitoring after a brief delay to ensure clean state
            self.root.after(1000, self.restart_monitoring_after_reset)
            
        except Exception as e:
            print(f"Error resetting page: {e}")
            self.safe_update_message(f"Error resetting page: {e}", "red")

    def restart_monitoring_after_reset(self):
        """Restart monitoring after page reset to ensure clean operation"""
        try:
            if hasattr(self, 'plc_client') and self.plc_client and self.plc_client.is_socket_open():
                if hasattr(self, 'current_part_number') and self.current_part_number:
                    print("Restarting monitoring after page reset")
                    self.start_status_monitoring()
                    self.safe_update_message("Monitoring restarted - Ready for next LOT number", "green")
                else:
                    print("No part number selected - monitoring not restarted")
            else:
                print("PLC not connected - cannot restart monitoring")
        except Exception as e:
            print(f"Error restarting monitoring: {e}")

    def reset_process_status_labels(self):
        """Reset all process status labels to default blue state"""
        try:
            # List of status labels to reset
            status_labels = ['auto', 'home', '1st', '2nd', 'test']
            
            for label_name in status_labels:
                label_obj = getattr(self, f"{label_name}_label", None)
                if label_obj:
                    label_obj.config(bg="#00BFFF")  # Default blue color
                    print(f"Reset {label_name} label to default")
            
        except Exception as e:
            print(f"Error resetting process status labels: {e}")
    
    def reset_process_status_labels_keep_plc_high(self):
        """Reset process status labels to default but maintain PLC high state visual indicators"""
        try:
            # List of status labels to reset - but keep their current state if PLC is high
            status_labels = ['auto', 'home', '1st', '2nd', 'test']
            
            # Read current PLC state to maintain visual consistency
            if hasattr(self, 'plc_client') and self.plc_client and self.plc_client.is_socket_open():
                status_values = self.read_process_status_values()
                
                for label_name in status_labels:
                    label_obj = getattr(self, f"{label_name}_label", None)
                    if label_obj:
                        # Check if this label corresponds to a high PLC state
                        plc_state_active = False
                        
                        # Map label names to their PLC status check
                        if label_name == 'auto' and hasattr(self, 'process_status_array') and len(self.process_status_array) > 0:
                            auto_address = self.process_status_array[0] if self.process_status_array[0] else None
                            plc_state_active = status_values.get(auto_address, False) if auto_address else False
                        elif label_name == 'home' and hasattr(self, 'process_status_array') and len(self.process_status_array) > 1:
                            home_address = self.process_status_array[1] if self.process_status_array[1] else None
                            plc_state_active = status_values.get(home_address, False) if home_address else False
                        elif label_name == 'test' and hasattr(self, 'process_status_array') and len(self.process_status_array) > 4:
                            test_address = self.process_status_array[4] if self.process_status_array[4] else None
                            plc_state_active = status_values.get(test_address, False) if test_address else False
                        
                        # Set color based on PLC state
                        if plc_state_active:
                            label_obj.config(bg="green")  # Keep green for active PLC states
                            print(f"Maintained {label_name} label as active (green)")
                        else:
                            label_obj.config(bg="#00BFFF")  # Default blue color
                            print(f"Reset {label_name} label to default")
            else:
                # PLC not connected, reset all to default
                for label_name in status_labels:
                    label_obj = getattr(self, f"{label_name}_label", None)
                    if label_obj:
                        label_obj.config(bg="#00BFFF")  # Default blue color
                        print(f"Reset {label_name} label to default (PLC not connected)")
            
        except Exception as e:
            print(f"Error resetting process status labels while keeping PLC high: {e}")
            # Fallback to regular reset if there's an error
            self.reset_process_status_labels()

    def get_device_result_from_spec_tree(self, device_name):
        """Get the PASS/NG result for a specific device from the spec tree"""
        if not hasattr(self, 'spec_tree') or not self.spec_tree:
            return None
            
        for item in self.spec_tree.get_children():
            values = self.spec_tree.item(item, "values")
            if len(values) > 1 and values[1] == device_name:
                # Return the result column (last column)
                return values[-1] if len(values) > 5 else None
        return None

    def get_spec_result(self, device_name):
        """Get the result value for a specific device from the spec tree"""
        if not hasattr(self, 'spec_tree') or not self.spec_tree:
            return None
            
        # Loop through all rows in the spec tree
        for item in self.spec_tree.get_children():
            values = self.spec_tree.item(item, "values")
            # Check if the device column matches the requested device
            if len(values) > 1 and values[1] == device_name:
                # Return the result column value (last column)
                return values[-1] if values[-1] else None
                
        return None

    def save_lot_data_to_database(self, values_dict):
        """Save lot number data to database and return success status"""
        conn = None
        cursor = None
        try:
            # Validate values
            if not values_dict or "LOT NUMBER" not in values_dict:
                print("Invalid values provided for database save")
                return False
                
            # Connect to database
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="12345",
                database="EOL"
            )
            
            cursor = conn.cursor()
            
            # Check if table exists, create if not
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS TBL_TEST_RESULTS (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    LOT_NUMBER VARCHAR(255),
                    PART_NUMBER VARCHAR(255),
                    L1 VARCHAR(50),
                    L2 VARCHAR(50),
                    L3 VARCHAR(50),
                    L4 VARCHAR(50),
                    P1 VARCHAR(50),
                    P2 VARCHAR(50),
                    P3 VARCHAR(50),
                    P4 VARCHAR(50),
                    RESULT VARCHAR(50),
                    SCAN_RESULT VARCHAR(255),
                    CREATED_BY VARCHAR(255),
                    CREATED_DATE DATETIME
                )
            """)
            
            # Get values for insertion
            lot_number = values_dict.get("LOT NUMBER", "")
            part_number = getattr(self, 'current_part_number', '')
            
            # Get employee code
            emp_code = self.emp_entry.get() if (self.emp_entry.get() and self.emp_entry.get() != "EMP CODE") else "Unknown"
            
            # Get all device values - store everything directly in the main columns
            # All obtained values (whether numeric measurements or PASS/NG results) go directly to L1-L4, P1-P4
            device_values = {}
            
            for device in ["L1", "L2", "L3", "L4", "P1", "P2", "P3", "P4"]:
                if device in values_dict:
                    raw_value = values_dict[device]
                    device_values[device] = raw_value
                else:
                    device_values[device] = ""
            
            l1_value = device_values.get("L1", "")
            l2_value = device_values.get("L2", "")
            l3_value = device_values.get("L3", "")
            l4_value = device_values.get("L4", "")
            p1_value = device_values.get("P1", "")
            p2_value = device_values.get("P2", "")
            p3_value = device_values.get("P3", "")
            p4_value = device_values.get("P4", "")
            
            
            result = values_dict.get("RESULT", "")
            scan_result = f"LOT: {lot_number}"
            
            # Print debug info about what's being saved
            print(f"Database Save - LOT: {lot_number}, Part: {part_number}, Employee: {emp_code}")
            print(f"Values - L1:{l1_value}, L2:{l2_value}, L3:{l3_value}, L4:{l4_value}")
            print(f"Values - P1:{p1_value}, P2:{p2_value}, P3:{p3_value}, P4:{p4_value}")
            print(f"Overall Result: {result}")
            
            # Check if record already exists
            cursor.execute(
                "SELECT ID FROM TBL_TEST_RESULTS WHERE LOT_NUMBER = %s AND PART_NUMBER = %s",
                (lot_number, part_number)
            )
            existing_record = cursor.fetchone()
            
            if existing_record:
                # Update existing record
                query = """
                UPDATE TBL_TEST_RESULTS 
                SET L1 = %s, L2 = %s, L3 = %s, L4 = %s, 
                    P1 = %s, P2 = %s, P3 = %s, P4 = %s,
                    RESULT = %s, SCAN_RESULT = %s,
                    CREATED_BY = %s, 
                    CREATED_DATE = %s 
                WHERE LOT_NUMBER = %s AND PART_NUMBER = %s
                """
                cursor.execute(query, (
                    l1_value, l2_value, l3_value, l4_value,
                    p1_value, p2_value, p3_value, p4_value,
                    result, scan_result,
                    emp_code, 
                    datetime.now(), 
                    lot_number, 
                    part_number
                ))
                print(f"Updated existing database record for LOT {lot_number}")
            else:
                # Insert new record
                query = """
                INSERT INTO TBL_TEST_RESULTS 
                (LOT_NUMBER, PART_NUMBER, L1, L2, L3, L4, P1, P2, P3, P4, 
                 RESULT, SCAN_RESULT, CREATED_BY, CREATED_DATE) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (
                    lot_number, 
                    part_number, 
                    l1_value, l2_value, l3_value, l4_value,
                    p1_value, p2_value, p3_value, p4_value,
                    result, scan_result,
                    emp_code, 
                    datetime.now()
                ))
                print(f"Inserted new database record for LOT {lot_number}")
            
            # Commit changes
            conn.commit()
            print(f"Database save successful for LOT {lot_number}")
            return True
            
        except mysql.connector.Error as e:
            print(f"Database error: {str(e)}")
            return False
        except Exception as e:
            print(f"Error saving to database: {str(e)}")
            return False
        finally:
            # Ensure cleanup
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            
    def add_to_tree(self, lotnum, pass_tests, total_tests):
        """Add entry to the treeview"""
        # Create default values for all columns
        test_results = ["N/A"] * 8  # L1, L2, L3, L4, P1, P2, P3, P4
        
        # Map test indices to column positions
        # The tests are: L1, L2, L3, L4, P1, P2, P3, P4
        for test_idx in range(8):
            if test_idx in pass_tests:
                test_results[test_idx] = "PASS"
            else:
                test_results[test_idx] = "FAIL"
        
        # Overall pass only if all tests passed
        overall_result = "PASS" if len(pass_tests) == total_tests else "FAIL"
        
        # Create full values tuple
        values = [lotnum] + test_results + [overall_result]
        
        # Insert into treeview
        self.tree.insert("", "end", text=lotnum, values=values)
        
        return values

    def get_available_alc_codes(self):
        """Fetch all available ALC codes from the database"""
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="12345",
                database="EOL"
            )
            
            cursor = conn.cursor()
            
            # Query to get all unique ALC codes
            query = """
            SELECT DISTINCT MM_ALC_CODE, MM_MODEL_NAME, MM_PART_NUMBER 
            FROM TBL_MODEL_MASTER 
            WHERE MM_ALC_CODE IS NOT NULL AND MM_ALC_CODE != ''
            ORDER BY MM_MODEL_NAME
            """
            
            cursor.execute(query)
            
            # Format results as a list of dictionaries
            results = []
            for row in cursor.fetchall():
                results.append({
                    'alc_code': row[0],
                    'model_name': row[1],
                    'part_number': row[2]
                })
                
            cursor.close()
            conn.close()
            
            return results
            
        except mysql.connector.Error as e:
            print(f"Database error while fetching ALC codes: {str(e)}")
            self.safe_update_message(f"Database error: {str(e)}", "red")
            return []
        except Exception as e:
            print(f"Error fetching ALC codes: {str(e)}")
            self.safe_update_message(f"Error: {str(e)}", "red")
            return []
    
    def show_alc_code_selection(self):
        """Show dialog to select an ALC code from the database"""
        try:
            # Get available ALC codes
            alc_codes = self.get_available_alc_codes()
            
            if not alc_codes:
                messagebox.showinfo("No Data", "No ALC codes found in database")
                return
                
            # Create selection dialog
            selection_window = tk.Toplevel(self.root)
            selection_window.title("Select ALC Code")
            selection_window.geometry("500x300")
            selection_window.transient(self.root)  # Set as transient to main window
            selection_window.grab_set()  # Modal behavior
            
            # Create listbox with scrollbar
            frame = tk.Frame(selection_window)
            frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Listbox header
            header_frame = tk.Frame(frame)
            header_frame.pack(fill="x")
            
            tk.Label(header_frame, text="ALC Code", width=15, font=("Arial", 10, "bold")).pack(side="left")
            tk.Label(header_frame, text="Model", width=20, font=("Arial", 10, "bold")).pack(side="left")
            tk.Label(header_frame, text="Part Number", width=15, font=("Arial", 10, "bold")).pack(side="left")
            
            # Listbox with scrollbar
            list_frame = tk.Frame(frame)
            list_frame.pack(fill="both", expand=True)
            
            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")
            
            listbox = tk.Listbox(list_frame, width=50, height=10, yscrollcommand=scrollbar.set)
            listbox.pack(side="left", fill="both", expand=True)
            
            scrollbar.config(command=listbox.yview)
            
            # Populate the listbox
            for i, item in enumerate(alc_codes):
                display_text = f"{item['alc_code']} - {item['model_name']} - {item['part_number']}"
                listbox.insert("end", display_text)
                # Store the original data with the listbox item
                listbox.itemconfig(i, {"bg": "#f0f0f0" if i % 2 == 0 else "#ffffff"})
            
            # Button frame
            button_frame = tk.Frame(selection_window)
            button_frame.pack(fill="x", padx=10, pady=10)
            
            # Cancel button
            cancel_btn = tk.Button(
                button_frame, 
                text="Cancel", 
                command=selection_window.destroy,
                width=10
            )
            cancel_btn.pack(side="right", padx=5)
            
            # Select button
            def on_select():
                selection = listbox.curselection()
                if selection:
                    index = selection[0]
                    selected_item = alc_codes[index]
                    
                    # Set the ALC code in the entry field
                    self.alc_entry.delete(0, tk.END)
                    self.alc_entry.insert(0, selected_item['alc_code'])
                    
                    # Process the ALC code
                    self.process_alc_code()
                    
                    selection_window.destroy()
            
            select_btn = tk.Button(
                button_frame, 
                text="Select", 
                command=on_select,
                bg="#4CAF50",
                fg="white",
                width=10
            )
            select_btn.pack(side="right", padx=5)
            
            # Double-click to select
            listbox.bind("<Double-1>", lambda e: on_select())
            
            # Set focus
            listbox.focus_set()
            
            # Center the window
            selection_window.update_idletasks()
            width = selection_window.winfo_width()
            height = selection_window.winfo_height()
            x = (self.root.winfo_width() // 2) - (width // 2)
            y = (self.root.winfo_height() // 2) - (height // 2)
            selection_window.geometry(f"+{x}+{y}")
            
        except Exception as e:
            print(f"Error showing ALC code selection: {str(e)}")
            messagebox.showerror("Error", f"Could not show ALC code selection: {str(e)}")
            
    def get_lot_history(self, limit=50):
        """Get lot test result history from database"""
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="12345",
                database="EOL"
            )
            
            cursor = conn.cursor()
            
            # Get current part number if available
            part_number = getattr(self, 'current_part_number', '')
            
            if part_number:
                # If part number is available, filter by it
                query = """
                SELECT LOT_NUMBER, L1, L2, L3, L4, P1, P2, P3, P4, RESULT, SCAN_RESULT, CREATED_DATE
                FROM TBL_TEST_RESULTS
                WHERE PART_NUMBER = %s
                ORDER BY CREATED_DATE DESC
                LIMIT %s
                """
                cursor.execute(query, (part_number, limit))
            else:
                # Otherwise get the most recent results
                query = """
                SELECT LOT_NUMBER, L1, L2, L3, L4, P1, P2, P3, P4, RESULT, SCAN_RESULT, CREATED_DATE
                FROM TBL_TEST_RESULTS
                ORDER BY CREATED_DATE DESC
                LIMIT %s
                """
                cursor.execute(query, (limit,))
            
            # Get results
            results = cursor.fetchall()
            
            # Close connection
            cursor.close()
            conn.close()
            
            return results
            
        except mysql.connector.Error as e:
            print(f"Database error in get_lot_history: {str(e)}")
            return []
        except Exception as e:
            print(f"Error in get_lot_history: {str(e)}")
            return []

    def load_history_to_treeview(self):
        """Load lot history from database to treeview"""
        try:
            # Get lot history
            history = self.get_lot_history()
            
            if not history:
                self.safe_update_message("No history found", "blue")
                return
                
            # Clear treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Count records for reporting
            total_records = len(history)
            displayed_records = 0
                
            # Add history items to treeview
            for item in history:
                # Create a dictionary to map column names to values
                values_dict = {}
                values_dict["LOT NUMBER"] = item[0] if len(item) > 0 else ""
                
                # Track if this record has any device values with results
                has_device_values = False
                all_devices_pass = True
                
                # Map database columns to treeview columns
                db_columns = ["L1", "L2", "L3", "L4", "P1", "P2", "P3", "P4", "RESULT", "SCAN RESULT"]
                for i, col in enumerate(db_columns, 1):
                    if i < len(item):
                        db_value = item[i]
                        if db_value and db_value != "N/A":
                            has_device_values = True
                            
                            # For device columns (L1-P4), determine PASS/NG based on values
                            if i <= 8:  # Only the device columns (L1-P4)
                                try:
                                    # Try to convert the value to float for comparison
                                    # This is a simplified check - in a real implementation,
                                    # you'd need to load the min/max specs for this part number
                                    # Here we're just checking if the value exists
                                    float(db_value)
                                    # If we can parse it as a float, consider it PASS
                                    values_dict[col] = "PASS"
                                except (ValueError, TypeError):
                                    # If it's not a numeric value, check if it's a result value
                                    if db_value == "PASS":
                                        values_dict[col] = "PASS"
                                    elif db_value == "NG" or db_value == "FAIL":
                                        values_dict[col] = "NG"
                                        all_devices_pass = False
                                    else:
                                        # For any other value, just use it directly
                                        values_dict[col] = db_value
                            else:
                                # For non-device columns, use the value directly
                                values_dict[col] = db_value or "N/A"
                        else:
                            values_dict[col] = "N/A"
                
                # Only display records that have overall PASS or all existing device columns show PASS
                if has_device_values and (item[9] == "PASS" or all_devices_pass):
                    # Create values list in the same order as self.current_columns
                    values = []
                    for col in self.current_columns:
                        values.append(values_dict.get(col, "N/A"))
                    
                    # Insert the record into the tree
                    self.tree.insert("", "end", text=values[0], values=tuple(values))
                    displayed_records += 1
                
            # Display message about records
            if displayed_records > 0:
                self.safe_update_message(f"Loaded {displayed_records} PASS records (filtered from {total_records} total records)", "green")
            else:
                self.safe_update_message(f"No PASS records found (filtered from {total_records} total records)", "blue")
            
        except Exception as e:
            print(f"Error loading history: {str(e)}")
            traceback.print_exc()
            self.safe_update_message(f"Error loading history: {str(e)}", "red")

    def read_hold_registers(self, start_index, num_registers=4):
        """Read a range of hold registers from the PLC and return values in order"""
        try:
            if not self.plc_client or not self.plc_client.is_socket_open():
                print("PLC not connected")
                return None
                
            # Read hold register addresses from file
            txt_files_dir = os.path.join(os.path.dirname(__file__), 'txt_files')
            hold_registers_file = os.path.join(txt_files_dir, 'HoldRegistersRead.txt')
            
            if not os.path.exists(hold_registers_file):
                print(f"Hold registers file not found: {hold_registers_file}")
                return None
                
            with open(hold_registers_file, 'r') as f:
                register_line = f.readline().strip()
                register_addresses = [addr.strip() for addr in register_line.split(',')]
                
            if not register_addresses:
                print("No register addresses found in HoldRegistersRead.txt")
                return None
                
            # Check if we have enough addresses
            if start_index >= len(register_addresses):
                print(f"Start index {start_index} is out of range. Only have {len(register_addresses)} addresses.")
                return None
                
            # Adjust num_registers if needed
            if start_index + num_registers > len(register_addresses):
                print(f"Not enough register addresses. Requested indices {start_index} to {start_index+num_registers-1}, but only have {len(register_addresses)} addresses.")
                num_registers = len(register_addresses) - start_index
                
            if num_registers <= 0:
                return None
                
            # Get the requested addresses
            requested_addresses = register_addresses[start_index:start_index+num_registers]
            print(f"Reading hold registers: {requested_addresses}")
            
            # Read each register
            station_id = int(os.getenv('PLC_STATION_ID', '1'))
            results = {}
            
            for addr_str in requested_addresses:
                try:
                    # Extract register number from address string
                    if addr_str.startswith('D'):
                        reg_num = int(addr_str[1:])
                    else:
                        reg_num = int(addr_str)
                        
                    print(f"Reading register {addr_str} (number {reg_num})")
                        
                    # Read register value
                    response = self.plc_client.read_holding_registers(
                        address=reg_num,
                        count=1,
                        slave=station_id
                    )
                    
                    if not response.isError():
                        # Get raw register value (unsigned 16-bit)
                        raw_value = response.registers[0]
                        
                        # Convert to signed 16-bit integer if needed
                        # If the value is greater than 32767, it represents a negative number
                        if raw_value > 32767:
                            signed_value = raw_value - 65536
                        else:
                            signed_value = raw_value
                        
                        results[addr_str] = signed_value
                        print(f"Register {addr_str} = {signed_value} (raw: {raw_value})")
                    else:
                        print(f"Error reading register {addr_str}: {response}")
                        results[addr_str] = None
                except Exception as e:
                    print(f"Error reading register {addr_str}: {str(e)}")
                    results[addr_str] = None
                    
            return results
                
        except Exception as e:
            print(f"Error reading hold registers: {e}")
            traceback.print_exc()
            return None

    def update_spec_tree_with_register_values(self, register_values, device_prefix):
        """Update specification tree with values from registers"""
        if not register_values or not hasattr(self, 'spec_tree'):
            return
            
        # Get a list of register keys in order
        reg_keys = list(register_values.keys())
        if len(reg_keys) == 0:
            return
            
        # Create device names to look for in the spec tree (L1, L2, L3, L4 or P1, P2, P3, P4)
        devices = []
        for i in range(1, min(len(reg_keys) + 1, 5)):
            devices.append(f"{device_prefix}{i}")
            
        print(f"Updating spec tree for devices: {devices}")
        
        # Configure color tags if not already done
        if not hasattr(self, 'spec_color_tags_configured'):
            style = ttk.Style()
            self.spec_tree.tag_configure('pass', background='#90EE90')  # Light green for PASS
            self.spec_tree.tag_configure('ng', background='#FFCCCB')    # Light red for NG
            self.spec_tree.tag_configure('neutral', background='#FFFFFF')  # White for neutral
            self.spec_tree.tag_configure('value', background='#ADD8E6')  # Light blue for values
            
            # Store that we've configured the tags
            self.spec_color_tags_configured = True
        
        # Keep track of which devices were updated
        updated_devices = set()
        
        # Update each device in the specification tree
        for item in self.spec_tree.get_children():
            values = list(self.spec_tree.item(item, "values"))
            
            # Check the Device column (index 1)
            if len(values) > 1:
                device = values[1]
                
                # If this is one of our target devices (L1-L4 or P1-P4)
                if device in devices:
                    # Get device index (0-3)
                    device_index = int(device[1:]) - 1
                    
                    # If we have a register value for this index
                    if device_index < len(reg_keys):
                        reg_key = reg_keys[device_index]
                        reg_value = register_values[reg_key]
                        
                        if reg_value is not None:
                            # Store original values to compare for changes
                            old_values = values.copy()
                            
                            # Update the Actual column (second to last column)
                            values[-2] = f"{reg_value}"
                            
                            # Get min/max from columns 3 and 4
                            min_val = values[3] if len(values) > 3 and values[3] != "N/A" else None
                            max_val = values[4] if len(values) > 4 and values[4] != "N/A" else None
                            
                            # Default to no specific tag
                            result_tag = 'neutral'
                            
                            try:
                                # Convert to float for comparison
                                reg_float = float(reg_value)
                                min_float = float(min_val) if min_val else None
                                max_float = float(max_val) if max_val else None
                                
                                # Determine PASS/NG based on min/max comparison
                                if (min_float is None or reg_float >= min_float) and \
                                   (max_float is None or reg_float <= max_float):
                                    values[-1] = "PASS"
                                    result_tag = 'pass'
                                else:
                                    values[-1] = "NG"
                                    result_tag = 'ng'
                            except (ValueError, TypeError):
                                # If conversion fails, leave result unchanged
                                print(f"Error converting values for comparison: {reg_value}, {min_val}, {max_val}")
                            
                            # Update the tree item with new values
                            self.spec_tree.item(item, values=values)
                            
                            # Apply tag to color the row according to result
                            self.spec_tree.item(item, tags=(result_tag,))
                            
                            # If values changed, apply a visual highlight
                            if values != old_values:
                                # Flash the row briefly to highlight the change
                                self.flash_spec_row(item, result_tag)
                            
                            updated_devices.add(device)
                            print(f"Updated {device} with value {reg_value} from register {reg_key}, result={values[-1]}")
                            
        # Report any devices that weren't found
        for device in devices:
            if device not in updated_devices:
                print(f"Warning: Device {device} not found in specification tree")
                
    def flash_spec_row(self, item, final_tag):
        """Briefly flash a row to highlight it was updated"""
        # Store original tag
        original_tag = final_tag
        
        # Flash sequence: highlight → original → highlight → original
        def flash_sequence(count=0):
            if count >= 4:  # End after 4 changes
                self.spec_tree.item(item, tags=(original_tag,))
                return
                
            # Toggle between highlight and original
            if count % 2 == 0:
                self.spec_tree.item(item, tags=('value',))  # Highlight with blue
            else:
                self.spec_tree.item(item, tags=(original_tag,))  # Back to original
                
            # Schedule next flash
            self.root.after(250, lambda: flash_sequence(count + 1))
            
        # Start the flash sequence
        flash_sequence()

    def get_actual_value(self, device_name):
        """Get the actual value for a specific device from the spec tree"""
        if not hasattr(self, 'spec_tree') or not self.spec_tree:
            return None
            
        # Loop through all rows in the spec tree
        for item in self.spec_tree.get_children():
            values = self.spec_tree.item(item, "values")
            # Check if the device column matches the requested device
            if len(values) > 1 and values[1] == device_name:
                # Return the actual column value (second to last column)
                return values[-2] if len(values) > 2 else None
                
        return None

def main():
    try:
        root = tk.Tk()
        
        # Force-close any lingering connections before starting
        try:
            # Try to release COM ports before initialization
            plc_port = os.getenv('PLC_COM_PORT')
            if plc_port:
                try:
                    test_serial = serial.Serial(plc_port)
                    test_serial.close()
                    print(f"Pre-startup: Successfully released {plc_port}")
                except Exception as e:
                    print(f"Pre-startup: COM port {plc_port} may already be in use: {e}")
        except Exception as e:
            print(f"Error in pre-startup cleanup: {e}")
            
        # Initialize the application with error handling
        app = EOLTesterGUI(root)
        
        # Window closing is now handled by the class itself
        root.mainloop()
    except Exception as e:
        print(f"Critical error in main: {e}")
        messagebox.showerror("Critical Error", f"Application failed to start: {e}")
        try:
            if 'root' in locals() and root:
                root.destroy()
        except:
            pass

if __name__ == "__main__":
    main()


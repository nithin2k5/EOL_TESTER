import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import mysql.connector
import threading
import json
from pymodbus.client import ModbusSerialClient, ModbusTcpClient  # PLC functionality restored
import serial
from serial.tools import list_ports  # Proper import for port enumeration
import time
import traceback
from datetime import datetime
import sys
import queue
import math

import config
import db
import ui
import customtkinter as ctk


class SerializedModbusClient:
    """A Modbus client that lets one request through at a time.

    The status worker thread and the Tk thread both talk to the PLC. On a
    serial line two requests in flight at once garble each other's frames,
    so every call on the client goes through one lock.
    """

    def __init__(self, client):
        self._client = client
        self._lock = threading.RLock()

    def __getattr__(self, name):
        attr = getattr(self._client, name)
        if not callable(attr):
            return attr

        def call(*args, **kwargs):
            with self._lock:
                return attr(*args, **kwargs)
        return call


def send_raw_to_printer(printer_name, data):
    """Send bytes to a Windows printer untranslated.

    Label templates are printer command language, so they must reach the
    printer as-is rather than through a driver's page rendering.
    """
    import ctypes
    from ctypes import wintypes

    class DOC_INFO_1(ctypes.Structure):
        _fields_ = [("pDocName", wintypes.LPWSTR),
                    ("pOutputFile", wintypes.LPWSTR),
                    ("pDatatype", wintypes.LPWSTR)]

    winspool = ctypes.WinDLL("winspool.drv", use_last_error=True)
    handle = wintypes.HANDLE()
    if not winspool.OpenPrinterW(printer_name, ctypes.byref(handle), None):
        raise OSError(f"Printer '{printer_name}' not found (error {ctypes.get_last_error()})")
    try:
        doc = DOC_INFO_1("EOL BARCODE LABEL", None, "RAW")
        if not winspool.StartDocPrinterW(handle, 1, ctypes.byref(doc)):
            raise OSError(f"Could not start print job (error {ctypes.get_last_error()})")
        try:
            winspool.StartPagePrinter(handle)
            written = wintypes.DWORD()
            ok = winspool.WritePrinter(handle, data, len(data), ctypes.byref(written))
            winspool.EndPagePrinter(handle)
            if not ok or written.value != len(data):
                raise OSError(f"Printer accepted {written.value} of {len(data)} bytes "
                              f"(error {ctypes.get_last_error()})")
        finally:
            winspool.EndDocPrinter(handle)
    finally:
        winspool.ClosePrinter(handle)


class EOLTesterGUI:
    def __init__(self, root):
        self.root = root
        ui.apply(root)
        
        # Get machine ID from environment
        machine_id = config.get('MACHINE_ID', '')
        
        # Set title with machine ID
        title = "EOL (END OF LINE) TESTER"
        if machine_id:
            title += f" - Machine ID: {machine_id}"
        self.root.title(title)
        
        # Initialize variables before setting up the window
        self.initialize_variables()
        
        # Set up the window after initialization
        self.root.after(100, self.setup_window)  # Delay window setup slightly
        
        # Set up window closing handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Continue with the rest of your initialization...

    def ensure_settings_file_exists(self):
        """Make sure the settings file exists; config.py creates it on demand."""
        config.reload()
        return config.CONFIG_FILE

    def load_plc_config(self):
        """Load PLC configuration from the settings file"""
        try:
            # PLC connection settings
            self.plc_com_port = config.get('PLC_COM_PORT', 'COM5').strip("'")
            self.plc_baud_rate = int(config.get('PLC_BAUD_RATE', '38400'))
            self.plc_station_id = int(config.get('PLC_STATION_ID', '1'))
            
            # TCP settings (if available)
            self.plc_tcp_ip = config.get('MODBUS_TCP_IP', '').strip("'")
            self.plc_tcp_port = int(config.get('MODBUS_TCP_PORT', '502')) if config.get('MODBUS_TCP_PORT') else 502
            
            # Register settings
            self.plc_reg_address = config.get('PLC_REG_ADDRESS', '').strip("'")
            self.plc_points_to_read = int(config.get('PLC_POINTS_TO_READ', '1'))

            # Per-request timeout and retries. Keep them short: every PLC
            # request waits its turn, so one the PLC never answers holds up
            # all the others, including the window's own.
            self.plc_timeout = config.get_int('PLC_READ_TIMEOUT', 500) / 1000.0
            self.plc_retries = config.get_int('PLC_RETRIES', 0)
            
            print(f"PLC Config loaded - COM: {self.plc_com_port}, Baud: {self.plc_baud_rate}, Station: {self.plc_station_id}")
            if self.plc_tcp_ip:
                print(f"PLC TCP Config - IP: {self.plc_tcp_ip}, Port: {self.plc_tcp_port}")
                
        except Exception as e:
            print(f"Error loading PLC configuration: {e}")
            # Set defaults
            self.plc_com_port = 'COM5'
            self.plc_baud_rate = 38400
            self.plc_station_id = 1
            self.plc_tcp_ip = ''
            self.plc_tcp_port = 502
            self.plc_timeout = 0.5
            self.plc_retries = 0

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
        
        # Thread-safe queue for PLC status updates
        self.plc_status_queue = queue.Queue(maxsize=10)
        self.plc_read_thread = None
        self.plc_thread_running = False
        
        # Initialize PLC connection status
        self.plc_connected = False
        self.plc_client = None
        
        # Hold register addresses for loadcell/pressure data
        self.hold_register_addresses = []
        self.latest_register_data = {}  # Store latest register readings
        
        # Process step tracking - ensure all 8 steps are visited
        self.visited_steps = set()  # Track which steps have been visited
        self.step_visit_times = {}  # Track when each step was visited
        self.required_steps = ['M0067', 'M0068', 'M0076', 'M0085', 'M0078', 'M0087', 'M0075', 'M0079']
        self.last_active_step = None  # Track last active step for transition detection
        
        # P0000 keep-alive to prevent PLC from stopping
        self.p0000_keepalive_active = False
        self.p0000_last_write = 0
        
        # Dynamic monitoring - adjust speed based on PLC activity
        self.monitoring_interval = 3000  # Start with 3 seconds
        self.last_status_values = {}  # Track last status to detect changes
        
        # Make sure the settings file exists and is freshly read
        self.ensure_settings_file_exists()
        
        # Load PLC configuration from the settings file
        self.load_plc_config()
        
        # Get machine ID from the settings file and store it
        self.machineid = config.get('MACHINE_ID', 'Not Set')
        
        # Initialize arrays for different data types
        self.process_status_array = []
        self.program_selection_array = []
        self.input_sensors_array = []
        self.employee_codes = []
        
        # Employee validation system
        self.current_employee_id = None
        self.employee_validation_complete = False
        self.authorized_employee_codes = []
        self.current_part_number = None
        self.current_lot_number = None
        self.specifications = {}
        
        # Initialize additional variables  
        self.keepWriting = False
        self.breakLoop = False
        
        # Initialize loadcell clients
        self.loadcell1_client = None
        self.loadcell2_client = None
        
        # Initialize test flow variables
        self.rcvdTestRslt = False
        self.awaiting_result_clear = False
        self.plc_status_loop_running = False
        # Most recent coil snapshot from the worker thread, for code on the
        # Tk thread that must not wait on the PLC itself
        self.latest_plc_status = {}

        # Labels on the part image and the sensors behind them. The worker
        # thread reads sensor_label_keys and writes sensor_states; the Tk
        # thread owns placed_labels.
        self.placed_labels = {}
        self.sensor_label_keys = []
        self.sensor_states = {}
        self.input_sensor_addresses = []

        # The printed label waiting to be scanned, if any
        self.current_alc_code = ""
        self.awaiting_label_scan = False
        self.label_scan_code = ""
        self.loadcell01Value = 0.0
        self.loadcell02Value = 0.0
        self.loadcell03Value = 0.0
        self.loadcell04Value = 0.0
        self.L1MaxValue = 0.0
        self.L2MaxValue = 0.0
        self.L3MaxValue = 0.0
        self.L4MaxValue = 0.0
        self.P01Value = 0.0
        self.P02Value = 0.0
        self.P03Value = 0.0
        self.P04Value = 0.0
        self.failCounter = 0
        self.passCounter = 0
        self.columnL2 = False
        self.columnL3 = False
        self.columnL4 = False
        self.columnP3 = False
        self.columnP4 = False
        self.cam1Result = ""
        self.deviceToRead = []
        self.inputSensorsToReadList = []
        self.mldDataTable = []
        
        # Database configuration for test flow
        self.db_config = db.get_config()
        
        # Part information variables
        self.partNumber = ""
        self.modelName = ""
        self.vendorCode = ""
        self.eoNumber = ""
        self.specialData = ""
        self.initialID = ""
        self.supplierSection = ""
        self.lotNo = ""
        self.traceabilityCode = ""
        self.today = datetime.today().date()
        self.dataPointX = 0

        # Plotted chart points, keyed by series name
        self.chart_series = {name: [] for name in
                             ('L1', 'L2', 'L3', 'L4', 'P1', 'P2', 'P3', 'P4')}

        self.barcodePrintFileName = ""
        self.prnFileContent = ""
        self.programSelectionPLCAddress = ""
        self.machineOnPLCCoilAddress = ""
        self.alertOnPLCCoilAddress = ""
        self.partRunningSerialExists = False
        
        # NG Cable validation flags
        self.startingNGCableValidation = False
        self.endingNGCableValidation = False
        self.endingNGCableValidated = False
        
        # Barcode scanning variables
        self.printedLabelScanDataInput_Received = False
        self.alcInput_TimeInterval = 3000
        self.printedLabelScanDataInput_TimeInterval = 4000
        self.printedLabelScanDataInput_WaitTime = 6000
        self.alertOn_TimeInterval = 5000
        
        # EOL Testing Variables
        self.alcInput_TimeInterval = 3000  # 3000ms for manual entry
        # Label scan timings come from the Testing section of .config
        self.printedLabelScanDataInput_TimeInterval = config.get_int('PRINTED_LABEL_SCAN_TIME_INTERVAL', 4000)
        self.printedLabelScanDataInput_WaitTime = config.get_int('PRINTED_LABEL_SCAN_WAIT_TIME', 6000)
        self.alertOn_TimeInterval = config.get_int('ALERT_ON_TIME_INTERVAL', 5000)
        self.alertOn_TimeInterval = 5000  # 5 secs alert duration
        self.printedLabelScanDataInput_Received = False
        
        # Part Information Variables
        self.barcodePrintFileName = ""
        self.barcodePrintFileNamePath = ""
        self.prnFileContent = ""
        self.partNumber = ""
        self.modelName = ""
        self.vendorCode = ""
        self.eoNumber = ""
        self.specialData = ""
        self.initialID = ""
        self.supplierSection = ""
        self.lotNo = ""
        self.traceabilityCode = ""
        self.today = datetime.today().date()
        self.dataPointX = 0
        self.chart_series = {name: [] for name in
                             ('L1', 'L2', 'L3', 'L4', 'P1', 'P2', 'P3', 'P4')}
        
        # Machine and Process Variables
        self.machineID = self.machineid  # Use existing machine ID
        self.startingNGCableValidation = False
        self.endingNGCableValidated = False
        self.endingNGCableValidation = False
        self.deviceToRead = []
        
        # Load Cell Values
        self.loadcell01Value = 0.0
        self.loadcell02Value = 0.0
        self.loadcell03Value = 0.0
        self.loadcell04Value = 0.0
        
        # Maximum Values During Test
        self.L1MaxValue = 0.0
        self.L2MaxValue = 0.0
        self.L3MaxValue = 0.0
        self.L4MaxValue = 0.0
        
        # Pressure Values
        self.P01Value = 0.0
        self.P02Value = 0.0
        self.P03Value = 0.0
        self.P04Value = 0.0
        
        # Test Control Variables
        self.failCounter = 0
        self.passCounter = 0
        self.blink = False
        
        # Column Visibility Flags
        self.columnL2 = False
        self.columnL3 = False
        self.columnL4 = False
        self.columnP3 = False
        self.columnP4 = False
        
        # PLC Communication Variables
        self.slaveAddress = 1
        self.inputSensorsArray = []
        self.processStatusArray = []
        self.dataRegistersArray = []
        self.employeeCodesArray = []
        self.processStatusLabels = ["AUTO", "HOME", "PULL1_OK", "PULL1_NG", "PULL2_OK", "PULL2_NG", "TESTRESULT_OK", "TESTRESULT_NG"]
        self.rcvdTestRslt = False
        self.inputSensorsToReadList = []
        self.programSelectionPLCAddress = ""
        
        # Camera and Alert Variables
        self.cam1Result = ""
        self.resetPLCOnFormClosing = False
        self.machineOnPLCCoilAddress = ""
        self.alertOnPLCCoilAddress = ""
        self.partRunningSerialExists = False
        
        # Monitoring and Threading
        self.monitoring_active = False
        self.test_in_progress = False
        self.employee_validated = False
        self.alc_validated = False
        
        # Specification Data
        self.mldDataTable = []
        self.specificationData = []
        self.failCounter = 0
        self.startingNGCableValidation = False
        self.endingNGCableValidation = False
        self.noOfValues = 0
        self.process_status_index = 0  # Initialize process status index for tracking cycle position
        
        # Initialize blinking jobs tracking
        self.blinking_jobs = {}
        
        # Initialize timers
        self.alc_timer = None
        self.alcInput_TimeInterval = 200  # milliseconds
        
        # Track test result states to prevent duplicate saves
        self.last_test_result_pass_state = False
        self.last_test_result_ng_state = False
        self.test_result_saved = False
        
        # Initialize continuous loop control variables
        self.continuous_loop_active = False
        self.current_cycle_number = 0
        self.loop_start_time = None
        self.cycle_start_time = None
        self.auto_cycle_delay = 3.0  # Seconds between cycles
        self.max_auto_cycles = 50   # Safety limit for auto cycling
        self.cycle_completion_detected = False
        self.loop_mode = "MANUAL"   # "MANUAL" or "MONITOR" 
        self.step_duration = 3.0    # Duration for each step in manual mode

    def setup_window(self):
        """Set up the window after initialization"""
        # Change from fullscreen to maximized state
        self.root.state('zoomed')  # Replace fullscreen with maximized state
        self.root.lift()  # Bring window to front
        self.root.focus_force()  # Force focus
        
        # Create the main_container first to ensure it exists before other operations
        # Create main container
        self.main_container = tk.Frame(self.root, bg=ui.APP_BG)
        self.main_container.pack(fill="both", expand=True)

        # The machine status line. This is what an operator looks at first
        # when the line stops, so it is a filled, iconed strip rather than a
        # word of coloured text - legible from standing distance at the cell.
        self.message_label = ui.StatusBanner(self.main_container)
        self.message_label.pack(fill="x", padx=ui.PAD, pady=(ui.PAD, 0))
        
        # Make sure the settings file exists and is freshly read
        self.ensure_settings_file_exists()
        
        # Load data after the settings are loaded
        self.load_configuration_data()
        
        # Set up GUI components before connecting to devices
        self.setup_gui()
        self.setup_barcode_listener()
        
        # Connect to devices after GUI is set up
        self.connect_to_devices()
        
        # Connect to PLC after GUI setup
        self.root.after(2000, self.connect_to_plc)
        
        # Initialize employee validation after GUI setup
        self.root.after(1000, self.initialize_employee_validation)
        
        # Ensure window stays on top during initialization
        self.root.after(500, lambda: self.root.attributes('-topmost', False))

    def setup_gui(self):
        # Main container and message label are already created in setup_window
        # Do not recreate them here
        
        # Process control bar
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
        title_frame = tk.Frame(self.main_container, bg=ui.SURFACE)
        title_frame.pack(fill="x")

        # PLC Process Control Button
        self.create_plc_control_section(title_frame)

        # Process Status Indicator
        self.create_process_status_indicator(title_frame)

        # A hairline separating the bar from the workspace below
        tk.Frame(self.main_container, bg=ui.BORDER, height=1).pack(fill="x")

    def create_plc_control_section(self, parent_frame):
        """Create PLC process control section in the title frame"""
        try:
            # Control card
            control_frame = ui.ctk_card(parent_frame, corner_radius=ui.CORNER_RADIUS_SMALL)
            control_frame.pack(side="left", padx=(0, ui.PAD), pady=ui.PAD)

            # Control label
            control_label = tk.Label(control_frame, text="Process Control",
                                   font=ui.FONT_SMALL, bg=ui.SURFACE,
                                   fg=ui.TEXT_MUTED)
            control_label.pack(padx=ui.PAD_LARGE, pady=(ui.PAD, 2))

            # Initialize process status
            self.process_status = "LOW"  # HIGH or LOW

            # Process control button - starts disabled until ALC code is
            # processed; toggle_process_status() and the monitoring loop
            # recolour it live via fg_color, same as any other CTkButton.
            self.process_control_btn = ui.ctk_button(
                control_frame, text="START TESTING", icon='play', kind='success',
                width=150, command=self.toggle_process_status, state='disabled')
            self.process_control_btn.pack(padx=ui.PAD, pady=(0, ui.PAD))

        except Exception as e:
            print(f"Error creating PLC control section: {e}")

    def create_process_status_indicator(self, parent_frame):
        """Create process status indicator in the title frame"""
        try:
            # Status card
            status_frame = ui.ctk_card(parent_frame, corner_radius=ui.CORNER_RADIUS_SMALL)
            status_frame.pack(side="left", padx=(0, ui.PAD_LARGE), pady=ui.PAD)

            # Status label
            status_label = tk.Label(status_frame, text="Process Status",
                                  font=ui.FONT_SMALL, bg=ui.SURFACE,
                                  fg=ui.TEXT_MUTED)
            status_label.pack(padx=ui.PAD_LARGE, pady=(ui.PAD, 2))

            # Initialize process indicator status
            self.process_indicator_status = "IDLE"  # IDLE, RUNNING, COMPLETED, FAILED

            # Status indicator (LED-style) - update_process_indicator()
            # recolours this via text_color.
            self.status_indicator = ctk.CTkLabel(
                status_frame, text="● IDLE", font=ui.FONT_BODY_BOLD,
                fg_color=ui.SURFACE, text_color=ui.TEXT_MUTED, width=100)
            self.status_indicator.pack(padx=ui.PAD, pady=(0, ui.PAD))

        except Exception as e:
            print(f"Error creating process status indicator: {e}")

    def toggle_process_status(self):
        """
        Toggle process status between HIGH and LOW
        
        NOTE: test starts automatically after ALC code entry
              This button is mainly for STOPPING the test or manual restart
        """
        try:
            # Check if employee validation is complete
            if not getattr(self, 'employee_validation_complete', False):
                self.safe_update_message("Employee validation required before process control", "red")
                messagebox.showwarning("Employee Validation Required", 
                                     "Please validate your Employee ID before starting the process")
                return
            
            # Toggle status
            if self.process_status == "LOW":
                # Manual start/restart (test auto-starts after ALC)
                if not hasattr(self, 'current_part_number') or not self.current_part_number:
                    self.safe_update_message("Part Number selection required", "red")
                    messagebox.showwarning("Part Number Required", 
                                         "Please enter a valid ALC code first")
                    return
                
                print("Manual test start/restart requested...")
                
                # If PLC writes haven't been done yet, do them now
                if hasattr(self, 'programSelectionPLCAddress') and self.programSelectionPLCAddress:
                    self.write_program_selection_to_plc()
                if hasattr(self, 'machineOnPLCCoilAddress') and self.machineOnPLCCoilAddress:
                    self.write_machine_on_to_plc()
                
                # Start monitoring
                self.process_status = "HIGH"
                self.process_control_btn.configure(text="STOP TESTING", fg_color=ui.DANGER, hover_color=ui.DANGER_HOVER)
                self.start_check_async()
            else:
                # Stop EOL testing process
                self.stop_eol_testing_process()
                
        except Exception as e:
            print(f"Error toggling process status: {e}")
            self.safe_update_message(f"Error controlling process: {e}", "red")

    def stop_eol_testing_process(self):
        """Stop the EOL testing process - PLC connection remains active"""
        try:
            print("[*] Stopping EOL Testing Process")
            
            # Set operator stop flag to prevent monitoring from continuing
            self.operator_stop_requested = True
            
            # Update status variables
            self.process_status = "LOW"
            self.process_control_btn.configure(text="START TESTING", fg_color=ui.SUCCESS, hover_color=ui.SUCCESS_HOVER)
                
            # CRITICAL: Stop P0000 keep-alive first
            self.p0000_keepalive_active = False
            print("🔄 Stopping P0000 keep-alive...")
            time.sleep(0.5)  # Let keep-alive stop
            
            # Send PLC command to stop testing (ONLY P0000 - don't touch M coils)
            print("🔄 Writing P0000 (Start Signal) to LOW...")
            print("   (Not writing to M coils - letting PLC control them)")
            success = self.write_plc_command("P0000", False)
            if success:
                self.update_process_indicator("IDLE")
                self.safe_update_message("EOL Testing Stopped by operator. PLC remains connected.", "orange")
                print("✅ PLC Command: Set P0000 LOW - EOL Testing Stopped")
                
                # Log the testing stop
                self.log_plc_command("WRITE", "P0000", "LOW", "EOL Testing Stop Command")
                self.log_operator_action("TEST_STOP", "Testing stopped by operator", 
                                       getattr(self, 'current_employee_id', 'UNKNOWN'))
                
                # Stop test execution monitoring but keep PLC status monitoring active
                self.continuous_testing_active = False
                # DO NOT set self.status_monitoring_active = False
                # PLC monitoring continues for status updates
                print("[*] Test execution stopped - PLC monitoring continues")
                
            else:
                self.safe_update_message("Failed to send stop command to PLC", "red")
                print("[ERROR] Failed to send PLC stop command")
                
        except Exception as e:
            print(f"Error stopping EOL testing process: {e}")
            self.safe_update_message(f"Error stopping testing: {e}", "red")

    def connect_to_plc(self):
        """Connect to PLC using configuration from .env file"""
        try:
            if self.plc_connected:
                print("PLC already connected")
                return True
                
            print("[*] Attempting to connect to PLC...")
            
            # Try TCP connection first if IP is configured
            if self.plc_tcp_ip:
                try:
                    self.plc_client = SerializedModbusClient(ModbusTcpClient(
                        host=self.plc_tcp_ip,
                        port=self.plc_tcp_port,
                        timeout=self.plc_timeout,
                        retries=self.plc_retries
                    ))
                    connection_result = self.plc_client.connect()
                    if connection_result:
                        self.plc_connected = True
                        self.plc_communication_errors = 0  # Reset error counter
                        self.plc_last_successful_read = time.time()  # Reset health timer
                        print(f"[OK] PLC connected via TCP - {self.plc_tcp_ip}:{self.plc_tcp_port}")
                        self.safe_update_message(f"PLC Connected via TCP: {self.plc_tcp_ip}", "green")
                        # Start automatic process status monitoring with reduced frequency
                        self.root.after(1000, self.start_plc_status_monitoring)
                        return True
                    else:
                        print("[ERROR] TCP connection failed, trying serial...")
                except Exception as e:
                    print(f"TCP connection error: {e}")
            
            # Try serial connection
            try:
                self.plc_client = SerializedModbusClient(ModbusSerialClient(
                    port=self.plc_com_port,
                    baudrate=self.plc_baud_rate,
                    bytesize=8,
                    parity='N',
                    stopbits=1,
                    timeout=self.plc_timeout,
                    retries=self.plc_retries
                ))
                connection_result = self.plc_client.connect()
                if connection_result:
                    self.plc_connected = True
                    self.plc_communication_errors = 0  # Reset error counter
                    self.plc_last_successful_read = time.time()  # Reset health timer
                    print(f"[OK] PLC connected via Serial - {self.plc_com_port}")
                    self.safe_update_message(f"PLC Connected via Serial: {self.plc_com_port}", "green")
                    # Start automatic process status monitoring with reduced frequency
                    self.root.after(1000, self.start_plc_status_monitoring)
                    return True
                else:
                    print("[ERROR] Serial connection failed")
                    self.safe_update_message("PLC connection failed - check configuration", "red")
                    return False
            except Exception as e:
                print(f"Serial connection error: {e}")
                self.safe_update_message(f"PLC connection error: {e}", "red")
                return False
                
        except Exception as e:
            print(f"Error connecting to PLC: {e}")
            self.safe_update_message(f"PLC connection error: {e}", "red")
            return False

    def disconnect_plc(self):
        """Disconnect from PLC"""
        try:
            if self.plc_client and self.plc_connected:
                self.status_monitoring_active = False  # Stop monitoring loops
                self.plc_thread_running = False  # Stop background thread
                self.plc_client.close()
                self.plc_connected = False
                print("PLC disconnected")
                self.safe_update_message("PLC Disconnected", "orange")
        except Exception as e:
            print(f"Error disconnecting PLC: {e}")

    def write_plc_command(self, address, value):
        """Write command to PLC using actual Modbus communication with enhanced error handling"""
        try:
            # Check PLC connection status
            if not self.plc_connected or not self.plc_client:
                print(f"⚠️ PLC not connected - cannot write: Address {address} = {'HIGH' if value else 'LOW'}")
                return False
            
            # CRITICAL: Verify socket is still open before writing
            try:
                if not self.plc_client.is_socket_open():
                    print(f"⚠️ PLC socket closed - attempting reconnection...")
                    if not self.connect_to_plc():
                        print(f"❌ Failed to reconnect PLC")
                        return False
                    print(f"✅ PLC reconnected successfully")
            except Exception as e:
                print(f"⚠️ Socket check error: {e} - attempting reconnection...")
                if not self.connect_to_plc():
                    print(f"❌ Failed to reconnect PLC")
                    return False
            
            # Convert P0000 style address to coil number (P addresses are coils, not registers)
            if address.startswith('P'):
                coil_address = int(address[1:])  # P0000 -> 0, P0001 -> 1, etc.
            else:
                coil_address = 0
            
            # Write to coil (not holding register - P addresses are digital coils)
            coil_value = True if value else False
            result = self.plc_client.write_coil(
                address=coil_address,
                value=coil_value,
                device_id=self.plc_station_id
            )
            
            if not result.isError():
                print(f"[OK] PLC WRITE SUCCESS: {address} = {'HIGH' if value else 'LOW'}")
                return True
            else:
                print(f"[ERROR] PLC WRITE FAILED: {address} - {result}")
                return False
            
        except Exception as e:
            print(f"Error writing PLC command: {e}")
            return False

    def update_process_indicator(self, status):
        """Update the process status indicator"""
        try:
            self.process_indicator_status = status
            
            if status == "IDLE":
                self.status_indicator.configure(text="● IDLE", text_color=ui.TEXT_MUTED)
            elif status == "RUNNING":
                self.status_indicator.configure(text="● RUNNING", text_color=ui.SUCCESS)
            elif status == "COMPLETED":
                self.status_indicator.configure(text="● COMPLETED", text_color=ui.ACCENT)
            elif status == "FAILED":
                self.status_indicator.configure(text="● FAILED", text_color=ui.DANGER)
            else:
                self.status_indicator.configure(text="● UNKNOWN", text_color=ui.WARNING)
                
            print(f"Process indicator updated to: {status}")
            
        except Exception as e:
            print(f"Error updating process indicator: {e}")

    def log_plc_command(self, command_type, address, value, description=""):
        """Log PLC commands for audit trail"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            employee_id = getattr(self, 'current_employee_id', 'UNKNOWN')
            
            log_entry = {
                'timestamp': timestamp,
                'employee_id': employee_id,
                'command_type': command_type,
                'address': address,
                'value': value,
                'description': description
            }
            
            # Log to console
            print(f"PLC LOG: {timestamp} | {employee_id} | {command_type} {address}={value} | {description}")
            
            # In a real implementation, this would also:
            # 1. Write to log file
            # 2. Store in database
            # 3. Send to monitoring system
            
        except Exception as e:
            print(f"Error logging PLC command: {e}")

    def log_operator_action(self, action_type, description, employee_id=None):
        """Log operator actions for audit trail"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            emp_id = employee_id or getattr(self, 'current_employee_id', 'UNKNOWN')
            part_number = getattr(self, 'current_part_number', 'N/A')
            
            log_entry = {
                'timestamp': timestamp,
                'employee_id': emp_id,
                'action_type': action_type,
                'description': description,
                'part_number': part_number
            }
            
            # Log to console
            print(f"OPERATOR LOG: {timestamp} | {emp_id} | {action_type} | {description} | Part: {part_number}")
            
            # In a real implementation, this would also:
            # 1. Write to log file
            # 2. Store in database audit table
            # 3. Send to monitoring/compliance system
            
        except Exception as e:
            print(f"Error logging operator action: {e}")

    def execute_cycle_restart(self):
        """Execute the actual cycle restart"""
        try:
            print("🔄 EXECUTING CYCLE RESTART")
            
            # Keep employee ID validated (don't require re-validation)
            # Only prompt for new part number
            
            # Clear current part number to force new selection
            if hasattr(self, 'current_part_number'):
                delattr(self, 'current_part_number')
            
            # Clear ALC entry for new part number input
            if hasattr(self, 'alc_entry'):
                self.alc_entry.delete(0, tk.END)
                self.alc_entry.insert(0, "ALC CODE")
                self.alc_entry.config(fg='gray')
                self.alc_entry.focus()
            
            # Reset spec tree
            if hasattr(self, 'spec_tree'):
                for item in self.spec_tree.get_children():
                    self.spec_tree.delete(item)
            
            # Reset test result saved flag
            self.test_result_saved = False

            # The sensor labels belong to the part that just left
            self.stop_all_label_blinking()
            for label in self.placed_labels.values():
                label.destroy()
            self.placed_labels = {}
            self.sensor_label_keys = []
            self.sensor_states = {}

            # next_model_command() disabled this while the closing NG cable
            # check ran; with the part released, the next one can use it.
            if getattr(self, 'next_model_btn', None):
                self.next_model_btn.configure(state='normal')

            # Show ready message
            self.safe_update_message(f"Cycle restarted. Employee {self.current_employee_id} - Enter new Part Number", "green")
            
            # Log the restart completion
            self.log_operator_action("CYCLE_RESTART_COMPLETED", "Ready for new part number", 
                                   getattr(self, 'current_employee_id', None))
            
            print("[*] CYCLE RESTART COMPLETED - READY FOR NEW PART NUMBER")
            
        except Exception as e:
            print(f"Error executing cycle restart: {e}")
            self.safe_update_message(f"Error in cycle restart: {e}", "red")

    def create_quadrants(self):
        # Configure grid weights for equal space and responsive layout
        self.workspace.grid_columnconfigure(0, weight=1, uniform='quad')  # First column
        self.workspace.grid_columnconfigure(1, weight=1, uniform='quad')  # Second column
        self.workspace.grid_rowconfigure(0, weight=1, uniform='quad')     # First row
        self.workspace.grid_rowconfigure(1, weight=1, uniform='quad')     # Second row
        
        # Create quadrants
        self.q1 = self.create_first_quadrant()
        self.q2 = self.create_second_quadrant()
        self.q3 = self.create_third_quadrant()
        self.q4 = self.create_fourth_quadrant()
        
        # Place quadrants with consistent spacing
        self.q1.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.q2.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        self.q3.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.q4.grid(row=1, column=1, sticky="nsew", padx=4, pady=4)

    def create_first_quadrant(self):
        """Create the image display quadrant with correct dimensions."""
        q1 = ui.ctk_card(self.workspace)

        # Header strip, inset so the card's own rounded corners show around
        # it. model_header's text gets swapped in and out elsewhere to show
        # the loaded model/part - so it is built here rather than through
        # ui.ctk_card_header(), which owns its label outright.
        header_frame = ctk.CTkFrame(q1, corner_radius=ui.CORNER_RADIUS_SMALL,
                                    fg_color=ui.SUBTLE, height=34)
        header_frame.pack(fill="x", padx=6, pady=(6, ui.PAD))
        header_frame.pack_propagate(False)

        ctk.CTkLabel(header_frame, text='', fg_color=ui.SUBTLE,
                    image=ui.icon_image('box', ui.ACCENT, 18)).pack(
                        side="left", padx=(ui.PAD_LARGE, 0))

        self.model_header = ctk.CTkLabel(header_frame,
                                    text="MODEL - PART NUMBER",
                                    fg_color=ui.SUBTLE,
                                    text_color=ui.ACCENT,
                                    font=ui.FONT_SECTION)
        self.model_header.pack(side="left", padx=ui.PAD)

        # Create a frame to hold the image
        self.image_frame = tk.Frame(q1, bg=ui.SURFACE)
        # Pinned to 750x450 to match model_settings.py: label coordinates are
        # stored as absolute pixels against this canvas, so it must not stretch.
        self.image_frame.pack(expand=True, padx=ui.PAD_LARGE, pady=ui.PAD)
        self.image_frame.pack_propagate(False)
        self.image_frame.config(width=750, height=450)

        # Create initial placeholder
        self.image_label = tk.Label(self.image_frame,
                                   text="☐\n\nNo image loaded\nLoad an image to start testing",
                                   bg=ui.SURFACE,
                                   fg=ui.TEXT_MUTED,
                                   justify='center',
                                   font=ui.FONT_BODY)
        self.image_label.place(relx=0.5, rely=0.5, anchor='center')

        # Create status labels frame with fixed height
        status_frame = tk.Frame(q1, bg=ui.SURFACE, height=60)  # Increased height
        status_frame.pack(fill="x", side="bottom", pady=ui.PAD_LARGE, before=self.image_frame)
        status_frame.pack_propagate(False)  # Prevent frame from shrinking

        # Configure grid for equal spacing
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=1)
        status_frame.grid_columnconfigure(2, weight=1)
        status_frame.grid_columnconfigure(3, weight=1)
        status_frame.grid_columnconfigure(4, weight=1)

        # Define status labels with their properties. They all start on the
        # same accent blue - the monitor loop is what tells them apart,
        # switching a step to green on pass or red on fail as it completes.
        status_labels = [
            {'text': 'AUTO', 'bg': ui.ACCENT, 'icon': 'refresh'},
            {'text': 'HOME', 'bg': ui.ACCENT, 'icon': 'home'},
            {'text': '1st PULL\n(Load Test)', 'bg': ui.ACCENT, 'icon': 'download'},
            {'text': '2nd PULL\n(Length Test)', 'bg': ui.ACCENT, 'icon': 'ruler'},
            {'text': 'TEST\nRESULT', 'bg': ui.ACCENT, 'icon': 'document'}
        ]

        # Initialize process status labels dictionary
        self.process_status_labels = {}

        # One grid cell each, all of equal weight, so the five stay the
        # same size whatever their labels say.
        for i, label_info in enumerate(status_labels):
            label = ui.StepLamp(status_frame, label_info['text'],
                                label_info['icon'], color=label_info['bg'])
            label.grid(row=0, column=i, padx=4, pady=2, sticky="nsew")

            # Store reference to the label in dictionary
            label_key = label_info['text'].split()[0].lower()
            self.process_status_labels[label_key] = label

            # Also store as attribute for backward compatibility
            setattr(self, f"{label_key}_label", label)

        # Create bottom frame for label info
        bottom_frame = tk.Frame(q1, height=30, bg=ui.SURFACE)
        bottom_frame.pack(fill="x", side="bottom", pady=ui.PAD)
        bottom_frame.pack_propagate(False)

        # Add label info text
        self.label_info = tk.Label(bottom_frame,
                                  text="Placed Labels: None",
                                  bg=ui.SURFACE,
                                  fg=ui.TEXT_MUTED,
                                  font=ui.FONT_SMALL)
        self.label_info.pack(pady=2)

        return q1

    def create_second_quadrant(self):
        """Create the specifications display quadrant."""
        q2 = ui.ctk_card(self.workspace)

        # Define camera frame dimensions
        cam_width = 120  # Width for camera frames
        cam_height = 90  # Height for camera frames

        # Add header
        ui.ctk_card_header(q2, "TEST SPECIFICATIONS", icon='clipboard')

        # Create specifications table frame
        spec_frame = tk.Frame(q2, bg=ui.SURFACE)  # Add border to spec frame

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
                       relief="flat",  # Border style
                       fieldbackground=ui.SURFACE,  # Background color
                       background=ui.SURFACE,  # Row background color
                       foreground=ui.TEXT,  # Text color
                       font=ui.FONT_BODY,
                       rowheight=28)  # Increase row height to fill space better

        # Header band, selection colours and fonts are inherited from the
        # base Treeview style in ui.py, so every grid in the app matches.

        # Configure selection colors
        style.map("Custom.Treeview",
                 background=[("selected", ui.ACCENT_SOFT)],  # Soft tint for selected row
                 foreground=[("selected", ui.ACCENT)])

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

        # Pack the treeview inside spec_frame
        self.spec_tree.pack(fill="both", expand=True)

        # Create camera frame container (fixed height at bottom)
        camera_container = tk.Frame(q2, bg=ui.SUBTLE)
        camera_container.pack(fill="x", side="bottom", padx=1, pady=1)
        
        # Pack spec_frame after camera_container so it takes the remaining space
        spec_frame.pack(fill="both", expand=True, padx=ui.PAD, pady=ui.PAD)

        # Configure grid for equal spacing
        camera_container.grid_columnconfigure(0, weight=1)  # First camera
        camera_container.grid_columnconfigure(1, weight=1)  # Second camera
        camera_container.grid_columnconfigure(2, weight=1)  # Spacing
        camera_container.grid_columnconfigure(3, weight=1)  # Text box

        def camera_slot(column):
            """A rounded box for a camera. No images are fed in; camera 1's
            caption shows the verdict its PLC coils report."""
            frame = ctk.CTkFrame(camera_container, width=cam_width, height=cam_height,
                                 corner_radius=ui.CORNER_RADIUS_SMALL,
                                 fg_color=ui.SURFACE, border_width=1,
                                 border_color=ui.BORDER)
            frame.grid(row=1, column=column, padx=10, pady=(0, 5))
            frame.grid_propagate(False)
            frame.status = ctk.CTkLabel(frame, text="No image", fg_color=ui.SURFACE,
                                        text_color=ui.TEXT_MUTED, font=ui.FONT_SMALL,
                                        compound='top',
                                        image=ui.icon_image('camera', ui.BORDER_STRONG, 28))
            frame.status.place(relx=0.5, rely=0.5, anchor='center')
            return frame

        # Camera 1 section
        tk.Label(camera_container, text="CAM 1", fg=ui.TEXT_MUTED, bg=ui.SUBTLE,
                font=ui.FONT_SMALL).grid(row=0, column=0, pady=(0, 5))
        self.cam1_frame = camera_slot(0)
        self.cam1_status = self.cam1_frame.status

        # Camera 2 section
        tk.Label(camera_container, text="CAM 2", fg=ui.TEXT_MUTED, bg=ui.SUBTLE,
                font=ui.FONT_SMALL).grid(row=0, column=1, pady=(0, 5))
        self.cam2_frame = camera_slot(1)

        # Text box (moved to column 3 for equal spacing)
        tk.Label(camera_container, text="LABEL SCAN RESULT", bg=ui.SUBTLE,
                fg=ui.TEXT_MUTED, font=ui.FONT_SMALL).grid(
                    row=0, column=3, pady=(0, 5))
        textbox_slot = ctk.CTkFrame(camera_container, corner_radius=ui.CORNER_RADIUS_SMALL,
                                    fg_color=ui.SURFACE, border_width=1,
                                    border_color=ui.BORDER)
        textbox_slot.grid(row=1, column=3, padx=10, pady=1, sticky="nsew")

        # Where the printed label gets scanned back in. It only opens while a
        # freshly printed label is waiting to be checked.
        self.label_scan_entry = tk.Entry(textbox_slot, bg=ui.SURFACE, fg=ui.TEXT,
                                         disabledbackground=ui.SUBTLE,
                                         font=ui.FONT_BODY_BOLD, justify="center",
                                         relief="flat", highlightthickness=1,
                                         highlightbackground=ui.BORDER,
                                         highlightcolor=ui.ACCENT)
        self.label_scan_entry.pack(fill="x", padx=4, pady=(4, 0))
        self.label_scan_entry.configure(state='disabled')
        self.label_scan_entry.bind("<Return>", self.submit_label_scan)
        self.label_scan_entry.bind("<KeyRelease>", self.on_label_scan_key)

        self.cam_textbox = tk.Text(textbox_slot, width=40, height=5,
                                   bg=ui.SURFACE, fg=ui.TEXT, font=ui.FONT_BODY,
                                   relief="flat", borderwidth=0,
                                   highlightthickness=0, padx=ui.PAD, pady=ui.PAD)
        self.cam_textbox.pack(fill="both", expand=True, padx=4, pady=4)
        return q2

    def create_third_quadrant(self):
        q3 = ui.ctk_card(self.workspace)
        ui.ctk_card_header(q3, "LOAD & LENGTH GRAPH", icon='chart')

        # Add graph area directly without the labels
        self.create_graph_area(q3)

        return q3

    def create_fourth_quadrant(self):
        q4 = ui.ctk_card(self.workspace)
        ui.ctk_card_header(q4, "LOT INFORMATION", icon='list')

        # Default columns: LOT NUMBER, L1, L2, P1, P2, RESULT, SCAN RESULT
        self.default_columns = ["LOT NUMBER", "L1", "L2", "P1", "P2", "RESULT", "SR"]
        self.current_columns = self.default_columns.copy()

        # Main content frame to hold grid and entry fields
        content_frame = tk.Frame(q4, bg=ui.SUBTLE)
        content_frame.pack(fill="both", expand=True, padx=ui.PAD, pady=ui.PAD)

        # Configure grid for main content
        content_frame.grid_rowconfigure(0, weight=1)  # Treeview gets most space
        content_frame.grid_rowconfigure(1, weight=0)  # Scan counters
        content_frame.grid_rowconfigure(2, weight=0)  # Entry frame gets fixed space
        content_frame.grid_columnconfigure(0, weight=1)  # Single column takes full width

        # Create lot number tree view with frame - in the first row
        self.grid_frame = tk.Frame(content_frame, bg=ui.SUBTLE)
        self.grid_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 5))

        # Configure style for the lot number tree view
        style = ttk.Style()
        style.configure("LotTree.Treeview",
                       borderwidth=1,
                       relief="flat",
                       fieldbackground=ui.SURFACE,
                       background=ui.SURFACE,
                       foreground=ui.TEXT,
                       rowheight=25,  # Increase row height
                       font=ui.FONT_BODY)

        # The heading row is this panel's column header - it used to have a
        # second blue strip drawn above it saying the same things. Its
        # appearance comes from the base Treeview style in ui.py.

        # Configure selection colors
        style.map("LotTree.Treeview",
                 background=[("selected", ui.ACCENT_SOFT)],
                 foreground=[("selected", ui.ACCENT)])

        # Store the fixed width we want for our tree
        self.tree_fixed_width = 780  # Slightly less than frame width to account for padding

        # Create Treeview with default columns
        self.create_lot_tree(self.grid_frame, self.current_columns)

        # Scan result counters, sitting under the grid
        self.create_scan_counters(content_frame)

        # Bottom frame for entry fields - in the third row
        entry_frame = tk.Frame(content_frame, bg=ui.SUBTLE, height=50)  # Reduced height
        entry_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        entry_frame.grid_propagate(False)  # Prevent shrinking

        # Simplified layout with just the entry fields
        input_frame = tk.Frame(entry_frame, bg=ui.SUBTLE)
        input_frame.pack(fill="both", expand=True, pady=5)

        # Configure equal column weights
        input_frame.columnconfigure(0, weight=1)  # EMP CODE
        input_frame.columnconfigure(1, weight=1)  # NEXT LABEL button
        input_frame.columnconfigure(2, weight=1)  # NEXT MODEL button
        input_frame.columnconfigure(3, weight=1)  # ALC CODE

        # Employee Code Entry - a plain tk.Entry sitting in a rounded slot.
        # It stays a plain Entry rather than becoming a CTkEntry because the
        # validation flow elsewhere toggles it to a 'readonly' state, which
        # CTkEntry does not support.
        emp_slot = ctk.CTkFrame(input_frame, corner_radius=ui.CORNER_RADIUS_SMALL,
                                fg_color=ui.SURFACE, border_width=1, border_color=ui.BORDER)
        emp_slot.grid(row=0, column=0, padx=5, sticky="ew")
        self.emp_entry = tk.Entry(emp_slot,
                                 bg=ui.SURFACE,
                                 fg=ui.TEXT,
                                 font=ui.FONT_BODY_BOLD,
                                 justify="center",
                                 relief="flat",
                                 highlightthickness=0,
                                 width=15)
        self.emp_entry.pack(fill="both", expand=True, padx=6, pady=6)
        self.emp_entry.insert(0, "EMP CODE")

        # Next Label Button
        next_btn = ui.ctk_button(input_frame, text="NEXT LABEL", icon='arrow_right',
                                 kind='primary', command=self.next_label_command)
        next_btn.grid(row=0, column=1, padx=5, sticky="ew")

        # Next Model Button - ends the run on this part so another can be
        # loaded. Kept as an attribute because next_model_command() disables
        # it while the closing NG cable check is outstanding.
        self.next_model_btn = ui.ctk_button(input_frame, text="NEXT MODEL", icon='refresh',
                                            kind='neutral', command=self.next_model_command)
        self.next_model_btn.grid(row=0, column=2, padx=5, sticky="ew")

        # ALC Code Entry (initially disabled), same rounded-slot treatment.
        alc_slot = ctk.CTkFrame(input_frame, corner_radius=ui.CORNER_RADIUS_SMALL,
                                fg_color=ui.SURFACE, border_width=1, border_color=ui.BORDER)
        alc_slot.grid(row=0, column=3, padx=5, sticky="ew")
        self.alc_entry = tk.Entry(alc_slot,
                                 bg=ui.SURFACE,
                                 fg=ui.TEXT,
                                 font=ui.FONT_BODY_BOLD,
                                 justify="center",
                                 relief="flat",
                                 highlightthickness=0,
                                 width=15)
        self.alc_entry.pack(fill="both", expand=True, padx=6, pady=6)
        # The placeholder has to go in before the box is disabled - Tk
        # silently ignores insert() on a disabled Entry, which is why this
        # well used to come up blank and unlabelled.
        self.alc_entry.insert(0, "ALC CODE")
        self.alc_entry.config(state='disabled')
        
        # Bind events
        self.emp_entry.bind("<FocusIn>", lambda e: self.on_emp_entry_focus(True))
        self.emp_entry.bind("<FocusOut>", lambda e: self.on_emp_entry_focus(False))
        self.emp_entry.bind("<Return>", self.validate_employee_code)
        
        self.alc_entry.bind("<FocusIn>", lambda e: self.on_alc_entry_focus(True))
        self.alc_entry.bind("<FocusOut>", lambda e: self.on_alc_entry_focus(False))
        self.alc_entry.bind("<Return>", self.process_alc_code)
        
        return q4
        
    def create_scan_counters(self, parent_frame):
        """Build the OK / NG / invalid / total strip shown under the results grid."""
        counter_frame = tk.Frame(parent_frame, bg=ui.SUBTLE, height=30)
        counter_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 4))
        counter_frame.grid_propagate(False)

        definitions = [
            ("OK", ui.SUCCESS),
            ("NG", ui.DANGER),
            ("INVALID", ui.WARNING),
            ("TOTAL", ui.ACCENT),
        ]

        self.scan_count_labels = {}
        for column, (caption, color) in enumerate(definitions):
            counter_frame.columnconfigure(column, weight=1)

            cell = tk.Frame(counter_frame, bg=ui.SUBTLE)
            cell.grid(row=0, column=column, sticky="ew", padx=4)

            tk.Label(cell, text=f"{caption}:", bg=ui.SUBTLE, fg=color,
                     font=ui.FONT_BODY_BOLD).pack(side="left")

            value = ctk.CTkLabel(cell, text="0", fg_color=ui.SURFACE, text_color=color,
                                 width=44, corner_radius=8, font=ui.FONT_BODY_BOLD)
            value.pack(side="left", padx=(4, 0))
            self.scan_count_labels[caption] = value

        self.ok_count_label = self.scan_count_labels["OK"]
        self.ng_count_label = self.scan_count_labels["NG"]
        self.invalid_count_label = self.scan_count_labels["INVALID"]
        self.total_count_label = self.scan_count_labels["TOTAL"]

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

    def update_tree_columns(self, devices=None):
        """Update tree columns to always include all L1-L4 and P1-P4 columns"""
        # Always include all columns regardless of data availability
        new_columns = ["LOT NUMBER"]
        
        # Always include all L1-L4 and P1-P4 devices
        for device in ["L1", "L2", "L3", "L4", "P1", "P2", "P3", "P4"]:
            new_columns.append(device)
            print(f"Including {device} column - auto-generated")
        
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
            
            # Store new columns
            self.current_columns = new_columns
            
            # Try to restore data with mapping to new columns
            self.load_history_to_treeview()
            
            print(f"Tree columns updated to: {new_columns}")
        else:
            print(f"No column update needed - columns remain: {new_columns}")

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
        """The two trend charts, stacked, sharing the card's surface."""
        graph_container = tk.Frame(parent, bg=ui.CHART_SURFACE)
        graph_container.pack(fill="both", expand=True, padx=ui.PAD_LARGE,
                             pady=(0, ui.PAD))

        # A title row and a plot row per chart; only the plots take height.
        graph_container.grid_rowconfigure(0, weight=0)
        graph_container.grid_rowconfigure(1, weight=1)
        graph_container.grid_rowconfigure(2, weight=0)
        graph_container.grid_rowconfigure(3, weight=1)
        graph_container.grid_columnconfigure(0, weight=1)

        def chart_title(row, text, unit):
            strip = tk.Frame(graph_container, bg=ui.CHART_SURFACE)
            strip.grid(row=row, column=0, sticky="ew", pady=(0, 2))
            tk.Label(strip, text=text, bg=ui.CHART_SURFACE, fg=ui.TEXT,
                     font=ui.FONT_BODY_BOLD).pack(side="left")
            # The unit belongs on the chart, not in an operator's head.
            tk.Label(strip, text=unit, bg=ui.CHART_SURFACE, fg=ui.TEXT_MUTED,
                     font=ui.FONT_SMALL).pack(side="left", padx=(ui.PAD, 0))

        def plot(row):
            canvas = tk.Canvas(graph_container, bg=ui.CHART_SURFACE,
                               highlightthickness=0, height=100)
            canvas.grid(row=row, column=0, sticky="nsew", pady=(0, ui.PAD_LARGE))
            return canvas

        chart_title(0, "LOAD GRAPH", "kgf, by sample")
        self.load_canvas = plot(1)

        chart_title(2, "LENGTH GRAPH", "mm deviation, by sample")
        self.length_canvas = plot(3)

        # Bind resize events
        self.load_canvas.bind('<Configure>', lambda e: self.draw_load_graph())
        self.length_canvas.bind('<Configure>', lambda e: self.draw_length_graph())

    def visible_series(self, names):
        """Of the given series, the ones this part actually reports."""
        optional = {
            'L2': self.columnL2,
            'L3': self.columnL3,
            'L4': self.columnL4,
            'P3': self.columnP3,
            'P4': self.columnP4,
        }
        return [name for name in names if optional.get(name, True)]

    # The y-axis is divided into this many bands, so the scale has to land
    # on a step that divides cleanly by it.
    Y_DIVISIONS = 5

    @staticmethod
    def nice_step(rough, divisions):
        """A round step at least `rough`/divisions - 1, 2, 2.5 or 5 x 10^n.

        An axis read off raw data bounds is labelled 12.04, 26.41, 40.77;
        snapping the step first gives 10, 20, 30, which is what an operator
        can actually compare a reading against.
        """
        span = rough / divisions
        if span <= 0:
            return 1.0
        magnitude = 10 ** math.floor(math.log10(span))
        for multiple in (1, 2, 2.5, 5, 10):
            if span <= multiple * magnitude:
                return multiple * magnitude
        return 10 * magnitude

    def series_bounds(self, names):
        """Y-axis range covering the plotted points, snapped to round ticks."""
        values = [value for name in names for value in self.chart_series.get(name, [])]
        values = [v for v in values if v is not None]
        if not values:
            return None

        low, high = min(values), max(values)
        if low == high:
            # A flat line still needs a band to sit in.
            padding = abs(low) * 0.1 or 1.0
            low, high = low - padding, high + padding
        else:
            padding = (high - low) * 0.1
            low, high = low - padding, high + padding

        step = self.nice_step(high - low, self.Y_DIVISIONS)
        low = math.floor(low / step) * step
        high = low + step * self.Y_DIVISIONS
        return low, high

    def draw_graph(self, canvas, names, colors, default_labels):
        """Draw one chart: grid, y-axis scale, plotted series and legend."""
        canvas.delete("all")

        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1:
            width = canvas.winfo_reqwidth()   # not mapped yet
        if height <= 1:
            height = canvas.winfo_reqheight()
        if width <= 1 or height <= 1:
            return

        left_margin = 52
        right_margin = 74   # room for the legend
        top_margin = 12
        bottom_margin = 26

        graph_width = width - (left_margin + right_margin)
        graph_height = height - (top_margin + bottom_margin)
        if graph_width <= 0 or graph_height <= 0:
            return

        names = self.visible_series(names)
        bounds = self.series_bounds(names)

        # Number of points across the x-axis, at least one grid span.
        point_count = max((len(self.chart_series.get(n, [])) for n in names), default=0)
        span = max(point_count - 1, 1)

        baseline = height - bottom_margin
        plot_right = width - right_margin

        # Grid: hairline, solid and one step off the surface. The dashed
        # grey ruling drew more attention than the traces in front of it.
        for i in range(9):
            x = left_margin + (i * graph_width / 8)
            canvas.create_line(x, top_margin, x, baseline, fill=ui.CHART_GRID)
            if point_count:
                first = self.dataPointX - point_count + 1
                label = str(int(first + round(i * span / 8)))
            else:
                label = str(i + 1)
            canvas.create_text(x, baseline + 12, text=label,
                               fill=ui.TEXT_MUTED, font=ui.FONT_SMALL)

        # Horizontal grid lines, labelled from the data when there is any.
        divisions = self.Y_DIVISIONS
        for i in range(divisions + 1):
            y = baseline - (i * graph_height / divisions)
            canvas.create_line(left_margin, y, plot_right, y, fill=ui.CHART_GRID)
            if bounds:
                low, high = bounds
                value = low + (high - low) * i / divisions
                # Whole numbers lose the trailing ".00"; fine steps keep
                # enough places to stay distinct from their neighbours.
                step = (high - low) / divisions
                places = 0 if step >= 1 else (1 if step >= 0.1 else 2)
                label = f"{value:,.{places}f}"
            else:
                label = str(default_labels[i])
            canvas.create_text(left_margin - 6, y, text=label, anchor="e",
                               fill=ui.TEXT_MUTED, font=ui.FONT_SMALL)

        # The two axes themselves, a shade stronger than the grid, so the
        # plot reads as a framed area rather than as loose ruling.
        canvas.create_line(left_margin, top_margin, left_margin, baseline,
                           fill=ui.CHART_AXIS)
        canvas.create_line(left_margin, baseline, plot_right, baseline,
                           fill=ui.CHART_AXIS)

        # Plot each series.
        if bounds and point_count > 1:
            low, high = bounds
            value_range = high - low

            for name in names:
                points = self.chart_series.get(name, [])
                if len(points) < 2:
                    continue

                coordinates = []
                for index, value in enumerate(points):
                    if value is None:
                        continue
                    x = left_margin + (index * graph_width / span)
                    y = height - bottom_margin - ((value - low) / value_range) * graph_height
                    coordinates.extend((x, y))

                if len(coordinates) >= 4:
                    # A casing in the surface colour under each trace, so
                    # that where two cross the upper one stays readable.
                    canvas.create_line(*coordinates, fill=ui.CHART_SURFACE,
                                       width=6, capstyle="round",
                                       joinstyle="round")
                    canvas.create_line(*coordinates, fill=colors[name], width=2,
                                       capstyle="round", joinstyle="round")

        # Legend, showing only the series this part reports.
        legend_x = plot_right + 18
        legend_y = top_margin + 10
        for name in names:
            canvas.create_line(legend_x, legend_y, legend_x + 18, legend_y,
                               fill=colors[name], width=3, capstyle="round")
            # The label wears a text token and the swatch beside it carries
            # the identity, so the pair never depends on colour alone.
            canvas.create_text(legend_x + 26, legend_y, text=name, anchor="w",
                               fill=ui.TEXT_MUTED, font=ui.FONT_SMALL)
            legend_y += 18

    # Categorical slots in fixed order, so L1 and P1 keep their colour
    # whether or not the part reports L2-L4. Colour follows the channel,
    # never its position among whichever ones happen to be on show.
    LOAD_COLORS = dict(zip(['L1', 'L2', 'L3', 'L4'], ui.SERIES))
    LENGTH_COLORS = dict(zip(['P1', 'P2', 'P3', 'P4'], ui.SERIES))

    def draw_load_graph(self):
        self.draw_graph(self.load_canvas,
                        ['L1', 'L2', 'L3', 'L4'],
                        self.LOAD_COLORS,
                        [0, 20, 40, 60, 80, 100])

    def draw_length_graph(self):
        self.draw_graph(self.length_canvas,
                        ['P1', 'P2', 'P3', 'P4'],
                        self.LENGTH_COLORS,
                        [-5, -3, -1, 1, 3, 5])

    def redraw_graphs(self):
        """Repaint both charts, ignoring canvases that are not on screen yet."""
        try:
            self.draw_load_graph()
            self.draw_length_graph()
        except Exception as e:
            print(f"Error drawing graphs: {e}")

    def create_footer(self):
        tk.Frame(self.main_container, bg=ui.BORDER, height=1).pack(fill="x", side="bottom")
        footer = tk.Label(self.main_container,
                        text="Powered By: NICE COMPUTERS AND SOFTWARE SOLUTIONS, Kavali, A.P",
                        bg=ui.SURFACE, fg=ui.TEXT_MUTED, font=ui.FONT_SMALL, height=2)
        footer.pack(fill="x", side="bottom")

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
        label_key = getattr(label, 'label_key', label.cget('text'))
        self.label_positions[label_key] = (x, y)
        print(f"Label {label_key} dropped at x={x}, y={y}")
        
        # Save the updated positions to database
        self.save_label_positions()

    def test_result_command(self):
        """Score and record the test the PLC just finished.

        Every spec row is judged against its limits, then the result either
        settles an NG cable check or is saved as a production part.
        """
        try:
            print("=== TEST COMPLETION DETECTED ===")

            # With no part loaded there is nothing to score or save against.
            if not getattr(self, 'current_part_number', None):
                print("No part loaded - ignoring PLC result")
                self.rcvdTestRslt = False
                return

            self.score_spec_rows()

            if self.startingNGCableValidation:
                # The operator ran the known-bad cable, so a failure is the
                # proof the rig still catches one. Nothing is saved.
                if self.failCounter > 0:
                    self.safe_update_message("NG Validation successful, continue to testing...", "green")
                    self.startingNGCableValidation = False
                else:
                    self.safe_update_message("NG Validation NOT OK, please repeat NG Validation...", "red")
            elif self.endingNGCableValidation:
                if self.failCounter > 0:
                    self.safe_update_message("NG Validation successful.", "green")
                    self.endingNGCableValidated = True
                    self.endingNGCableValidation = False
                    self.write_program_selection_to_plc(False)
                else:
                    self.safe_update_message("NG Validation NOT OK, please repeat NG Validation...", "red")
                    self.endingNGCableValidated = False
            else:
                self.complete_test_cycle()

        except Exception as e:
            print(f"Error in test_result_command: {e}")
            traceback.print_exc()
            self.safe_update_message(f"Error processing test results: {e}", "red")

        self.root.after(1200, self.prepare_next_cycle)

    def score_spec_rows(self):
        """Fill Actual and Result on every spec row and count passes and fails."""
        self.failCounter = 0
        self.passCounter = 0

        for item in self.spec_tree.get_children():
            device = str(self.spec_tree.item(item, "values")[1])
            value = self.get_actual_value_for_device(device)
            shown = f"{value:.1f}" if device.startswith("L") else f"{value:.2f}"
            self.update_specification_result(device, shown)

            if self.spec_tree.item(item, "values")[-1] == "PASS":
                self.passCounter += 1
            else:
                self.failCounter += 1

    def prepare_next_cycle(self):
        """Clear the finished test and hand the machine the next part."""
        try:
            self.reset_test_parameters()
            self.reset_dgv_spec_data()
            self.write_machine_on_to_plc()

            if self.endingNGCableValidated:
                # The closing check passed, so this part is done with.
                self.endingNGCableValidated = False
                self.execute_cycle_restart()
        except Exception as e:
            print(f"Error preparing next cycle: {e}")
            traceback.print_exc()

    def next_model_command(self):
        """Finish with this part so a different one can be loaded.

        Moving to another model closes out the current part, and the machine
        is not allowed to simply stop: the operator has to pull a known-bad
        cable through first, which proves the rig still reports a failure.
        So this clears the readings and restarts the check in
        ending-validation mode, where test_result_command() waits for that
        failure before the part is released.
        """
        # With no part loaded there is nothing to close out, and the check
        # would never release the button again.
        if not getattr(self, 'current_part_number', None):
            messagebox.showinfo("Next Model", "No part is loaded.")
            return

        if not messagebox.askyesno("Confirm Move",
                                   "Do you really want to move on to a different part?"):
            return

        try:
            self.breakLoop = True

            # One closing validation at a time - execute_cycle_restart()
            # turns the button back on once the check releases the part.
            if getattr(self, 'next_model_btn', None):
                self.next_model_btn.configure(state='disabled')

            self.endingNGCableValidation = True

            self.reset_dgv_spec_data()
            self.reset_test_parameters()

            # After the resets, not before: reset_test_parameters() blanks the
            # status line, so setting the prompt first would wipe the one
            # instruction the operator needs here.
            self.safe_update_message("Please Validate NG Cable...", "blue")

            self.start_check_async()
        except Exception as e:
            print(f"Error starting next model: {e}")
            messagebox.showerror("Next Model", f"Could not start the next model: {e}")

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

        # A printed label waiting to be checked takes the scan, even if the
        # scan box lost focus - otherwise it would be read as an ALC code.
        if self.awaiting_label_scan:
            self.label_scan_entry.delete(0, tk.END)
            self.label_scan_entry.insert(0, barcode)
            self.barcode_data = ""
            self.submit_label_scan()
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
            
        # Ready for testing when both codes are entered
        elif (hasattr(self, 'current_part_number') and self.current_part_number and 
              self.emp_entry.get() and self.emp_entry.get() != "EMP CODE" and
              self.alc_entry.get() and self.alc_entry.get() != "ALC CODE"):
            
            self.safe_update_message("Ready for testing - waiting for test completion", "green")
            print("System ready for testing")
            
            # Reset barcode data after processing
            self.barcode_data = ""
            return
            
        # Reset barcode data if not used
        self.barcode_data = ""

    def get_database_connection(self):
        """Get MySQL database connection"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            return connection
        except mysql.connector.Error as e:
            print(f"Database connection error: {e}")
            messagebox.showerror("Database Error", f"Failed to connect to database: {e}")
            return None

    def test_database_connection(self):
        """Test database connectivity and create tables if needed"""
        try:
            connection = self.get_database_connection()
            if connection and connection.is_connected():
                cursor = connection.cursor()
                
                # Create necessary tables
                self.create_database_tables(cursor)
                
                connection.commit()
                cursor.close()
                connection.close()
                return True
                
        except mysql.connector.Error as e:
            print(f"Database test failed: {e}")
            messagebox.showerror("Database Error", f"Database test failed: {e}")
            return False

    def create_database_tables(self, cursor):
        """Create the database tables used by the EOL test flow."""
        db.init_database(raise_on_error=True)
        print("Database tables created/verified successfully")

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
                    print(f"Loaded register file from: {plc_register_path}")
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
            
            # Load Machine On PLC Coil Address
            machine_on_path = os.path.join(txt_files_dir, 'MachineOnPLCCoilAddress.txt')
            if os.path.exists(machine_on_path):
                with open(machine_on_path, 'r') as file:
                    self.machineOnPLCCoilAddress = file.read().strip()
                    print(f"Loaded Machine On PLC Coil Address: {self.machineOnPLCCoilAddress}")
            else:
                print(f"⚠️ WARNING: MachineOnPLCCoilAddress.txt not found at {machine_on_path}")
                print("   This file is REQUIRED for PLC to start test!")
                self.machineOnPLCCoilAddress = ""
            
            # Load Alert On PLC Coil Address
            alert_on_path = os.path.join(txt_files_dir, 'AlertOnPLCCoilAddress.txt')
            if os.path.exists(alert_on_path):
                with open(alert_on_path, 'r') as file:
                    self.alertOnPLCCoilAddress = file.read().strip()
                    print(f"Loaded Alert On PLC Coil Address: {self.alertOnPLCCoilAddress}")
            else:
                print(f"Warning: AlertOnPLCCoilAddress.txt not found at {alert_on_path}")
                self.alertOnPLCCoilAddress = ""
            
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

    def load_authorized_employee_codes(self):
        """Load authorized employee codes from txt_files/EmployeeCodes.txt"""
        try:
            txt_files_dir = os.path.join(os.path.dirname(__file__), 'txt_files')
            employee_codes_path = os.path.join(txt_files_dir, 'EmployeeCodes.txt')
            
            if os.path.exists(employee_codes_path):
                with open(employee_codes_path, 'r') as file:
                    # Read all lines and strip whitespace
                    self.authorized_employee_codes = [line.strip() for line in file.readlines() if line.strip()]
                print(f"Loaded {len(self.authorized_employee_codes)} authorized employee codes")
                return True
            else:
                print(f"Warning: EmployeeCodes.txt not found at {employee_codes_path}")
                # Create default file with sample employee code
                with open(employee_codes_path, 'w') as file:
                    file.write("S041\n")
                self.authorized_employee_codes = ["S041"]
                print("Created default EmployeeCodes.txt with sample code S041")
                return True
                
        except Exception as e:
            print(f"Error loading employee codes: {e}")
            self.safe_update_message(f"Error loading employee codes: {e}", "red")
            return False

    def disable_controls_pending_employee_validation(self):
        """Disable controls until employee validation is complete"""
        try:
            # Disable part number entry
            if hasattr(self, 'alc_entry'):
                self.alc_entry.config(state='disabled')
                self.alc_entry.config(bg='#f0f0f0')
            
            # Disable camera textbox
            if hasattr(self, 'cam_textbox'):
                self.cam_textbox.config(state='disabled')
            
            print("Controls disabled pending employee validation")
            
        except Exception as e:
            print(f"Error disabling controls: {e}")

    def initialize_employee_validation(self):
        """Initialize employee validation on startup"""
        try:
            # Disable all controls initially
            self.disable_controls_pending_employee_validation()
            
            # Show welcome message
            self.safe_update_message("Welcome! Employee validation required to proceed.", "blue")
            
            # Load employee codes
            self.load_authorized_employee_codes()
            
            print("Employee validation system initialized")
            
        except Exception as e:
            print(f"Error initializing employee validation: {e}")
            self.safe_update_message(f"Error initializing employee validation: {e}", "red")
            
    def read_process_status_values(self):
        """
        Read process status values from PLC - Enhanced Error Handling
        
        Reads the process status coils:
        - Read coils individually
        - Return dictionary of address:value pairs
        - Return an empty dict when the PLC cannot be read. Never invent
          coil states: a made-up TESTRESULT would be saved as a real test.
        - Better connection health monitoring
        """
        try:
            # Check if PLC is connected with better error handling
            if not hasattr(self, 'plc_client') or not self.plc_client:
                print("⚠️ PLC client not initialized - no status read")
                return {}
            
            # Check socket status with detailed error reporting
            try:
                if not self.plc_client.is_socket_open():
                    print("⚠️ PLC socket closed - attempting reconnection")
                    if not self.connect_to_plc():
                        print("⚠️ PLC reconnection failed - no status read")
                        return {}
            except Exception as e:
                print(f"⚠️ PLC socket check failed: {e} - no status read")
                return {}
            
            # Read from PLC
            status_values = {}
            
            # Load process addresses if not loaded
            if not hasattr(self, 'process_addresses'):
                self.load_process_addresses()
            
            if not hasattr(self, 'process_addresses') or not self.process_addresses:
                print("⚠️ No process addresses loaded - no status read")
                return {}
            
            station_id = int(config.get('PLC_STATION_ID', '1'))
            
            # Parse addresses from process status array
            # Convert hex addresses to decimal
            try:
                for i, address in enumerate(self.process_addresses):
                    if not address.strip():
                        continue
                    
                    try:
                        # Parse address - check if hex or decimal
                        addr_str = address[1:] if len(address) > 1 else "0"
                        
                        # Try hex first (hex is expected), fallback to decimal
                        try:
                            addr_num = int(addr_str, 16)  # Hex conversion
                        except ValueError:
                            addr_num = int(addr_str)  # Decimal fallback
                        
                        # Read coil
                        if address.startswith('M') or address.startswith('X'):
                            result = self.plc_client.read_coils(addr_num, count=1, device_id=station_id)
                            
                            if not result.isError():
                                status_values[address] = result.bits[0] if result.bits else False
                                # Update successful read timestamp
                                self.plc_last_successful_read = time.time()
                                self.plc_communication_errors = 0  # Reset error counter
                            else:
                                # A PLC that fails one read will fail the rest
                                # too, each after a full timeout. Give up on this
                                # snapshot rather than hold the line that long.
                                self.plc_communication_errors += 1
                                print(f"⚠️ PLC read error for {address}: {result}")
                                return {}
                        
                        # Small delay to prevent overwhelming PLC
                        time.sleep(0.01)
                        
                    except Exception as e:
                        self.plc_communication_errors += 1
                        print(f"⚠️ Error reading PLC address {address}: {e}")
                        return {}
                
                # Too many failed reads: this snapshot is not trustworthy
                if self.plc_communication_errors >= 5:
                    print("⚠️ Too many PLC communication errors - discarding this read")
                    return {}
                
            except Exception as e:
                print(f"Error reading PLC coils: {e}")
                self.plc_communication_errors += 1
                return {}
            
            return status_values
                
        except Exception as e:
            print(f"Error in read_process_status_values: {e}")
            self.plc_communication_errors += 1
            return {}

    def load_hold_register_addresses(self):
        """Load hold register addresses from HoldRegistersRead.txt file"""
        try:
            txt_files_dir = os.path.join(os.path.dirname(__file__), 'txt_files')
            hold_registers_file = os.path.join(txt_files_dir, 'HoldRegistersRead.txt')
            
            if os.path.exists(hold_registers_file):
                with open(hold_registers_file, 'r') as file:
                    content = file.read().strip()
                    if content:
                        self.hold_register_addresses = [addr.strip() for addr in content.split(',')]
                        print(f"Loaded hold register addresses: {self.hold_register_addresses}")
                    else:
                        # Default addresses if file is empty
                        self.hold_register_addresses = ["D001", "D002", "D003", "D004", "D005", "D006", "D007", "D008"]
                        print("Using default hold register addresses")
            else:
                # Default addresses if file doesn't exist
                self.hold_register_addresses = ["D001", "D002", "D003", "D004", "D005", "D006", "D007", "D008"]
                print("HoldRegistersRead.txt not found, using default addresses")
                
        except Exception as e:
            print(f"Error loading hold register addresses: {e}")
            self.hold_register_addresses = ["D001", "D002", "D003", "D004", "D005", "D006", "D007", "D008"]
    
    def load_process_addresses(self):
        """Load process addresses from ProcessStatus.txt file"""
        try:
            # Get the txt_files directory path
            txt_files_dir = os.path.join(os.path.dirname(__file__), 'txt_files')
            process_status_file = os.path.join(txt_files_dir, 'ProcessStatus.txt')
            
            if os.path.exists(process_status_file):
                with open(process_status_file, 'r') as file:
                    content = file.read().strip()
                    if content:
                        self.process_addresses = [addr.strip() for addr in content.split(',')]
                        print(f"Loaded process addresses: {self.process_addresses}")
                    else:
                        # Default addresses if file is empty
                        self.process_addresses = ["M100", "M101", "M102", "M103", "M104", "M105", "M106", "M107"]
                        print("Using default process addresses")
            else:
                # Default addresses if file doesn't exist
                self.process_addresses = ["M100", "M101", "M102", "M103", "M104", "M105", "M106", "M107"]
                print("ProcessStatus.txt not found, using default addresses")
                
        except Exception as e:
            print(f"Error loading process addresses: {e}")
            # Fallback to default addresses
            self.process_addresses = ["M100", "M101", "M102", "M103", "M104", "M105", "M106", "M107"]
            
    def safe_update_message(self, message, color="black"):
        """Safely update message label with proper error handling"""
        try:
            if hasattr(self, 'root') and self.root.winfo_exists():
                if hasattr(self, 'message_label') and self.message_label and self.message_label.winfo_exists():
                    self.message_label.show(message, color)
                else:
                    print(f"Cannot display message '{message}' - message_label not ready")
            else:
                print(f"Cannot display message '{message}' - root window not ready")
        except Exception as e:
            print(f"Error updating message: {e}")
            print(f"Original message was: {message}")

    def connect_to_devices(self):
        """Device connection functionality simplified - PLC removed"""
        try:
            # Check if main_container exists
            if not hasattr(self, 'main_container'):
                print("Error: main_container does not exist. Creating it now.")
                self.main_container = tk.Frame(self.root)
                self.main_container.pack(fill="both", expand=True)
            
            # Check if message_label exists
            if not hasattr(self, 'message_label'):
                print("Error: message_label does not exist. Creating it now.")
                self.message_label = ui.StatusBanner(self.main_container)
                self.message_label.pack(fill="x", padx=ui.PAD, pady=(ui.PAD, 0))
                
            self.safe_update_message("System ready.", "green")
            
        except Exception as e:
            print(f"Error connecting to devices: {str(e)}")
            self.safe_update_message(f"Error connecting to devices: {str(e)}", "red")

    def cleanup(self):
        """Enhanced cleanup method with forced resource release for PLC connection"""
        try:
            # Stop all monitoring first
            self.keepWriting = False
            self.breakLoop = True
            
            # Stop PLC background thread
            if hasattr(self, 'plc_thread_running'):
                self.plc_thread_running = False
                print("PLC background thread stopped")
            
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
            
            # Release the part's program so the PLC is not left running it
            # after the console closes.
            if self.programSelectionPLCAddress and self.plc_client:
                self.write_program_selection_to_plc(False)

            # PLC client cleanup
            self.disconnect_plc()
            
            # Give time for ports to be released
            # Non-blocking delay - operation will complete asynchronously
            
            # Additional force close to ensure COM ports are released
            self.force_close_com_ports()
            
            print("All connections cleaned up successfully")
                
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")
    
    def force_close_com_ports(self):
        """Force close COM ports that might be in use with enhanced error handling"""
        try:
            # Get all available ports first
            available_ports = [p.device for p in list_ports.comports()]
            print(f"Available COM ports: {available_ports}")
            
            # PLC port handling removed
                
            # Also check if any loadcell ports need to be closed
            loadcell1_port = config.get('LOADCELL_01_COM_PORT')
            if loadcell1_port and loadcell1_port.strip():
                if loadcell1_port not in available_ports:
                    print(f"Warning: Configured Loadcell 1 port {loadcell1_port} is not available on this system")
                else:
                    self._force_close_port(loadcell1_port)
                    
            loadcell2_port = config.get('LOADCELL_02_COM_PORT')
            if loadcell2_port and loadcell2_port.strip():
                if loadcell2_port not in available_ports:
                    print(f"Warning: Configured Loadcell 2 port {loadcell2_port} is not available on this system")
                else:
                    self._force_close_port(loadcell2_port)
                    
            # Force garbage collection to ensure any lingering port references are cleaned up
            import gc
            gc.collect()
            
        except Exception as e:
            print(f"Error force-closing COM ports: {e}")
            
    def _force_close_port(self, port):
        """Helper method to force close a single COM port with multiple attempts"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Try with different timeouts and settings
                if attempt == 0:
                    # First attempt - standard settings
                    test_serial = serial.Serial(port, timeout=0.5)
                elif attempt == 1:
                    # Second attempt - shorter timeout
                    test_serial = serial.Serial(port, timeout=0.1, baudrate=9600)
                else:
                    # Third attempt - different settings
                    test_serial = serial.Serial(
                        port, 
                        baudrate=9600, 
                        bytesize=8,
                        parity='N',
                        stopbits=1,
                        timeout=0.1
                    )
                    
                # Successfully opened, now close it
                test_serial.close()
                print(f"Successfully force-closed {port} on attempt {attempt+1}")
                return True
                
            except serial.SerialException as e:
                if "Access is denied" in str(e) or "Port is in use" in str(e):
                    print(f"Attempt {attempt+1}: Port {port} is in use, trying different approach...")
                    # Wait briefly before next attempt
                    # Non-blocking delay - operation will complete asynchronously
                else:
                    print(f"Could not force-close {port} on attempt {attempt+1}: {e}")
                    
            except Exception as e:
                print(f"Error on attempt {attempt+1} to force-close {port}: {e}")
                
        print(f"Failed to force-close {port} after {max_attempts} attempts")
        return False

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
            
            # Use the same exact fixed dimensions as model_settings.py for perfect label alignment
            target_width = 750
            target_height = 450
            
            print(f"Loading image with fixed dimensions: {target_width}x{target_height}")
            
            # Load and resize image to exactly match the model settings dimensions
            original_image = Image.open(image_path)
            resized_image = original_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(resized_image)
            
            # Remove old image label if it exists
            if hasattr(self, 'image_label'):
                self.image_label.destroy()
            
            # Create new image label with exact same dimensions
            self.image_label = tk.Label(self.image_frame, image=photo, bg=ui.SURFACE)
            self.image_label.image = photo  # Keep a reference
            self.image_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Store image dimensions for label positioning
            self.image_dimensions = {
                'width': target_width,
                'height': target_height,
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
                        
                        # Create label with enhanced visibility. label_text is
                        # the canonical key; the caption may have been renamed in
                        # Model Settings, so show the stored text when there is one.
                        label_text = f'L{label_num}'
                        display_text = coord_data.get('text', label_text)
                        new_label = tk.Label(self.image_frame,
                                           text=display_text,
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
                        new_label.label_key = label_text
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

            # Hand the worker thread the sensors to read for these labels
            self.sensor_states = {}
            self.sensor_label_keys = list(self.placed_labels)
            
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
                    'text': label.cget('text')  # Preserve the caption from Model Settings
                }

        try:
            conn = db.connect()
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
        """Validate employee code against EmployeeCodes.txt"""
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
                messagebox.showerror("Error", "Employee Codes text file is either missing or empty!!")
                return
            
            # Read employee codes
            with open(employee_codes_path, 'r') as file:
                content = file.read().strip()
                if content:
                    self.employeeCodesArray = content.split(',')
                    # Clean up employee codes (remove whitespace)
                    self.employeeCodesArray = [code.strip() for code in self.employeeCodesArray]
                else:
                    messagebox.showerror("Error", "Employee Codes text file is either missing or empty!!")
                    return
            
            # Validate employee code
            if emp_code in self.employeeCodesArray:
                # Set employee validation flags
                self.current_employee_id = emp_code
                self.employee_validation_complete = True
                self.employee_validated = True
                
                # Make employee entry read-only
                self.emp_entry.configure(state='readonly', bg="lightgreen")
                
                # Enable ALC entry and set focus
                self.alc_entry.configure(state='normal')
                self.alc_entry.focus_set()
                
                self.safe_update_message("Employee code validated - Enter ALC code", "green")
                
                print(f"Employee {emp_code} validated successfully")
                
                # Initialize database connection test
                self.test_database_connection()
                
            else:
                messagebox.showerror(
                    "Unauthorized Employee", 
                    f"Employee code: {emp_code} is NOT AUTHORIZED to operate this machine, please consult SUPERVISOR."
                )
                self.emp_entry.delete(0, tk.END)
                self.emp_entry.focus_set()
                return
                
        except Exception as e:
            print(f"Error validating employee code: {e}")
            messagebox.showerror("Error", f"Error reading employee codes: {e}")
            # Reset validation flags on error
            self.current_employee_id = None
            self.employee_validation_complete = False
            return

    def process_alc_code_cs_style(self, alc_code):
        """Load the part for a scanned ALC code and start testing it."""
        try:
            # Make ALC entry read-only
            self.alc_entry.configure(state='readonly')
            
            part_exists = False
            self.barcodePrintFileName = ""
            self.prnFileContent = ""
            
            # Database connection using configured settings
            connection = self.get_database_connection()
            if not connection:
                messagebox.showerror("Database Error", "Failed to connect to database")
                return
                
            cursor = connection.cursor(dictionary=True)

            # Query TBL_MODEL_MASTER for part information
            model_query = """
            SELECT 
                MM_PART_NUMBER,
                MM_MODEL_NAME,
                MM_VENDOR_CODE,
                MM_EO_NUMBER,
                MM_SPECIAL_DATA,
                MM_INITIAL_ID,
                MM_SUPPLIER_SECTION,
                MM_IMAGE_PATH,
                MM_BARCODE_LABEL_CODE,
                MM_PLC_ADDRESS,
                MM_LABEL_COORDINATES
            FROM TBL_MODEL_MASTER 
            WHERE MM_ALC_CODE = %s AND MM_STATUS = %s
            """
            cursor.execute(model_query, (alc_code, True))
            model_result = cursor.fetchone()
            
            if model_result:
                # Store part information
                self.current_alc_code = alc_code
                self.partNumber = model_result['MM_PART_NUMBER']
                self.modelName = model_result['MM_MODEL_NAME'] 
                self.vendorCode = model_result['MM_VENDOR_CODE'] or ""
                self.eoNumber = model_result['MM_EO_NUMBER'] or ""
                self.specialData = model_result['MM_SPECIAL_DATA'] or ""
                self.initialID = model_result['MM_INITIAL_ID'] or ""
                self.supplierSection = model_result['MM_SUPPLIER_SECTION'] or ""
                
                # Update part name label
                if hasattr(self, 'model_header'):
                    self.model_header.configure(text=f"{self.modelName} - {self.partNumber}")
                
                # Load part image, then the sensor labels that sit on it
                image_path = self.get_absolute_image_path(model_result['MM_IMAGE_PATH'])
                if image_path and os.path.exists(image_path) and self.load_image_with_path(image_path):
                    coordinates = model_result['MM_LABEL_COORDINATES']
                    if coordinates:
                        try:
                            self.place_labels_from_positions(json.loads(coordinates))
                        except json.JSONDecodeError:
                            messagebox.showwarning("Warning", "Invalid label coordinate data")
                
                # Handle barcode print file
                self.barcodePrintFileName = model_result['MM_BARCODE_LABEL_CODE'] or ""
                if self.barcodePrintFileName and self.barcodePrintFileName != "NO_BARCODE_PRINT_FILE":
                    self.barcodePrintFileNamePath = os.path.join(os.getcwd(), self.barcodePrintFileName)
                    if os.path.exists(self.barcodePrintFileNamePath):
                        with open(self.barcodePrintFileNamePath, 'r') as f:
                            self.prnFileContent = f.read()
                
                # ===================================================================
                # NOTE: Write to PLC during ALC code processing
                # These writes TRIGGER the PLC to start the test automatically
                # ===================================================================
                
                # Get PLC program selection address from database
                self.programSelectionPLCAddress = model_result['MM_PLC_ADDRESS']
                
                print(f"\n{'='*60}")
                print("🎯 PLC INITIALIZATION")
                print(f"{'='*60}")
                
                # Write Program Selection to PLC
                if self.programSelectionPLCAddress:
                    print(f"📝 Program Selection Address: {self.programSelectionPLCAddress}")
                    success = self.write_program_selection_to_plc()
                    if success:
                        print(f"✅ PLC Program Selected - Test will start automatically")
                    else:
                        print(f"❌ Failed to write Program Selection - PLC may not start")
                else:
                    print(f"⚠️ No Program Selection address in database - skipping")
                
                # Write Machine On signal to PLC
                if self.machineOnPLCCoilAddress:
                    print(f"📝 Machine On Address: {self.machineOnPLCCoilAddress}")
                    success = self.write_machine_on_to_plc()
                    if success:
                        print(f"✅ Machine On written - PLC should start running now")
                    else:
                        print(f"❌ Failed to write Machine On - PLC will not start")
                else:
                    print(f"❌ ERROR: MachineOnPLCCoilAddress not configured!")
                    print(f"   Check txt_files/MachineOnPLCCoilAddress.txt exists")
                    messagebox.showwarning("Configuration Error", 
                        "Machine On PLC Coil Address is not configured!\n" +
                        "Test cannot start without this address.")
                
                print(f"{'='*60}\n")
                
                part_exists = True
            
            if part_exists:
                # Load model specifications
                self.load_model_specifications(cursor)
                
                # Load label details for dynamic UI
                self.load_model_label_details(cursor)
                
                # Initialize data display and graphs
                self.display_data()
                self.load_graph()
                
                # Get lot number for this part
                self.get_lot_number()
                
                # ===================================================================
                # NOTE: Auto-start test after ALC code processing
                # Immediately calls start_check_async
                # Test begins automatically without button click
                # ===================================================================
                
                print("\n✅ Part loaded successfully!")
                print("🚀 Starting test automatically - no button click required")
                
                # ===================================================================
                # PLC LABEL COLORING: Set Auto and Home labels to GREEN when part loads
                # Labels remain green until reset (persistent)
                # ===================================================================
                self.set_label_color('auto', 'green', persistent=True)
                self.set_label_color('home', 'green', persistent=True)
                print("🟢 AUTO and HOME labels set to GREEN (part loaded - persistent)")
                
                # Set current part number for testing
                self.current_part_number = self.partNumber
                
                # Update UI to show test is running
                self.process_status = "HIGH"
                if hasattr(self, 'process_control_btn'):
                    self.process_control_btn.configure(text="STOP TESTING", fg_color=ui.DANGER, hover_color=ui.DANGER_HOVER)
                    self.process_control_btn.configure(state='normal')
                
                # Update process indicator
                if hasattr(self, 'update_process_indicator'):
                    self.update_process_indicator("RUNNING")
                
                # Start NG cable validation process
                self.startingNGCableValidation = True
                
                # Update status message
                self.safe_update_message(
                    f"Part loaded - next LOT: {self.next_lot_number()} - Waiting for PLC pull1 state...", 
                    "orange"
                )
                
                # ===================================================================
                # WAIT FOR PULL1 STATE BEFORE STARTING TEST
                # System must wait for PLC to return to pull1 position/state
                # Test will not start until pull1 state is confirmed
                # ===================================================================
                print("⏳ Waiting for PLC to return to pull1 state before starting test...")
                self.wait_for_pull1_and_start_test()
                
                # Reset ALC entry field for next entry
                self.alc_entry.configure(state='normal')
                self.alc_entry.delete(0, tk.END)
                self.alc_entry.insert(0, "ALC CODE")
                self.alc_entry.configure(bg="#fff9c4")
                
            else:
                messagebox.showwarning("Part Not Found", "Scanned Part Does NOT Exist...")
                self.alc_entry.delete(0, tk.END)
                self.alc_entry.configure(state='normal')
                self.alc_entry.focus_set()
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"Error processing ALC code: {e}")
            messagebox.showerror("Error", f"Error processing ALC code: {e}")
            self.alc_entry.delete(0, tk.END)
            self.alc_entry.configure(state='normal')
            self.alc_entry.focus_set()

    def load_model_specifications(self, cursor):
        """Load model specifications from database"""
        try:
            spec_query = """
            SELECT 
                MS_DESCRIPTION,
                MS_DEVICE,
                MS_NORMAL_MIN,
                MS_UNIT,
                MS_NORMAL_MAX
            FROM TBL_MODEL_SPECIFICATION 
            WHERE MS_PART_NUMBER = %s
            ORDER BY MS_DEVICE
            """
            cursor.execute(spec_query, (self.partNumber,))
            specifications = cursor.fetchall()
            
            # Clear existing specification tree
            if hasattr(self, 'spec_tree'):
                self.spec_tree.delete(*self.spec_tree.get_children())
            
            # Reset device visibility flags
            self.columnL2 = self.columnL3 = self.columnL4 = False
            self.columnP3 = self.columnP4 = False
            self.deviceToRead = []
            
            # Process each specification
            for spec in specifications:
                device = spec['MS_DEVICE'].upper()
                self.deviceToRead.append(device)
                
                # Set column visibility flags
                if device == "L2":
                    self.columnL2 = True
                elif device == "L3":
                    self.columnL3 = True
                elif device == "L4":
                    self.columnL4 = True
                elif device == "P3":
                    self.columnP3 = True
                elif device == "P4":
                    self.columnP4 = True
                
                # Add to specification tree
                if hasattr(self, 'spec_tree'):
                    values = (
                        spec['MS_DESCRIPTION'],
                        device,
                        spec['MS_UNIT'],
                        f"{float(spec['MS_NORMAL_MIN']):.2f}" if spec['MS_NORMAL_MIN'] is not None else "N/A",
                        f"{float(spec['MS_NORMAL_MAX']):.2f}" if spec['MS_NORMAL_MAX'] is not None else "N/A",
                        "",  # Actual value (empty initially)
                        ""   # Result (empty initially)
                    )
                    self.spec_tree.insert('', 'end', values=values)
            
            # Update tree columns based on devices
            if hasattr(self, 'spec_tree'):
                self.update_tree_columns(set(self.deviceToRead))
                
        except Exception as e:
            print(f"Error loading model specifications: {e}")

    def load_model_label_details(self, cursor):
        """Load model label details for dynamic UI"""
        try:
            label_query = """
            SELECT 
                MLD_LABEL_ID,
                MLD_ON_STATUS,
                MLD_OFF_STATUS,
                MLD_X,
                MLD_Y,
                MLD_FONT
            FROM TBL_MODEL_LABEL_DETAILS 
            WHERE MLD_PART_NUMBER = %s
            """
            cursor.execute(label_query, (self.partNumber,))
            label_details = cursor.fetchall()
            
            self.mldDataTable = label_details
            self.inputSensorsToReadList = []
            
            # Process each label detail
            for label in label_details:
                if label['MLD_ON_STATUS'] and label['MLD_ON_STATUS'].strip():
                    self.inputSensorsToReadList.append(label['MLD_LABEL_ID'])
                    
                    # Create or update label widget (simplified for now)
                    # In full implementation, this would create dynamic labels on the UI
                    print(f"Label {label['MLD_LABEL_ID']}: {label['MLD_OFF_STATUS']} -> {label['MLD_ON_STATUS']}")
                    
        except Exception as e:
            print(f"Error loading model label details: {e}")

    def write_program_selection_to_plc(self, value=True):
        """
        Write program selection to PLC. False releases the program once the
        closing NG cable check has passed.
        Returns: bool - Success status
        """
        try:
            if not self.programSelectionPLCAddress or not self.plc_client:
                return False
                
            # Convert hex address to int (remove 'M' prefix)
            if self.programSelectionPLCAddress.startswith('M'):
                coil_address = int(self.programSelectionPLCAddress[1:], 16)
                result = self.plc_client.write_coil(coil_address, value, device_id=self.plc_station_id)
                if result.isError():
                    print(f"Error writing program selection to PLC: {result}")
                    return False
                else:
                    print(f"✅ Program selection written: {self.programSelectionPLCAddress} = {value}")
                    return True
            return False
        except Exception as e:
            print(f"Error writing program selection to PLC: {e}")
            return False

    def write_machine_on_to_plc(self):
        """
        Write Machine On signal to PLC
        Returns: bool - Success status
        """
        try:
            if not self.machineOnPLCCoilAddress or not self.plc_client:
                return False
                
            # Convert hex address to int (remove 'M' prefix)  
            if self.machineOnPLCCoilAddress.startswith('M'):
                coil_address = int(self.machineOnPLCCoilAddress[1:], 16)
                result = self.plc_client.write_coil(coil_address, True, device_id=self.plc_station_id)
                if result.isError():
                    print(f"Error writing machine on signal to PLC: {result}")
                    return False
                else:
                    print(f"✅ Machine On written: {self.machineOnPLCCoilAddress}")
                    return True
            else:
                print("⚠️ Machine On PLC Coil Address not configured")
                return False
        except Exception as e:
            print(f"Error writing machine on signal to PLC: {e}")
            return False

    def display_data(self):
        """Show today's passing results for the current part and refresh the counters."""
        if not self.partNumber:
            self.reset_scan_result_counters()
            return

        try:
            connection = self.get_database_connection()
            if not connection:
                return

            cursor = connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT *
                FROM TBL_TEST_DATA
                WHERE TD_RECORD_DATE = CURDATE()
                  AND TD_PART_NUMBER = %s
                  AND TD_OVERALL_STATUS = 'OK'
                ORDER BY ID DESC
            """, (self.partNumber,))
            rows = cursor.fetchall()
            cursor.close()
            connection.close()

            self.update_scan_result_counters(rows)
            self.populate_data_grid(rows)
            print(f"Displaying {len(rows)} test records for part: {self.partNumber}")

        except Exception as e:
            print(f"Error displaying test data: {e}")

    def populate_data_grid(self, rows):
        """Fill the results grid, banding every five rows so they are easy to scan."""
        try:
            self.tree.tag_configure('band', background='#FFFF99')
            self.tree.tag_configure('plain', background='#FFFFFF')

            for item in self.tree.get_children():
                self.tree.delete(item)

            for position, row in enumerate(rows):
                values = []
                for column in self.current_columns:
                    if column == "LOT NUMBER":
                        values.append(row.get('TD_LOT_NUMBER', ''))
                    elif column == "RESULT":
                        values.append(row.get('TD_OVERALL_STATUS', ''))
                    elif column in ("SCAN RESULT", "SR"):
                        values.append(row.get('TD_BARCODE_SCAN_RESULT', ''))
                    else:
                        values.append(row.get(column, ''))

                # Rows alternate in blocks of five, matching the older grid.
                tag = 'band' if (position // 5) % 2 == 0 else 'plain'
                self.tree.insert('', 'end', values=tuple(values), tags=(tag,))

            self.tree.selection_remove(self.tree.selection())

        except Exception as e:
            print(f"Error populating data grid: {e}")

    def update_scan_result_counters(self, rows):
        """Count OK, NG and invalid barcode scans across the displayed rows."""
        try:
            results = [str(row.get('TD_BARCODE_SCAN_RESULT') or '') for row in rows]
            self.ok_count_label.configure(text=str(results.count('OK')))
            self.ng_count_label.configure(text=str(results.count('NG')))
            self.invalid_count_label.configure(text=str(results.count('***')))
            self.total_count_label.configure(text=str(len(rows)))
        except Exception as e:
            print(f"Error updating scan result counters: {e}")

    def reset_scan_result_counters(self):
        """Blank the scan counters, ready for the next part."""
        try:
            for label in (self.ok_count_label, self.ng_count_label,
                          self.invalid_count_label, self.total_count_label):
                label.config(text="")
        except Exception as e:
            print(f"Error resetting scan result counters: {e}")

    def load_graph(self):
        """Load today's readings for the current part into the charts."""
        if not self.partNumber:
            return

        try:
            connection = self.get_database_connection()
            if not connection:
                return

            cursor = connection.cursor()
            cursor.execute("""
                SELECT COUNT(*)
                FROM TBL_TEST_DATA
                WHERE TD_PART_NUMBER = %s AND TD_RECORD_DATE = CURDATE()
            """, (self.partNumber,))
            total_records = cursor.fetchone()[0] or 0

            # Only the most recent 1000 readings are plotted.
            cursor.execute("""
                SELECT ID, L1, L2, L3, L4, P1, P2, P3, P4
                FROM TBL_TEST_DATA
                WHERE TD_PART_NUMBER = %s AND TD_RECORD_DATE = CURDATE()
                ORDER BY ID DESC
                LIMIT 1000
            """, (self.partNumber,))
            rows = cursor.fetchall()
            cursor.close()
            connection.close()

            rows.reverse()  # oldest first, so the chart reads left to right

            names = ('L1', 'L2', 'L3', 'L4', 'P1', 'P2', 'P3', 'P4')
            self.chart_series = {name: [] for name in names}
            for row in rows:
                for offset, name in enumerate(names, start=1):
                    self.chart_series[name].append(self.to_chart_value(row[offset]))

            # Keep numbering continuous when older readings were left out.
            self.dataPointX = total_records if total_records > 1000 else len(rows)

            self.redraw_graphs()
            print(f"Loaded {len(rows)} chart points for part: {self.partNumber}")

        except Exception as e:
            print(f"Error loading graph data: {e}")

    def to_chart_value(self, value):
        """Chart values arrive as text or decimals; anything unparsable is a gap."""
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def update_charts(self, values=None):
        """Append the readings just measured as the next point on each chart."""
        try:
            if values is None:
                values = {
                    'L1': self.L1MaxValue,
                    'L2': self.L2MaxValue,
                    'L3': self.L3MaxValue,
                    'L4': self.L4MaxValue,
                    'P1': self.P01Value,
                    'P2': self.P02Value,
                    'P3': self.P03Value,
                    'P4': self.P04Value,
                }

            self.dataPointX += 1
            for name, series in self.chart_series.items():
                series.append(self.to_chart_value(values.get(name)))
                # Charts hold the same 1000-point window as the initial load.
                if len(series) > 1000:
                    del series[:len(series) - 1000]

            self.redraw_graphs()
            print(f"Updated charts with data point {self.dataPointX}")

        except Exception as e:
            print(f"Error updating charts: {e}")

    def next_lot_number(self):
        """The lot number the next saved test will get, for showing the operator.

        generate_lot_and_traceability() assigns it when the test is saved,
        counting on from the part's running serial.
        """
        try:
            last = int(self.lotNo or 0)
        except ValueError:
            last = 0
        if datetime.today().date() != self.today:
            last = 0  # the count starts again on a new day
        return f"{last + 1:07d}"

    def get_lot_number(self):
        """Get lot number from database"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return
                
            cursor = connection.cursor(dictionary=True)
            
            lot_query = """
            SELECT RUNNING_LOT_NUMBER
            FROM TBL_PART_RUNNING_SERIAL 
            WHERE PART_NUMBER = %s AND TEST_DAY_DATE = %s
            ORDER BY RUNNING_LOT_NUMBER DESC
            LIMIT 1
            """
            cursor.execute(lot_query, (self.partNumber, datetime.today().date()))
            result = cursor.fetchone()
            
            if result:
                self.lotNo = result['RUNNING_LOT_NUMBER']
                self.partRunningSerialExists = True
            else:
                self.lotNo = "0"
                self.partRunningSerialExists = False
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"Error getting lot number: {e}")
            self.lotNo = "0"

    def wait_for_pull1_and_start_test(self):
        """
        Wait for PLC to return to pull1 position/state before starting test
        
        Process flow:
        1. Check if PLC is at pull1 state (not at pull1 OK or NG)
        2. Wait until pull1 state is confirmed
        3. Only then start the test process
        4. Provides visual feedback during wait
        """
        try:
            print("🔍 Checking PLC pull1 state before test initiation...")
            
            # Initialize wait counter
            if not hasattr(self, 'pull1_wait_counter'):
                self.pull1_wait_counter = 0
            
            # Check if we have process addresses loaded
            if not hasattr(self, 'process_addresses') or len(self.process_addresses) < 4:
                print("⚠️ Process addresses not loaded - starting test without pull1 check")
                self.start_check_async()
                return
            
            # Use the worker's latest reading. This runs on the Tk thread and
            # repeats every second, so reading the PLC here would stall the
            # window each time the PLC was slow to answer.
            status_values = self.latest_plc_status

            # Get pull1 addresses (index 2 and 3)
            pull1_ok_addr = self.process_addresses[2] if len(self.process_addresses) > 2 else None
            pull1_ng_addr = self.process_addresses[3] if len(self.process_addresses) > 3 else None
            
            # Check if PLC is ready (not at pull1 OK or NG state)
            pull1_ok_state = status_values.get(pull1_ok_addr, False) if pull1_ok_addr else False
            pull1_ng_state = status_values.get(pull1_ng_addr, False) if pull1_ng_addr else False
            
            # Condition: Wait for PLC to be at neutral/ready state (not at pull1 result)
            # The PLC should be ready to start pull1 test
            is_pull1_ready = not pull1_ok_state and not pull1_ng_state
            
            if is_pull1_ready:
                # PLC is at pull1 ready state - can start test
                print("✅ PLC at pull1 ready state - Starting test now")
                self.safe_update_message(
                    f"PLC ready at pull1 - Starting test for LOT: {self.next_lot_number()}", 
                    "green"
                )
                self.pull1_wait_counter = 0  # Reset counter
                
                # Reset 1st PULL label color from yellow (waiting) to default blue
                if hasattr(self, 'process_status_labels') and '1st' in self.process_status_labels:
                    self.process_status_labels['1st'].config(bg="#00BFFF")
                
                # Start the test)
                print("🔄 Calling start_check_async() - coil read loop will begin...")
                self.start_check_async()
                
            else:
                # PLC not ready - wait and check again
                self.pull1_wait_counter += 1
                
                # Update status message with wait indication
                wait_msg = f"Waiting for PLC pull1 ready state... ({self.pull1_wait_counter}s)"
                self.safe_update_message(wait_msg, "orange")
                print(f"⏳ {wait_msg}")
                
                # Visual feedback: Set 1st PULL label to yellow (waiting state)
                if hasattr(self, 'process_status_labels') and '1st' in self.process_status_labels:
                    self.process_status_labels['1st'].config(bg="#FFD700")  # Gold/Yellow for waiting
                
                # Print detailed state for debugging
                if self.pull1_wait_counter % 5 == 0:  # Print every 5 seconds
                    print(f"   Pull1 OK: {pull1_ok_state}, Pull1 NG: {pull1_ng_state}")
                
                # Timeout after 60 seconds
                if self.pull1_wait_counter >= 60:
                    print("⚠️ Timeout waiting for pull1 state - Starting test anyway")
                    self.safe_update_message(
                        "Timeout waiting for pull1 - Starting test", 
                        "red"
                    )
                    self.pull1_wait_counter = 0
                    self.start_check_async()
                    return
                
                # Check again after 1 second
                self.root.after(1000, self.wait_for_pull1_and_start_test)
                
        except Exception as e:
            print(f"Error waiting for pull1 state: {e}")
            print("⚠️ Starting test without pull1 check")
            self.start_check_async()
    
    def start_check_async(self):
        """Start asynchronous testing process"""
        # Start the main testing workflow
        print("Starting EOL testing process...")
        self.safe_update_message("Starting test process...", "blue")
        
        # In full implementation, this would start:
        # 1. PLC status coils
        # 2. Part-presence sensors
        # 3. Load cell/position registers
        
        # Start real PLC monitoring process
        self.root.after(1000, self.start_real_plc_test_process)

    def start_real_plc_test_process(self):
        """
        Start real PLC-controlled testing process
        
        NOTE: PLC writes already done in process_alc_code_cs_style()
              This method ONLY starts the continuous read loops
        """
        try:
            print("🔄 Starting PLC monitoring loops (continuous coil reads)...")
            
            # PLC writes already done during ALC code processing
            # Now we just start the continuous read loops
            
            # Verify PLC connection
            if not hasattr(self, 'plc_client') or not self.plc_client or not self.plc_client.is_socket_open():
                print("⚠️ PLC not connected - cannot start monitoring")
                self.safe_update_message("PLC not connected - cannot start test", "red")
                return
            
            print("✅ PLC connected - starting coil read loop")
            
            # ===================================================================
            # PLC LABEL COLORING: Set Test label to GREEN when test process starts
            # Label remains green until reset (persistent)
            # ===================================================================
            self.set_label_color('test', 'green', persistent=True)
            print("🟢 TEST label set to GREEN (test process started - persistent)")
            
            # Initialize test state flags. Readings taken while the machine
            # sat idle must not count as this test's peaks.
            self.reset_measurements()
            self.rcvdTestRslt = False  # flag for test completion
            self.noOfValues = 0        # counter for loadcell values
            
            # Start PLC coil monitoring (the coil read step - line 558)
            self.status_monitoring_active = True
            self.start_plc_status_monitoring()
            
            # Start sensor input monitoring (the sensor input step - line 559)
            # This would monitor input sensors if configured
            
            print("✅ Monitoring loops started")
            print("   📖 Monitoring process status coils")
            print("   📖 Reading coils every 200ms")
            print("   ⏳ Waiting for rcvdTestRslt = True")
            
            self.safe_update_message("Test in progress - Monitoring PLC...", "blue")
            
        except Exception as e:
            print(f"Error starting real PLC test process: {e}")
            self.safe_update_message(f"Test Process Error: {e}", "red")

    def start_plc_status_monitoring(self):
        """Start monitoring PLC process status in real-time"""
        try:
            print("Starting PLC status monitoring...")
            self.status_monitoring_active = True
            
            # Start background PLC reading thread
            if not self.plc_thread_running:
                self.plc_thread_running = True
                self.plc_read_thread = threading.Thread(target=self._plc_read_worker, daemon=True)
                self.plc_read_thread.start()
            
            # Start GUI update loop. Only one may run: every test start comes
            # through here, and a second loop would see each result twice.
            if not self.plc_status_loop_running:
                self.plc_status_loop_running = True
                self.monitor_plc_status()
        except Exception as e:
            print(f"Error starting PLC status monitoring: {e}")
    
    def _plc_read_worker(self):
        """Background worker thread for reading PLC status and sensor data - prevents GUI blocking"""
        while self.plc_thread_running and self.status_monitoring_active:
            try:
                # Read PLC coil status in background thread
                status_values = self.read_process_status_values()
                self.latest_plc_status = status_values

                if not status_values:
                    # PLC not answering. Skip the register and sensor reads,
                    # which would each wait out a timeout, and leave the line
                    # free for the window's writes for a while.
                    time.sleep(1)
                    continue

                # Put result in queue (non-blocking)
                try:
                    self.plc_status_queue.put_nowait(status_values)
                except queue.Full:
                    # Queue full, discard oldest value
                    try:
                        self.plc_status_queue.get_nowait()
                        self.plc_status_queue.put_nowait(status_values)
                    except:
                        pass
                
                # Also read input registers for loadcell/pressure data (the input register step)
                self._read_all_input_registers()

                # And the part-presence sensors behind the labels on the image
                self._read_sensor_inputs()

                # Wait 200ms between reads
                time.sleep(0.2)

            except Exception as e:
                print(f"Error in PLC read worker: {e}")
                time.sleep(1)  # Wait longer on error

        # Let start_plc_status_monitoring() start a fresh worker next time.
        self.plc_thread_running = False

    def load_input_sensor_addresses(self):
        """PLC input addresses from InputSensors.txt; label Ln reads the nth one."""
        path = os.path.join(os.path.dirname(__file__), 'txt_files', 'InputSensors.txt')
        try:
            with open(path, 'r') as f:
                return [a.strip() for a in f.read().split(',') if a.strip()]
        except OSError as e:
            print(f"Could not read input sensor addresses: {e}")
            return []

    def _read_sensor_inputs(self):
        """Read the sensor behind each placed label - runs in the worker thread."""
        if not self.plc_client or not self.sensor_label_keys:
            return
        if not self.input_sensor_addresses:
            self.input_sensor_addresses = self.load_input_sensor_addresses()

        states = {}
        for key in self.sensor_label_keys:
            index = int(key[1:]) - 1
            if index >= len(self.input_sensor_addresses):
                continue
            try:
                address = int(self.input_sensor_addresses[index][1:], 16)
                result = self.plc_client.read_discrete_inputs(
                    address, count=1, device_id=self.plc_station_id)
                if not result.isError():
                    states[key] = bool(result.bits[0])
            except Exception as e:
                print(f"Error reading sensor for {key}: {e}")
        self.sensor_states = states

    def apply_sensor_states(self):
        """Show each sensor on its label: steady green when made, blinking when not."""
        for key, is_on in self.sensor_states.items():
            label = self.placed_labels.get(key)
            if label is None:
                continue
            if is_on:
                self.stop_label_blinking(key)
                label.configure(bg="#00FF00")
            elif key not in getattr(self, 'blinking_jobs', {}):
                self.blink_label(label, key)

    def update_camera_status(self, status_values):
        """Show camera 1's verdict from its OK, NG and ON/OFF coils.

        ProcessStatus.txt lists them after the eight process steps. Lines
        without them have no camera, and cam1Result stays blank.
        """
        if len(self.process_addresses) < 11:
            return

        cam_ok = status_values.get(self.process_addresses[8], False)
        cam_ng = status_values.get(self.process_addresses[9], False)
        cam_on = status_values.get(self.process_addresses[10], False)

        if not cam_on:
            text, color = "CAMERA OFF", ui.TEXT_MUTED
            self.cam1Result = "OFF"
        elif cam_ok and cam_ng:
            text, color = "CAMERA ERROR", "#FFA500"
        elif cam_ok:
            text, color = "CAMERA PASS", "#00AA00"
            self.cam1Result = "PASS"
        elif cam_ng:
            text, color = "CAMERA NG", "#FF0000"
            self.cam1Result = "NG"
        else:
            text, color = "CAMERA ON", ui.ACCENT

        self.cam1_status.configure(text=text, text_color=color)

    def _read_all_input_registers(self):
        """Read all input registers and update internal values - runs in background thread"""
        try:
            if not hasattr(self, 'plc_client') or not self.plc_client:
                return

            # Once the PLC has reported a result the readings are frozen for
            # scoring.
            if self.rcvdTestRslt:
                return

            # Load register addresses if not loaded
            if not hasattr(self, 'hold_register_addresses') or not self.hold_register_addresses:
                self.load_hold_register_addresses()

            if not self.hold_register_addresses:
                return

            station_id = int(config.get('PLC_STATION_ID', '1'))
            register_data = {}
            
            # Track if we should print debug info (every 5 seconds)
            if not hasattr(self, '_last_register_debug_time'):
                self._last_register_debug_time = 0
            
            should_debug = (time.time() - self._last_register_debug_time) > 5
            
            # Read all 8 registers (D001-D008: L1-L4, P1-P4)
            for i, reg_addr_str in enumerate(self.hold_register_addresses):
                if not reg_addr_str.strip():
                    continue
                
                try:
                    # Parse register address
                    if reg_addr_str.startswith('D'):
                        addr_num = int(reg_addr_str[1:])
                    else:
                        addr_num = int(reg_addr_str)
                    
                    # Read input register
                    result = self.plc_client.read_input_registers(
                        address=addr_num,
                        count=1,
                        device_id=station_id
                    )
                    
                    if not result.isError():
                        raw = result.registers[0] if result.registers else 0
                        register_data[reg_addr_str] = raw

                        # Registers hold signed 16-bit values scaled by the
                        # PLC: load in tenths, position in hundredths.
                        signed = raw - 0x10000 if raw >= 0x8000 else raw
                        value = signed / 10.0 if i < 4 else signed / 100.0

                        # Map to device names (L1-L4, P1-P4)
                        if i < 4:
                            device_name = f"L{i+1}"
                            max_attr = f"L{i+1}MaxValue"
                            current_max = getattr(self, max_attr, 0)
                            new_max = max(current_max, value)
                            setattr(self, max_attr, new_max)
                            if should_debug and value > 0:
                                print(f"📊 {device_name}: {value} (Max: {new_max})")
                        elif i < 8:
                            device_name = f"P{i-3}"
                            value_attr = f"P0{i-3}Value"
                            setattr(self, value_attr, value)
                            if should_debug and value > 0:
                                print(f"📊 {device_name}: {value}")
                        
                except Exception as e:
                    # Silently continue on error to avoid flooding logs
                    pass
            
            # Store latest data and update debug time
            if register_data:
                self.latest_register_data = register_data
                if should_debug:
                    self._last_register_debug_time = time.time()
                    print(f"✅ Register data updated: {len(register_data)} registers read")
                
        except Exception as e:
            # Silently handle errors in background thread
            pass
    
    def monitor_plc_status(self):
        """
        Continuously monitor PLC status and update UI
        
        - Simple do-while loop that reads all coils
        - Updates label colors immediately (Lime/Green, OrangeRed/Red, DeepSkyBlue/Blue)
        - Continues until test result is received
        - Uses 200ms delay between iterations (a 200ms pause)
        
        NOTE: PLC reads now happen in background thread to prevent GUI freezing
        """
        try:
            if not hasattr(self, 'status_monitoring_active') or not self.status_monitoring_active:
                self.plc_status_loop_running = False
                return

            # Get PLC status from queue (non-blocking - prevents GUI freeze)
            status_values = {}
            try:
                status_values = self.plc_status_queue.get_nowait()
            except queue.Empty:
                # Nothing new from the worker yet. Reading the PLC from here
                # instead would stall the window behind the worker's request.
                status_values = {}

            self.apply_sensor_states()

            # Update UI labels based on coil values
            if status_values and hasattr(self, 'process_addresses') and self.process_addresses:
                self.update_camera_status(status_values)

                # mapping: processStatusArray indices
                # [0]=AUTO, [1]=HOME, [2]=PULL1_OK, [3]=PULL1_NG, 
                # [4]=PULL2_OK, [5]=PULL2_NG, [6]=TESTRESULT_OK, [7]=TESTRESULT_NG
                
                # AUTO label update
                # Only update if not set to persistent green from part load
                if len(self.process_addresses) > 0:
                    auto_addr = self.process_addresses[0]
                    auto_result = status_values.get(auto_addr, False)
                    if hasattr(self, 'auto_label') and not self.is_label_persistent('auto'):
                        # Lime if HIGH, DeepSkyBlue if LOW
                        self.auto_label.config(bg="#00FF00" if auto_result else "#00BFFF")
                
                # HOME label update
                # Only update if not set to persistent green from part load
                if len(self.process_addresses) > 1:
                    home_addr = self.process_addresses[1]
                    home_result = status_values.get(home_addr, False)
                    if hasattr(self, 'home_label') and not self.is_label_persistent('home'):
                        self.home_label.config(bg="#00FF00" if home_result else "#00BFFF")
                
                # PULL1 label update
                if len(self.process_addresses) > 3:
                    pull1_ok_addr = self.process_addresses[2]
                    pull1_ng_addr = self.process_addresses[3]
                    pull1_ok_result = status_values.get(pull1_ok_addr, False)
                    pull1_ng_result = status_values.get(pull1_ng_addr, False)
                    
                    # Use process_status_labels dict instead (safer)
                    if hasattr(self, 'process_status_labels') and '1st' in self.process_status_labels:
                        label = self.process_status_labels['1st']
                        if pull1_ok_result:
                            label.config(bg="#00FF00")  # Lime
                        elif pull1_ng_result:
                            label.config(bg="#FF4500")  # OrangeRed
                        else:
                            label.config(bg="#00BFFF")  # DeepSkyBlue
                
                # PULL2 label update
                if len(self.process_addresses) > 5:
                    pull2_ok_addr = self.process_addresses[4]
                    pull2_ng_addr = self.process_addresses[5]
                    pull2_ok_result = status_values.get(pull2_ok_addr, False)
                    pull2_ng_result = status_values.get(pull2_ng_addr, False)
                    
                    # Use process_status_labels dict instead (safer)
                    if hasattr(self, 'process_status_labels') and '2nd' in self.process_status_labels:
                        label = self.process_status_labels['2nd']
                        if pull2_ok_result:
                            label.config(bg="#00FF00")  # Lime
                        elif pull2_ng_result:
                            label.config(bg="#FF4500")  # OrangeRed
                        else:
                            label.config(bg="#00BFFF")  # DeepSkyBlue
                
                # TEST RESULT label update
                if len(self.process_addresses) > 7:
                    test_ok_addr = self.process_addresses[6]
                    test_ng_addr = self.process_addresses[7]
                    test_ok_result = status_values.get(test_ok_addr, False)
                    test_ng_result = status_values.get(test_ng_addr, False)
                    
                    if hasattr(self, 'test_label'):
                        # Allow updating to OK (green) or NG (red) results
                        # But keep persistent green if test is running (before results)
                        if test_ok_result:
                            self.test_label.config(bg="#00FF00")  # Lime
                        elif test_ng_result:
                            self.test_label.config(bg="#FF4500")  # OrangeRed
                        elif not self.is_label_persistent('test'):
                            # Only revert to blue if not persistent (before test starts)
                            self.test_label.config(bg="#00BFFF")  # DeepSkyBlue
                    
                    # Check if test result received. A result coil the PLC
                    # still holds from the test just scored is not a new
                    # result, so wait until both drop before accepting another.
                    if test_ok_result or test_ng_result:
                        if (not getattr(self, 'rcvdTestRslt', False)
                                and not self.awaiting_result_clear):
                            self.rcvdTestRslt = True
                            self.awaiting_result_clear = True
                            print("✅ Test result received from PLC")
                            # Handle test completion
                            self.root.after(500, self.test_result_command)
                    else:
                        self.awaiting_result_clear = False
            
            # Continue monitoring loop (a 200ms pause)
            if self.status_monitoring_active:
                self.root.after(200, self.monitor_plc_status)
            else:
                self.plc_status_loop_running = False

        except Exception as e:
            print(f"Error in monitor_plc_status: {e}")
            # Continue monitoring despite errors
            if hasattr(self, 'status_monitoring_active') and self.status_monitoring_active:
                self.root.after(200, self.monitor_plc_status)
            else:
                self.plc_status_loop_running = False

    def get_actual_value_for_device(self, device):
        """Get actual value for a specific device"""
        device_map = {
            "L1": self.L1MaxValue,
            "L2": self.L2MaxValue,
            "L3": self.L3MaxValue,
            "L4": self.L4MaxValue,
            "P1": self.P01Value,
            "P2": self.P02Value,
            "P3": self.P03Value,
            "P4": self.P04Value
        }
        return device_map.get(device, 0.0)

    def complete_test_cycle(self):
        """Complete the test cycle and save results"""
        try:
            # Generate lot number and traceability code
            self.generate_lot_and_traceability()
            
            # Check for duplicate traceability code
            if self.check_traceability_duplicate():
                messagebox.showwarning("Duplicate Code", 
                    f"Generated Traceability Code: {self.traceabilityCode} already exists. Saving as 'NG'.")
                self.save_testing_data("NG")
            elif self.passCounter == len(self.deviceToRead):
                # All tests passed
                self.save_testing_data("OK")
                # Print barcode if configured
                if self.barcodePrintFileName and self.barcodePrintFileName != "NO_BARCODE_PRINT_FILE":
                    self.print_barcode_label_async()
            else:
                # Some tests failed
                self.save_testing_data("NG")
            
            # Update charts and displays
            self.update_charts()
            
        except Exception as e:
            print(f"Error completing test cycle: {e}")

    def generate_lot_and_traceability(self):
        """Generate lot number and traceability code"""
        try:
            # Check if day has changed
            current_date = datetime.today().date()
            if (current_date - self.today).days >= 1:
                self.lotNo = "0"
                self.today = current_date
                self.partRunningSerialExists = False
            
            # Increment lot number
            lot_num = int(self.lotNo) + 1
            self.lotNo = f"{lot_num:07d}"  # 7-digit format
            
            # Generate traceability code: yyMMdd + I + MachineID + G1A + LotNumber
            date_str = current_date.strftime("%y%m%d")
            machine_suffix = self.machineID[2:] if len(self.machineID) > 2 else "01"
            self.traceabilityCode = f"{date_str}I{machine_suffix}G1A{self.lotNo}"
            
            print(f"Generated lot: {self.lotNo}, traceability: {self.traceabilityCode}")
            
        except Exception as e:
            print(f"Error generating lot and traceability: {e}")

    def check_traceability_duplicate(self):
        """Check if traceability code already exists"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            duplicate_query = """
            SELECT TD_TRACEABILITY_CODE 
            FROM TBL_TEST_DATA 
            WHERE TD_PART_NUMBER = %s 
            AND TD_RECORD_DATE = %s 
            AND TD_TRACEABILITY_CODE = %s
            """
            cursor.execute(duplicate_query, (self.partNumber, datetime.today().date(), self.traceabilityCode))
            result = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            return result is not None
            
        except Exception as e:
            print(f"Error checking traceability duplicate: {e}")
            return False

    def reset_dgv_spec_data(self):
        """Blank the measured half of the specification grid.

        The Description/Device/Unit/Min/Max columns describe the part and
        stay put; Actual and Result belong to the test that just ran, so a
        new part must not start out showing the previous one's readings.
        """
        if not hasattr(self, 'spec_tree') or not self.spec_tree:
            return

        try:
            for item in self.spec_tree.get_children():
                values = list(self.spec_tree.item(item, "values"))
                if len(values) >= 7:
                    values[-2] = ""  # Actual
                    values[-1] = ""  # Result
                    self.spec_tree.item(item, values=values, tags=('neutral',))
        except Exception as e:
            print(f"Error resetting specification grid: {e}")

    def reset_test_parameters(self):
        """Reset test parameters for next cycle"""
        # Reset message
        self.safe_update_message("", "black")

        # Put the step lamps back to their waiting colour. Without this a
        # finished cycle leaves AUTO/HOME/PULL1/PULL2/TESTRESULT showing the
        # last run's pass and fail colours into the next part.
        self.reset_process_status_labels()

        self.reset_measurements()

        # Reset counters
        self.failCounter = 0
        self.passCounter = 0

        # Reset flags
        self.rcvdTestRslt = False
        self.cam1Result = ""
        if hasattr(self, 'cam1_status'):
            self.cam1_status.configure(text="No image", text_color=ui.TEXT_MUTED)

    def reset_measurements(self):
        """Zero the readings so the next test's peaks start from nothing."""
        # Reset load cell values
        self.loadcell01Value = 0.0
        self.loadcell02Value = 0.0
        self.loadcell03Value = 0.0
        self.loadcell04Value = 0.0
        
        # Reset maximum values
        self.L1MaxValue = 0.0
        self.L2MaxValue = 0.0
        self.L3MaxValue = 0.0
        self.L4MaxValue = 0.0
        
        # Reset pressure values
        self.P01Value = 0.0
        self.P02Value = 0.0
        self.P03Value = 0.0
        self.P04Value = 0.0

    def save_testing_data(self, status):
        """Save testing data to database"""
        try:
            connection = self.get_database_connection()
            if not connection:
                messagebox.showerror("Database Error", "Failed to connect to database for saving results")
                return
                
            cursor = connection.cursor()
            
            # Build dynamic INSERT query based on available columns
            base_columns = [
                'TD_MACHINE_ID', 'TD_PART_NUMBER', 'TD_LOT_NUMBER', 
                'TD_TRACEABILITY_CODE', 'TD_RECORD_DATE', 'TD_DATETIME', 
                'L1', 'P1', 'P2', 'CAM1', 'TD_OVERALL_STATUS', 'TD_EMP_CODE'
            ]
            
            base_values = [
                self.machineID, self.partNumber, self.lotNo,
                self.traceabilityCode, datetime.today().date(), datetime.now(),
                self.L1MaxValue, self.P01Value, self.P02Value,
                self.cam1Result, status, self.current_employee_id
            ]
            
            # Add optional columns based on part configuration
            if self.columnL2:
                base_columns.append('L2')
                base_values.append(self.L2MaxValue)
            if self.columnL3:
                base_columns.append('L3')
                base_values.append(self.L3MaxValue)
            if self.columnL4:
                base_columns.append('L4')
                base_values.append(self.L4MaxValue)
            if self.columnP3:
                base_columns.append('P3')
                base_values.append(self.P03Value)
            if self.columnP4:
                base_columns.append('P4')
                base_values.append(self.P04Value)
            
            # Create INSERT query
            columns_str = ', '.join(base_columns)
            placeholders = ', '.join(['%s'] * len(base_values))
            
            insert_query = f"""
            INSERT INTO TBL_TEST_DATA ({columns_str})
            VALUES ({placeholders})
            """
            
            cursor.execute(insert_query, base_values)

            # The Data Console reports from TBL_TEST_RESULTS, so the same test
            # goes there too, in the same transaction. Devices this part does
            # not use stay NULL.
            measured = dict(zip(base_columns, base_values))
            devices = ['L1', 'L2', 'L3', 'L4', 'P1', 'P2', 'P3', 'P4']
            cursor.execute("""
                INSERT INTO TBL_TEST_RESULTS
                (LOT_NUMBER, PART_NUMBER, L1, L2, L3, L4, P1, P2, P3, P4,
                 RESULT, CREATED_BY, EMP_CODE, SPEC_DATA)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.lotNo, self.partNumber,
                *(measured.get(d) for d in devices),
                "PASS" if status == "OK" else "NG",
                self.current_employee_id, self.current_employee_id,
                json.dumps({d: measured[d] for d in devices if d in measured}),
            ))
            connection.commit()

            print(f"Test data saved: {status} - Lot: {self.lotNo}, Traceability: {self.traceabilityCode}")
            
            # Update or insert part running serial
            if status == "OK":
                self.update_part_running_serial(cursor)
                connection.commit()
            
            cursor.close()
            connection.close()
            
            # Update display
            self.display_data()
            
        except Exception as e:
            print(f"Error saving testing data: {e}")
            messagebox.showerror("Database Error", f"Failed to save test data: {e}")

    def update_part_running_serial(self, cursor):
        """Update or insert part running serial record"""
        try:
            if not self.partRunningSerialExists:
                # Insert new record
                insert_query = """
                INSERT INTO TBL_PART_RUNNING_SERIAL 
                (PART_NUMBER, TEST_DAY_DATE, TEST_DAY_LAST_DATE_TIME, TRACEABILITY_CODE, RUNNING_LOT_NUMBER)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    self.partNumber,
                    datetime.today().date(),
                    datetime.now(),
                    self.traceabilityCode,
                    self.lotNo
                ))
                self.partRunningSerialExists = True
                print("Inserted new part running serial record")
            else:
                # Update existing record
                update_query = """
                UPDATE TBL_PART_RUNNING_SERIAL 
                SET TEST_DAY_LAST_DATE_TIME = %s,
                    TRACEABILITY_CODE = %s,
                    RUNNING_LOT_NUMBER = %s
                WHERE PART_NUMBER = %s AND TEST_DAY_DATE = %s
                """
                cursor.execute(update_query, (
                    datetime.now(),
                    self.traceabilityCode,
                    self.lotNo,
                    self.partNumber,
                    datetime.today().date()
                ))
                print("Updated existing part running serial record")
                
        except Exception as e:
            print(f"Error updating part running serial: {e}")

    def print_barcode_label_async(self):
        """Print barcode label asynchronously"""
        try:
            if not self.prnFileContent:
                print("No barcode template content available")
                return
            
            # Replace placeholders in template
            print_file_text = self.prnFileContent
            
            # Replace all placeholders with actual values
            replacements = {
                # The ALC box is cleared once the part loads, so use the
                # code the part was loaded with.
                '@alcCode@': self.current_alc_code,
                '@partNumber@': self.partNumber,
                '@modelName@': self.modelName,
                '@vendorCode@': self.vendorCode,
                '@eoNumber@': self.eoNumber,
                '@specialData@': self.specialData,
                '@initialID@': self.initialID,
                '@supplierSection@': self.supplierSection,
                '@lotNo@': self.lotNo,
                '@traceabilityCode@': self.traceabilityCode,
                '@L1MaxValue@': f"{self.L1MaxValue:.1f}",
                '@L2MaxValue@': f"{self.L2MaxValue:.1f}",
                '@L3MaxValue@': f"{self.L3MaxValue:.1f}",
                '@L4MaxValue@': f"{self.L4MaxValue:.1f}",
                '@P01Value@': f"+{self.P01Value:.2f}" if self.P01Value >= 0 else f"{self.P01Value:.2f}",
                '@P02Value@': f"+{self.P02Value:.2f}" if self.P02Value >= 0 else f"{self.P02Value:.2f}",
                '@P03Value@': f"+{self.P03Value:.2f}" if self.P03Value >= 0 else f"{self.P03Value:.2f}",
                '@P04Value@': f"+{self.P04Value:.2f}" if self.P04Value >= 0 else f"{self.P04Value:.2f}",
                '@ddMMyy@': datetime.now().strftime("%d%m%y"),
                '@HH:mm:ss@': datetime.now().strftime("%H:%M:%S"),
                '@machineID@': self.machineID,
                '@machineID_NoAlphabet@': self.machineID[2:] if len(self.machineID) > 2 else "01"
            }
            
            for placeholder, value in replacements.items():
                print_file_text = print_file_text.replace(placeholder, str(value))
            
            printer_name = config.get('LABEL_PRINTER_NAME', 'EOL_LABEL_PRNTR')
            send_raw_to_printer(printer_name, print_file_text.encode('utf-8'))
            print(f"Barcode label sent to printer: {printer_name}")

            # Start waiting for barcode scan verification
            self.wait_for_barcode_scan()

        except Exception as e:
            print(f"Error printing barcode label: {e}")
            messagebox.showerror("Print Error", f"Printing failed: {e}")

    def wait_for_barcode_scan(self):
        """Open the scan box for the label just printed and start its timeout."""
        self.printedLabelScanDataInput_Received = False
        self.awaiting_label_scan = True
        self.label_scan_code = self.traceabilityCode

        self.label_scan_entry.configure(state='normal')
        self.label_scan_entry.delete(0, tk.END)
        self.label_scan_entry.focus_set()
        self.safe_update_message("Scan the printed label...", "blue")

        code = self.label_scan_code
        self.root.after(self.printedLabelScanDataInput_WaitTime,
                        lambda: self.check_barcode_scan_timeout(code))

    def check_barcode_scan_timeout(self, code):
        """Record '***' when the label printed for code was never scanned."""
        if self.awaiting_label_scan and self.label_scan_code == code                 and not self.printedLabelScanDataInput_Received:
            self.close_label_scan()
            self.update_scan_result("***", code)
            print("Barcode scan timed out - marked as '***'")

    def on_label_scan_key(self, event=None):
        """Treat the first character as the scan starting.

        Scanners that send no Enter are read once PRINTED_LABEL_SCAN_TIME_INTERVAL
        has passed, which is long enough for the whole code to arrive.
        """
        if (not self.awaiting_label_scan or self.printedLabelScanDataInput_Received
                or not self.label_scan_entry.get()):
            return
        self.printedLabelScanDataInput_Received = True
        self.root.after(self.printedLabelScanDataInput_TimeInterval, self.submit_label_scan)

    def submit_label_scan(self, event=None):
        """Check the scanned label against the code it was printed with."""
        if not self.awaiting_label_scan:
            return "break"
        scanned = self.label_scan_entry.get().strip()
        if not scanned:
            return "break"
        self.printedLabelScanDataInput_Received = True
        code = self.label_scan_code
        self.close_label_scan()
        self.process_barcode_scan_result(scanned, code)
        return "break"

    def close_label_scan(self):
        self.awaiting_label_scan = False
        self.label_scan_entry.delete(0, tk.END)
        self.label_scan_entry.configure(state='disabled')

    def process_barcode_scan_result(self, scanned_text, code):
        """Record OK when the scanned label carries code, otherwise NG and alert."""
        try:
            if code and code in scanned_text:
                self.update_scan_result("OK", code)
                self.safe_update_message("Label scan OK", "green")
                print("Barcode scan successful - marked as 'OK'")
            else:
                self.update_scan_result("NG", code)
                print("Barcode scan failed - marked as 'NG'")
                
                # Sound the line alert
                self.activate_plc_alert()
                
                messagebox.showwarning(
                    "Scan NG",
                    "Barcode Scan found NG.\nDo NOT fix the Barcode Label to the part.\nPaste it on Production Log Book as NG."
                )
            
        except Exception as e:
            print(f"Error processing barcode scan result: {e}")

    def update_scan_result(self, result, code):
        """Record the scan result against the test whose label carries code."""
        try:
            connection = self.get_database_connection()
            if not connection:
                return
                
            cursor = connection.cursor()
            
            update_query = """
            UPDATE TBL_TEST_DATA 
            SET TD_BARCODE_SCAN_RESULT = %s
            WHERE TD_PART_NUMBER = %s AND TD_TRACEABILITY_CODE = %s
            """
            cursor.execute(update_query, (result, self.partNumber, code))
            connection.commit()
            
            cursor.close()
            connection.close()
            
            print(f"Barcode scan result updated: {result}")
            
            # The grid and counters both show scan results, so refresh them.
            self.display_data()
            
        except Exception as e:
            print(f"Error updating scan result: {e}")

    def activate_plc_alert(self):
        """Activate PLC alert signal"""
        try:
            if self.alertOnPLCCoilAddress and self.plc_client:
                # Convert hex address to int (remove 'M' prefix)
                if self.alertOnPLCCoilAddress.startswith('M'):
                    coil_address = int(self.alertOnPLCCoilAddress[1:], 16)
                    
                    # Turn alert ON
                    result = self.plc_client.write_coil(coil_address, True, device_id=self.plc_station_id)
                    if result.isError():
                        print(f"Error activating PLC alert: {result}")
                    else:
                        print(f"PLC alert activated at address {self.alertOnPLCCoilAddress}")
                        
                        # Schedule alert OFF after timeout
                        self.root.after(self.alertOn_TimeInterval, lambda: self.deactivate_plc_alert(coil_address))
                else:
                    messagebox.showerror("Error", f"Alert On PLC Coil Address '{self.alertOnPLCCoilAddress}' "
                                                  "is not an M coil address (e.g. M1001).")
            else:
                messagebox.showerror("Error", "Alert On PLC Coil Address text file is either missing or empty!!")
                
        except Exception as e:
            print(f"Error activating PLC alert: {e}")

    def deactivate_plc_alert(self, coil_address):
        """Deactivate PLC alert signal"""
        try:
            if self.plc_client:
                result = self.plc_client.write_coil(coil_address, False, device_id=self.plc_station_id)
                if result.isError():
                    print(f"Error deactivating PLC alert: {result}")
                else:
                    print(f"PLC alert deactivated at address {coil_address}")
        except Exception as e:
            print(f"Error deactivating PLC alert: {e}")

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
        # Check employee validation first
        if not self.employee_validation_complete or not self.current_employee_id:
            self.safe_update_message("Employee validation required before Part Number entry", "red")
            messagebox.showwarning("Employee Validation Required", 
                                 "Please validate your Employee ID before entering Part Number")
            return
        
        # Use the value from the entry field
        alc_code = self.alc_entry.get().strip()
        
        if not alc_code or alc_code == "ALC CODE":
            messagebox.showwarning("Warning", "Please enter a valid ALC code")
            return
            
        # Log part number entry attempt
        self.log_operator_action("PART_NUMBER_ENTRY", f"ALC Code: {alc_code}", self.current_employee_id)
        
        # Look the part up on the Tk thread: the lookup builds widgets and
        # shows dialogs, which Tkinter only allows from this thread. The code
        # arrives complete on Enter, so there is no settling wait.
        self.process_alc_code_cs_style(alc_code)
        return

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
        """Record the test on the machine now, without waiting for the PLC.

        It goes through the same scoring and saving as a result the PLC
        reports, so the test lands in the same tables either way.
        """
        if not getattr(self, 'current_part_number', None):
            messagebox.showwarning("Next Label", "Load a part before recording a test.")
            return
        if self.rcvdTestRslt:
            return  # a result is already being recorded

        # Freeze the readings, as a PLC-reported result does
        self.rcvdTestRslt = True
        self.test_result_command()

    def set_label_color(self, label_name, color, persistent=False):
        """
        Set the color of a process status label
        
        Args:
            label_name: Name of label ('auto', 'home', '1st', '2nd', 'test')
            color: Color to set (e.g., 'green', '#00FF00', 'red', etc.)
            persistent: If True, label color persists until reset (used for part load indicators)
        
        Usage:
            self.set_label_color('auto', 'green', persistent=True)  # Set AUTO label to green, keep it green
            self.set_label_color('test', '#00FF00')  # Set TEST label to lime green
        """
        try:
            # Initialize persistent label tracking if not exists
            if not hasattr(self, 'persistent_label_colors'):
                self.persistent_label_colors = {}
            
            # Get label object using attribute name pattern
            label_obj = getattr(self, f"{label_name}_label", None)
            
            if label_obj:
                label_obj.config(bg=color)
                print(f"✓ Set {label_name.upper()} label color to {color}{' (persistent)' if persistent else ''}")
                
                # Track persistent labels
                if persistent:
                    self.persistent_label_colors[label_name] = color
            else:
                print(f"⚠️ Label '{label_name}' not found")
                
        except Exception as e:
            print(f"Error setting label color for '{label_name}': {e}")
    
    def is_label_persistent(self, label_name):
        """Check if a label has a persistent color set"""
        if not hasattr(self, 'persistent_label_colors'):
            return False
        return label_name in self.persistent_label_colors
    
    def reset_process_status_labels(self):
        """Reset all process status labels to default blue state"""
        try:
            # Clear persistent label tracking
            if hasattr(self, 'persistent_label_colors'):
                self.persistent_label_colors.clear()
                print("Cleared persistent label colors")
            
            # List of status labels to reset
            status_labels = ['auto', 'home', '1st', '2nd', 'test']
            
            for label_name in status_labels:
                label_obj = getattr(self, f"{label_name}_label", None)
                if label_obj:
                    label_obj.config(bg="#00BFFF")  # Default blue color
                    print(f"Reset {label_name} label to default blue")
            
        except Exception as e:
            print(f"Error resetting process status labels: {e}")
    
    def get_lot_history(self, limit=50):
        """Get lot test result history from database"""
        try:
            print(f"Getting lot history (limit: {limit})...")
            conn = db.connect(connection_timeout=10, charset='utf8mb4', use_unicode=True, autocommit=True)
            
            cursor = conn.cursor()
            
            # Get current part number if available
            part_number = getattr(self, 'current_part_number', '')
            print(f"Current part number: {part_number}")
            
            if part_number:
                # If part number is available, filter by it and show only PASS results
                query = """
                SELECT LOT_NUMBER, L1, L2, L3, L4, P1, P2, P3, P4, 
                       RESULT, SCAN_RESULT, EMP_CODE, CREATED_DATE, SPEC_DATA
                FROM TBL_TEST_RESULTS
                WHERE PART_NUMBER = %s AND RESULT = 'PASS'
                ORDER BY CREATED_DATE DESC
                LIMIT %s
                """
                cursor.execute(query, (part_number, limit))
                print(f"Executed query with part number filter (PASS only): {part_number}")
            else:
                # Otherwise get the most recent PASS results only
                query = """
                SELECT LOT_NUMBER, L1, L2, L3, L4, P1, P2, P3, P4, 
                       RESULT, SCAN_RESULT, EMP_CODE, CREATED_DATE, SPEC_DATA
                FROM TBL_TEST_RESULTS
                WHERE RESULT = 'PASS'
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
            print("=== LOADING HISTORY TO TREEVIEW ===")
            
            # Get lot history
            history = self.get_lot_history()
            print(f"Retrieved {len(history)} records from database")
            
            if not history:
                print("No history found in database")
                self.safe_update_message("No history found", "blue")
                return
            
            # Update tree columns based on available data before loading
            self.update_tree_columns()
                
            # Don't clear treeview - keep existing data
            print("Keeping existing tree view items")
            
            # Count records for reporting
            total_records = len(history)
            displayed_records = 0
                
                        # Add history items to treeview (only if not already present)
            existing_lots = set()
            for existing_item in self.tree.get_children():
                existing_values = self.tree.item(existing_item, "values")
                if existing_values and len(existing_values) > 0:
                    existing_lots.add(existing_values[0])  # LOT NUMBER is first column
            
            for item in history:
                # Create a dictionary to map column names to values
                values_dict = {}
                values_dict["LOT NUMBER"] = item[0] if len(item) > 0 else ""
                
                # Skip if this lot number is already in the tree
                if values_dict["LOT NUMBER"] in existing_lots:
                    print(f"Skipping existing lot number: {values_dict['LOT NUMBER']}")
                    continue
                
                # Track if this record has any actual values
                has_actual_values = False
                
                # Map database columns to treeview columns using actual column names
                # item structure: LOT_NUMBER, L1, L2, L3, L4, P1, P2, P3, P4, 
                #                RESULT, SCAN_RESULT, EMP_CODE, CREATED_DATE, SPEC_DATA
                device_columns = ["L1", "L2", "L3", "L4", "P1", "P2", "P3", "P4"]
                for i, device in enumerate(device_columns, 1):  # Start from index 1
                    if i < len(item):
                        device_value = item[i]
                        if device_value is not None:
                            has_actual_values = True
                            # Display the actual measurement value stored in device columns
                            values_dict[device] = f"{device_value:.3f}" if isinstance(device_value, (int, float)) else str(device_value)
                        else:
                            values_dict[device] = "N/A"
                    else:
                        values_dict[device] = "N/A"
                
                # Add result and scan result from correct positions
                if len(item) > 9:
                    values_dict["RESULT"] = item[9] or "N/A"  # RESULT column
                else:
                    values_dict["RESULT"] = "N/A"
                
                if len(item) > 10:
                    values_dict["SCAN RESULT"] = item[10] or f"LOT: {item[0]}"  # SCAN_RESULT column
                else:
                    values_dict["SCAN RESULT"] = f"LOT: {item[0]}"
                
                # Only display PASS records with actual values
                result_value = item[9] if len(item) > 9 else ""
                if result_value == "PASS" and has_actual_values:
                    # Create values list in the same order as self.current_columns
                    values = []
                    for col in self.current_columns:
                        if col == "SR":  # Handle short form of SCAN RESULT
                            values.append(values_dict.get("SCAN RESULT", "N/A"))
                        elif col == "SCAN RESULT":
                            values.append(values_dict.get("SCAN RESULT", "N/A"))
                        else:
                            values.append(values_dict.get(col, "N/A"))
                    
                    # Insert the record into the tree
                    print(f"Adding new PASS record to tree: {values}")
                    self.tree.insert("", "end", text=values[0], values=tuple(values))
                    displayed_records += 1
                else:
                    print(f"Skipping record (not PASS or no device values): {item}")
                
            # Display message about records
            if displayed_records > 0:
                self.safe_update_message(f"Loaded {displayed_records} PASS test records from database", "green")
                print(f"Successfully displayed {displayed_records} PASS records out of {total_records} total records")
            else:
                print("No PASS records met display criteria")
                self.safe_update_message(f"No PASS test records found (filtered from {total_records} total records)", "blue")
            
        except Exception as e:
            print(f"Error loading history: {str(e)}")
            traceback.print_exc()
            self.safe_update_message(f"Error loading history: {str(e)}", "red")

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
                self.spec_tree.item(item, tags=(original_tag,))  # Backm to original
                
            # Schedule next flash
            self.root.after(250, lambda: flash_sequence(count + 1))
            
        # Start the flash sequence
        flash_sequence()

    def update_specification_result(self, device_name, value, result_tag=""):
        """Update specification tree with actual value and result for a specific device"""
        try:
            if not hasattr(self, 'spec_tree') or not self.spec_tree:
                return False
                
            # Configure color tags if not already done
            if not hasattr(self, 'spec_color_tags_configured'):
                self.spec_tree.tag_configure('pass', background='#90EE90')  # Light green for PASS
                self.spec_tree.tag_configure('ng', background='#FFCCCB')    # Light red for NG
                self.spec_tree.tag_configure('neutral', background='#FFFFFF')  # White for neutral
                self.spec_tree.tag_configure('value', background='#ADD8E6')  # Light blue for values
                self.spec_color_tags_configured = True
                
            # Loop through all rows in the spec tree
            for item in self.spec_tree.get_children():
                values = list(self.spec_tree.item(item, "values"))
                # Check if the device column matches the requested device
                if len(values) > 1 and values[1] == device_name:
                    # Store original values to compare for changes
                    old_values = values.copy()
                    
                    # Update the Actual column (second to last column)
                    values[-2] = f"{value}"
                    
                    # Get min/max from columns 3 and 4
                    min_val = values[3] if len(values) > 3 and values[3] != "N/A" else None
                    max_val = values[4] if len(values) > 4 and values[4] != "N/A" else None
                    
                    # Default to no specific tag
                    result_tag = 'neutral'
                    
                    try:
                        # Convert to float for comparison
                        value_float = float(value)
                        min_float = float(min_val) if min_val else None
                        max_float = float(max_val) if max_val else None
                        
                        # Determine PASS/NG based on min/max comparison
                        if (min_float is None or value_float >= min_float) and \
                           (max_float is None or value_float <= max_float):
                            values[-1] = "PASS"
                            result_tag = 'pass'
                        else:
                            values[-1] = "NG"
                            result_tag = 'ng'
                    except (ValueError, TypeError):
                        # If conversion fails, leave result unchanged
                        print(f"Error converting values for comparison: {value}, {min_val}, {max_val}")
                    
                    # Update the tree item with new values
                    self.spec_tree.item(item, values=values)
                    
                    # Apply tag to color the row according to result
                    self.spec_tree.item(item, tags=(result_tag,))
                    
                    # If values changed, apply a visual highlight
                    if values != old_values:
                        # Flash the row briefly to highlight the change
                        self.flash_spec_row(item, result_tag)
                    
                    return True
            
            # Device not found in tree
            print(f"Warning: Device {device_name} not found in specification tree")
            return False
                
        except Exception as e:
            print(f"Error updating specification result: {e}")
            traceback.print_exc()
            return False


def main():
    try:
        root = tk.Tk()
        
            
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

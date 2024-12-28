import tkinter as tk
from tkinter import ttk, messagebox
from utils.plc_comm import PLCCommunication
from utils.constants import Constants
import serial.tools.list_ports
import json
import os

class COMPortSettings(tk.Toplevel):
    def __init__(self):
        super().__init__()
        
        self.title("COM Port Settings")
        self.geometry("1000x800")
        
        # PLC connections
        self.plc_connections = {}
        self.monitoring_active = False
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Device sections
        self.create_lvdt_section(main_frame)
        self.create_plc_section(main_frame)
        self.create_loadcell_sections(main_frame)
        self.create_camera_sections(main_frame)
        
        # Control buttons
        self.create_control_buttons(main_frame)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self, textvariable=self.status_var)
        self.status_bar.pack(side="bottom", fill="x")
        
    def create_lvdt_section(self, parent):
        frame = ttk.LabelFrame(parent, text="LVDT Settings")
        frame.pack(fill="x", padx=5, pady=5)
        
        # COM Port
        ttk.Label(frame, text="COM Port:").grid(row=0, column=0, padx=5, pady=5)
        self.cb_lvdt_port = ttk.Combobox(frame, values=self.get_com_ports())
        self.cb_lvdt_port.grid(row=0, column=1, padx=5, pady=5)
        
        # Baud Rate
        ttk.Label(frame, text="Baud Rate:").grid(row=0, column=2, padx=5, pady=5)
        self.cb_lvdt_baud = ttk.Combobox(frame, values=['9600', '19200', '38400', '57600', '115200'])
        self.cb_lvdt_baud.grid(row=0, column=3, padx=5, pady=5)
        self.cb_lvdt_baud.set('9600')
        
        # Test button
        self.btn_test_lvdt = ttk.Button(frame, text="Test", command=lambda: self.test_connection('LVDT'))
        self.btn_test_lvdt.grid(row=0, column=4, padx=5, pady=5)
        
    def create_plc_section(self, parent):
        frame = ttk.LabelFrame(parent, text="PLC Settings")
        frame.pack(fill="x", padx=5, pady=5)
        
        # COM Port
        ttk.Label(frame, text="COM Port:").grid(row=0, column=0, padx=5, pady=5)
        self.cb_plc_port = ttk.Combobox(frame, values=self.get_com_ports())
        self.cb_plc_port.grid(row=0, column=1, padx=5, pady=5)
        
        # Baud Rate
        ttk.Label(frame, text="Baud Rate:").grid(row=0, column=2, padx=5, pady=5)
        self.cb_plc_baud = ttk.Combobox(frame, values=['9600', '19200', '38400', '57600', '115200'])
        self.cb_plc_baud.grid(row=0, column=3, padx=5, pady=5)
        self.cb_plc_baud.set('9600')
        
        # Station ID
        ttk.Label(frame, text="Station ID:").grid(row=0, column=4, padx=5, pady=5)
        self.entry_station_id = ttk.Entry(frame, width=5)
        self.entry_station_id.grid(row=0, column=5, padx=5, pady=5)
        self.entry_station_id.insert(0, "1")
        
        # Test button
        self.btn_test_plc = ttk.Button(frame, text="Test", command=lambda: self.test_connection('PLC'))
        self.btn_test_plc.grid(row=0, column=6, padx=5, pady=5)
        
        # Response frame
        response_frame = ttk.LabelFrame(frame, text="PLC Response")
        response_frame.grid(row=1, column=0, columnspan=7, padx=5, pady=5, sticky="ew")
        
        self.txt_plc_response = tk.Text(response_frame, height=4)
        self.txt_plc_response.pack(fill="both", expand=True, padx=5, pady=5)
        
    def create_loadcell_sections(self, parent):
        loadcell_frame = ttk.LabelFrame(parent, text="Load Cell Settings")
        loadcell_frame.pack(fill="x", padx=5, pady=5)
        
        for i in range(1, 5):
            frame = ttk.Frame(loadcell_frame)
            frame.pack(fill="x", padx=5, pady=5)
            
            ttk.Label(frame, text=f"Load Cell {i}:").grid(row=0, column=0, padx=5)
            
            # COM Port
            ttk.Label(frame, text="COM Port:").grid(row=0, column=1, padx=5)
            cb_port = ttk.Combobox(frame, values=self.get_com_ports(), width=10)
            cb_port.grid(row=0, column=2, padx=5)
            setattr(self, f'cb_lc{i}_port', cb_port)
            
            # Baud Rate
            ttk.Label(frame, text="Baud Rate:").grid(row=0, column=3, padx=5)
            cb_baud = ttk.Combobox(frame, values=['9600', '19200', '38400'], width=10)
            cb_baud.grid(row=0, column=4, padx=5)
            cb_baud.set('9600')
            setattr(self, f'cb_lc{i}_baud', cb_baud)
            
            # Test button
            btn_test = ttk.Button(frame, text="Test", 
                                command=lambda x=i: self.test_connection(f'LC{x}'))
            btn_test.grid(row=0, column=5, padx=5)
            
            # Response display
            txt_response = tk.Text(frame, height=2, width=40)
            txt_response.grid(row=1, column=1, columnspan=5, padx=5, pady=5)
            setattr(self, f'txt_lc{i}_response', txt_response)
            
    def create_camera_sections(self, parent):
        camera_frame = ttk.LabelFrame(parent, text="Camera Settings")
        camera_frame.pack(fill="x", padx=5, pady=5)
        
        for i in range(1, 3):
            frame = ttk.Frame(camera_frame)
            frame.pack(fill="x", padx=5, pady=5)
            
            ttk.Label(frame, text=f"Camera {i}:").grid(row=0, column=0, padx=5)
            
            # COM Port
            ttk.Label(frame, text="COM Port:").grid(row=0, column=1, padx=5)
            cb_port = ttk.Combobox(frame, values=self.get_com_ports(), width=10)
            cb_port.grid(row=0, column=2, padx=5)
            setattr(self, f'cb_cam{i}_port', cb_port)
            
            # Baud Rate
            ttk.Label(frame, text="Baud Rate:").grid(row=0, column=3, padx=5)
            cb_baud = ttk.Combobox(frame, values=['9600', '19200', '38400'], width=10)
            cb_baud.grid(row=0, column=4, padx=5)
            cb_baud.set('9600')
            setattr(self, f'cb_cam{i}_baud', cb_baud)
            
            # Status indicator
            canvas = tk.Canvas(frame, width=20, height=20)
            canvas.grid(row=0, column=5, padx=5)
            canvas.create_oval(2, 2, 18, 18, fill="red", tags=f"status_cam{i}")
            setattr(self, f'canvas_cam{i}', canvas)
            
    def create_control_buttons(self, parent):
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=5, pady=10)
        
        self.btn_save = ttk.Button(btn_frame, text="Save", command=self.save_settings)
        self.btn_save.pack(side="right", padx=5)
        
        self.btn_reset = ttk.Button(btn_frame, text="Reset", command=self.reset_settings)
        self.btn_reset.pack(side="right", padx=5)
        
    def get_com_ports(self):
        """Get list of available COM ports"""
        return [port.device for port in serial.tools.list_ports.comports()]
        
    def test_connection(self, device):
        """Test connection to specified device"""
        try:
            port = getattr(self, f'cb_{device.lower()}_port').get()
            baud = int(getattr(self, f'cb_{device.lower()}_baud').get())
            
            if device == 'PLC':
                plc = PLCCommunication(port, baud)
                if plc.connect():
                    self.txt_plc_response.insert('end', "PLC connection successful\n")
                    plc.disconnect()
                else:
                    self.txt_plc_response.insert('end', "PLC connection failed\n")
            elif device.startswith('LC'):
                # Test load cell connection
                response_widget = getattr(self, f'txt_{device.lower()}_response')
                response_widget.delete(1.0, tk.END)
                response_widget.insert('end', f"Testing {device} connection...\n")
                # Add actual load cell communication here
            
            self.status_var.set(f"Tested {device} connection")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error testing {device} connection: {str(e)}")
            
    def save_settings(self):
        """Save all communication settings"""
        config = Constants.load_config()
        
        # Save COM port settings
        settings = {
            'LVDT': {
                'port': self.cb_lvdt_port.get(),
                'baud': self.cb_lvdt_baud.get()
            },
            'PLC': {
                'port': self.cb_plc_port.get(),
                'baud': self.cb_plc_baud.get(),
                'station_id': self.entry_station_id.get()
            }
        }
        
        # Save load cell settings
        for i in range(1, 5):
            settings[f'LC{i}'] = {
                'port': getattr(self, f'cb_lc{i}_port').get(),
                'baud': getattr(self, f'cb_lc{i}_baud').get()
            }
            
        # Save camera settings
        for i in range(1, 3):
            settings[f'CAM{i}'] = {
                'port': getattr(self, f'cb_cam{i}_port').get(),
                'baud': getattr(self, f'cb_cam{i}_baud').get()
            }
            
        config['COM_SETTINGS'] = json.dumps(settings)
        Constants.save_config(config)
        
        messagebox.showinfo("Success", "Settings saved successfully")
        
    def load_settings(self):
        """Load saved communication settings"""
        config = Constants.load_config()
        try:
            settings = json.loads(config.get('COM_SETTINGS', '{}'))
            
            # Load LVDT settings
            if 'LVDT' in settings:
                self.cb_lvdt_port.set(settings['LVDT']['port'])
                self.cb_lvdt_baud.set(settings['LVDT']['baud'])
                
            # Load PLC settings
            if 'PLC' in settings:
                self.cb_plc_port.set(settings['PLC']['port'])
                self.cb_plc_baud.set(settings['PLC']['baud'])
                self.entry_station_id.delete(0, tk.END)
                self.entry_station_id.insert(0, settings['PLC']['station_id'])
                
            # Load load cell settings
            for i in range(1, 5):
                if f'LC{i}' in settings:
                    getattr(self, f'cb_lc{i}_port').set(settings[f'LC{i}']['port'])
                    getattr(self, f'cb_lc{i}_baud').set(settings[f'LC{i}']['baud'])
                    
            # Load camera settings
            for i in range(1, 3):
                if f'CAM{i}' in settings:
                    getattr(self, f'cb_cam{i}_port').set(settings[f'CAM{i}']['port'])
                    getattr(self, f'cb_cam{i}_baud').set(settings[f'CAM{i}']['baud'])
                    
        except Exception as e:
            messagebox.showwarning("Settings", f"Error loading settings: {str(e)}")
            
    def reset_settings(self):
        """Reset all settings to default"""
        if messagebox.askyesno("Reset", "Are you sure you want to reset all settings?"):
            # Reset LVDT
            self.cb_lvdt_port.set('')
            self.cb_lvdt_baud.set('9600')
            
            # Reset PLC
            self.cb_plc_port.set('')
            self.cb_plc_baud.set('9600')
            self.entry_station_id.delete(0, tk.END)
            self.entry_station_id.insert(0, "1")
            
            # Reset load cells
            for i in range(1, 5):
                getattr(self, f'cb_lc{i}_port').set('')
                getattr(self, f'cb_lc{i}_baud').set('9600')
                
            # Reset cameras
            for i in range(1, 3):
                getattr(self, f'cb_cam{i}_port').set('')
                getattr(self, f'cb_cam{i}_baud').set('9600')
                
            self.status_var.set("Settings reset to default")

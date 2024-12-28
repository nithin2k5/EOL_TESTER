import tkinter as tk
from tkinter import ttk, messagebox
from PyXGT.LS import plc_ls
import configparser
import threading
import time

class PLCTester(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("EOL Tester - PLC Communication")
        self.geometry("1200x800")
        
        # PLC connection variables
        self.plc = None
        self.is_connected = False
        self.monitoring_active = False
        
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        # Create main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Connection Frame
        self.create_connection_frame()
        
        # Test Data Frame
        self.create_test_data_frame()
        
        # Status Frame
        self.create_status_frame()
        
    def create_connection_frame(self):
        conn_frame = ttk.LabelFrame(self.main_frame, text="PLC Connection Settings")
        conn_frame.pack(fill="x", padx=5, pady=5)
        
        # COM Port
        ttk.Label(conn_frame, text="COM Port:").grid(row=0, column=0, padx=5, pady=5)
        self.com_port = ttk.Entry(conn_frame, width=10)
        self.com_port.grid(row=0, column=1, padx=5, pady=5)
        self.com_port.insert(0, "COM1")
        
        # Baud Rate
        ttk.Label(conn_frame, text="Baud Rate:").grid(row=0, column=2, padx=5, pady=5)
        self.baud_rate = ttk.Combobox(conn_frame, values=['9600', '19200', '38400', '57600', '115200'], width=10)
        self.baud_rate.grid(row=0, column=3, padx=5, pady=5)
        self.baud_rate.set('9600')
        
        # Connect Button
        self.btn_connect = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.btn_connect.grid(row=0, column=4, padx=5, pady=5)
        
        # Status Label
        self.lbl_status = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.lbl_status.grid(row=0, column=5, padx=5, pady=5)
        
    def create_test_data_frame(self):
        test_frame = ttk.LabelFrame(self.main_frame, text="Test Data")
        test_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create columns for different data types
        self.create_data_column(test_frame, "Input Signals (X)", 0)
        self.create_data_column(test_frame, "Output Signals (Y)", 1)
        self.create_data_column(test_frame, "Memory (M)", 2)
        self.create_data_column(test_frame, "Data (D)", 3)
        
    def create_data_column(self, parent, title, column):
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=column, padx=5, pady=5, sticky="nsew")
        
        ttk.Label(frame, text=title).pack(fill="x")
        
        # Address entry
        addr_frame = ttk.Frame(frame)
        addr_frame.pack(fill="x", pady=2)
        ttk.Label(addr_frame, text="Address:").pack(side="left")
        addr_entry = ttk.Entry(addr_frame, width=8)
        addr_entry.pack(side="left", padx=2)
        
        # Value display
        val_frame = ttk.Frame(frame)
        val_frame.pack(fill="x", pady=2)
        ttk.Label(val_frame, text="Value:").pack(side="left")
        val_label = ttk.Label(val_frame, text="---")
        val_label.pack(side="left", padx=2)
        
        # Store references
        setattr(self, f'addr_{title.split()[0].lower()}', addr_entry)
        setattr(self, f'val_{title.split()[0].lower()}', val_label)
        
    def create_status_frame(self):
        status_frame = ttk.LabelFrame(self.main_frame, text="Communication Log")
        status_frame.pack(fill="x", padx=5, pady=5)
        
        # Log text
        self.txt_log = tk.Text(status_frame, height=6)
        self.txt_log.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Control buttons
        btn_frame = ttk.Frame(status_frame)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        self.btn_monitor = ttk.Button(btn_frame, text="Start Monitoring", command=self.toggle_monitoring)
        self.btn_monitor.pack(side="left", padx=5)
        
        ttk.Button(btn_frame, text="Clear Log", command=self.clear_log).pack(side="left", padx=5)
        
    def toggle_connection(self):
        if not self.is_connected:
            try:
                port = self.com_port.get()
                baud = int(self.baud_rate.get())
                self.plc = plc_ls(port, baud)
                self.is_connected = True
                self.btn_connect.config(text="Disconnect")
                self.lbl_status.config(text="Connected", foreground="green")
                self.log_message("Connected to PLC")
            except Exception as e:
                messagebox.showerror("Connection Error", str(e))
                self.log_message(f"Connection error: {str(e)}")
        else:
            try:
                if self.plc:
                    self.plc.close()
                self.is_connected = False
                self.btn_connect.config(text="Connect")
                self.lbl_status.config(text="Disconnected", foreground="red")
                self.log_message("Disconnected from PLC")
            except Exception as e:
                self.log_message(f"Disconnection error: {str(e)}")
                
    def toggle_monitoring(self):
        if not self.is_connected:
            messagebox.showwarning("Warning", "Please connect to PLC first")
            return
            
        self.monitoring_active = not self.monitoring_active
        if self.monitoring_active:
            self.btn_monitor.config(text="Stop Monitoring")
            threading.Thread(target=self.monitor_plc, daemon=True).start()
        else:
            self.btn_monitor.config(text="Start Monitoring")
            
    def monitor_plc(self):
        while self.monitoring_active and self.is_connected:
            try:
                # Read Input signals
                if hasattr(self, 'addr_input') and self.addr_input.get():
                    value = self.plc.read_word(self.addr_input.get())
                    self.val_input.config(text=str(value))
                    
                # Read Output signals
                if hasattr(self, 'addr_output') and self.addr_output.get():
                    value = self.plc.read_word(self.addr_output.get())
                    self.val_output.config(text=str(value))
                    
                # Read Memory
                if hasattr(self, 'addr_memory') and self.addr_memory.get():
                    value = self.plc.read_word(self.addr_memory.get())
                    self.val_memory.config(text=str(value))
                    
                # Read Data
                if hasattr(self, 'addr_data') and self.addr_data.get():
                    value = self.plc.read_word(self.addr_data.get())
                    self.val_data.config(text=str(value))
                    
            except Exception as e:
                self.log_message(f"Monitoring error: {str(e)}")
                self.monitoring_active = False
                self.btn_monitor.config(text="Start Monitoring")
                break
                
            time.sleep(0.1)  # Polling interval
            
    def log_message(self, message):
        self.txt_log.insert('end', f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.txt_log.see('end')
        
    def clear_log(self):
        self.txt_log.delete(1.0, tk.END)
        
    def load_settings(self):
        config = configparser.ConfigParser()
        try:
            config.read('plc_config.ini')
            if 'PLC' in config:
                self.com_port.delete(0, tk.END)
                self.com_port.insert(0, config['PLC'].get('com_port', 'COM1'))
                self.baud_rate.set(config['PLC'].get('baud_rate', '9600'))
        except Exception as e:
            self.log_message(f"Error loading settings: {str(e)}")
            
    def save_settings(self):
        config = configparser.ConfigParser()
        config['PLC'] = {
            'com_port': self.com_port.get(),
            'baud_rate': self.baud_rate.get()
        }
        try:
            with open('plc_config.ini', 'w') as f:
                config.write(f)
            self.log_message("Settings saved successfully")
        except Exception as e:
            self.log_message(f"Error saving settings: {str(e)}")
            
    def on_closing(self):
        if self.is_connected:
            self.toggle_connection()
        self.destroy()

if __name__ == "__main__":
    app = PLCTester()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
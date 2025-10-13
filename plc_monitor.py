"""
PLC Monitor Module
==================
Handles PLC coil reading and GUI label updates for EOL testing.

Features:
- PLC connection management (TCP/Serial)
- Read PLC coils (M registers)
- Update GUI labels based on PLC status
- Keep-alive functionality for P0000
- Process step tracking
"""

import tkinter as tk
from pymodbus.client import ModbusSerialClient, ModbusTcpClient
import time
import os
from dotenv import load_dotenv
from datetime import datetime


class PLCMonitor:
    """Monitor PLC coils and update GUI labels"""
    
    def __init__(self, root, status_labels=None):
        """
        Initialize PLC Monitor
        
        Args:
            root: Tkinter root window
            status_labels: Dictionary of label widgets {label_name: label_widget}
        """
        self.root = root
        self.status_labels = status_labels or {}
        
        # Load environment variables
        load_dotenv()
        
        # PLC connection settings
        self.plc_client = None
        self.plc_connected = False
        self.plc_com_port = os.getenv('PLC_COM_PORT', 'COM5').strip("'")
        self.plc_baud_rate = int(os.getenv('PLC_BAUD_RATE', '38400'))
        self.plc_station_id = int(os.getenv('PLC_STATION_ID', '1'))
        self.plc_tcp_ip = os.getenv('MODBUS_TCP_IP', '').strip("'")
        self.plc_tcp_port = int(os.getenv('MODBUS_TCP_PORT', '502')) if os.getenv('MODBUS_TCP_PORT') else 502
        
        # Process addresses (M coils to monitor)
        self.process_addresses = []
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_interval = 3000  # 3 seconds default
        
        # Keep-alive for P0000
        self.p0000_keepalive_active = False
        self.p0000_last_write = 0
        
        # Step tracking
        self.visited_steps = set()
        self.step_visit_times = {}
        self.last_active_step = None
        self.required_steps = ['M0067', 'M0068', 'M0076', 'M0085', 'M0078', 'M0087', 'M0075', 'M0079']
        
        # Connection health
        self.plc_last_successful_read = time.time()
        self.plc_communication_errors = 0
        self.plc_read_lock = False
        
        # Callbacks
        self.on_status_change = None  # Callback when status changes
        self.on_step_complete = None  # Callback when a step completes
        
        print("PLC Monitor initialized")
    
    def load_process_addresses(self, file_path='txt_files/ProcessStatus.txt'):
        """Load process addresses from file"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        self.process_addresses = [addr.strip() for addr in content.split(',')]
                        print(f"Loaded {len(self.process_addresses)} process addresses: {self.process_addresses}")
                        return True
            else:
                # Default addresses
                self.process_addresses = ["M0067", "M0068", "M0076", "M0085", "M0078", "M0087", "M0075", "M0079"]
                print(f"Using default process addresses: {self.process_addresses}")
                return True
        except Exception as e:
            print(f"Error loading process addresses: {e}")
            return False
    
    def connect_to_plc(self):
        """Connect to PLC via TCP or Serial"""
        try:
            if self.plc_connected:
                print("PLC already connected")
                return True
            
            print(f"Connecting to PLC...")
            
            # Try TCP connection first if IP is configured
            if self.plc_tcp_ip:
                try:
                    self.plc_client = ModbusTcpClient(
                        host=self.plc_tcp_ip,
                        port=self.plc_tcp_port,
                        timeout=10,
                        retries=2
                    )
                    if self.plc_client.connect():
                        self.plc_connected = True
                        self.plc_communication_errors = 0
                        self.plc_last_successful_read = time.time()
                        print(f"✅ PLC connected via TCP: {self.plc_tcp_ip}:{self.plc_tcp_port}")
                        return True
                except Exception as e:
                    print(f"TCP connection failed: {e}, trying serial...")
            
            # Try serial connection
            try:
                self.plc_client = ModbusSerialClient(
                    port=self.plc_com_port,
                    baudrate=self.plc_baud_rate,
                    bytesize=8,
                    parity='N',
                    stopbits=1,
                    timeout=10,
                    retries=2
                )
                if self.plc_client.connect():
                    self.plc_connected = True
                    self.plc_communication_errors = 0
                    self.plc_last_successful_read = time.time()
                    print(f"✅ PLC connected via Serial: {self.plc_com_port}")
                    return True
                else:
                    print("❌ Serial connection failed")
                    return False
            except Exception as e:
                print(f"Serial connection error: {e}")
                return False
                
        except Exception as e:
            print(f"Error connecting to PLC: {e}")
            return False
    
    def disconnect_plc(self):
        """Disconnect from PLC"""
        try:
            if self.plc_client and self.plc_connected:
                self.monitoring_active = False
                self.p0000_keepalive_active = False
                self.plc_client.close()
                self.plc_connected = False
                print("PLC disconnected")
        except Exception as e:
            print(f"Error disconnecting PLC: {e}")
    
    def write_plc_coil(self, address, value):
        """
        Write to PLC coil
        
        Args:
            address: Coil address (e.g., "P0000", "M0067")
            value: True/False or HIGH/LOW
        
        Returns:
            bool: Success status
        """
        try:
            if not self.plc_connected or not self.plc_client:
                print(f"⚠️ PLC not connected - cannot write {address}")
                return False
            
            # Verify socket is open
            if not self.plc_client.is_socket_open():
                print(f"⚠️ PLC socket closed - attempting reconnect...")
                if not self.connect_to_plc():
                    return False
            
            # Parse address
            if address.startswith('P'):
                coil_address = int(address[1:])  # P0000 -> 0
            elif address.startswith('M'):
                coil_address = int(address[1:])  # M0067 -> 67
            else:
                coil_address = 0
            
            # Write coil
            coil_value = True if value else False
            result = self.plc_client.write_coil(
                address=coil_address,
                value=coil_value,
                device_id=self.plc_station_id
            )
            
            if not result.isError():
                print(f"✅ PLC WRITE: {address} = {'HIGH' if value else 'LOW'}")
                return True
            else:
                print(f"❌ PLC WRITE FAILED: {address} - {result}")
                return False
                
        except Exception as e:
            print(f"Error writing to PLC: {e}")
            return False
    
    def read_plc_coils(self):
        """
        Read all configured PLC coils
        
        Returns:
            dict: {address: value} mapping of coil states
        """
        try:
            # Implement read lock
            if self.plc_read_lock:
                print("⏳ PLC read in progress - skipping")
                return {}
            
            self.plc_read_lock = True
            
            try:
                if not self.plc_client or not self.plc_client.is_socket_open():
                    print("⚠️ PLC not connected")
                    return {}
                
                status_values = {}
                
                # Read each coil individually
                for address in self.process_addresses:
                    if not address.strip():
                        continue
                    
                    try:
                        addr_num = int(address[1:]) if len(address) > 1 else 0
                        
                        # Read coil or discrete input
                        if address.startswith('M'):
                            result = self.plc_client.read_coils(
                                addr_num, 
                                count=1, 
                                device_id=self.plc_station_id
                            )
                        elif address.startswith('X'):
                            result = self.plc_client.read_discrete_inputs(
                                addr_num, 
                                count=1, 
                                device_id=self.plc_station_id
                            )
                        else:
                            continue
                        
                        if not result.isError():
                            status_values[address] = result.bits[0] if result.bits else False
                            self.plc_communication_errors = 0
                            self.plc_last_successful_read = time.time()
                        else:
                            status_values[address] = False
                            print(f"⚠️ Error reading {address}: {result}")
                            self.plc_communication_errors += 1
                        
                        # Delay between reads to prevent PLC overload
                        time.sleep(0.1)
                        
                    except Exception as e:
                        print(f"Error reading {address}: {e}")
                        status_values[address] = False
                        self.plc_communication_errors += 1
                
                return status_values
                
            finally:
                self.plc_read_lock = False
                
        except Exception as e:
            print(f"Error in read_plc_coils: {e}")
            self.plc_read_lock = False
            return {}
    
    def update_labels(self, status_values):
        """
        Update GUI labels based on PLC status
        
        Args:
            status_values: dict of {address: True/False}
        """
        try:
            if not self.status_labels:
                return
            
            # Label mapping
            label_mapping = {
                0: "auto",    # AUTO - M0067
                1: "home",    # HOME - M0068
                2: "1st",     # 1st PULL - M0076
                3: "2nd",     # 2nd PULL - M0085
                4: "test"     # TEST RESULT - M0078
            }
            
            # Track currently active step
            currently_active_address = None
            
            for i, address in enumerate(self.process_addresses):
                if not address.strip() or i not in label_mapping:
                    continue
                
                label_key = label_mapping[i]
                is_active = status_values.get(address, False)
                
                # Track step visits
                if is_active:
                    currently_active_address = address
                    
                    if address not in self.visited_steps:
                        self.visited_steps.add(address)
                        self.step_visit_times[address] = time.time()
                        print(f"🎯 NEW STEP: {address} ({label_key}) - Step {i+1}/8")
                        
                        # Trigger callback
                        if self.on_step_complete:
                            self.on_step_complete(address, label_key, i+1)
                
                # Update label color
                if label_key in self.status_labels:
                    label = self.status_labels[label_key]
                    
                    if is_active:
                        # Active - set to green
                        current_bg = label.cget("bg")
                        if current_bg != "green":
                            label.config(bg="green", fg="white")
                            print(f"✅ {label_key} → GREEN (active)")
                    else:
                        # Not active - keep green if visited, blue otherwise
                        if address in self.visited_steps:
                            label.config(bg="green", fg="white")
                        else:
                            label.config(bg="#00BFFF", fg="black")
            
            # Track step transitions
            if currently_active_address and currently_active_address != self.last_active_step:
                if self.last_active_step:
                    print(f"📍 Step transition: {self.last_active_step} → {currently_active_address}")
                self.last_active_step = currently_active_address
                
                # Trigger callback
                if self.on_status_change:
                    self.on_status_change(status_values, currently_active_address)
                    
        except Exception as e:
            print(f"Error updating labels: {e}")
            import traceback
            traceback.print_exc()
    
    def start_monitoring(self):
        """Start PLC monitoring loop"""
        try:
            if not self.plc_connected:
                print("Cannot start monitoring - PLC not connected")
                return False
            
            self.monitoring_active = True
            print("✅ PLC monitoring started")
            
            # Start monitoring loop
            self.monitor_loop()
            return True
            
        except Exception as e:
            print(f"Error starting monitoring: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop PLC monitoring loop"""
        self.monitoring_active = False
        print("PLC monitoring stopped")
    
    def monitor_loop(self):
        """Main monitoring loop"""
        try:
            if not self.monitoring_active:
                return
            
            # Check connection health
            if hasattr(self, 'plc_client') and self.plc_client:
                try:
                    is_open = self.plc_client.is_socket_open()
                    if not is_open:
                        print("⚠️ PLC connection lost - attempting reconnect...")
                        if self.connect_to_plc():
                            print("✅ PLC reconnected")
                except Exception as e:
                    print(f"⚠️ Connection check error: {e}")
            
            # Read PLC coils
            status_values = self.read_plc_coils()
            
            # Update labels
            if status_values:
                self.update_labels(status_values)
            
            # Schedule next monitoring cycle
            if self.monitoring_active:
                self.root.after(self.monitoring_interval, self.monitor_loop)
                
        except Exception as e:
            print(f"Error in monitor loop: {e}")
            # Continue monitoring despite errors
            if self.monitoring_active:
                self.root.after(self.monitoring_interval, self.monitor_loop)
    
    def start_p0000_keepalive(self):
        """Start P0000 keep-alive to maintain HIGH signal"""
        try:
            self.p0000_keepalive_active = True
            self.p0000_last_write = time.time()
            print("✅ P0000 keep-alive started")
            
            # Initial write
            self.write_plc_coil("P0000", True)
            
            # Start keep-alive loop
            self.root.after(2000, self.p0000_keepalive_loop)
            
        except Exception as e:
            print(f"Error starting keep-alive: {e}")
    
    def stop_p0000_keepalive(self):
        """Stop P0000 keep-alive"""
        self.p0000_keepalive_active = False
        print("P0000 keep-alive stopped")
    
    def p0000_keepalive_loop(self):
        """Maintain P0000 HIGH during testing"""
        try:
            if not self.p0000_keepalive_active:
                return
            
            current_time = time.time()
            
            # Re-write P0000 every 5 seconds
            if current_time - self.p0000_last_write >= 5:
                if self.plc_client and self.plc_client.is_socket_open():
                    result = self.plc_client.write_coil(0, True, device_id=self.plc_station_id)
                    
                    if not result.isError():
                        print("🔄 Keep-alive: P0000 refreshed HIGH")
                        self.p0000_last_write = current_time
                    else:
                        print(f"⚠️ Keep-alive write failed: {result}")
            
            # Schedule next keep-alive check
            if self.p0000_keepalive_active:
                self.root.after(2000, self.p0000_keepalive_loop)
                
        except Exception as e:
            print(f"Error in keep-alive loop: {e}")
            # Continue keep-alive despite errors
            if self.p0000_keepalive_active:
                self.root.after(2000, self.p0000_keepalive_loop)
    
    def reset_step_tracking(self):
        """Reset step tracking for new test cycle"""
        self.visited_steps = set()
        self.step_visit_times = {}
        self.last_active_step = None
        print("🔄 Step tracking reset")
    
    def get_progress(self):
        """
        Get current test progress
        
        Returns:
            dict: Progress information
        """
        total_steps = len(self.required_steps)
        visited_count = len(self.visited_steps)
        
        return {
            'total_steps': total_steps,
            'visited_steps': visited_count,
            'progress_percent': (visited_count / total_steps * 100) if total_steps > 0 else 0,
            'visited_addresses': sorted(list(self.visited_steps)),
            'remaining_steps': sorted(list(set(self.required_steps) - self.visited_steps))
        }


# Example usage
if __name__ == "__main__":
    # Create test window
    root = tk.Tk()
    root.title("PLC Monitor Test")
    root.geometry("600x400")
    
    # Create test labels
    label_frame = tk.Frame(root)
    label_frame.pack(pady=20)
    
    status_labels = {}
    label_names = ["auto", "home", "1st", "2nd", "test"]
    
    for name in label_names:
        label = tk.Label(
            label_frame,
            text=name.upper(),
            bg="#00BFFF",
            fg="black",
            font=("Arial", 12, "bold"),
            width=15,
            height=2
        )
        label.pack(side="left", padx=5)
        status_labels[name] = label
    
    # Status display
    status_text = tk.Text(root, height=10, width=70)
    status_text.pack(pady=10)
    
    # Create PLC monitor
    monitor = PLCMonitor(root, status_labels)
    
    # Load process addresses
    monitor.load_process_addresses()
    
    # Callbacks
    def on_status_change(status_values, active_step):
        status_text.insert("end", f"Status changed: {active_step} active\n")
        status_text.see("end")
    
    def on_step_complete(address, label_key, step_num):
        status_text.insert("end", f"✅ Step {step_num} complete: {address} ({label_key})\n")
        status_text.see("end")
    
    monitor.on_status_change = on_status_change
    monitor.on_step_complete = on_step_complete
    
    # Control buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    
    def connect_plc():
        if monitor.connect_to_plc():
            status_text.insert("end", "✅ PLC Connected\n")
            connect_btn.config(state='disabled')
            start_btn.config(state='normal')
        else:
            status_text.insert("end", "❌ PLC Connection Failed\n")
        status_text.see("end")
    
    def start_monitoring():
        if monitor.start_monitoring():
            status_text.insert("end", "✅ Monitoring Started\n")
            start_btn.config(state='disabled')
            stop_btn.config(state='normal')
            keepalive_btn.config(state='normal')
        status_text.see("end")
    
    def stop_monitoring():
        monitor.stop_monitoring()
        status_text.insert("end", "⏸️ Monitoring Stopped\n")
        stop_btn.config(state='disabled')
        start_btn.config(state='normal')
        status_text.see("end")
    
    def toggle_keepalive():
        if monitor.p0000_keepalive_active:
            monitor.stop_p0000_keepalive()
            keepalive_btn.config(text="Start Keep-Alive", bg="#4CAF50")
            status_text.insert("end", "🛑 Keep-alive stopped\n")
        else:
            monitor.start_p0000_keepalive()
            keepalive_btn.config(text="Stop Keep-Alive", bg="#f44336")
            status_text.insert("end", "🔄 Keep-alive started\n")
        status_text.see("end")
    
    def show_progress():
        progress = monitor.get_progress()
        status_text.insert("end", f"\n📊 Progress: {progress['visited_steps']}/{progress['total_steps']} ({progress['progress_percent']:.1f}%)\n")
        status_text.insert("end", f"Visited: {progress['visited_addresses']}\n")
        if progress['remaining_steps']:
            status_text.insert("end", f"Remaining: {progress['remaining_steps']}\n")
        status_text.see("end")
    
    connect_btn = tk.Button(button_frame, text="Connect PLC", command=connect_plc, 
                           bg="#4CAF50", fg="white", width=15)
    connect_btn.pack(side="left", padx=5)
    
    start_btn = tk.Button(button_frame, text="Start Monitoring", command=start_monitoring,
                         bg="#2196F3", fg="white", width=15, state='disabled')
    start_btn.pack(side="left", padx=5)
    
    stop_btn = tk.Button(button_frame, text="Stop Monitoring", command=stop_monitoring,
                        bg="#f44336", fg="white", width=15, state='disabled')
    stop_btn.pack(side="left", padx=5)
    
    keepalive_btn = tk.Button(button_frame, text="Start Keep-Alive", command=toggle_keepalive,
                             bg="#4CAF50", fg="white", width=15, state='disabled')
    keepalive_btn.pack(side="left", padx=5)
    
    progress_btn = tk.Button(button_frame, text="Show Progress", command=show_progress,
                            bg="#FF9800", fg="white", width=15)
    progress_btn.pack(side="left", padx=5)
    
    # Initial message
    status_text.insert("end", "PLC Monitor Ready\n")
    status_text.insert("end", "Click 'Connect PLC' to begin\n")
    
    root.mainloop()



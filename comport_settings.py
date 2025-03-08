import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error
from pymodbus.client import ModbusSerialClient
from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
import serial.tools.list_ports
import os
import time
from dotenv import load_dotenv, set_key, find_dotenv

class ComPortSettings:
    def __init__(self, root):
        self.root = root
        self.root.title("COM Port Settings")
        
        # Initialize all_comboboxes list
        self.all_comboboxes = []  # Add this line at the start
        
        # Make it full screen
        self.root.state('zoomed')
        
        # Configure the main background color
        self.root.configure(bg='#f0f0f0')  # Light gray background
        
        # Header with border lines
        header_frame = tk.Frame(self.root, bg='#f0f0f0')
        header_frame.pack(fill=tk.X, padx=5)
        
        # Top border line
        tk.Canvas(header_frame, height=2, bg='#2c3e50').pack(fill=tk.X)
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="COM PORT SETTINGS",
            bg='#f0f0f0',
            fg='#2c3e50',
            font=('Arial', 28, 'bold')
        )
        title_label.pack(pady=10)
        
        # Bottom border line
        tk.Canvas(header_frame, height=2, bg='#2c3e50').pack(fill=tk.X)

        # Main content frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Control buttons frame
        control_frame = tk.Frame(main_frame, bg='#f0f0f0')
        control_frame.pack(side=tk.RIGHT, padx=20)
        
        # Control buttons with commands
        self.buttons = {
            "EDIT": {'bg': '#3498db', 'fg': 'white', 'command': self.enable_editing},
            "SAVE": {'bg': '#2ecc71', 'fg': 'white', 'command': self.save_settings},
            "RESET": {'bg': '#e74c3c', 'fg': 'white', 'command': self.reset_settings}
        }
        
        # Create buttons
        self.control_buttons = {}
        for text, props in self.buttons.items():
            btn = tk.Button(
                control_frame, 
                text=text, 
                bg=props['bg'], 
                fg=props['fg'],
                width=15, 
                font=('Arial', 12, 'bold'),
                command=props['command']
            )
            btn.pack(pady=5)
            self.control_buttons[text] = btn

        # Initially disable Save button
        self.control_buttons["SAVE"].config(state="disabled")

        # Panels frame using grid
        panels_frame = tk.Frame(main_frame, bg='#f0f0f0')
        panels_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid columns to have equal width
        panels_frame.grid_columnconfigure(0, weight=1)
        panels_frame.grid_columnconfigure(1, weight=1)
        panels_frame.grid_columnconfigure(2, weight=1)

        # PLC Section
        plc_frame = self.create_section(
            panels_frame, "PLC", '#e8f6e9',
            width=400, height=400
        )
        plc_frame.grid(row=0, column=0, padx=10, sticky='nsew')
        self.add_plc_content(plc_frame)

        # Loadcell Sections
        for i in range(1, 3):  # Creating 2 loadcells
            loadcell_frame = self.create_section(
                panels_frame, f"LOADCELL - {i:02d} (L{i})", '#f5e6e8',
                width=400, height=400
            )
            loadcell_frame.grid(row=0, column=i, padx=10, sticky='nsew')
            self.add_loadcell_content(loadcell_frame)

        # Modbus TCP Section
        modbus_tcp_frame = self.create_section(
            panels_frame, "MODBUS TCP", '#e8f6e9',
            width=400, height=400
        )
        modbus_tcp_frame.grid(row=1, column=0, padx=10, sticky='nsew')
        self.add_modbus_tcp_content(modbus_tcp_frame)

        # Load environment variables
        self.env_file = '.env'
        load_dotenv(self.env_file)
        
        # Create .env file if it doesn't exist
        if not os.path.exists(self.env_file):
            with open(self.env_file, 'w') as f:
                f.write('# COM Port Settings\n')

        # Add Modbus client attribute
        self.modbus_client = None

        # Initialize loadcell serial ports dictionary
        self.loadcell_ports = {}

    def create_section(self, parent, title, bg_color, width, height):
        frame = tk.Frame(parent, bg=bg_color, width=width, height=height, relief='solid', borderwidth=1)
        frame.pack_propagate(False)
        
        # Add title with background color
        tk.Label(frame, text=title, bg=bg_color, fg='black',
                font=('Arial', 10, 'bold')).pack(anchor='w', padx=5, pady=2)
        
        return frame

    def add_plc_content(self, frame):
        # Test button and Station ID
        top_frame = tk.Frame(frame, bg=frame['bg'])
        top_frame.pack(fill='x', padx=5, pady=5)
        
        # Test Button
        self.test_button = tk.Button(top_frame, text="TEST", bg='darkred', fg='white', 
                              width=8, font=('Arial', 9, 'bold'),
                                    command=self.read_plc_data)
        self.test_button.pack(side='left', padx=5)
        
        # Station ID
        station_frame = tk.Frame(top_frame, bg=frame['bg'])
        station_frame.pack(side='left', padx=5)
        self.station_id_entry = tk.Entry(station_frame, width=10)
        self.station_id_entry.pack(side='left', padx=2)
        tk.Label(station_frame, text="Station ID", bg=frame['bg']).pack(side='left')
        
        # Style the labels and comboboxes
        label_style = {'bg': frame['bg'], 'fg': 'black', 'font': ('Arial', 10)}
        
        # COM Port
        tk.Label(frame, text="COM Port", **label_style).pack(anchor='w', padx=5, pady=2)
        self.plc_com_combo = ttk.Combobox(frame, width=25, state="readonly")
        self.plc_com_combo.pack(anchor='w', padx=5)
        
        # BAUD Rate
        tk.Label(frame, text="BAUD Rate", **label_style).pack(anchor='w', padx=5, pady=2)
        self.plc_baud_combo = ttk.Combobox(frame, width=25, state="readonly")
        self.plc_baud_combo.pack(anchor='w', padx=5)
        
        # Get available COM ports
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
        
        # Update combobox values
        self.plc_com_combo['values'] = available_ports if available_ports else ["No Ports"]
        self.plc_com_combo.set(available_ports[0] if available_ports else "No Ports")
        self.plc_baud_combo['values'] = [9600, 19200, 38400, 57600, 115200]
        self.plc_baud_combo.set(9600)
        
        # Connect Button
        self.connect_button = tk.Button(frame, text="Connect", bg='green', fg='white',
                                      font=('Arial', 9, 'bold'), command=self.connect_to_plc)
        self.connect_button.pack(anchor='w', padx=5, pady=5)
        
        # Rx String
        tk.Label(frame, text="Rx String", **label_style).pack(anchor='w', padx=5, pady=2)
        self.rx_text = tk.Text(frame, height=10, width=30, font=('Consolas', 10))
        self.rx_text.pack(padx=5, pady=5)
        
        # Initially disable test button
        self.test_button.config(state="disabled")

    def connect_to_plc(self):
        """Connect to PLC using Modbus RTU"""
        port = self.plc_com_combo.get()
        baudrate = int(self.plc_baud_combo.get())
        slave_id = self.station_id_entry.get().strip()

        try:
            if port == "No Ports":
                raise ValueError("No COM ports available.")
            if not slave_id.isdigit():
                raise ValueError("Station ID must be a valid number.")

            slave_id = int(slave_id)

            # Close existing connection if any
            if self.modbus_client and self.modbus_client.is_socket_open():
                self.modbus_client.close()

            # Initialize Modbus client with RTU settings
            self.modbus_client = ModbusSerialClient(
                port=port,
                baudrate=baudrate,
                timeout=1,
                stopbits=1,
                bytesize=8,
                parity='N'
            )

            if self.modbus_client.connect():
                messagebox.showinfo("Connection Status", "Connected to PLC!")
                self.test_button.config(state="normal")
            else:
                self.modbus_client.close()
                messagebox.showerror("Connection Status", "Failed to connect to PLC.")
        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"Connection Error: {str(e)}")

    def read_plc_data(self):
        """Read data from PLC registers and coils"""
        if self.modbus_client is None or not self.modbus_client.is_socket_open():
            messagebox.showerror("Error", "Not connected to PLC.")
            return

        try:
            slave_id = self.station_id_entry.get().strip()
            
            # Validate inputs
            if not slave_id:
                messagebox.showerror("Error", "Station ID is mandatory!")
                return

            slave_id = int(slave_id)
            
            # Clear the text box
            self.rx_text.delete("1.0", tk.END)
            
            # Define file paths relative to the script location
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            process_status_file = os.path.join(current_dir, "ProcessStatus.txt")
            input_sensors_file = os.path.join(current_dir, "InputSensors.txt")
            program_selection_file = os.path.join(current_dir, "ProgramSelectionInPLC.txt")
            
            # Initialize arrays
            process_status_array = []
            input_sensors_array = []
            program_selection_array = []
            
            # Read and process each file
            for file_path, array_name in [
                (process_status_file, "Process Status"),
                (input_sensors_file, "Input Sensors"),
                (program_selection_file, "Program Selection")
            ]:
                try:
                    if not os.path.exists(file_path):
                        self.rx_text.insert(tk.END, f"Warning: {os.path.basename(file_path)} not found\n")
                        continue
                        
                    with open(file_path, 'r') as f:
                        content = f.read().strip()
                        if not content:
                            self.rx_text.insert(tk.END, f"Warning: {os.path.basename(file_path)} is empty\n")
                            continue
                            
                        # Split by comma and clean the addresses
                        addresses = [addr.strip() for addr in content.split(',') if addr.strip()]
                        
                        if not addresses:
                            self.rx_text.insert(tk.END, f"Warning: No valid addresses found in {os.path.basename(file_path)}\n")
                            continue
                            
                        # Store addresses in appropriate array
                        if "ProcessStatus" in file_path:
                            process_status_array = addresses
                        elif "InputSensors" in file_path:
                            input_sensors_array = addresses
                        else:
                            program_selection_array = addresses
                            
#self.rx_text.insert(tk.END, f"Loaded {len(addresses)} {array_name} addresses\n")
                        
                except Exception as e:
                    self.rx_text.insert(tk.END, f"Error reading {os.path.basename(file_path)}: {str(e)}\n")
            
          #  self.rx_text.insert(tk.END, "\n--- Reading PLC Data ---\n")
            
            # Read coils for each address array
         #   if input_sensors_array:
          #      self._read_coils(input_sensors_array, "Input Sensors", slave_id)
            if process_status_array:
                self._read_coils(process_status_array, "Process Status", slave_id)
           # if program_selection_array:
            #    self._read_coils(program_selection_array, "Program Selection", slave_id)

            if not any([input_sensors_array, process_status_array, program_selection_array]):
                self.rx_text.insert(tk.END, "\nNo valid addresses found in any configuration file.")

        except ValueError as ve:
            messagebox.showerror("Error", "Invalid Station ID")
        except Exception as e:
            messagebox.showerror("Read Error", str(e))

    def _read_coils(self, addresses, section_name, slave_id):
        """Helper method to read coils and display results"""
        if not addresses:
            return
        
        # Add section header
        self.rx_text.insert(tk.END, f"\n{section_name}:\n")
        
        for address in addresses:
            try:
                # Convert hex address (ignoring first character)
                coil_address = int(address[1:], 16)

                # Read 1 coil from the PLC
                response = self.modbus_client.read_coils(
                    address=coil_address,
                    count=1,
                    slave=slave_id
                )

                if getattr(response, 'isError', lambda: True)():
                    self.rx_text.insert(tk.END, f"{address} --> Error reading coil\n")
                    continue

                # Display result
                status = "ON" if response.bits[0] else "OFF"
                self.rx_text.insert(tk.END, f"{address} --> {status}\n")

            except Exception as e:
                self.rx_text.insert(tk.END, f"{address} --> Error: {str(e)}\n")

    def add_loadcell_content(self, frame):
        # Add serial port attribute for each loadcell
        self.loadcell_ports = {}  # Store serial connections for each loadcell
        
        # Get loadcell number from frame title
        loadcell_num = frame.winfo_children()[0]['text'].split('-')[1].strip()[:2]
        frame.loadcell_num = loadcell_num  # Store loadcell number in frame
        
        # Test button with consistent styling
        test_button = tk.Button(
            frame, 
            text="TEST", 
            bg='darkred', 
            fg='white', 
            width=8, 
            font=('Arial', 9, 'bold'),
            command=lambda f=frame: self.test_loadcell(f)
        )
        test_button.pack(anchor='w', padx=5, pady=5)
        
        # Style settings
        label_style = {'bg': frame['bg'], 'fg': 'black', 'font': ('Arial', 10)}
        
        # COM Port
        tk.Label(frame, text="COM Port", **label_style).pack(anchor='w', padx=5, pady=2)
        com_combo = ttk.Combobox(frame, width=25, state="readonly")
        com_combo.pack(anchor='w', padx=5)
        
        # BAUD Rate
        tk.Label(frame, text="BAUD Rate", **label_style).pack(anchor='w', padx=5, pady=2)
        baud_combo = ttk.Combobox(frame, width=25, state="readonly")
        baud_combo.pack(anchor='w', padx=5)
        
        # Add comboboxes to the list
        self.all_comboboxes.extend([com_combo, baud_combo])
        
        # Get available COM ports
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
        
        # Update combobox values with detected ports
        if available_ports:
            com_combo['values'] = available_ports
            com_combo.set(available_ports[0])
        else:
            com_combo['values'] = ["No Ports Available"]
            com_combo.set("No Ports Available")
            messagebox.showwarning("Port Warning", "No COM ports are currently available!")
        
        # BAUD Rate
        tk.Label(frame, text="BAUD Rate", **label_style).pack(anchor='w', padx=5, pady=2)
        baud_combo = ttk.Combobox(frame, width=25, state="readonly")
        baud_combo['values'] = [9600, 19200, 38400, 57600, 115200]
        baud_combo.set(9600)
        baud_combo.pack(anchor='w', padx=5)
        
        # Connect Button
        connect_button = tk.Button(
            frame, 
            text="Connect", 
            bg='green', 
            fg='white',
            font=('Arial', 9, 'bold'),
            command=lambda: self.connect_loadcell(frame, com_combo, baud_combo, test_button)
        )
        connect_button.pack(anchor='w', padx=5, pady=5)
        
        # Rx String
        tk.Label(frame, text="Rx String", **label_style).pack(anchor='w', padx=5, pady=2)
        rx_text = tk.Text(frame, height=8, width=25, font=('Consolas', 10))
        rx_text.pack(padx=5, pady=5)
        
        # Store the rx_text widget reference
        frame.rx_text = rx_text
        
        # Initially disable test button
        test_button.config(state="disabled")
        
        # Store the test button reference
        frame.test_button = test_button

    def connect_loadcell(self, frame, com_combo, baud_combo, test_button):
        """Connect to loadcell using serial communication"""
        port = com_combo.get()
        baudrate = int(baud_combo.get())
        loadcell_num = frame.loadcell_num
        
        try:
            # Check if port is "No Ports Available"
            if port == "No Ports Available":
                messagebox.showerror("Connection Error", 
                                   f"No COM ports available for Loadcell {loadcell_num}!\n"
                                   "Please check your device connection and try again.")
                return
            
            # Check if port still exists
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            if port not in available_ports:
                messagebox.showerror("Connection Error", 
                                   f"COM Port {port} is no longer available!\n"
                                   "The device may have been disconnected.")
                
                # Update the combobox with current available ports
                if available_ports:
                    com_combo['values'] = available_ports
                    com_combo.set(available_ports[0])
                else:
                    com_combo['values'] = ["No Ports Available"]
                    com_combo.set("No Ports Available")
                return
            
            # Close existing connection if any
            if frame in self.loadcell_ports and self.loadcell_ports[frame].is_open:
                self.loadcell_ports[frame].close()
            
            # Try to open the serial port
            try:
                ser = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    bytesize=8,
                    parity='N',
                    stopbits=1,
                    timeout=1
                )
                
                if ser.is_open:
                    self.loadcell_ports[frame] = ser
                    messagebox.showinfo("Connection Status", 
                                      f"Successfully connected to Loadcell {loadcell_num} on {port}!")
                    test_button.config(state="normal")
                else:
                    raise serial.SerialException("Failed to open port")
                    
            except serial.SerialException as se:
                messagebox.showerror("Connection Error", 
                                   f"Could not open {port} for Loadcell {loadcell_num}!\n"
                                   f"Error: {str(se)}\n"
                                   "The port might be in use by another application.")
                
        except Exception as e:
            messagebox.showerror("Error", 
                               f"Unexpected error while connecting to Loadcell {loadcell_num}!\n"
                               f"Error: {str(e)}")

    def test_loadcell(self, frame):
        """Test loadcell communication"""
        try:
            # Check if port is still available
            if frame not in self.loadcell_ports or not self.loadcell_ports[frame].is_open:
                loadcell_num = frame.loadcell_num
                messagebox.showerror("Connection Error", 
                                   f"Loadcell {loadcell_num} is not connected!\n"
                                   "Please connect the device first.")
                return
            
            # Clear the rx text
            frame.rx_text.delete("1.0", tk.END)
            
            # Get loadcell number
            loadcell_num = frame.loadcell_num
            
            # Command structure for different loadcells
            commands = {
                "01": b"ID01P",  # Command for Loadcell 1
                "02": b"ID02P"   # Command for Loadcell 2
            }
            
            # Send the appropriate command based on loadcell number
            command = commands.get(loadcell_num)
            if not command:
                raise ValueError(f"Invalid loadcell number: {loadcell_num}")
            
            # Clear any existing data in the buffer
            self.loadcell_ports[frame].reset_input_buffer()
            
            # Send command
            self.loadcell_ports[frame].write(command)
            frame.rx_text.insert(tk.END, f"Sent command: {command.decode()}\n")
            
            # Wait for response (with timeout)
            time.sleep(0.1)  # Give device time to respond
            
            # Read response
            if self.loadcell_ports[frame].in_waiting:
                try:
                    response = self.loadcell_ports[frame].readline()
                    if response:
                        decoded_response = response.decode('utf-8', errors='replace').strip()
                        frame.rx_text.insert(tk.END, f"Response: {decoded_response}\n")
                        
                        # Parse the response if needed
                        # Example: If response format is "ID01,VALUE"
                        try:
                            parts = decoded_response.split(',')
                            if len(parts) > 1:
                                value = parts[1]
                                frame.rx_text.insert(tk.END, f"Parsed value: {value}\n")
                        except IndexError:
                            frame.rx_text.insert(tk.END, "Could not parse value from response\n")
                    else:
                        frame.rx_text.insert(tk.END, "No response data received\n")
                except UnicodeDecodeError:
                    frame.rx_text.insert(tk.END, "Error: Received invalid data\n")
            else:
                frame.rx_text.insert(tk.END, "No response from device\n")
            
        except ValueError as ve:
            frame.rx_text.insert(tk.END, f"Error: {str(ve)}\n")
        except Exception as e:
            frame.rx_text.insert(tk.END, f"Error: {str(e)}\n")

    def add_modbus_tcp_content(self, frame):
        # Test button and IP Address
        top_frame = tk.Frame(frame, bg=frame['bg'])
        top_frame.pack(fill='x', padx=5, pady=5)
        
        # Test Button
        self.test_tcp_button = tk.Button(top_frame, text="TEST", bg='darkred', fg='white', 
                              width=8, font=('Arial', 9, 'bold'),
                                    command=self.read_modbus_tcp_data)
        self.test_tcp_button.pack(side='left', padx=5)
        
        # IP Address
        ip_frame = tk.Frame(top_frame, bg=frame['bg'])
        ip_frame.pack(side='left', padx=5)
        self.ip_entry = tk.Entry(ip_frame, width=15)
        self.ip_entry.pack(side='left', padx=2)
        tk.Label(ip_frame, text="IP Address", bg=frame['bg']).pack(side='left')
        
        # Port
        port_frame = tk.Frame(top_frame, bg=frame['bg'])
        port_frame.pack(side='left', padx=5)
        self.port_entry = tk.Entry(port_frame, width=5)
        self.port_entry.pack(side='left', padx=2)
        tk.Label(port_frame, text="Port", bg=frame['bg']).pack(side='left')
        
        # Style the labels and comboboxes
        label_style = {'bg': frame['bg'], 'fg': 'black', 'font': ('Arial', 10)}
        
        # Connect Button
        self.connect_tcp_button = tk.Button(frame, text="Connect", bg='green', fg='white',
                                      font=('Arial', 9, 'bold'), command=self.connect_to_modbus_tcp)
        self.connect_tcp_button.pack(anchor='w', padx=5, pady=5)
        
        # Rx String
        tk.Label(frame, text="Rx String", **label_style).pack(anchor='w', padx=5, pady=2)
        self.rx_tcp_text = tk.Text(frame, height=10, width=30, font=('Consolas', 10))
        self.rx_tcp_text.pack(padx=5, pady=5)
        
        # Initially disable test button
        self.test_tcp_button.config(state="disabled")

    def connect_to_modbus_tcp(self):
        """Connect to PLC using Modbus TCP"""
        ip_address = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()

        try:
            if not ip_address:
                raise ValueError("IP Address is required.")
            if not port.isdigit():
                raise ValueError("Port must be a valid number.")

            port = int(port)

            # Create a Modbus TCP client
            self.modbus_tcp_client = ModbusTcpClient(ip_address, port=port)

            if self.modbus_tcp_client.connect():
                messagebox.showinfo("Connection Status", "Connected to PLC via Modbus TCP!")
                self.test_tcp_button.config(state="normal")
            else:
                self.modbus_tcp_client.close()
                messagebox.showerror("Connection Status", "Failed to connect to PLC via Modbus TCP.")
        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"Connection Error: {str(e)}")

    def read_modbus_tcp_data(self):
        """Read data from PLC using Modbus TCP"""
        if self.modbus_tcp_client is None or not self.modbus_tcp_client.is_socket_open():
            messagebox.showerror("Error", "Not connected to PLC via Modbus TCP.")
            return

        try:
            # Clear the text box
            self.rx_tcp_text.delete("1.0", tk.END)
            
            # Read holding register (D register) at address 0 (D0000)
            response = self.modbus_tcp_client.read_holding_registers(0, 1, unit=1)  # Adjust unit ID if needed

            if not response.isError():
                value = response.registers[0]  # Read the integer value
                self.rx_tcp_text.insert(tk.END, f"Value in D0000: {value}\n")
            else:
                self.rx_tcp_text.insert(tk.END, f"Error reading from PLC: {response}\n")

        except Exception as e:
            self.rx_tcp_text.insert(tk.END, f"Error: {str(e)}\n")

    def save_settings(self):
        """Save settings to environment variables and disable editing"""
        try:
            # Get the .env file path
            env_path = find_dotenv()
            if not env_path:
                env_path = self.env_file

            # Save PLC settings
            set_key(env_path, 'PLC_COM_PORT', self.plc_com_combo.get())
            set_key(env_path, 'PLC_BAUD_RATE', self.plc_baud_combo.get())
            
            # Save Loadcell settings
            for frame, port in self.loadcell_ports.items():
                loadcell_num = frame.loadcell_num
                com_port = frame.winfo_children()[2].get()  # Get COM port value
                baud_rate = frame.winfo_children()[4].get()  # Get BAUD rate value
                
                set_key(env_path, f'LOADCELL_{loadcell_num}_COM_PORT', com_port)
                set_key(env_path, f'LOADCELL_{loadcell_num}_BAUD_RATE', baud_rate)
            
            # Save Modbus TCP settings
            set_key(env_path, 'MODBUS_TCP_IP', self.ip_entry.get())
            set_key(env_path, 'MODBUS_TCP_PORT', self.port_entry.get())
            
            # Disable all comboboxes
            for combo in self.all_comboboxes:
                combo.config(state="disabled")
            
            # Update button states
            self.control_buttons["SAVE"].config(state="disabled")
            self.control_buttons["EDIT"].config(state="normal")
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings!\nError: {str(e)}")

    def load_saved_settings(self):
        """Load settings from environment variables"""
        try:
            # Load PLC settings
            plc_port = os.getenv('PLC_COM_PORT')
            plc_baud = os.getenv('PLC_BAUD_RATE')
            if plc_port:
                self.plc_com_combo.set(plc_port)
            if plc_baud:
                self.plc_baud_combo.set(plc_baud)
            
            # Load Loadcell settings
            for frame in self.loadcell_ports.keys():
                loadcell_num = frame.loadcell_num
                com_port = os.getenv(f'LOADCELL_{loadcell_num}_COM_PORT')
                baud_rate = os.getenv(f'LOADCELL_{loadcell_num}_BAUD_RATE')
                
                if com_port:
                    frame.winfo_children()[2].set(com_port)
                if baud_rate:
                    frame.winfo_children()[4].set(baud_rate)
            
            # Load Modbus TCP settings
            modbus_ip = os.getenv('MODBUS_TCP_IP')
            modbus_port = os.getenv('MODBUS_TCP_PORT')
            if modbus_ip:
                self.ip_entry.delete(0, tk.END)
                self.ip_entry.insert(0, modbus_ip)
            if modbus_port:
                self.port_entry.delete(0, tk.END)
                self.port_entry.insert(0, modbus_port)
                
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load settings!\nError: {str(e)}")

    def reset_settings(self):
        """Reset all settings and clear environment variables"""
        try:
            # Ask for confirmation
            if not messagebox.askyesno("Confirm Reset", 
                                     "Are you sure you want to reset all settings?"):
                return
            
            # Get the .env file path
            env_path = find_dotenv()
            if not env_path:
                env_path = self.env_file
            
            # Clear environment variables
            env_vars = [
                'PLC_COM_PORT', 'PLC_BAUD_RATE',
                'MODBUS_TCP_IP', 'MODBUS_TCP_PORT'
            ]
            
            # Add loadcell environment variables
            for frame in self.loadcell_ports.keys():
                loadcell_num = frame.loadcell_num
                env_vars.extend([
                    f'LOADCELL_{loadcell_num}_COM_PORT',
                    f'LOADCELL_{loadcell_num}_BAUD_RATE'
                ])
            
            # Clear each environment variable
            for var in env_vars:
                set_key(env_path, var, '')
            
            # Reset PLC settings
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            
            # Reset COM port combos
            for combo in self.all_comboboxes:
                if 'values' in combo.configure():  # Check if it's a COM port combo
                    if available_ports:
                        combo['values'] = available_ports
                        combo.set(available_ports[0])
                    else:
                        combo['values'] = ["No Ports Available"]
                        combo.set("No Ports Available")
            
            # Reset BAUD rate combos
            for combo in self.all_comboboxes:
                if 'values' in combo.configure():  # Check if it's a BAUD rate combo
                    if '9600' in combo['values']:
                        combo.set('9600')
            
            # Reset Modbus TCP settings
            self.ip_entry.delete(0, tk.END)
            self.port_entry.delete(0, tk.END)
            
            # Enable editing
            self.enable_editing()
            
            # Close any existing connections
            self.cleanup()
            
            messagebox.showinfo("Reset Complete", "All settings have been reset to default values")
            
        except Exception as e:
            messagebox.showerror("Reset Error", f"Error during reset: {str(e)}")

    def enable_editing(self):
        """Enable editing of comboboxes"""
        # Enable all comboboxes
        for combo in self.all_comboboxes:
            combo.config(state="readonly")
        
        # Update button states
        self.control_buttons["SAVE"].config(state="normal")
        self.control_buttons["EDIT"].config(state="disabled")
        
        messagebox.showinfo("Edit Mode", "Settings are now editable")

    def cleanup(self):
        """Close all connections"""
        try:
            # Close loadcell connections
            for ser in self.loadcell_ports.values():
                if ser.is_open:
                    ser.close()
            
            # Close PLC connection if exists
            if hasattr(self, 'modbus_client') and self.modbus_client:
                self.modbus_client.close()
            
            # Close Modbus TCP connection if exists
            if hasattr(self, 'modbus_tcp_client') and self.modbus_tcp_client:
                self.modbus_tcp_client.close()
                
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

def main():
    root = tk.Tk()
    app = ComPortSettings(root)
    app.load_saved_settings()  # Load saved settings on startup
    root.protocol("WM_DELETE_WINDOW", lambda: [app.cleanup(), root.destroy()])
    root.mainloop()

if __name__ == "__main__":
    main()
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
import json
from datetime import datetime

class ComPortSettings:
    def __init__(self, root):
        self.root = root
        self.root.title("COM Port Settings")
        
        # Initialize lists and dictionaries at the start
        self.all_comboboxes = []  # Move this to the top
        self.loadcell_ports = {}  # Move this here too
        self.modbus_client = None
        
        # Make it full screen
        self.root.state('zoomed')
        
        # Configure the main background color
        self.root.configure(bg='#f0f0f0')  # Light gray background
        
        # Get machine ID from environment variable
        self.machine_id = os.getenv('MACHINE_ID', 'Not Set')
        
        # Create and setup the UI
        self.setup_ui()
        
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

        # Initialize loadcell data in environment
        self.initialize_loadcell_env()

        # Load saved settings and values
        self.load_saved_settings()
        self.load_device_values()

    def setup_ui(self):
        # Header with border lines
        header_frame = tk.Frame(self.root, bg='#f0f0f0')
        header_frame.pack(fill=tk.X, padx=5)
        
        # Top border line
        tk.Canvas(header_frame, height=2, bg='#2c3e50').pack(fill=tk.X)
        
        # Header content frame
        header_content = tk.Frame(header_frame, bg='#f0f0f0')
        header_content.pack(fill=tk.X, pady=5)
        
        # Title (Center)
        title_label = tk.Label(
            header_content, 
            text="COM PORT SETTINGS",
            bg='#f0f0f0',
            fg='#2c3e50',
            font=('Arial', 28, 'bold')
        )
        title_label.pack(expand=True)
        
        # Machine ID Label (Right side)
        machine_id = os.getenv('MACHINE_ID', 'Not Set')  # Get from environment variable
        machine_label = tk.Label(
            header_content, 
            text=f"Machine ID: {machine_id}",
            bg='#f0f0f0',
            fg='#2c3e50',
            font=('Arial', 12, 'bold')
        )
        machine_label.pack(side=tk.RIGHT, padx=20)
        
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

        # Initially enable Save button and disable Edit button
        self.control_buttons["SAVE"].config(state="normal")
        self.control_buttons["EDIT"].config(state="disabled")

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
        
        # Buttons frame for TEST and READ buttons side by side
        buttons_frame = tk.Frame(top_frame, bg=frame['bg'])
        buttons_frame.pack(side='left', padx=2)
        
        # Test Button
        self.test_button = tk.Button(buttons_frame, text="TEST", bg='darkred', fg='white', 
                              width=8, font=('Arial', 9, 'bold'),
                                    command=self.read_plc_data)
        self.test_button.pack(side='left', padx=2)
        
        # Read Button (new)
        self.read_button = tk.Button(buttons_frame, text="READ", bg='navy', fg='white',
                              width=8, font=('Arial', 9, 'bold'),
                                    command=self.read_holding_registers)
        self.read_button.pack(side='left', padx=2)
        
        # Station ID
        station_frame = tk.Frame(top_frame, bg=frame['bg'])
        station_frame.pack(side='left', padx=5)
        self.station_id_entry = tk.Entry(station_frame, width=10)
        self.station_id_entry.pack(side='left', padx=2)
        tk.Label(station_frame, text="Station ID", bg=frame['bg']).pack(side='left')
        
        # Register Address (new)
        reg_frame = tk.Frame(frame, bg=frame['bg'])
        reg_frame.pack(anchor='w', padx=5, pady=5)
        tk.Label(reg_frame, text="Register Address (e.g., D0001):", bg=frame['bg']).pack(side='left')
        self.reg_address_entry = tk.Entry(reg_frame, width=15)
        self.reg_address_entry.pack(side='left', padx=5)
        
        # Number of Points to Read (new)
        points_frame = tk.Frame(frame, bg=frame['bg'])
        points_frame.pack(anchor='w', padx=5, pady=5)
        tk.Label(points_frame, text="Number of Points to Read:", bg=frame['bg']).pack(side='left')
        self.points_entry = tk.Entry(points_frame, width=5)
        self.points_entry.pack(side='left', padx=5)
        self.points_entry.insert(0, "1")  # Default to 1 point
        
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
        
        # Update combobox values with empty default
        self.plc_com_combo['values'] = available_ports if available_ports else [""]
        self.plc_com_combo.set("")  # Empty default
        self.plc_baud_combo['values'] = [9600, 19200, 38400, 57600, 115200]
        self.plc_baud_combo.set("")  # Empty default
        
        # Initially enable all inputs
        self.plc_com_combo.config(state="readonly")
        self.plc_baud_combo.config(state="readonly")
        self.station_id_entry.config(state="normal")
        self.reg_address_entry.config(state="normal")
        self.points_entry.config(state="normal")
        
        # Connect Button
        self.connect_button = tk.Button(frame, text="Connect", bg='green', fg='white',
                                      font=('Arial', 9, 'bold'), command=self.connect_to_plc)
        self.connect_button.pack(anchor='w', padx=5, pady=5)
        
        # Rx String
        tk.Label(frame, text="Rx String", **label_style).pack(anchor='w', padx=5, pady=2)
        self.rx_text = tk.Text(frame, height=10, width=30, font=('Consolas', 10))
        self.rx_text.pack(padx=5, pady=5)
        
        # Initially disable test and read buttons
        self.test_button.config(state="disabled")
        self.read_button.config(state="disabled")

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

            # Check if there's an existing connection
            if self.modbus_client and self.modbus_client.is_socket_open():
                try:
                    # Test if the existing connection is still working
                    test_response = self.modbus_client.read_coils(
                        address=0,
                        count=1,
                        slave=slave_id
                    )
                    if not test_response.isError():
                        messagebox.showinfo("Connection Status", "Already connected to PLC!")
                        self.test_button.config(state="normal")
                        self.read_button.config(state="normal")
                        return True
                except:
                    # If test fails, close the existing connection
                    try:
                        self.modbus_client.close()
                    except:
                        pass

            # Initialize Modbus client with RTU settings
            self.modbus_client = ModbusSerialClient(
                port=port,
                baudrate=baudrate,
                timeout=1,
                stopbits=1,
                bytesize=8,
                parity='N'
            )

            # Try to connect with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if self.modbus_client.connect():
                        # Test connection by reading a coil
                        test_response = self.modbus_client.read_coils(
                            address=0,
                            count=1,
                            slave=slave_id
                        )
                        
                        if not test_response.isError():
                            messagebox.showinfo("Connection Status", "Connected to PLC!")
                            self.test_button.config(state="normal")
                            self.read_button.config(state="normal")
                            return True
                    
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Wait before retrying
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    raise e

            # If we get here, connection failed after all retries
            if self.modbus_client:
                self.modbus_client.close()
            messagebox.showerror("Connection Status", "Failed to connect to PLC after multiple attempts.")
            return False
            
        except ValueError as ve:
            messagebox.showerror("Input Error", str(ve))
            return False
        except Exception as e:
            messagebox.showerror("Error", f"Connection Error: {str(e)}")
            if self.modbus_client:
                self.modbus_client.close()
            return False

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
            
            # Define file paths in txt_files directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            txt_files_dir = os.path.join(current_dir, "txt_files")
            
            process_status_file = os.path.join(txt_files_dir, "ProcessStatus.txt")
            input_sensors_file = os.path.join(txt_files_dir, "InputSensors.txt")
            program_selection_file = os.path.join(txt_files_dir, "ProgramSelectionInPLC.txt")
            
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
                        self.rx_text.insert(tk.END, f"Warning: {os.path.basename(file_path)} not found in txt_files directory\n")
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
                            
                        # Store addresses in appropriate array and read coils
                        if "ProcessStatus" in file_path:
                            self._read_coils(addresses, "Process Status", slave_id)
                        elif "InputSensors" in file_path:
                            self._read_coils(addresses, "Input Sensors", slave_id)
                        elif "ProgramSelection" in file_path:
                            self._read_coils(addresses, "Program Selection", slave_id)
                            
                except Exception as e:
                    self.rx_text.insert(tk.END, f"Error reading {os.path.basename(file_path)}: {str(e)}\n")

            # After reading data, save the values
            self.save_device_values()

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
        
        # If addresses is a string, split it into a list
        if isinstance(addresses, str):
            addresses = [addr.strip() for addr in addresses.split(',')]
        
        for address in addresses:
            try:
                # Clean up the address string
                address = address.strip()
                if not address:
                    continue
                    
                # Extract the hex part based on whether it starts with M or P
                if address.startswith('M'):
                    hex_part = address[1:]  # Remove 'M'
                elif address.startswith('P'):
                    hex_part = address[1:]  # Remove 'P'
                else:
                    self.rx_text.insert(tk.END, f"{address} --> Invalid address format (must start with M or P)\n")
                    continue
                
                # Convert hex address to integer
                try:
                    coil_address = int(hex_part, 16)
                except ValueError:
                    self.rx_text.insert(tk.END, f"{address} --> Invalid hex value: {hex_part}\n")
                    continue

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
        # Style settings
        label_style = {'bg': frame['bg'], 'fg': 'black', 'font': ('Arial', 10)}
        
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
        
        # COM Port
        tk.Label(frame, text="COM Port", **label_style).pack(anchor='w', padx=5, pady=2)
        com_combo = ttk.Combobox(frame, width=25, state="readonly")
        com_combo.pack(anchor='w', padx=5)
        
        # BAUD Rate
        tk.Label(frame, text="BAUD Rate", **label_style).pack(anchor='w', padx=5, pady=2)
        baud_combo = ttk.Combobox(frame, width=25, state="readonly")
        baud_combo['values'] = [9600, 19200, 38400, 57600, 115200]
        baud_combo.set("")  # Empty default
        baud_combo.pack(anchor='w', padx=5)
        
        # Add comboboxes to the list
        self.all_comboboxes.extend([com_combo, baud_combo])
        
        # Get available COM ports
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
        
        # Get loadcell number and store it
        loadcell_num = frame.winfo_children()[0].cget("text").split('-')[1].strip()[:2]
        frame.loadcell_num = loadcell_num
        
        # Update combobox values with empty default
        if available_ports:
            com_combo['values'] = available_ports
            com_combo.set("")  # Empty default
        else:
            com_combo['values'] = [""]
            com_combo.set("")
        
        baud_combo['values'] = [9600, 19200, 38400, 57600, 115200]
        baud_combo.set("")  # Empty default
        
        # Initially enable all inputs
        com_combo.config(state="readonly")
        baud_combo.config(state="readonly")
        
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

    def test_loadcell(self, frame):
        """Test loadcell communication and save data"""
        try:
            if frame not in self.loadcell_ports or not self.loadcell_ports[frame].is_open:
                loadcell_num = frame.loadcell_num
                messagebox.showerror("Connection Error", 
                                   f"Loadcell {loadcell_num} is not connected!")
                return
            
            frame.rx_text.delete("1.0", tk.END)
            loadcell_num = frame.loadcell_num
            
            try:
                # Clear buffers
                self.loadcell_ports[frame].reset_input_buffer()
                self.loadcell_ports[frame].reset_output_buffer()
                
                # Set timeout
                self.loadcell_ports[frame].timeout = 0.5
                
                # Send command
                command = f"ID{loadcell_num}P".encode()
                self.loadcell_ports[frame].write(command)
                frame.rx_text.insert(tk.END, f"Sent command: ID{loadcell_num}P\n")
                
                # Update GUI
                self.root.update()
                
                # Read response
                response = self.loadcell_ports[frame].readline()
                
                if response:
                    decoded_response = response.decode('utf-8', errors='replace').strip()
                    frame.rx_text.insert(tk.END, f"Response: {decoded_response}\n")
                    
                    # Parse and save data
                    try:
                        parts = decoded_response.split(',')
                        if len(parts) > 1:
                            value = parts[1]
                            frame.rx_text.insert(tk.END, f"Parsed value: {value}\n")
                            
                            # Save to environment variable
                            self.save_loadcell_data(loadcell_num, value)
                            
                    except IndexError:
                        frame.rx_text.insert(tk.END, "Could not parse value\n")
                else:
                    frame.rx_text.insert(tk.END, "No response received\n")
                    
            except Exception as e:
                frame.rx_text.insert(tk.END, f"Communication error: {str(e)}\n")
                
            finally:
                self.loadcell_ports[frame].timeout = 1
                
            # After reading data, save the values
            self.save_device_values()
            
        except Exception as e:
            frame.rx_text.insert(tk.END, f"Error: {str(e)}\n")
        
        self.root.update()

    def connect_loadcell(self, frame, com_combo, baud_combo, test_button):
        """Connect to loadcell using serial communication"""
        try:
            port = com_combo.get()
            baudrate = int(baud_combo.get())
            loadcell_num = frame.loadcell_num
            
            # Check if port is "No Ports Available"
            if port == "No Ports Available":
                messagebox.showerror("Connection Error", 
                                   f"No COM ports available for Loadcell {loadcell_num}!")
                return
            
            # Check if port still exists
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            if port not in available_ports:
                messagebox.showerror("Connection Error", 
                                   f"COM Port {port} is no longer available!")
                return
            
            # Close existing connection if any
            if frame in self.loadcell_ports and self.loadcell_ports[frame].is_open:
                self.loadcell_ports[frame].close()
            
            # Create new serial connection with timeout
            ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=0.5,  # Shorter initial timeout
                write_timeout=0.5  # Add write timeout
            )
            
            if ser.is_open:
                self.loadcell_ports[frame] = ser
                test_button.config(state="normal")
                messagebox.showinfo("Success", f"Connected to Loadcell {loadcell_num}")
            else:
                raise serial.SerialException("Failed to open port")
                
        except ValueError as ve:
            messagebox.showerror("Error", f"Invalid baudrate: {str(ve)}")
        except serial.SerialException as se:
            messagebox.showerror("Error", f"Serial port error: {str(se)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")

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
            # Validate all required fields are filled
            if not self._validate_settings():
                messagebox.showerror("Validation Error", "Please fill in all required fields!")
                return

            # Get the .env file path
            env_path = find_dotenv()
            if not env_path:
                env_path = self.env_file

            # Save PLC settings
            set_key(env_path, 'PLC_COM_PORT', self.plc_com_combo.get())
            set_key(env_path, 'PLC_BAUD_RATE', self.plc_baud_combo.get())
            set_key(env_path, 'PLC_STATION_ID', self.station_id_entry.get())
            
            # Save Register Address and Points settings
            set_key(env_path, 'PLC_REG_ADDRESS', self.reg_address_entry.get())
            set_key(env_path, 'PLC_POINTS_TO_READ', self.points_entry.get())
            
            # Save Loadcell settings
            for frame in self.root.winfo_children():
                if isinstance(frame, tk.Frame):
                    for child in frame.winfo_children():
                        if isinstance(child, tk.Frame):
                            title_label = child.winfo_children()[0]
                            if isinstance(title_label, tk.Label) and "LOADCELL" in title_label.cget("text"):
                                loadcell_num = title_label.cget("text").split('-')[1].strip()[:2]
                                com_combo = child.winfo_children()[2]  # COM port combo
                                baud_combo = child.winfo_children()[4]  # BAUD rate combo
                                
                                set_key(env_path, f'LOADCELL_{loadcell_num}_COM_PORT', com_combo.get())
                                set_key(env_path, f'LOADCELL_{loadcell_num}_BAUD_RATE', baud_combo.get())
            
            # Save Modbus TCP settings
            set_key(env_path, 'MODBUS_TCP_IP', self.ip_entry.get())
            set_key(env_path, 'MODBUS_TCP_PORT', self.port_entry.get())
            
            # Disable all inputs
            self._freeze_all_inputs()
            
            # Update button states
            self.control_buttons["SAVE"].config(state="disabled")
            self.control_buttons["EDIT"].config(state="normal")
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings!\nError: {str(e)}")

    def _validate_settings(self):
        """Validate that at least one frame has all fields filled"""
        # Check if PLC frame is complete
        if all([self.plc_com_combo.get(), self.plc_baud_combo.get(), self.station_id_entry.get()]):
            return True
            
        # Check if any Loadcell frame is complete
        for frame in self.root.winfo_children():
            if isinstance(frame, tk.Frame):
                for child in frame.winfo_children():
                    if isinstance(child, tk.Frame):
                        title_label = child.winfo_children()[0]
                        if isinstance(title_label, tk.Label) and "LOADCELL" in title_label.cget("text"):
                            com_combo = child.winfo_children()[2]  # COM port combo
                            baud_combo = child.winfo_children()[4]  # BAUD rate combo
                            if all([com_combo.get(), baud_combo.get()]):
                                return True
        
        # Check if Modbus TCP frame is complete
        if all([self.ip_entry.get(), self.port_entry.get()]):
            return True
            
        return False

    def _freeze_all_inputs(self):
        """Helper method to disable all input fields"""
        # Disable PLC inputs
        self.plc_com_combo.config(state="disabled")
        self.plc_baud_combo.config(state="disabled")
        self.station_id_entry.config(state="disabled")
        self.reg_address_entry.config(state="disabled") 
        self.points_entry.config(state="disabled")
        
        # Disable all comboboxes
        for combo in self.all_comboboxes:
            combo.config(state="disabled")
        
        # Disable Modbus TCP inputs
        self.ip_entry.config(state="disabled")
        self.port_entry.config(state="disabled")

    def enable_editing(self):
        """Enable editing of all input fields"""
        # Enable PLC inputs
        self.plc_com_combo.config(state="readonly")
        self.plc_baud_combo.config(state="readonly")
        self.station_id_entry.config(state="normal")
        self.reg_address_entry.config(state="normal")
        self.points_entry.config(state="normal")
        
        # Enable all comboboxes
        for combo in self.all_comboboxes:
            combo.config(state="readonly")
        
        # Enable Modbus TCP inputs
        self.ip_entry.config(state="normal")
        self.port_entry.config(state="normal")
        
        # Update button states
        self.control_buttons["SAVE"].config(state="normal")
        self.control_buttons["EDIT"].config(state="disabled")
        
        messagebox.showinfo("Edit Mode", "Settings are now editable")

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
                'PLC_COM_PORT', 'PLC_BAUD_RATE', 'PLC_STATION_ID',
                'MODBUS_TCP_IP', 'MODBUS_TCP_PORT'
            ]
            
            # Add loadcell environment variables
            for i in range(1, 3):  # For LOADCELL-01 and LOADCELL-02
                loadcell_num = f"{i:02d}"
                env_vars.extend([
                    f'LOADCELL_{loadcell_num}_COM_PORT',
                    f'LOADCELL_{loadcell_num}_BAUD_RATE'
                ])
            
            # Clear each environment variable
            for var in env_vars:
                set_key(env_path, var, '')
            
            # Reset all inputs to default values
            self._reset_to_defaults()
            
            # Enable editing
            self.enable_editing()
            
            # Close any existing connections
            self.cleanup()
            
            messagebox.showinfo("Reset Complete", "All settings have been reset to default values")
            
        except Exception as e:
            messagebox.showerror("Reset Error", f"Error during reset: {str(e)}")

    def _reset_to_defaults(self):
        """Helper method to reset all inputs to default values"""
        try:
            # Get the .env file path
            env_path = find_dotenv()
            if not env_path:
                env_path = self.env_file

            # Clear saved values from environment
            set_key(env_path, 'PLC_RX_DATA', '')
            set_key(env_path, 'LOADCELL_01_RX_DATA', '')
            set_key(env_path, 'LOADCELL_02_RX_DATA', '')
            set_key(env_path, 'PLC_REG_ADDRESS', '')
            set_key(env_path, 'PLC_POINTS_TO_READ', '1')

            # Get available COM ports
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            
            # Reset PLC settings
            self.plc_com_combo.set("")
            self.plc_baud_combo.set("")
            self.station_id_entry.delete(0, tk.END)
            self.reg_address_entry.delete(0, tk.END)
            self.points_entry.delete(0, tk.END)
            self.points_entry.insert(0, "1")  # Reset to default of 1
            self.rx_text.delete("1.0", tk.END)
            
            # Reset all COM port combos and Rx strings for Loadcells
            for frame in self.root.winfo_children():
                if isinstance(frame, tk.Frame):
                    for child in frame.winfo_children():
                        if isinstance(child, tk.Frame):
                            if "LOADCELL" in child.winfo_children()[0].cget("text"):
                                com_combo = child.winfo_children()[2]
                                baud_combo = child.winfo_children()[4]
                                rx_text = child.rx_text
                                
                                com_combo['values'] = available_ports if available_ports else [""]
                                com_combo.set("")
                                baud_combo.set("")
                                rx_text.delete("1.0", tk.END)
            
            # Reset Modbus TCP settings
            self.ip_entry.delete(0, tk.END)
            self.port_entry.delete(0, tk.END)
            self.rx_tcp_text.delete("1.0", tk.END)

        except Exception as e:
            print(f"Error resetting to defaults: {str(e)}")

    def load_saved_settings(self):
        """Load settings from environment variables"""
        try:
            # Load PLC settings
            plc_port = os.getenv('PLC_COM_PORT', '')
            plc_baud = os.getenv('PLC_BAUD_RATE', '')
            plc_station_id = os.getenv('PLC_STATION_ID', '')
            
            self.plc_com_combo.set(plc_port)
            self.plc_baud_combo.set(plc_baud)
            self.station_id_entry.delete(0, tk.END)
            self.station_id_entry.insert(0, plc_station_id)
            
            # Load Register Address and Points settings if they exist
            reg_address = os.getenv('PLC_REG_ADDRESS', '')
            points_to_read = os.getenv('PLC_POINTS_TO_READ', '1')
            
            self.reg_address_entry.delete(0, tk.END)
            self.reg_address_entry.insert(0, reg_address)
            
            self.points_entry.delete(0, tk.END)
            self.points_entry.insert(0, points_to_read)
            
            # Load Loadcell settings
            for frame in self.root.winfo_children():
                if isinstance(frame, tk.Frame):
                    for child in frame.winfo_children():
                        if isinstance(child, tk.Frame):
                            title_label = child.winfo_children()[0]
                            if isinstance(title_label, tk.Label) and "LOADCELL" in title_label.cget("text"):
                                loadcell_num = title_label.cget("text").split('-')[1].strip()[:2]
                                com_combo = child.winfo_children()[2]
                                baud_combo = child.winfo_children()[4]
                                
                                com_port = os.getenv(f'LOADCELL_{loadcell_num}_COM_PORT', '')
                                baud_rate = os.getenv(f'LOADCELL_{loadcell_num}_BAUD_RATE', '')
                                
                                com_combo.set(com_port)
                                baud_combo.set(baud_rate)
            
            # Load Modbus TCP settings
            modbus_ip = os.getenv('MODBUS_TCP_IP', '')
            modbus_port = os.getenv('MODBUS_TCP_PORT', '')
            
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, modbus_ip)
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, modbus_port)
            
            # If we have saved settings, freeze the inputs
            if any([plc_port, plc_baud, plc_station_id, modbus_ip, modbus_port]):
                self._freeze_all_inputs()
                self.control_buttons["SAVE"].config(state="disabled")
                self.control_buttons["EDIT"].config(state="normal")
                
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load settings!\nError: {str(e)}")

    def initialize_loadcell_env(self):
        """Initialize environment variables for loadcell data if they don't exist"""
        try:
            for i in range(1, 3):  # For loadcell 1 and 2
                env_key = f'LOADCELL_{i}_DATA'
                if not os.getenv(env_key):
                    # Initialize with empty data list
                    os.environ[env_key] = json.dumps([])
        except Exception as e:
            print(f"Error initializing environment variables: {str(e)}")

    def save_loadcell_data(self, loadcell_num, value):
        """Save loadcell data to environment variable"""
        try:
            env_key = f'LOADCELL_{loadcell_num}_DATA'
            
            # Get existing data
            existing_data = json.loads(os.getenv(env_key, '[]'))
            
            # Create new data entry
            new_entry = {
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'value': value
            }
            
            # Add new entry and keep only last 100 readings
            existing_data.append(new_entry)
            if len(existing_data) > 100:  # Limit to last 100 readings
                existing_data = existing_data[-100:]
            
            # Save back to environment variable
            os.environ[env_key] = json.dumps(existing_data)
            
        except Exception as e:
            print(f"Error saving loadcell data: {str(e)}")

    def load_loadcell_data(self, frame):
        """Load previous loadcell data from environment variable"""
        try:
            loadcell_num = frame.loadcell_num
            env_key = f'LOADCELL_{loadcell_num}_DATA'
            
            # Get data from environment variable
            data = json.loads(os.getenv(env_key, '[]'))
            
            # Clear current display
            frame.rx_text.delete("1.0", tk.END)
            
            if data:
                # Display last 5 entries
                frame.rx_text.insert(tk.END, "Previous readings:\n")
                for entry in data[-5:]:
                    frame.rx_text.insert(tk.END, 
                                       f"{entry['timestamp']}: {entry['value']}\n")
            else:
                frame.rx_text.insert(tk.END, "No previous readings available\n")
            
        except Exception as e:
            frame.rx_text.insert(tk.END, f"Error loading previous data: {str(e)}\n")

    def save_device_values(self):
        """Save PLC and loadcell values to environment variables"""
        try:
            env_path = find_dotenv()
            if not env_path:
                env_path = self.env_file

            # Save PLC Rx string
            plc_rx = self.rx_text.get("1.0", tk.END).strip()
            set_key(env_path, 'PLC_RX_DATA', plc_rx)

            # Save Loadcell Rx strings
            for frame in self.root.winfo_children():
                if isinstance(frame, tk.Frame):
                    for child in frame.winfo_children():
                        if isinstance(child, tk.Frame):
                            title_label = child.winfo_children()[0]
                            if isinstance(title_label, tk.Label) and "LOADCELL" in title_label.cget("text"):
                                loadcell_num = title_label.cget("text").split('-')[1].strip()[:2]
                                rx_text = child.rx_text  # Get the Text widget reference
                                rx_data = rx_text.get("1.0", tk.END).strip()
                                set_key(env_path, f'LOADCELL_{loadcell_num}_RX_DATA', rx_data)

        except Exception as e:
            print(f"Error saving device values: {str(e)}")

    def load_device_values(self):
        """Load PLC and loadcell values from environment variables"""
        try:
            # Load PLC Rx string
            plc_rx = os.getenv('PLC_RX_DATA', '')
            if plc_rx:
                self.rx_text.delete("1.0", tk.END)
                self.rx_text.insert(tk.END, plc_rx)

            # Load Loadcell Rx strings
            for frame in self.root.winfo_children():
                if isinstance(frame, tk.Frame):
                    for child in frame.winfo_children():
                        if isinstance(child, tk.Frame):
                            title_label = child.winfo_children()[0]
                            if isinstance(title_label, tk.Label) and "LOADCELL" in title_label.cget("text"):
                                loadcell_num = title_label.cget("text").split('-')[1].strip()[:2]
                                rx_text = child.rx_text  # Get the Text widget reference
                                rx_data = os.getenv(f'LOADCELL_{loadcell_num}_RX_DATA', '')
                                if rx_data:
                                    rx_text.delete("1.0", tk.END)
                                    rx_text.insert(tk.END, rx_data)

        except Exception as e:
            print(f"Error loading device values: {str(e)}")

    def cleanup(self):
        """Close all connections and save values before closing"""
        try:
            # Save all current values
            self.save_device_values()
            
            # Close all connections
            if hasattr(self, 'modbus_client') and self.modbus_client:
                self.modbus_client.close()
            
            if hasattr(self, 'modbus_tcp_client') and self.modbus_tcp_client:
                self.modbus_tcp_client.close()
                
            # Close loadcell connections
            for frame, ser in self.loadcell_ports.items():
                if ser and ser.is_open:
                    ser.close()
                
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

    def load_plc_options(self):
        """Load PLC address options from plc_register.txt"""
        try:
            # Use path in txt_files directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, "txt_files", "PLC_on_register.txt")
            
            with open(file_path, 'r') as file:
                # Read content and split by commas
                content = file.read().strip()
                options = [opt.strip() for opt in content.split(',') if opt.strip()]
                print(f"Loaded PLC options: {options}")  # Debug print
                return options
        except FileNotFoundError:
            print(f"Warning: PLC_on_register.txt not found in txt_files directory at {file_path}")
            return []
        except Exception as e:
            print(f"Error reading PLC options: {str(e)}")
            return []

    def load_barcode_options(self):
        """Load barcode options from barcodeprintfilename.txt"""
        try:
            # Use path in txt_files directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, "txt_files", "barcodeprintfilenames.txt")
            
            with open(file_path, 'r') as file:
                # Read content and split by commas
                content = file.read().strip()
                options = [opt.strip() for opt in content.split(',') if opt.strip()]
                print(f"Loaded barcode options: {options}")  # Debug print
                return options
        except FileNotFoundError:
            print(f"Warning: barcodeprintfilenames.txt not found in txt_files directory at {file_path}")
            return []
        except Exception as e:
            print(f"Error reading barcode options: {str(e)}")
            return []

    def read_holding_registers(self):
        """Read holding registers from PLC and interpret as double datatype values"""
        if self.modbus_client is None or not self.modbus_client.is_socket_open():
            messagebox.showerror("Error", "Not connected to PLC.")
            return

        try:
            slave_id = self.station_id_entry.get().strip()
            register_address = self.reg_address_entry.get().strip()
            points_to_read = self.points_entry.get().strip()
            
            # Validate inputs
            if not slave_id:
                messagebox.showerror("Error", "Station ID is mandatory!")
                return
            
            if not register_address:
                messagebox.showerror("Error", "Register address is mandatory!")
                return
            
            if not points_to_read or not points_to_read.isdigit():
                messagebox.showerror("Error", "Number of points must be a valid integer!")
                return

            slave_id = int(slave_id)
            points_to_read = int(points_to_read)
            
            # Validate points_to_read range
            if points_to_read < 1 or points_to_read > 125:  # Modbus limits for holding registers
                messagebox.showerror("Error", "Number of points must be between 1 and 125!")
                return
            
            # Clear the text box
            self.rx_text.delete("1.0", tk.END)
            
            # Process the register address
            try:
                # Handle D-prefixed addresses (e.g., D0001) by extracting the numeric part
                if register_address.startswith('D'):
                    # Remove 'D' prefix and convert to integer
                    addr = int(register_address[1:])
                elif register_address.startswith('0x'):
                    addr = int(register_address, 16)
                else:
                    # Try to parse as a direct integer
                    addr = int(register_address)
                
                # Add section header
                self.rx_text.insert(tk.END, f"Reading {points_to_read} Holding Register(s) starting at address {register_address}:\n\n")
                
                # Read holding registers
                response = self.modbus_client.read_holding_registers(
                    address=addr,
                    count=points_to_read,
                    slave=slave_id
                )
                
                if response.isError():
                    self.rx_text.insert(tk.END, f"Error reading registers at address {register_address}\n")
                    return
                
                # Display raw register values
                self.rx_text.insert(tk.END, "Raw Register Values:\n")
                for i, reg_value in enumerate(response.registers):
                    self.rx_text.insert(tk.END, f"Register {addr + i}: {reg_value} (0x{reg_value:04X})\n")
                
                self.rx_text.insert(tk.END, "\n")
                
                # Process registers as doubles if we have at least 2 registers
                if len(response.registers) >= 2:
                    import struct
                    self.rx_text.insert(tk.END, "Interpreting as Double Values:\n")
                    
                    # Process each pair of registers as a double
                    for i in range(0, len(response.registers) - 1, 2):
                        reg1 = response.registers[i]
                        reg2 = response.registers[i + 1]
                        
                        self.rx_text.insert(tk.END, f"\nRegisters {addr + i} & {addr + i + 1} [{reg1}, {reg2}]:\n")
                        
                        # Try different byte orders for maximum compatibility
                        try:
                            # Standard 32-bit IEEE float format (big endian)
                            register_bytes = struct.pack('>HH', reg1, reg2)
                            float_value = struct.unpack('>f', register_bytes)[0]
                            self.rx_text.insert(tk.END, f"  Big-Endian (>f): {float_value:.6f}\n")
                        except Exception as e:
                            self.rx_text.insert(tk.END, f"  Big-Endian error: {str(e)}\n")
                        
                        try:
                            # Little endian format
                            register_bytes = struct.pack('<HH', reg1, reg2)
                            float_value = struct.unpack('<f', register_bytes)[0]
                            self.rx_text.insert(tk.END, f"  Little-Endian (<f): {float_value:.6f}\n")
                        except Exception as e:
                            self.rx_text.insert(tk.END, f"  Little-Endian error: {str(e)}\n")
                        
                        try:
                            # Swapped bytes format
                            register_bytes = struct.pack('>HH', reg2, reg1)
                            float_value = struct.unpack('>f', register_bytes)[0]
                            self.rx_text.insert(tk.END, f"  Swapped registers (>f): {float_value:.6f}\n")
                        except Exception as e:
                            self.rx_text.insert(tk.END, f"  Swapped registers error: {str(e)}\n")
                        
                        try:
                            # Swapped bytes with little endian
                            register_bytes = struct.pack('<HH', reg2, reg1)
                            float_value = struct.unpack('<f', register_bytes)[0]
                            self.rx_text.insert(tk.END, f"  Swapped registers (<f): {float_value:.6f}\n")
                        except Exception as e:
                            self.rx_text.insert(tk.END, f"  Swapped registers little-endian error: {str(e)}\n")
                else:
                    self.rx_text.insert(tk.END, "Need at least 2 registers to interpret as double value.\n")
                
            except ValueError as ve:
                self.rx_text.insert(tk.END, f"Invalid address format: {str(ve)}\n")
            except Exception as e:
                self.rx_text.insert(tk.END, f"Error reading register: {str(e)}\n")
            
            # Save the display values
            self.save_device_values()
            
        except ValueError as ve:
            messagebox.showerror("Error", f"Invalid input: {str(ve)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read holding registers: {str(e)}")

def main():
    root = tk.Tk()
    app = ComPortSettings(root)
    
    # Add cleanup on window close
    root.protocol("WM_DELETE_WINDOW", lambda: [app.cleanup(), root.destroy()])
    
    root.mainloop()

if __name__ == "__main__":
    main()
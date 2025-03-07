import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import serial.tools.list_ports

class ComPortSettings:
    def __init__(self, root):
        self.root = root
        self.root.title("COM Port Settings")
        
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
        
        # Control buttons
        buttons = [
            ("EDIT", '#3498db', 'white'),
            ("SAVE", '#2ecc71', 'white'),
            ("RESET", '#e74c3c', 'white')
        ]
        
        for text, bg, fg in buttons:
            btn = tk.Button(control_frame, text=text, bg=bg, fg=fg, 
                          width=15, font=('Arial', 12, 'bold'))
            btn.pack(pady=5)

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

        self.db_config = {
            'host': 'localhost',
            'port': '3360',
            'user': 'root',
            'password': 'nk446420',
            'database': 'EOL'
        }
        self.test_database_connection()

        # Add Modbus client attribute
        self.modbus_client = None

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

            self.modbus_client = ModbusSerialClient(
                port=port,
                baudrate=baudrate,
                parity='N',
                stopbits=1,
                bytesize=8,
                timeout=1
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
        """Read data from PLC registers"""
        if self.modbus_client is None or not self.modbus_client.is_socket_open():
            messagebox.showerror("Error", "Not connected to PLC.")
            return

        try:
            slave_id = int(self.station_id_entry.get())

            # Read Holding Registers (D)
            d_response = self.modbus_client.read_holding_registers(
                address=100,
                count=5,
                slave=slave_id
            )
            d_values = d_response.registers if not getattr(d_response, 'isError', lambda: True)() else "Error"

            # Read Coils (M)
            m_response = self.modbus_client.read_coils(
                address=10,
                count=5,
                slave=slave_id
            )
            m_values = m_response.bits if not getattr(m_response, 'isError', lambda: True)() else "Error"

            # Read Discrete Inputs (X)
            x_response = self.modbus_client.read_discrete_inputs(
                address=5,
                count=5,
                slave=slave_id
            )
            x_values = x_response.bits if not getattr(x_response, 'isError', lambda: True)() else "Error"

            # Read Input Registers (W)
            w_response = self.modbus_client.read_input_registers(
                address=20,
                count=5,
                slave=slave_id
            )
            w_values = w_response.registers if not getattr(w_response, 'isError', lambda: True)() else "Error"

            # Display results
            self.rx_text.delete("1.0", tk.END)
            self.rx_text.insert(tk.END, f"D100-104: {d_values}\n")
            self.rx_text.insert(tk.END, f"M10-14: {m_values}\n")
            self.rx_text.insert(tk.END, f"X5-9: {x_values}\n")
            self.rx_text.insert(tk.END, f"W20-24: {w_values}\n")

        except Exception as e:
            messagebox.showerror("Read Error", str(e))

    def add_loadcell_content(self, frame):
        # Test button with consistent styling
        tk.Button(frame, text="TEST", bg='darkred', fg='white', 
                 width=8, font=('Arial', 9, 'bold')).pack(anchor='w', padx=5, pady=5)
        
        # Style settings
        label_style = {'bg': frame['bg'], 'fg': 'black', 'font': ('Arial', 10)}
        
        # COM Port
        tk.Label(frame, text="COM Port", **label_style).pack(anchor='w', padx=5, pady=2)
        com_combo = ttk.Combobox(frame, width=25)
        
        # Get available COM ports
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
        
        # Update combobox values with detected ports
        com_combo['values'] = available_ports
        com_combo.pack(anchor='w', padx=5)
        
        # BAUD Rate
        tk.Label(frame, text="BAUD Rate", **label_style).pack(anchor='w', padx=5, pady=2)
        baud_combo = ttk.Combobox(frame, width=25)
        baud_combo['values'] = [9600, 19200, 38400, 57600, 115200]
        baud_combo.pack(anchor='w', padx=5)
        
        # Rx String
        tk.Label(frame, text="Rx String", **label_style).pack(anchor='w', padx=5, pady=2)
        rx_text = tk.Text(frame, height=8, width=25, font=('Consolas', 10))
        rx_text.pack(padx=5, pady=5)
        
        # Relay entries with improved styling
        relay_frame = tk.Frame(frame, bg=frame['bg'])
        relay_frame.pack(fill='x', padx=5, pady=5)
        
        # Create a 2x2 grid for relay entries
        for i in range(1, 5):
            row = (i-1) // 2
            col = (i-1) % 2
            
            relay_subframe = tk.Frame(relay_frame, bg=frame['bg'])
            relay_subframe.grid(row=row, column=col, padx=5, pady=2)
            
            tk.Label(relay_subframe, text=f"Relay - {i:02d}", 
                    **label_style, width=10, anchor='w').pack(side='left')
            tk.Entry(relay_subframe, width=12, font=('Arial', 10)).pack(side='left', padx=2)

    def test_database_connection(self):
        try:
            connection = mysql.connector.connect(**self.db_config)
            
            if connection.is_connected():
                cursor = connection.cursor()
                
                # Create test table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS com_port_settings (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        device_type VARCHAR(50),
                        com_port VARCHAR(20),
                        baud_rate INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                connection.commit()
                messagebox.showinfo(
                    "Success", 
                    "Database connection successful!\n"
                    "Table 'com_port_settings' created/verified."
                )
                
                cursor.close()
                connection.close()
                return True
                
        except Error as e:
            messagebox.showerror(
                "Database Error", 
                f"Failed to connect to database!\nError: {str(e)}"
            )
            return False

    def save_settings_to_db(self, device_type, com_port, baud_rate):
        try:
            connection = mysql.connector.connect(**self.db_config)
            
            if connection.is_connected():
                cursor = connection.cursor()
                
                sql = """INSERT INTO com_port_settings 
                        (device_type, com_port, baud_rate) 
                        VALUES (%s, %s, %s)"""
                values = (device_type, com_port, baud_rate)
                
                cursor.execute(sql, values)
                connection.commit()
                
                cursor.close()
                connection.close()
                return True
                
        except Error as e:
            messagebox.showerror("Database Error", f"Failed to save settings!\nError: {str(e)}")
            return False

def main():
    root = tk.Tk()
    app = ComPortSettings(root)
    root.mainloop()

if __name__ == "__main__":
    main()
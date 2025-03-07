import tkinter as tk
from tkinter import ttk, messagebox
from pymodbus.client import ModbusSerialClient
import serial.tools.list_ports

# Function to get available COM ports
def get_com_ports():
    ports = [port.device for port in serial.tools.list_ports.comports()]
    return ports

# Function to connect to PLC
def connect_to_plc():
    global client
    port = port_dropdown.get()
    baudrate = int(baudrate_dropdown.get())
    slave_id = slave_id_entry.get()

    try:
        if not slave_id:
            raise ValueError("Slave ID must be filled.")

        slave_id = int(slave_id)  # Validate slave ID

        # Initialize Modbus client
        client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=1
        )

        if client.connect():
            messagebox.showinfo("Connection Status", "Successfully connected to PLC!")
            # Enable read and write buttons
            read_button.config(state="normal")
            write_button.config(state="normal")
        else:
            messagebox.showerror("Connection Status", "Failed to connect to PLC.")
    except ValueError as ve:
        messagebox.showerror("Input Error", str(ve))
    except Exception as e:
        messagebox.showerror("Error", f"Error: {str(e)}")

# Function to read input registers
def read_registers():
    try:
        # Validate inputs
        address_str = read_address_entry.get()
        count = read_count_entry.get()

        if not address_str or not count:
            raise ValueError("Both Address and Count fields must be filled.")

        # Parse the address format (e.g., M0010)
        if not address_str[0].isalpha():
            raise ValueError("Address must start with a memory area letter (e.g., M, D)")
            
        memory_type = address_str[0].upper()
        address_num = int(address_str[1:])  # Convert the numeric part to integer
        
        # Map memory type to appropriate address range
        if memory_type == 'M':
            actual_address = address_num  # You might need to adjust this offset based on your PLC
        else:
            raise ValueError(f"Unsupported memory type: {memory_type}")

        count = int(count)

        # Read registers
        response = client.read_input_registers(address=actual_address, count=count, unit=int(slave_id_entry.get()))
        if response.isError():
            messagebox.showerror("Error", f"Read Error: {response}")
        else:
            result_label.config(text=f"Input Registers: {response.registers}")
    except ValueError as ve:
        messagebox.showerror("Input Error", str(ve))
    except Exception as e:
        messagebox.showerror("Error", f"Error: {str(e)}")

# Function to write to output register
def write_register():
    try:
        # Validate inputs
        address = write_address_entry.get()
        value = write_value_entry.get()

        if not address or not value:
            raise ValueError("Both Address and Value fields must be filled.")

        address = int(address)
        value = int(value)

        # Write register
        response = client.write_register(address=address, value=value, unit=int(slave_id_entry.get()))
        if response.isError():
            messagebox.showerror("Error", f"Write Error: {response}")
        else:
            messagebox.showinfo("Success", "Write Successful!")
    except ValueError as ve:
        messagebox.showerror("Input Error", str(ve))
    except Exception as e:
        messagebox.showerror("Error", f"Error: {str(e)}")

# GUI setup
root = tk.Tk()
root.title("RS-485 Communication with XGT PLC")

# Connection settings
tk.Label(root, text="COM Port:").grid(row=0, column=0, sticky='w')
available_ports = get_com_ports()
port_dropdown = ttk.Combobox(root, values=available_ports, state="readonly")
port_dropdown.grid(row=0, column=1)
port_dropdown.set(available_ports[0] if available_ports else "No Ports")

tk.Label(root, text="Baudrate:").grid(row=1, column=0, sticky='w')
baudrate_options = [9600, 19200, 38400, 57600, 115200]
baudrate_dropdown = ttk.Combobox(root, values=baudrate_options, state="readonly")
baudrate_dropdown.grid(row=1, column=1)
baudrate_dropdown.set(baudrate_options[0])

tk.Label(root, text="Slave ID:").grid(row=2, column=0, sticky='w')
slave_id_entry = tk.Entry(root)
slave_id_entry.grid(row=2, column=1)

connect_button = tk.Button(root, text="Connect", command=connect_to_plc)
connect_button.grid(row=3, columnspan=2)

# Read registers
tk.Label(root, text="Read Address:").grid(row=4, column=0, sticky='w')
read_address_entry = tk.Entry(root)
read_address_entry.grid(row=4, column=1)

tk.Label(root, text="Count:").grid(row=5, column=0, sticky='w')
read_count_entry = tk.Entry(root)
read_count_entry.grid(row=5, column=1)

read_button = tk.Button(root, text="Read Registers", command=read_registers, state="disabled")
read_button.grid(row=6, columnspan=2)

# Write register
tk.Label(root, text="Write Address:").grid(row=7, column=0, sticky='w')
write_address_entry = tk.Entry(root)
write_address_entry.grid(row=7, column=1)

tk.Label(root, text="Value:").grid(row=8, column=0, sticky='w')
write_value_entry = tk.Entry(root)
write_value_entry.grid(row=8, column=1)

write_button = tk.Button(root, text="Write Register", command=write_register, state="disabled")
write_button.grid(row=9, columnspan=2)

# Result display
result_label = tk.Label(root, text="", fg="blue")
result_label.grid(row=10, columnspan=2)

# Start the application
root.mainloop()
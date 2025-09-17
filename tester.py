import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pymodbus.client import ModbusSerialClient
import serial.tools.list_ports
import pandas as pn

client = None  # Modbus client

# Get available COM ports
def get_com_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

# Connect to PLC
def connect_to_plc():
    global client
    port = com_port_dropdown.get()
    baudrate = int(baud_rate_dropdown.get())
    slave_id = station_id_entry.get().strip()

    try:
        if port == "No Ports":
            raise ValueError("No COM ports available.")
        if not slave_id.isdigit():
            raise ValueError("Station ID must be a valid number.")

        slave_id = int(slave_id)

        client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            parity='N',
            stopbits=1,
            bytesize=8,
            timeout=1
        )

        if client.connect():
            messagebox.showinfo("Connection Status", "Connected to PLC!")
            test_button.config(state="normal")
        else:
            client.close()
            messagebox.showerror("Connection Status", "Failed to connect to PLC.")
    except ValueError as ve:
        messagebox.showerror("Input Error", str(ve))
    except Exception as e:
        messagebox.showerror("Error", f"Connection Error: {str(e)}")

# Read PLC data
def read_plc_data():
    if client is None or not client.is_socket_open():
        messagebox.showerror("Error", "Not connected to PLC.")
        return

    try:
        slave_id = int(station_id_entry.get())

        # Read Holding Registers (D)
        d_response = client.read_holding_registers(
            address=100,
            count=5,
            device_id=slave_id
        )
        d_values = d_response.registers if not getattr(d_response, 'isError', lambda: True)() else "Error"

        # Read Coils (M)
        m_response = client.read_coils(
            address=10,
            count=5,
            device_id=slave_id
        )
        m_values = m_response.bits if not getattr(m_response, 'isError', lambda: True)() else "Error"

        # Read Discrete Inputs (X)
        x_response = client.read_discrete_inputs(
            address=5,
            count=5,
            device_id=slave_id
        )
        x_values = x_response.bits if not getattr(x_response, 'isError', lambda: True)() else "Error"

        # Read Input Registers (W)
        w_response = client.read_input_registers(
            address=20,
            count=5,
            device_id=slave_id
        )
        w_values = w_response.registers if not getattr(w_response, 'isError', lambda: True)() else "Error"

        # Display results
        rx_textbox.delete("1.0", tk.END)
        rx_textbox.insert(tk.END, f"D100-104: {d_values}\n")
        rx_textbox.insert(tk.END, f"M10-14: {m_values}\n")
        rx_textbox.insert(tk.END, f"X5-9: {x_values}\n")
        rx_textbox.insert(tk.END, f"W20-24: {w_values}\n")

    except Exception as e:
        messagebox.showerror("Read Error", str(e))

# GUI setup
root = tk.Tk()
root.title("PLC Modbus GUI")
root.geometry("400x300")
root.configure(bg="#A3C19F")  # Set background color

# PLC Section
frame = tk.Frame(root, bg="#A3C19F")
frame.pack(padx=10, pady=10, fill="both", expand=True)

tk.Label(frame, text="PLC", bg="#A3C19F", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")

# Test Button
test_button = tk.Button(frame, text="TEST", bg="red", fg="white", font=("Arial", 10, "bold"), command=read_plc_data)
test_button.grid(row=1, column=0, padx=5, pady=5)

# Station ID
station_id_entry = tk.Entry(frame, width=10)
station_id_entry.grid(row=1, column=1, padx=5, pady=5)
tk.Label(frame, text="Station ID", bg="#A3C19F").grid(row=1, column=2, padx=5, pady=5)

# COM Port Dropdown
tk.Label(frame, text="COM Port", bg="#A3C19F").grid(row=2, column=2, padx=5, pady=5)
available_ports = get_com_ports()
com_port_dropdown = ttk.Combobox(frame, values=available_ports if available_ports else ["No Ports"], state="readonly", width=10)
com_port_dropdown.grid(row=2, column=1, padx=5, pady=5)
com_port_dropdown.set(available_ports[0] if available_ports else "No Ports")

# Baud Rate Dropdown
tk.Label(frame, text="BAUD Rate", bg="#A3C19F").grid(row=3, column=2, padx=5, pady=5)
baud_rate_dropdown = ttk.Combobox(frame, values=[9600, 19200, 38400, 57600, 115200], state="readonly", width=10)
baud_rate_dropdown.grid(row=3, column=1, padx=5, pady=5)
baud_rate_dropdown.set(9600)

# Connect Button
connect_button = tk.Button(frame, text="Connect", bg="green", fg="white", font=("Arial", 10, "bold"), command=connect_to_plc)
connect_button.grid(row=3, column=0, padx=5, pady=5)

# Rx String Label
tk.Label(frame, text="Rx String", bg="#A3C19F", font=("Arial", 10, "bold")).grid(row=4, column=0, columnspan=2, sticky="w")

# Textbox for results
rx_textbox = tk.Text(frame, height=10, width=50)
rx_textbox.grid(row=5, column=0, columnspan=3, padx=5, pady=5)

# Initially disable test button
test_button.config(state="disabled")

# Run the GUI
root.mainloop()
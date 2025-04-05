import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import serial.tools.list_ports

class VisionInspectionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Vision Inspection System")
        self.root.state('zoomed')  # Make it full screen
        
        # Initialize PLC connection attributes
        self.modbus_client = None
        
        # Configure main background
        self.root.configure(bg='#f0f0f0')
        
        # Create header
        self.create_header()
        
        # Create PLC connection panel
        self.create_plc_panel()
        
        # Top Panel for Image Thumbnails
        self.thumbnail_frame = tk.Frame(root, height=100, bg="#e8f6e9")
        self.thumbnail_frame.pack(fill=tk.X, padx=10, pady=5)
        self.load_thumbnails()
        
        # Main Image Display Panel
        self.image_frame = tk.Frame(root, bg='#f0f0f0')
        self.image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.canvas = tk.Canvas(self.image_frame, bg="#2c3e50")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bottom Panel for OK/NG Buttons
        self.result_frame = tk.Frame(root, bg='#f0f0f0')
        self.result_frame.pack(fill=tk.X, padx=10, pady=5)
        self.load_result_panel()
        
        # Load default image
        self.load_image("sample.jpg")  # Change to an actual image path

    def create_header(self):
        """Create header with title and border lines"""
        header_frame = tk.Frame(self.root, bg='#f0f0f0')
        header_frame.pack(fill=tk.X, padx=5)
        
        # Top border line
        tk.Canvas(header_frame, height=2, bg='#2c3e50').pack(fill=tk.X)
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="VISION INSPECTION SYSTEM",
            bg='#f0f0f0',
            fg='#2c3e50',
            font=('Arial', 28, 'bold')
        )
        title_label.pack(pady=10)
        
        # Bottom border line
        tk.Canvas(header_frame, height=2, bg='#2c3e50').pack(fill=tk.X)

    def create_plc_panel(self):
        """Create PLC connection controls"""
        plc_frame = tk.Frame(self.root, bg='#f0f0f0')
        plc_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Create a titled border frame for PLC controls
        control_frame = tk.LabelFrame(
            plc_frame, 
            text="PLC Connection",
            bg='#f0f0f0',
            font=('Arial', 10, 'bold'),
            pady=5
        )
        control_frame.pack(side=tk.LEFT)
        
        # COM Port selection
        tk.Label(
            control_frame,
            text="COM Port:",
            bg='#f0f0f0',
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=5)
        
        self.plc_com_combo = ttk.Combobox(control_frame, width=10)
        self.plc_com_combo['values'] = [port.device for port in serial.tools.list_ports.comports()]
        self.plc_com_combo.pack(side=tk.LEFT, padx=5)
        
        # Baud Rate selection
        tk.Label(
            control_frame,
            text="Baud Rate:",
            bg='#f0f0f0',
            font=('Arial', 10)
        ).pack(side=tk.LEFT, padx=5)
        
        self.plc_baud_combo = ttk.Combobox(control_frame, width=8)
        self.plc_baud_combo['values'] = [9600, 19200, 38400, 57600, 115200]
        self.plc_baud_combo.set(9600)  # Set default value
        self.plc_baud_combo.pack(side=tk.LEFT, padx=5)
        
        # Connect button
        self.connect_btn = tk.Button(
            control_frame, 
            text="Connect PLC",
            command=self.connect_plc,
            bg='#3498db',
            fg='white',
            font=('Arial', 10, 'bold'),
            width=12
        )
        self.connect_btn.pack(side=tk.LEFT, padx=10)

    def load_thumbnails(self):
        """Create image thumbnail buttons"""
        for i in range(5):
            btn = tk.Button(
                self.thumbnail_frame,
                text=f"Image {i+1}",
                command=lambda i=i: self.load_image(f"image_{i+1}.jpg"),
                bg='#3498db',
                fg='white',
                font=('Arial', 10),
                width=12
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)
    
    def load_image(self, filepath):
        """Load and display an image"""
        try:
            image = Image.open(filepath)
            image = image.resize((800, 600), Image.Resampling.LANCZOS)  # Updated from ANTIALIAS
            self.tk_image = ImageTk.PhotoImage(image)
            self.canvas.create_image(
                self.canvas.winfo_width()//2,
                self.canvas.winfo_height()//2,
                image=self.tk_image
            )
            self.draw_annotations()
        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {str(e)}")
    
    def draw_annotations(self):
        """Draw inspection annotations on the image"""
        self.canvas.create_rectangle(100, 50, 200, 100, outline="red", width=2)
        self.canvas.create_rectangle(120, 150, 180, 200, outline="green", width=2)
    
    def load_result_panel(self):
        """Create inspection result buttons"""
        for i in range(3):
            frame = tk.Frame(self.result_frame, bg='#f0f0f0', pady=5)
            frame.pack(fill=tk.X)
            
            label = tk.Label(
                frame,
                text=f"Checkpoint {i+1}",
                font=("Arial", 12),
                bg='#f0f0f0'
            )
            label.pack(side=tk.LEFT, padx=10)
            
            btn_ng = tk.Button(
                frame,
                text="NG",
                bg="#e74c3c",
                fg="white",
                width=8,
                font=('Arial', 10, 'bold')
            )
            btn_ng.pack(side=tk.RIGHT, padx=5)
            
            btn_ok = tk.Button(
                frame,
                text="OK",
                bg="#2ecc71",
                fg="white",
                width=8,
                font=('Arial', 10, 'bold')
            )
            btn_ok.pack(side=tk.RIGHT, padx=5)

    def connect_plc(self):
        """Establish Modbus RTU connection to PLC"""
        try:
            # Close existing connection if any
            if self.modbus_client and self.modbus_client.is_socket_open():
                self.modbus_client.close()
            
            # Create new Modbus RTU client
            self.modbus_client = ModbusSerialClient(
                port=self.plc_com_combo.get(),
                baudrate=int(self.plc_baud_combo.get()),
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1
            )
            
            # Try to connect
            if self.modbus_client.connect():
                # Test communication by reading first register
                result = self.modbus_client.read_holding_registers(
                    address=0,
                    count=1,
                    slave=1
                )
                if result.isError():
                    raise ModbusException("Failed to read from PLC")
                    
                messagebox.showinfo("Success", "Successfully connected to PLC!")
                self.connect_btn.configure(bg='#2ecc71', text='Connected')
                return True
            else:
                raise ModbusException("Failed to connect to PLC")
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to PLC!\nError: {str(e)}")
            if self.modbus_client:
                self.modbus_client.close()
            self.connect_btn.configure(bg='#e74c3c', text='Connect PLC')
            return False

def main():
    root = tk.Tk()
    app = VisionInspectionGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 
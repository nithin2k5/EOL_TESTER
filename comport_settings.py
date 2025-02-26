import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error

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
        for i in range(1, 3):  # Only creating 2 loadcells
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
        
        tk.Button(top_frame, text="TEST", bg='darkred', fg='white', 
                 width=8, font=('Arial', 9, 'bold')).pack(side='left', padx=5)
        tk.Label(top_frame, text="Station ID", bg=frame['bg'], fg='black').pack(side='left', padx=5)
        tk.Entry(top_frame, width=15).pack(side='left', padx=5)
        
        # COM Port
        tk.Label(frame, text="COM Port", bg=frame['bg'], fg='black').pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # BAUD Rate
        tk.Label(frame, text="BAUD Rate", bg=frame['bg'], fg='black').pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # Rx String
        tk.Label(frame, text="Rx String", bg=frame['bg'], fg='black').pack(anchor='w', padx=5, pady=2)
        tk.Text(frame, height=10, width=30).pack(padx=5, pady=5)

    def add_loadcell_content(self, frame):
        # Test button
        tk.Button(frame, text="TEST", bg='darkred', fg='white', 
                 width=8, font=('Arial', 9, 'bold')).pack(anchor='w', padx=5, pady=5)
        
        # COM Port
        tk.Label(frame, text="COM Port", bg=frame['bg'], fg='black').pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # BAUD Rate
        tk.Label(frame, text="BAUD Rate", bg=frame['bg'], fg='black').pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # Rx String
        tk.Label(frame, text="Rx String", bg=frame['bg'], fg='black').pack(anchor='w', padx=5, pady=2)
        tk.Text(frame, height=8, width=25).pack(padx=5, pady=5)
        
        # Relay entries
        for i in range(1, 5):
            relay_frame = tk.Frame(frame, bg=frame['bg'])
            relay_frame.pack(fill='x', padx=5, pady=2)
            
            tk.Label(relay_frame, text=f"Relay - {i:02d}", 
                    bg=frame['bg'], fg='black', width=10, anchor='w').pack(side='left')
            tk.Entry(relay_frame, width=25).pack(side='left', padx=5)

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
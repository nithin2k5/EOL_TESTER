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
        self.root.configure(bg='white')
        
        # Header with border lines
        header_frame = tk.Frame(self.root, bg='white')
        header_frame.pack(fill=tk.X, padx=5)
        
        # Top border line
        tk.Canvas(header_frame, height=2, bg='black').pack(fill=tk.X)
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="COM PORT SETTINGS",
            bg='white',
            fg='black',
            font=('Arial', 28, 'bold')
        )
        title_label.pack(pady=10)
        
        # Bottom border line
        tk.Canvas(header_frame, height=2, bg='black').pack(fill=tk.X)

        # Top row frame
        top_row = tk.Frame(self.root, bg='black')
        top_row.pack(fill=tk.X, padx=5, pady=5)

        # LVDT Section (Pink background)
        lvdt_frame = tk.Frame(top_row, bg='#FFB6C1', relief='solid', borderwidth=1)  # Light pink
        lvdt_frame.pack(side=tk.LEFT, padx=5, fill=tk.BOTH)
        
        # LVDT Title
        tk.Label(lvdt_frame, text="LVDT (P01 - P04)", bg='#FFB6C1', fg='black',
                font=('Arial', 10, 'bold')).pack(anchor='w', padx=5, pady=2)
        
        self.add_lvdt_content(lvdt_frame)

        # CAM Sections (Yellow background)
        for i in range(1, 3):
            cam_frame = tk.Frame(top_row, bg='#FFFFE0', relief='solid', borderwidth=1)  # Light yellow
            cam_frame.pack(side=tk.LEFT, padx=5, fill=tk.BOTH)
            
            tk.Label(cam_frame, text=f"CAM - {i:02d}", bg='#FFFFE0', fg='black',
                    font=('Arial', 10, 'bold')).pack(anchor='w', padx=5, pady=2)
            
            self.add_cam_content(cam_frame)

        # Right side controls
        control_frame = tk.Frame(top_row, bg='white')
        control_frame.pack(side=tk.LEFT, padx=5)
        
        # Screen size with up/down arrows
        size_frame = tk.Frame(control_frame, bg='white', relief='solid', borderwidth=1)
        size_frame.pack(fill=tk.X, pady=2)
        
        tk.Label(size_frame, text="SCREEN SIZE:", bg='white', fg='black',
                font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        screen_entry = tk.Entry(size_frame, width=5, justify='right')
        screen_entry.insert(0, "0.0")
        screen_entry.pack(side=tk.LEFT)
        
        arrows = tk.Label(size_frame, text="▲\n▼", bg='white', fg='black')
        arrows.pack(side=tk.LEFT)

        # Control buttons
        buttons = [
            ("EDIT", 'black', 'white'),
            ("SAVE", 'black', 'white'),
            ("RESET", 'black', 'white')
        ]
        
        for text, bg, fg in buttons:
            btn = tk.Button(control_frame, text=text, bg=bg, fg=fg, 
                          width=10, font=('Arial', 10, 'bold'))
            btn.pack(pady=2)

        # Bottom row frames
        bottom_frame = tk.Frame(self.root, bg='black')
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # PLC Section (Green background)
        plc_frame = self.create_section(
            bottom_frame, "PLC", '#90EE90',  # Light green
            width=300, height=300
        )
        plc_frame.pack(side=tk.LEFT, padx=5)
        self.add_plc_content(plc_frame)

        # Loadcell Sections (Brown background)
        for i in range(1, 5):
            loadcell_frame = self.create_section(
                bottom_frame, f"LOADCELL - {i:02d} (L{i})", '#DEB887',  # Burlywood
                width=250, height=300
            )
            loadcell_frame.pack(side=tk.LEFT, padx=5)
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

    def add_lvdt_content(self, frame):
        # COM Port
        tk.Label(frame, text="COM Port", bg=frame['bg'], fg='black').pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # BAUD Rate
        tk.Label(frame, text="BAUD Rate", bg=frame['bg'], fg='black').pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # P01-P04 entries
        labels = [
            "P01 (Shift Conduit)",
            "P02 (Shift Inner)",
            "P03 (Select Conduit)",
            "P04 (Select Inner)"
        ]
        
        for label in labels:
            tk.Label(frame, text=label, bg=frame['bg'], fg='black').pack(anchor='w', padx=5, pady=2)
            entry_frame = tk.Frame(frame, bg=frame['bg'])
            entry_frame.pack(anchor='w', fill='x', padx=5)
            
            tk.Entry(entry_frame, width=25).pack(side='left')
            tk.Label(entry_frame, text="mm", bg=frame['bg'], fg='black').pack(side='left', padx=5)

    def add_cam_content(self, frame):
        # COM Port
        tk.Label(frame, text="COM Port", bg=frame['bg'], fg='black').pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # BAUD Rate
        tk.Label(frame, text="BAUD Rate", bg=frame['bg'], fg='black').pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # Text area
        text_area = tk.Text(frame, height=8, width=25)
        text_area.pack(padx=5, pady=5)

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
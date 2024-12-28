import tkinter as tk
from tkinter import ttk

class ComPortSettings:
    def __init__(self, root):
        self.root = root
        self.root.title("COM Port Settings")
        
        # Make it full screen
        self.root.state('zoomed')
        
        # Configure the main background color
        self.root.configure(bg='lightblue')
        
        self.setup_ui()

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg='lightblue', height=60)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        title_label = tk.Label(
            header_frame, 
            text="COM PORT SETTINGS",
            bg='lightblue',
            font=('Arial', 24, 'bold')
        )
        title_label.pack(expand=True)

        # Main content frame
        content_frame = tk.Frame(self.root, bg='lightblue')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Top row frames
        top_frame = tk.Frame(content_frame, bg='lightblue')
        top_frame.pack(fill=tk.X, pady=5)

        # LVDT Section (Pink)
        lvdt_frame = self.create_section(
            top_frame, "LVDT (P01 - P04)", 'pink', 
            width=300, height=250
        )
        lvdt_frame.pack(side=tk.LEFT, padx=5)

        self.add_lvdt_content(lvdt_frame)

        # CAM Sections (Yellow)
        for i in range(1, 3):
            cam_frame = self.create_section(
                top_frame, f"CAM - {i:02d}", 'khaki',
                width=250, height=250
            )
            cam_frame.pack(side=tk.LEFT, padx=5)
            
            self.add_cam_content(cam_frame)

        # Screen size and buttons
        control_frame = tk.Frame(top_frame, bg='lightblue')
        control_frame.pack(side=tk.LEFT, padx=5, fill=tk.BOTH)
        
        # Screen size
        size_frame = tk.Frame(control_frame, bg='white')
        size_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(size_frame, text="SCREEN SIZE:", bg='white').pack(side=tk.LEFT, padx=5)
        screen_entry = tk.Entry(size_frame, width=5)
        screen_entry.pack(side=tk.LEFT)
        tk.Label(size_frame, text="▲\n▼", bg='white').pack(side=tk.LEFT)

        # Control buttons
        buttons = [
            ("EDIT", 'navy', 'white'),
            ("SAVE", 'green', 'white'),
            ("RESET", 'red', 'white')
        ]
        
        for text, bg, fg in buttons:
            btn = tk.Button(control_frame, text=text, bg=bg, fg=fg, width=15)
            btn.pack(pady=5)

        # Bottom row frames
        bottom_frame = tk.Frame(content_frame, bg='lightblue')
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # PLC Section (Green)
        plc_frame = self.create_section(
            bottom_frame, "PLC", 'lightgreen',
            width=300, height=300
        )
        plc_frame.pack(side=tk.LEFT, padx=5)
        
        self.add_plc_content(plc_frame)

        # Loadcell Sections (Light Brown)
        for i in range(1, 5):
            loadcell_frame = self.create_section(
                bottom_frame, f"LOADCELL - {i:02d} (L{i})", 'rosybrown',
                width=250, height=300
            )
            loadcell_frame.pack(side=tk.LEFT, padx=5)
            
            self.add_loadcell_content(loadcell_frame)

        # Footer
        footer = tk.Label(
            self.root,
            text="Powered By: IRACRAT TECHNOLOGIES. Contact: INFO@IRACRAT.COM, (+91) 99623 44614.",
            bg='lightblue',
            font=('Arial', 8)
        )
        footer.pack(side=tk.BOTTOM, pady=5)

    def create_section(self, parent, title, bg_color, width, height):
        frame = tk.Frame(parent, bg=bg_color, width=width, height=height, relief='solid', borderwidth=1)
        frame.pack_propagate(False)
        return frame

    def add_lvdt_content(self, frame):
        # COM Port
        tk.Label(frame, text="COM Port", bg=frame['bg']).pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # BAUD Rate
        tk.Label(frame, text="BAUD Rate", bg=frame['bg']).pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # P01-P04 entries
        labels = [
            "P01 (Shift Conduit)",
            "P02 (Shift Inner)",
            "P03 (Select Conduit)",
            "P04 (Select Inner)"
        ]
        
        for label in labels:
            tk.Label(frame, text=label, bg=frame['bg']).pack(anchor='w', padx=5, pady=2)
            entry_frame = tk.Frame(frame, bg=frame['bg'])
            entry_frame.pack(anchor='w', fill='x', padx=5)
            
            tk.Entry(entry_frame, width=25).pack(side='left')
            tk.Label(entry_frame, text="mm", bg=frame['bg']).pack(side='left', padx=5)

    def add_cam_content(self, frame):
        # COM Port
        tk.Label(frame, text="COM Port", bg=frame['bg']).pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # BAUD Rate
        tk.Label(frame, text="BAUD Rate", bg=frame['bg']).pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # Text area
        text_area = tk.Text(frame, height=8, width=25)
        text_area.pack(padx=5, pady=5)

    def add_plc_content(self, frame):
        # Test button and Station ID
        top_frame = tk.Frame(frame, bg=frame['bg'])
        top_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Button(top_frame, text="TEST", bg='darkred', fg='white', width=8).pack(side='left', padx=5)
        tk.Label(top_frame, text="Station ID", bg=frame['bg']).pack(side='left', padx=5)
        tk.Entry(top_frame, width=15).pack(side='left', padx=5)
        
        # COM Port
        tk.Label(frame, text="COM Port", bg=frame['bg']).pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # BAUD Rate
        tk.Label(frame, text="BAUD Rate", bg=frame['bg']).pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # Rx String
        tk.Label(frame, text="Rx String", bg=frame['bg']).pack(anchor='w', padx=5, pady=2)
        tk.Text(frame, height=10, width=30).pack(padx=5, pady=5)

    def add_loadcell_content(self, frame):
        # Test button
        tk.Button(frame, text="TEST", bg='darkred', fg='white', width=8).pack(anchor='w', padx=5, pady=5)
        
        # COM Port
        tk.Label(frame, text="COM Port", bg=frame['bg']).pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # BAUD Rate
        tk.Label(frame, text="BAUD Rate", bg=frame['bg']).pack(anchor='w', padx=5, pady=2)
        ttk.Combobox(frame, width=25).pack(anchor='w', padx=5)
        
        # Rx String
        tk.Label(frame, text="Rx String", bg=frame['bg']).pack(anchor='w', padx=5, pady=2)
        tk.Text(frame, height=8, width=25).pack(padx=5, pady=5)
        
        # Relay entries
        for i in range(1, 5):
            tk.Label(frame, text=f"Relay - {i:02d}", bg=frame['bg']).pack(anchor='w', padx=5, pady=2)
            tk.Entry(frame, width=25).pack(anchor='w', padx=5)

def main():
    root = tk.Tk()
    app = ComPortSettings(root)
    root.mainloop()

if __name__ == "__main__":
    main()
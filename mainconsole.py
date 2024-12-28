import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os

class MainConsole(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EOL Tester")
        self.setup_ui()
        
    def setup_ui(self):
        # Create toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=5, pady=5)
        
        # Create toolbar buttons
        self.btn_com_settings = ttk.Button(toolbar, text="COM Port Settings", command=self.com_port_settings_click)
        self.btn_settings = ttk.Button(toolbar, text="Settings", command=self.settings_click)
        self.btn_test = ttk.Button(toolbar, text="Test", command=self.test_click)
        self.btn_work_data = ttk.Button(toolbar, text="Work Data", command=self.work_data_click)
        self.btn_admin = ttk.Button(toolbar, text="Admin", command=self.admin_click)
        self.btn_exit = ttk.Button(toolbar, text="Exit", command=self.exit_click)
        
        # Pack toolbar buttons
        for btn in (self.btn_com_settings, self.btn_settings, self.btn_test, 
                   self.btn_work_data, self.btn_admin, self.btn_exit):
            btn.pack(side="left", padx=2)
            
        # Create menu
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Manual", command=self.user_manual_click)
        help_menu.add_command(label="Support", command=self.support_click)
        
        self.load_settings()
        
    def load_settings(self):
        """Load application settings and validate machine ID"""
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        try:
            machine_id = config.get('DEFAULT', 'MACHINE_ID', fallback=None)
            valid_machine_id = machine_id is not None and len(machine_id) == 3
        except:
            valid_machine_id = False
            
        # Enable/disable buttons based on machine ID validation
        for btn in (self.btn_com_settings, self.btn_settings, 
                   self.btn_test, self.btn_work_data):
            btn.config(state='normal' if valid_machine_id else 'disabled')
            
    def com_port_settings_click(self):
        self.withdraw()  # Hide main window
        try:
            com_settings = COMPortSettings()
            com_settings.mainloop()
        finally:
            self.deiconify()  # Show main window again
            
    def settings_click(self):
        self.withdraw()
        try:
            model_settings = ModelSettings()
            model_settings.mainloop()
        finally:
            self.deiconify()
            
    def test_click(self):
        self.withdraw()
        try:
            test_console = TestConsole()
            test_console.mainloop()
        finally:
            self.deiconify()
            
    def work_data_click(self):
        self.withdraw()
        try:
            data_console = DataConsole()
            data_console.mainloop()
        finally:
            self.deiconify()
            
    def admin_click(self):
        self.withdraw()
        try:
            admin_console = AdminConsole()
            admin_console.mainloop()
            self.load_settings()  # Reload settings after admin console closes
        finally:
            self.deiconify()
            
    def user_manual_click(self):
        messagebox.showinfo("Info", "User Manual coming soon...")
        
    def support_click(self):
        support_info = SupportInfo()
        support_info.mainloop()
        
    def exit_click(self):
        self.quit()

# These would be defined in separate files
class COMPortSettings(tk.Toplevel): pass
class ModelSettings(tk.Toplevel): pass
class TestConsole(tk.Toplevel): pass
class DataConsole(tk.Toplevel): pass
class AdminConsole(tk.Toplevel): pass
class SupportInfo(tk.Toplevel): pass

if __name__ == "__main__":
    app = MainConsole()
    app.mainloop()
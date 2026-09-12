import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os
from model_settings import WorkspaceApp  # Import ModelSettings
from test_console import EOLTesterGUI    # Import TestConsole
from comport_settings import ComPortSettings  # Add this import
from dataconsole import DataConsole  # Add this import
from adminconsole import AdminConsole  # Add this import
from login_form import prompt_login
import theme

class MainConsole(tk.Tk):
    def __init__(self):
        super().__init__()
        theme.apply_professional_theme(self)
        self.title("EOL Tester")
        self.state('zoomed')  # Start maximized
        self.setup_ui()
        
    def setup_ui(self):
        # Set the main window to full screen
        self.state('zoomed')
        
        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        
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
        # Remove the machine ID validation since we want all buttons enabled
        for btn in (self.btn_com_settings, self.btn_settings, 
                   self.btn_test, self.btn_work_data, self.btn_admin):
            btn.config(state='normal')
            
    def com_port_settings_click(self):
        settings_window = tk.Toplevel(self)
        # Set the window to full screen
        settings_window.state('zoomed')
        settings_window.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        app = ComPortSettings(settings_window)
        settings_window.grab_set()
        self.withdraw()
        
        def on_settings_close():
            settings_window.destroy()
            self.deiconify()
            
        settings_window.protocol("WM_DELETE_WINDOW", on_settings_close)
            
    def settings_click(self):
        user = prompt_login(self)
        if user is None:
            return

        settings_window = tk.Toplevel(self)
        # Set the window to full screen
        settings_window.state('zoomed')
        settings_window.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        app = WorkspaceApp(settings_window, user=user)
        settings_window.grab_set()
        self.withdraw()
        
        def on_settings_close():
            settings_window.destroy()
            self.deiconify()
            
        settings_window.protocol("WM_DELETE_WINDOW", on_settings_close)
            
    def test_click(self):
        # Create a test window
        test_window = tk.Toplevel(self)
        test_window.title("EOL Tester - Test Console")
        
        # Set the window to full screen
        test_window.state('zoomed')
        test_window.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        
        # Try to ensure any existing COM port connections are released
        import serial
        import time
        import os
        
        try:
            # Attempt to force-release COM ports before creating new instance
            plc_port = os.getenv('PLC_COM_PORT')
            if plc_port:
                try:
                    # Try direct port open/close to force release
                    cleanup_serial = serial.Serial(plc_port)
                    cleanup_serial.close()
                    print(f"MainConsole: Successfully released {plc_port} before opening test console")
                    # Allow time for port to fully release
                    time.sleep(1)
                except Exception as e:
                    print(f"MainConsole: COM port {plc_port} is busy: {e}")
        except Exception as e:
            print(f"Error pre-cleaning COM ports: {e}")
        
        # Create the test console app with the window
        app = EOLTesterGUI(test_window)
        test_window.grab_set()
        self.withdraw()
        
        def on_test_close():
            try:
                # Ensure app cleanup is called first
                if hasattr(app, 'cleanup'):
                    app.cleanup()
                
                # Additional delay to ensure cleanup completes
                time.sleep(0.5)
                
                # Force an additional cleanup of COM ports
                try:
                    plc_port = os.getenv('PLC_COM_PORT')
                    if plc_port:
                        try:
                            cleanup_serial = serial.Serial(plc_port)
                            cleanup_serial.close()
                            print(f"MainConsole: Successfully released {plc_port} after closing test console")
                        except Exception as e:
                            print(f"MainConsole: Error releasing {plc_port}: {e}")
                except Exception as e:
                    print(f"Error in final COM port cleanup: {e}")
                
                # Destroy window and show main console
                test_window.destroy()
                self.deiconify()
                
            except Exception as e:
                print(f"Error during test console cleanup: {e}")
                test_window.destroy()
                self.deiconify()
            
        test_window.protocol("WM_DELETE_WINDOW", on_test_close)
            
    def work_data_click(self):
        # Open work data window
        work_data_window = tk.Toplevel(self)
        work_data_window.title("Work Data")
        
        # Set the window to full screen
        work_data_window.state('zoomed')
        work_data_window.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        app = DataConsole(work_data_window)
        work_data_window.grab_set()
        self.withdraw()
        
        def on_work_data_close():
            work_data_window.destroy()
            self.deiconify()
            
        work_data_window.protocol("WM_DELETE_WINDOW", on_work_data_close)
        
    def admin_click(self):
        if prompt_login(self) is None:
            return

        admin_window = tk.Toplevel(self)
        
        # Set the window to full screen
        admin_window.state('zoomed')
        admin_window.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        app = AdminConsole(admin_window)
        admin_window.grab_set()
        self.withdraw()
        
        def on_admin_close():
            admin_window.destroy()
            self.deiconify()
            
        admin_window.protocol("WM_DELETE_WINDOW", on_admin_close)

    def user_manual_click(self):
        messagebox.showinfo("User Manual", "User manual functionality will be implemented here.")

    def support_click(self):
        messagebox.showinfo("Support", "For technical support, please contact:\n\nEmail: support@company.com\nPhone: +1-800-SUPPORT\n\nFor immediate assistance, refer to the User Manual.")

    def exit_click(self):
        self.quit()

if __name__ == "__main__":
    app = MainConsole()
    app.mainloop()
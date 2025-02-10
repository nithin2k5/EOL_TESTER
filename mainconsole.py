import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import os
from model_settings import WorkspaceApp  # Import ModelSettings
from test_console import EOLTesterGUI    # Import TestConsole
from comport_settings import ComPortSettings  # Add this import
from dataconsole import DataConsole  # Add this import
from adminconsole import AdminConsole  # Add this import
# Add this import


class MainConsole(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EOL Tester")
        self.state('zoomed')  # Start maximized
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
        # Remove the machine ID validation since we want all buttons enabled
        for btn in (self.btn_com_settings, self.btn_settings, 
                   self.btn_test, self.btn_work_data, self.btn_admin):
            btn.config(state='normal')
            
    def com_port_settings_click(self):
        settings_window = tk.Toplevel(self)
        settings_window.state('zoomed')  # Make it full screen
        app = ComPortSettings(settings_window)
        settings_window.grab_set()  # Make the window modal
        self.withdraw()  # Hide main window
        
        def on_settings_close():
            settings_window.destroy()
            self.deiconify()  # Show main window again
            
        settings_window.protocol("WM_DELETE_WINDOW", on_settings_close)
            
    def settings_click(self):
        settings_window = tk.Toplevel(self)
        settings_window.state('zoomed')  # Make it full screen
        app = WorkspaceApp(settings_window)
        settings_window.grab_set()  # Make the window modal
        self.withdraw()  # Hide main window
        
        def on_settings_close():
            settings_window.destroy()
            self.deiconify()  # Show main window again
            
        settings_window.protocol("WM_DELETE_WINDOW", on_settings_close)
            
    def test_click(self):
        test_window = tk.Toplevel(self)
        test_window.state('zoomed')  # Make it full screen
        app = EOLTesterGUI(test_window)
        test_window.grab_set()  # Make the window modal
        self.withdraw()  # Hide main window
        
        def on_test_close():
            test_window.destroy()
            self.deiconify()  # Show main window again
            
        test_window.protocol("WM_DELETE_WINDOW", on_test_close)
            
    def work_data_click(self):
        # Open work data window
        work_data_window = tk.Toplevel(self)
        work_data_window.title("Work Data")
        # Add your work data window content here
        
    def admin_click(self):
        admin_window = tk.Toplevel(self)
        admin_window.state('zoomed')  # Make it full screen
        app = AdminConsole(admin_window)
        admin_window.grab_set()  # Make the window modal
        self.withdraw()  # Hide main window
        
        def on_admin_close():
            admin_window.destroy()
            self.deiconify()  # Show main window again
            
        admin_window.protocol("WM_DELETE_WINDOW", on_admin_close)

    def user_manual_click(self):
        messagebox.showinfo("User Manual", "User manual functionality will be implemented here.")

    def support_click(self):
        support_window = tk.Toplevel(self)
        support_window.state('zoomed')  # Make it full screen
        app = SupportInfo(support_window)
        support_window.grab_set()  # Make the window modal
        self.withdraw()  # Hide main window
        
        def on_support_close():
            support_window.destroy()
            self.deiconify()  # Show main window again
            
        support_window.protocol("WM_DELETE_WINDOW", on_support_close)

    def exit_click(self):
        self.quit()

if __name__ == "__main__":
    app = MainConsole()
    app.mainloop()
import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import csv
import os
from datetime import datetime
from model_settings import WorkspaceApp  # Import ModelSettings
from test_console import EOLTesterGUI    # Import TestConsole
from comport_settings import ComPortSettings  # Add this import
from dataconsole import DataConsole  # Add this import
from adminconsole import AdminConsole  # Add this import
from login_form import prompt_login
import config
import db
import theme

class MainConsole(tk.Tk):
    # Records older than this are written out to the archive folders.
    ARCHIVE_AFTER_DAYS = 120
    # Warn when the last test on this machine is older than this.
    STALE_TEST_WARNING_DAYS = 2

    def __init__(self):
        super().__init__()
        theme.apply_professional_theme(self)
        db.init_database()
        self.title("EOL Tester")
        self.state('zoomed')  # Start maximized

        # A clock behind the last recorded test would misdate new results.
        if not self.check_last_test_date():
            self.destroy()
            return

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
        
    def check_last_test_date(self):
        """Compare the clock against the last recorded test.

        Returns False when the machine should not be used - the system date
        is behind the last test, which would misdate everything saved next.
        """
        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DATEDIFF(CURDATE(), MAX(TEST_DAY_DATE))
                FROM TBL_PART_RUNNING_SERIAL
            """)
            row = cursor.fetchone()
            cursor.close()
            conn.close()
        except Exception as e:
            # A machine that cannot reach the database has bigger problems,
            # but it should not be stopped from opening the console.
            print(f"Could not check the last test date: {e}")
            return True

        if not row or row[0] is None:
            return True  # nothing tested yet

        days = int(row[0])

        if days < 0:
            messagebox.showerror(
                "System Date Incorrect",
                "The SYSTEM Date is incorrect. Please consult Line Supervisor "
                "and Line Quality Incharge. The Application will close now."
            )
            return False

        if days > self.STALE_TEST_WARNING_DAYS:
            messagebox.showwarning(
                "Old Test Data",
                f"The Last Test Date is more than {self.STALE_TEST_WARNING_DAYS} "
                "days older. Please consult Line Supervisor and Line Quality "
                "Incharge before you proceed with the Testing."
            )

        return True

    def archive_folders(self):
        """The two configured archive folders, when both exist on disk."""
        first = config.get('PRIMARY_BACKUP_PATH', '')
        second = config.get('SECONDARY_BACKUP_PATH', '')

        if not first or not second:
            return None
        if not os.path.isdir(first) or not os.path.isdir(second):
            return None
        return [first, second]

    def load_settings(self):
        """Enable the consoles once the machine is configured for testing."""
        machine_id = config.get('MACHINE_ID', '')
        folders = self.archive_folders()
        ready = bool(machine_id) and folders is not None

        for btn in (self.btn_com_settings, self.btn_settings,
                    self.btn_test, self.btn_work_data):
            btn.config(state='normal' if ready else 'disabled')

        # Admin stays reachable, since that is where the machine ID and the
        # archive folders are set in the first place.
        self.btn_admin.config(state='normal')

        if not ready:
            missing = []
            if not machine_id:
                missing.append("Machine ID")
            if folders is None:
                missing.append("both archive folders")
            self.after(300, lambda: messagebox.showwarning(
                "Setup Incomplete",
                "Testing is disabled until these are set in the Admin console:\n\n"
                + "\n".join(f"  - {item}" for item in missing)
            ))
            return

        # Let the window paint before touching the database.
        self.after(300, self.archive_old_data)

    def archive_old_data(self):
        """Write records older than the retention window out to both folders."""
        folders = self.archive_folders()
        if folders is None:
            return

        try:
            conn = db.connect()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM TBL_TEST_DATA
                WHERE TD_DATETIME < DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """, (self.ARCHIVE_AFTER_DAYS,))
            count = cursor.fetchone()[0] or 0

            if count == 0:
                cursor.close()
                conn.close()
                return

            cursor.execute("""
                SELECT * FROM TBL_TEST_DATA
                WHERE TD_DATETIME < DATE_SUB(CURDATE(), INTERVAL %s DAY)
                ORDER BY ID
            """, (self.ARCHIVE_AFTER_DAYS,))
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Could not read records for archiving: {e}")
            return

        messagebox.showinfo(
            "Archive",
            f"There are {count} records older than {self.ARCHIVE_AFTER_DAYS} days."
        )

        written = self.export_to_csv(columns, rows, folders)
        if written:
            messagebox.showinfo(
                "Archive",
                "Archived {} records to:\n\n{}".format(count, "\n".join(written))
            )

    def export_to_csv(self, columns, rows, folders):
        """Write the rows to one CSV per archive folder; returns the paths written."""
        file_name = "{}_Archive_{}.csv".format(
            config.get('MACHINE_ID', 'MACHINE'),
            datetime.now().strftime("%m%d%Y_%I%M%S%p"))

        written = []
        for folder in folders:
            path = os.path.join(folder, file_name)
            try:
                with open(path, 'w', newline='', encoding='utf-8') as handle:
                    writer = csv.writer(handle)
                    writer.writerow([column.upper() for column in columns])
                    for row in rows:
                        writer.writerow(['' if value is None else value for value in row])
                written.append(path)
            except OSError as e:
                # One unreachable folder should not lose the other copy.
                print(f"Could not write archive to {folder}: {e}")
                messagebox.showwarning(
                    "Archive",
                    f"Could not write the archive to:\n{path}\n\n{e}"
                )

        return written

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
            plc_port = config.get('PLC_COM_PORT')
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
                    plc_port = config.get('PLC_COM_PORT')
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
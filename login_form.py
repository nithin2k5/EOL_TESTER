"""Employee login dialog used to gate the Settings and Admin consoles."""

import tkinter as tk
from tkinter import ttk, messagebox

import mysql.connector

import auth
import config
import db

# Employee number of the support account, whose password lives in .env as a
# hash rather than in the EMPLOYEE_INFO table. It is checked before the table
# is consulted, so it works even when EMPLOYEE_INFO has no row for it - which
# is the point, since it is what gets you in when the table is the problem.
SERVICE_ACCOUNT_USER = config.get('SERVICE_ACCOUNT_USER', '')
SERVICE_ACCOUNT_PASSWORD_HASH = config.get('SERVICE_ACCOUNT_PASSWORD_HASH', '')


class LoginForm(tk.Toplevel):
    """Modal dialog asking for an employee number and password.

    After the dialog closes, ``authenticated`` says whether the login
    succeeded and ``user_name`` holds the employee number that was used.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.authenticated = False
        self.user_name = None
        self._passwords = {}   # employee number -> stored password value

        machine_id = config.get('MACHINE_ID', '')
        title = "Login"
        if machine_id:
            title += f" - Machine ID: {machine_id}"
        self.title(title)
        self.resizable(False, False)

        self.db_config = db.get_config()

        self.setup_ui()

        if not self.load_employees():
            self.destroy()
            return

        self.protocol("WM_DELETE_WINDOW", self.cancel_click)
        self.bind('<Escape>', lambda event: self.cancel_click())
        self.center_on_parent(parent)

        self.transient(parent)
        self.grab_set()
        self.txt_employee.focus_set()

    def setup_ui(self):
        container = ttk.Frame(self, padding=20)
        container.pack(fill='both', expand=True)

        header = ttk.Label(container, text="EMPLOYEE LOGIN", font=('Arial', 14, 'bold'))
        header.grid(row=0, column=0, columnspan=2, pady=(0, 15))

        ttk.Label(container, text="Employee Number :").grid(row=1, column=0, sticky='w', pady=5)
        self.employee_var = tk.StringVar()
        self.employee_var.trace_add('write', self.input_changed)
        self.txt_employee = ttk.Entry(container, width=35, textvariable=self.employee_var)
        self.txt_employee.grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=5)
        self.txt_employee.bind('<Return>', lambda event: self.txt_password.focus_set())

        ttk.Label(container, text="Password :").grid(row=2, column=0, sticky='w', pady=5)
        self.password_var = tk.StringVar()
        self.password_var.trace_add('write', self.input_changed)
        self.txt_password = ttk.Entry(container, show='*', width=35,
                                      textvariable=self.password_var)
        self.txt_password.grid(row=2, column=1, sticky='ew', padx=(10, 0), pady=5)
        self.txt_password.bind('<Return>', lambda event: self.enter_click())

        buttons = ttk.Frame(container)
        buttons.grid(row=3, column=0, columnspan=2, pady=(20, 0))

        self.btn_enter = ttk.Button(buttons, text="Enter", width=12,
                                    command=self.enter_click, state='disabled')
        self.btn_enter.pack(side='left', padx=5)

        ttk.Button(buttons, text="Cancel", width=12,
                   command=self.cancel_click).pack(side='left', padx=5)

    def center_on_parent(self, parent):
        """Place the dialog in the middle of its parent, or of the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()

        if parent is not None and parent.winfo_viewable():
            x = parent.winfo_rootx() + (parent.winfo_width() - width) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
        else:
            x = (self.winfo_screenwidth() - width) // 2
            y = (self.winfo_screenheight() - height) // 2

        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def load_employees(self):
        """Pre-load active employees into memory. False means database is unreachable."""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EMPLOYEE_NUMBER, PASSWORD
                FROM EMPLOYEE_INFO
                WHERE IS_ACTIVE = TRUE
            """)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error",
                                 f"Failed to load employee list: {err}", parent=self)
            return False

        for number, password in rows:
            self._passwords[number] = password

        if not self._passwords and not SERVICE_ACCOUNT_USER:
            messagebox.showwarning("Login",
                                   "There are no active employees to log in with.",
                                   parent=self)
            return False

        return True

    def input_changed(self, *args):
        has_employee = len(self.employee_var.get().strip()) > 0
        has_password = len(self.password_var.get().strip()) > 0
        self.btn_enter.config(state='normal' if (has_employee and has_password) else 'disabled')

    def selected_employee_number(self):
        return self.employee_var.get().strip()

    def stored_password_for(self, employee_number):
        """The value to check against, taking the service account into account."""
        if SERVICE_ACCOUNT_USER and employee_number == SERVICE_ACCOUNT_USER:
            return SERVICE_ACCOUNT_PASSWORD_HASH
        return self._passwords.get(employee_number)

    def enter_click(self):
        if str(self.btn_enter['state']) == 'disabled':
            return

        employee_number = self.selected_employee_number()
        if not employee_number:
            return

        stored_password = self.stored_password_for(employee_number)

        if stored_password and auth.verify_password(self.password_var.get(), stored_password):
            self.authenticated = True
            self.user_name = employee_number
            self.grab_release()
            self.destroy()
        else:
            messagebox.showerror("INVALID LOGIN",
                                 "Invalid Employee Number or Password!!", parent=self)
            self.password_var.set('')
            self.txt_password.focus_set()

    def cancel_click(self):
        self.authenticated = False
        self.user_name = None
        self.grab_release()
        self.destroy()


def prompt_login(parent=None):
    """Show the login dialog and return the employee number, or None if it failed."""
    dialog = LoginForm(parent)
    if not dialog.winfo_exists():
        # The dialog closed itself because no login is possible.
        return None

    dialog.wait_window()
    return dialog.user_name if dialog.authenticated else None

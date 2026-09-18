import tkinter as tk
from tkinter import ttk, messagebox
import configparser
import csv
import os
import time
from datetime import datetime

import serial
from model_settings import WorkspaceApp  # Import ModelSettings
from test_console import EOLTesterGUI    # Import TestConsole
from comport_settings import ComPortSettings  # Add this import
from dataconsole import DataConsole  # Add this import
from adminconsole import AdminConsole  # Add this import
from login_form import prompt_login
import config
import db
import ui


class PageFrame(tk.Frame):
    """A panel a console can be built into as though it were its own window.

    Each console was written to own a top level window: it names itself,
    maximises itself and registers a WM_DELETE_WINDOW handler. Hosted in a
    panel those calls have nowhere to go, so they are answered here - the
    title goes to the shell's window, the close handler is kept for the
    shell to call when the page is replaced, and the rest are dropped.
    """

    def __init__(self, master, shell, **kwargs):
        super().__init__(master, **kwargs)
        self.shell = shell
        self.close_handler = None

    def title(self, text=None):
        if text is None:
            return self.shell.wm_title()
        self.shell.wm_title(text)

    def protocol(self, name, callback=None):
        if name == 'WM_DELETE_WINDOW' and callback is not None:
            self.close_handler = callback
        return ''

    # A panel already fills the side of the window it was handed, so there
    # is nothing here to maximise, raise above other windows or resize.
    def state(self, *args):
        return 'normal'

    def attributes(self, *args):
        return ''

    def geometry(self, *args):
        return ''

    def resizable(self, *args):
        return ''

    def destroy(self):
        # A console closing itself through root.destroy(): the shell cannot
        # be left holding a panel that is no longer on screen.
        shell = self.shell
        super().destroy()
        if shell is not None:
            shell.page_closed(self)


class NavButton(tk.Frame):
    """One entry in the navigation rail: an icon above its label.

    A button takes a single font, and at this width the rail needs a large
    glyph over small text, so this is a frame that behaves like one.
    """

    ICON_FONT = (ui.FONT_FAMILY, 17)
    LABEL_FONT = (ui.FONT_FAMILY, 8, 'bold')

    def __init__(self, master, icon, label, command):
        super().__init__(master, bg=ui.ACCENT)
        self.command = command
        self.enabled = True

        self.icon = tk.Label(self, text=icon, bg=ui.ACCENT,
                             font=self.ICON_FONT)
        self.icon.pack(pady=(ui.PAD, 0))

        self.label = tk.Label(self, text=label, bg=ui.ACCENT,
                              font=self.LABEL_FONT, justify='center')
        self.label.pack(pady=(1, ui.PAD), padx=2)

        for part in self.parts():
            part.bind('<Button-1>', self.clicked)
            part.bind('<Enter>', self.entered)
            part.bind('<Leave>', self.left)

        self.set_enabled(True)

    def parts(self):
        return (self, self.icon, self.label)

    def paint(self, background):
        for part in self.parts():
            # ui gives every one of these readable text for the background
            # it is handed, so the icon and label follow along on their own.
            part.config(bg=background)

    def set_enabled(self, enabled):
        """Stand in for the `state` option a real button would take."""
        self.enabled = enabled
        self.paint(ui.ACCENT if enabled else ui.mix(ui.ACCENT, ui.SURFACE, 0.65))
        for part in self.parts():
            part.config(cursor='hand2' if enabled else 'arrow')

    def fit(self, width):
        """Wrap the label to the width the rail actually got."""
        self.label.config(wraplength=max(width, 40))

    def clicked(self, event=None):
        if self.enabled:
            self.command()

    def entered(self, event=None):
        if self.enabled:
            self.paint(ui.ACCENT_HOVER)

    def left(self, event=None):
        self.set_enabled(self.enabled)


class MainConsole(tk.Tk):
    # Records older than this are written out to the archive folders.
    ARCHIVE_AFTER_DAYS = 120
    # Warn when the last test on this machine is older than this.
    STALE_TEST_WARNING_DAYS = 2
    # Share of the window width given to the side navigation.
    NAV_SHARE = 0.05

    def __init__(self):
        super().__init__()
        ui.apply(self)
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
        
        # Compact: the rail and the page below want the height more
        # than a display-sized title does.
        ui.page_header(self, "EOL Tester", self.machine_label(), compact=True)

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True)

        # A tenth of the width to the navigation, the rest to the page. The
        # uniform group is what makes grid share the width out by weight;
        # without it each column would take whatever its content asked for,
        # and the consoles ask for a great deal.
        nav_weight = round(self.NAV_SHARE * 100)
        body.grid_columnconfigure(0, weight=nav_weight, uniform='shell')
        body.grid_columnconfigure(1, weight=100 - nav_weight, uniform='shell')
        body.grid_rowconfigure(0, weight=1)

        self.build_side_nav(body).grid(row=0, column=0, sticky="nsew")

        # Pages are built in here. Propagation is off so that a console laid
        # out wider than its share cannot push the navigation off the window.
        self.page_host = ttk.Frame(body, width=1, height=1)
        self.page_host.grid(row=0, column=1, sticky="nsew")
        self.page_host.pack_propagate(False)

        self.page = None
        self.page_app = None
        self.page_closed_hook = None
        self.placeholder = ttk.Label(
            self.page_host, anchor="center", style='Muted.TLabel',
            text="Choose a console from the navigation on the left.")
        self.show_placeholder()

        # Create menu
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Manual", command=self.user_manual_click)
        help_menu.add_command(label="Support", command=self.support_click)

        # Closing the window has to take the open page with it, or the test
        # console's serial threads and COM ports are left behind.
        self.protocol("WM_DELETE_WINDOW", self.exit_click)

        self.load_settings()

    def machine_label(self):
        machine_id = config.get('MACHINE_ID', '')
        return f"Machine ID: {machine_id}" if machine_id else ''

    def build_side_nav(self, parent):
        """The left-hand navigation rail.

        Each entry is one row of a single grid column, so they line up on
        both edges and stay the same size whatever their label says.
        """
        nav = tk.Frame(parent, bg=ui.SURFACE, highlightbackground=ui.BORDER,
                       highlightthickness=1, width=1)
        # The column's width comes from the weights on the body, so the frame
        # must not ask for a width of its own: grid honours the widest child,
        # which would pull the column back open past its share.
        nav.grid_propagate(False)
        nav.grid_columnconfigure(0, weight=1)

        entries = (
            ('btn_com_settings', "\u21c4", "COM Ports", self.com_port_settings_click),
            ('btn_settings', "\u2699", "Settings", self.settings_click),
            ('btn_test', "\u25b6", "Test", self.test_click),
            ('btn_work_data', "\u25a4", "Work Data", self.work_data_click),
            ('btn_admin', "\u26ca", "Admin", self.admin_click),
        )

        self.nav_buttons = []
        for row, (attribute, icon, label, command) in enumerate(entries):
            button = self.nav_button(nav, icon, label, command)
            button.grid(row=row, column=0, sticky="ew", padx=3, pady=(3, 0))
            setattr(self, attribute, button)

        # Exit sits apart at the foot of the rail, so it is never clicked by
        # someone reaching for the console above it.
        gap = len(entries)
        nav.grid_rowconfigure(gap, weight=1)

        self.btn_exit = self.nav_button(nav, "\u23fb", "Exit", self.exit_click)
        self.btn_exit.grid(row=gap + 1, column=0, sticky="ew", padx=3, pady=3)

        nav.bind('<Configure>', self.fit_nav_labels)
        return nav

    def nav_button(self, nav, icon, label, command):
        button = NavButton(nav, icon, label, command)
        self.nav_buttons.append(button)
        return button

    def fit_nav_labels(self, event):
        """Wrap the labels to whatever width the rail actually got."""
        for button in self.nav_buttons:
            button.fit(event.width - 4 * ui.PAD)

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
            btn.set_enabled(ready)

        # Admin stays reachable, since that is where the machine ID and the
        # archive folders are set in the first place.
        self.btn_admin.set_enabled(True)

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
        self.after(300, self.start_testing)

    def start_testing(self):
        """Do the start-up housekeeping, then open the test console.

        Testing is what the machine is for, so the application opens straight
        into that page instead of waiting for the operator to press Test.
        """
        self.archive_old_data()
        self.test_click()

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

    def shell_is_alive(self):
        """False once the window and its panel are being torn down.

        Closing the window destroys its children one at a time, so the panel
        can still be there when the placeholder inside it has already gone.
        """
        try:
            return bool(self.page_host.winfo_exists()
                        and self.placeholder.winfo_exists())
        except tk.TclError:
            return False

    def show_placeholder(self):
        """What the page panel shows while no console is open."""
        if self.shell_is_alive():
            self.placeholder.pack(fill="both", expand=True)

    def open_page(self, title, build, on_closed=None):
        """Build one console into the page panel, replacing what is there.

        `build` is handed the panel and returns the console instance, and
        `on_closed` runs once that page has been torn down again.
        """
        self.close_page()
        self.placeholder.pack_forget()

        page = PageFrame(self.page_host, self, bg=ui.APP_BG)
        page.pack(fill="both", expand=True)
        self.page = page
        self.wm_title(f"EOL Tester - {title}")

        try:
            self.page_app = build(page)
        except Exception as e:
            print(f"Could not open the {title} page: {e}")
            self.page = None
            self.page_app = None
            page.shell = None  # half built, so nothing to report back
            page.destroy()
            self.wm_title("EOL Tester")
            self.show_placeholder()
            messagebox.showerror(
                "EOL Tester",
                "The {} page could not be opened.\n\n{}".format(title, e))
            return False

        self.page_closed_hook = on_closed
        return True

    def close_page(self):
        """Tear down the page on show, if there is one."""
        page, app, hook = self.page, self.page_app, self.page_closed_hook
        self.page = None
        self.page_app = None
        self.page_closed_hook = None

        if page is None:
            return

        # The console registered a close handler to release its ports and
        # stop its threads, so let it close by the path it expects.
        handler = page.close_handler
        if handler is not None:
            try:
                handler()
            except Exception as e:
                print(f"Error closing the page: {e}")
        elif app is not None and hasattr(app, 'cleanup'):
            try:
                app.cleanup()
            except Exception as e:
                print(f"Error cleaning up the page: {e}")

        if page.winfo_exists():
            page.shell = None  # already being torn down here
            page.destroy()

        self.wm_title("EOL Tester")
        self.show_placeholder()
        self.run_closed_hook(hook)

    def page_closed(self, page):
        """A console that has just destroyed its own panel."""
        if page is not self.page:
            return  # already on its way out through close_page

        self.page = None
        self.page_app = None
        hook, self.page_closed_hook = self.page_closed_hook, None

        # Closing the window destroys its children too, and that comes
        # through here; there is then no panel left to put anything back in.
        if self.shell_is_alive():
            self.wm_title("EOL Tester")
            self.show_placeholder()

        # The hook releases the PLC port, so it runs either way.
        self.run_closed_hook(hook)

    def run_closed_hook(self, hook):
        if hook is None:
            return
        try:
            hook()
        except Exception as e:
            print(f"Error after closing the page: {e}")

    def release_plc_port(self, when):
        """Force the PLC port shut, so the next connection can have it."""
        port = config.get('PLC_COM_PORT')
        if not port:
            return

        try:
            handle = serial.Serial(port)
            handle.close()
            print(f"MainConsole: released {port} {when}")
            # The port needs a moment before it can be opened again.
            time.sleep(1)
        except Exception as e:
            print(f"MainConsole: {port} is busy {when}: {e}")

    def com_port_settings_click(self):
        self.open_page("COM Port Settings", ComPortSettings)

    def settings_click(self):
        # Ask before tearing down the open page, so a cancelled login
        # leaves the operator on whatever they were already looking at.
        user = prompt_login(self)
        if user is None:
            return

        self.open_page("Model Settings",
                       lambda page: WorkspaceApp(page, user=user))

    def test_click(self):
        self.open_page(
            "Test Console", self.build_test_console,
            on_closed=lambda: self.release_plc_port("after closing the test console"))

    def build_test_console(self, page):
        # A port left open by an earlier run would refuse to connect.
        self.release_plc_port("before opening the test console")
        return EOLTesterGUI(page)

    def work_data_click(self):
        self.open_page("Work Data", DataConsole)

    def admin_click(self):
        if prompt_login(self) is None:
            return

        self.open_page("Admin", AdminConsole)

    def user_manual_click(self):
        messagebox.showinfo("User Manual", "User manual functionality will be implemented here.")

    def support_click(self):
        messagebox.showinfo("Support", "For technical support, please contact:\n\nEmail: support@company.com\nPhone: +1-800-SUPPORT\n\nFor immediate assistance, refer to the User Manual.")

    def exit_click(self):
        self.close_page()
        self.quit()

if __name__ == "__main__":
    app = MainConsole()
    app.mainloop()
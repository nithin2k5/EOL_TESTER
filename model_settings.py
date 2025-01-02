import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import os
from datetime import datetime

class ModelSettings(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Model Settings")
        self.geometry("800x600")
        
        self.part_labels_list = []
        self.used_plc_addresses = []
        self.program_selection_array = []
        self.barcode_print_file_names_array = []
        
        self.action = None
        self.selected_part_number = None
        self.user = "TestUser"  # Placeholder for user
        
        self.plc_address_data = []
        self.barcode_print_file_names_data = []
        
        # Define the directory path for text files
        self.text_files_path = "/Users/nithink/Developer/python/EOL_TESTER/txt_files"  # Update this path
        
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # Create GUI components
        self.lbl_mac_id = tk.Label(self, text="Machine ID: ")
        self.lbl_mac_id.pack(pady=5)
        
        self.cb_plc_address = ttk.Combobox(self)
        self.cb_plc_address.pack(pady=5)
        
        self.cb_print_file_list = ttk.Combobox(self)
        self.cb_print_file_list.pack(pady=5)
        
        self.txt_part_number = tk.Entry(self)
        self.txt_part_number.pack(pady=5)
        
        self.txt_model_name = tk.Entry(self)
        self.txt_model_name.pack(pady=5)
        
        self.txt_alc = tk.Entry(self)
        self.txt_alc.pack(pady=5)
        
        self.txt_image_file_path = tk.Entry(self)
        self.txt_image_file_path.pack(pady=5)
        
        self.btn_browse = tk.Button(self, text="Browse", command=self.browse_image)
        self.btn_browse.pack(pady=5)
        
        self.btn_new_part = tk.Button(self, text="New Part", command=self.new_part)
        self.btn_new_part.pack(pady=5)
        
        self.btn_save = tk.Button(self, text="Save", command=self.save_data)
        self.btn_save.pack(pady=5)
        
        self.btn_edit = tk.Button(self, text="Edit", command=self.edit_data)
        self.btn_edit.pack(pady=5)
        
        self.btn_delete = tk.Button(self, text="Delete", command=self.delete_data)
        self.btn_delete.pack(pady=5)
        
        self.dGV_parts = ttk.Treeview(self, columns=("Part Number", "Model Name", "ALC Code"), show="headings")
        self.dGV_parts.heading("Part Number", text="Part Number")
        self.dGV_parts.heading("Model Name", text="Model Name")
        self.dGV_parts.heading("ALC Code", text="ALC Code")
        self.dGV_parts.pack(pady=5, fill=tk.BOTH, expand=True)
        
        self.dGV_parts.bind("<ButtonRelease-1>", self.on_part_select)

    def load_data(self):
        # Load data from files or database
        self.load_barcode_print_file_names_list()
        self.load_plc_addresses_combo()
        self.load_part_labels()
        self.display_parts()

    def load_barcode_print_file_names_list(self):
        # Load barcode print file names
        try:
            file_path = os.path.join(self.text_files_path, "BarcodePrintFileNames.txt")
            with open(file_path, "r") as file:
                barcode_print_file_names = file.read()
                if barcode_print_file_names:
                    self.barcode_print_file_names_array = barcode_print_file_names.split(',')
                    self.barcode_print_file_names_data = [(" - - Select Barcode Print File Name ", "0")]
                    for item in self.barcode_print_file_names_array:
                        if item not in self.barcode_print_file_names_data:
                            self.barcode_print_file_names_data.append((item, item))
                    self.cb_print_file_list['values'] = [item[0] for item in self.barcode_print_file_names_data]
                    self.cb_print_file_list.current(0)
                else:
                    messagebox.showwarning("Warning", "Barcode Print File Names text file is either missing or empty!")
        except FileNotFoundError:
            messagebox.showerror("Error", "Barcode Print File Names text file not found!")

    def load_plc_addresses_combo(self):
        # Load PLC addresses
        try:
            file_path = os.path.join(self.text_files_path, "ProgramSelectionInPLC.txt")
            with open(file_path, "r") as file:
                program_selection = file.read()
                if program_selection:
                    self.program_selection_array = program_selection.split(',')
                    self.plc_address_data = [(" - - Select PLC Address ", "0")]
                    for item in self.program_selection_array:
                        if item not in self.used_plc_addresses:
                            self.plc_address_data.append((item, item))
                    self.cb_plc_address['values'] = [item[0] for item in self.plc_address_data]
                    self.cb_plc_address.current(0)
                else:
                    messagebox.showwarning("Warning", "Program Selection text file is either missing or empty!")
        except FileNotFoundError:
            messagebox.showerror("Error", "Program Selection text file not found!")

    def load_part_labels(self):
        # Load part labels
        try:
            file_path = os.path.join(self.text_files_path, "partlabels.txt")
            with open(file_path, "r") as file:
                part_labels = file.read()
                if self.label_validation(part_labels):
                    part_labels_array = part_labels.split(',')
                    self.part_labels_list.clear()
                    for i, part_label in enumerate(part_labels_array):
                        self.part_labels_list.append(part_label)
                        # Additional logic to handle part labels
                else:
                    messagebox.showwarning("Warning", "Please verify and correct the Part Labels text file and then relaunch the settings screen...")
        except FileNotFoundError:
            messagebox.showerror("Error", "Part Labels text file not found!")

    def label_validation(self, part_labels):
        # Validate part labels
        if part_labels:
            part_labels_array = part_labels.split(',')
            if len(part_labels_array) == 16 and len(part_labels_array) == len(set(part_labels_array)):
                if all(len(label.strip()) == 3 for label in part_labels_array):
                    return True
                else:
                    messagebox.showwarning("Warning", "All Label Names in Part Labels text file MUST BE ONLY 3 CHARACTERS long.")
            else:
                messagebox.showwarning("Warning", "Part Labels text file MUST CONTAIN exactly 16 comma separated label names and MUST NOT end with any character - comma, full stop, etc...")
        else:
            messagebox.showwarning("Warning", "Part Labels text file is either missing or empty!!")
        return False

    def browse_image(self):
        # Browse for image file
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if file_path:
            self.txt_image_file_path.delete(0, tk.END)
            self.txt_image_file_path.insert(0, file_path)

    def new_part(self):
        # New part action
        self.action = "ADD"
        self.enable_components(self.action)
        self.clear_form()

    def save_data(self):
        # Save data to database
        if self.validate_part_details():
            conn = sqlite3.connect('eol_tester.db')
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS TBL_MODEL_MASTER (MM_PART_NUMBER TEXT, MM_MODEL_NAME TEXT, MM_ALC_CODE TEXT, MM_PLC_ADDRESS TEXT, MM_BARCODE_PRN_FILE_NAME TEXT, MM_IMAGE_PATH TEXT, MM_VENDOR_CODE TEXT, MM_EO_NUMBER TEXT, MM_SPECIAL_DATA TEXT, MM_INITIAL_ID TEXT, MM_SUPPLIER_SECTION TEXT, MM_CREATED_BY TEXT, MM_CREATED_DATE TEXT, MM_MODIFIED_BY TEXT, MM_MODIFIED_DATE TEXT, MM_STATUS INTEGER)")
            if self.action == "ADD":
                if not self.is_part_or_alc_exists():
                    cursor.execute("INSERT INTO TBL_MODEL_MASTER (MM_PART_NUMBER, MM_MODEL_NAME, MM_ALC_CODE, MM_PLC_ADDRESS, MM_BARCODE_PRN_FILE_NAME, MM_IMAGE_PATH, MM_VENDOR_CODE, MM_EO_NUMBER, MM_SPECIAL_DATA, MM_INITIAL_ID, MM_SUPPLIER_SECTION, MM_CREATED_BY, MM_CREATED_DATE, MM_MODIFIED_BY, MM_MODIFIED_DATE, MM_STATUS) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                   (self.txt_part_number.get(), self.txt_model_name.get(), self.txt_alc.get().upper(), self.cb_plc_address.get(), self.cb_print_file_list.get(), self.txt_image_file_path.get(), "", "", "", "", "", self.user, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.user, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 1))
                    conn.commit()
                    messagebox.showinfo("Success", "Record Inserted Successfully")
                else:
                    messagebox.showwarning("Warning", "Part Number/ALC Code already exists in the database")
            elif self.action == "EDIT":
                cursor.execute("UPDATE TBL_MODEL_MASTER SET MM_MODEL_NAME = ?, MM_PLC_ADDRESS = ?, MM_BARCODE_PRN_FILE_NAME = ?, MM_IMAGE_PATH = ?, MM_VENDOR_CODE = ?, MM_EO_NUMBER = ?, MM_SPECIAL_DATA = ?, MM_INITIAL_ID = ?, MM_SUPPLIER_SECTION = ?, MM_MODIFIED_BY = ?, MM_MODIFIED_DATE = ? WHERE MM_PART_NUMBER = ?",
                               (self.txt_model_name.get(), self.cb_plc_address.get(), self.cb_print_file_list.get(), self.txt_image_file_path.get(), "", "", "", "", "", self.user, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.txt_part_number.get()))
                conn.commit()
                messagebox.showinfo("Success", "Record Updated Successfully")
            conn.close()
            self.display_parts()
            self.disable_components()
            self.clear_form()

    def edit_data(self):
        # Edit data action
        self.action = "EDIT"
        self.enable_components(self.action)

    def delete_data(self):
        # Delete data from database
        if self.selected_part_number:
            result = messagebox.askokcancel("Confirm Deletion", f"Are you sure, you want to delete {self.selected_part_number} Part Number from the database?")
            if result:
                conn = sqlite3.connect('eol_tester.db')
                cursor = conn.cursor()
                cursor.execute("UPDATE TBL_MODEL_MASTER SET MM_STATUS = 0 WHERE MM_PART_NUMBER = ?", (self.selected_part_number,))
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", "Record Deleted Successfully")
                self.display_parts()
                self.clear_form()

    def on_part_select(self, event):
        # Handle part selection from Treeview
        selected_item = self.dGV_parts.selection()
        if selected_item:
            item = self.dGV_parts.item(selected_item)
            self.selected_part_number = item['values'][0]
            self.txt_part_number.delete(0, tk.END)
            self.txt_part_number.insert(0, item['values'][0])
            self.txt_model_name.delete(0, tk.END)
            self.txt_model_name.insert(0, item['values'][1])
            self.txt_alc.delete(0, tk.END)
            self.txt_alc.insert(0, item['values'][2])
            self.disable_components()

    def enable_components(self, action):
        # Enable components based on action
        if action == "ADD":
            self.txt_part_number.config(state=tk.NORMAL)
            self.txt_model_name.config(state=tk.NORMAL)
            self.txt_alc.config(state=tk.NORMAL)
            self.cb_print_file_list.config(state=tk.NORMAL)
            self.cb_plc_address.config(state=tk.NORMAL)
            self.btn_save.config(state=tk.NORMAL)
            self.btn_edit.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)
        elif action == "EDIT":
            self.txt_model_name.config(state=tk.NORMAL)
            self.cb_print_file_list.config(state=tk.NORMAL)
            self.cb_plc_address.config(state=tk.NORMAL)
            self.btn_save.config(state=tk.NORMAL)
            self.btn_edit.config(state=tk.DISABLED)
            self.btn_delete.config(state=tk.DISABLED)

    def disable_components(self):
        # Disable components
        self.txt_part_number.config(state=tk.DISABLED)
        self.txt_model_name.config(state=tk.DISABLED)
        self.txt_alc.config(state=tk.DISABLED)
        self.cb_print_file_list.config(state=tk.DISABLED)
        self.cb_plc_address.config(state=tk.DISABLED)
        self.btn_save.config(state=tk.DISABLED)
        self.btn_edit.config(state=tk.NORMAL)
        self.btn_delete.config(state=tk.NORMAL)

    def clear_form(self):
        # Clear form fields
        self.txt_part_number.delete(0, tk.END)
        self.txt_model_name.delete(0, tk.END)
        self.txt_alc.delete(0, tk.END)
        self.txt_image_file_path.delete(0, tk.END)
        self.cb_print_file_list.current(0)
        self.cb_plc_address.current(0)

    def validate_part_details(self):
        # Validate part details
        if not self.txt_part_number.get() or not self.txt_model_name.get() or not self.txt_alc.get() or not self.txt_image_file_path.get() or self.cb_plc_address.current() < 1 or self.cb_print_file_list.current() < 1:
            messagebox.showwarning("Warning", "Please make sure all details are properly filled under Part Details section...")
            return False
        return True

    def is_part_or_alc_exists(self):
        # Check if part number or ALC code exists
        conn = sqlite3.connect('eol_tester.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM TBL_MODEL_MASTER")
        rows = cursor.fetchall()
        conn.close()
        part_number_exists = any(row[0].upper() == self.txt_part_number.get().upper() for row in rows)
        alc_exists = any(row[2].upper() == self.txt_alc.get().upper() for row in rows)
        return part_number_exists or alc_exists

    def display_parts(self):
        # Display parts in Treeview
        self.dGV_parts.delete(*self.dGV_parts.get_children())
        conn = sqlite3.connect('eol_tester.db')
        cursor = conn.cursor()
        cursor.execute("SELECT MM_PART_NUMBER, MM_MODEL_NAME, MM_ALC_CODE FROM TBL_MODEL_MASTER WHERE MM_STATUS = 1")
        rows = cursor.fetchall()
        for row in rows:
            self.dGV_parts.insert("", tk.END, values=row)
        conn.close()

if __name__ == "__main__":
    app = ModelSettings()
    app.mainloop()        
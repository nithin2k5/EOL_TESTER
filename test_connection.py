import tkinter as tk
from tkinter import ttk
import mysql.connector

class SpecificationManager:
    def __init__(self, root):
        self.root = root
        self.setup_ui()

    def setup_ui(self):
        # Create entry widgets for specification input
        self.spec_entries = [tk.Entry(self.root) for _ in range(7)]  # Adjust the range for the number of fields
        for entry in self.spec_entries:
            entry.pack(pady=5)

        # Create Treeview widget
        self.spec_tree = ttk.Treeview(self.root, columns=("Description", "Device", "Unit", "Master Min", "Master Max", "Normal Min", "Normal Max"), show='headings')
        self.spec_tree.heading("Description", text="Description")
        self.spec_tree.heading("Device", text="Device")
        self.spec_tree.heading("Unit", text="Unit")
        self.spec_tree.heading("Master Min", text="Master Min")
        self.spec_tree.heading("Master Max", text="Master Max")
        self.spec_tree.heading("Normal Min", text="Normal Min")
        self.spec_tree.heading("Normal Max", text="Normal Max")
        self.spec_tree.pack(pady=10)

        # Create buttons
        self.create_buttons()

    def create_buttons(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="ADD", bg="green", fg="white", width=10,
                  command=lambda: self.insert_specification(self.spec_entries, self.spec_tree)).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="REMOVE", bg="red", fg="white", width=10,
                  command=lambda: self.remove_specification(self.spec_tree)).pack(side=tk.LEFT, padx=5)

    def insert_specification(self, spec_entries, spec_tree):
        # Collect data from entry widgets
        spec_data = [entry.get() for entry in spec_entries]
        
        # Check if all fields are filled
        if all(spec_data):
            # Insert data into the treeview
            spec_tree.insert("", "end", values=spec_data)
            
            # Insert data into the database
            try:
                conn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="nk446420",
                    database="EOL"
                )
                cursor = conn.cursor()
                
                query = """
                INSERT INTO TBL_MODEL_SPECIFICATIONS 
                (MS_DESCRIPTION, MS_DEVICE, MS_UNIT, MS_MASTER_MIN, MS_MASTER_MAX, MS_NORMAL_MIN, MS_NORMAL_MAX)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, spec_data)
                conn.commit()
                cursor.close()
                conn.close()
                
                # New message box after successful insertion
                tk.messagebox.showinfo("Success", "Specification added successfully!")
            except mysql.connector.Error as err:
                print(f"Error: {err}")
            
            # Clear the entry fields after insertion
            for entry in spec_entries:
                entry.delete(0, tk.END)
        else:
            print("Please fill all fields before adding a specification.")

    def remove_specification(self, spec_tree):
        # Get selected item
        selected_item = spec_tree.selection()
        if selected_item:
            # Remove the selected item
            spec_tree.delete(selected_item)
        else:
            print("Please select a specification to remove.")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Specification Manager")
    root.geometry("600x400")
    app = SpecificationManager(root)
    root.mainloop()
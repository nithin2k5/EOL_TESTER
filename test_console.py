import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import mysql.connector
from pynput import keyboard
import threading
import json

class EOLTesterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EOL (END OF LINE) TESTER")
        
        # Set window to full screen
        self.root.attributes('-fullscreen', True)  # Change from state('zoomed') to true fullscreen
        
        # Add escape key binding to exit fullscreen
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        
        # Initialize variables
        self.image_label = None
        self.current_image = None
        self.label_positions = {}
        self.selected_label = None
        self.barcode_data = ""
        self.label_widgets = {}
        
        self.setup_gui()
        self.setup_barcode_listener()

    def setup_gui(self):
        # Main container
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)

        # Add message label for status updates
        self.message_label = tk.Label(self.main_container, text="", font=("Arial", 10))
        self.message_label.pack(fill="x", pady=2)
        
        # Title bar with INFAC logo
        self.create_title_bar()
        
        # Main workspace
        self.workspace = tk.Frame(self.main_container)
        self.workspace.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Force the workspace to update its geometry
        self.root.update_idletasks()
        
        # Create quadrants
        self.create_quadrants()
        
        # Footer
        self.create_footer()

    def create_title_bar(self):
        title_frame = tk.Frame(self.main_container, bg="#FFB6C1", height=40)
        title_frame.pack(fill="x")
        
        # INFAC Logo (left side)
        logo_label = tk.Label(title_frame, text="INFAC\nINDIA", 
                            bg="#FFB6C1", font=("Arial", 10, "bold"))
        logo_label.pack(side="left", padx=10)
        
        # Title (center)
        title_label = tk.Label(title_frame, text="EOL (END OF LINE) TESTER",
                             font=("Arial", 16, "bold"), bg="#FFB6C1")
        title_label.pack(pady=5)

    def create_quadrants(self):
        """Update the create_quadrants method to remove borders"""
        # Configure grid weights for equal space
        self.workspace.grid_columnconfigure(0, weight=1)  # First column
        self.workspace.grid_columnconfigure(1, weight=1)  # Second column
        self.workspace.grid_rowconfigure(0, weight=1)     # First row
        self.workspace.grid_rowconfigure(1, weight=1)     # Second row
        
        # Create quadrants without borders
        self.q1 = self.create_first_quadrant()
        self.q2 = self.create_second_quadrant()
        self.q3 = self.create_third_quadrant()
        self.q4 = self.create_fourth_quadrant()
        
        # Place quadrants with minimal spacing
        self.q1.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        self.q2.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
        self.q3.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)
        self.q4.grid(row=1, column=1, sticky="nsew", padx=1, pady=1)
        
        # Prevent resizing
        for quadrant in [self.q1, self.q2, self.q3, self.q4]:
            quadrant.grid_propagate(False)

    def create_first_quadrant(self):
        """Create the image display quadrant with correct dimensions."""
        q1 = tk.Frame(self.workspace)
        
        # Create header frame at the top
        header_frame = tk.Frame(q1, bg="#00BFFF", height=30)
        header_frame.pack(fill="x", side="top")
        
        # Add header label
        self.model_header = tk.Label(header_frame, 
                                    text="MODEL - PART NUMBER",
                                    bg="#00BFFF",
                                    font=("Arial", 12, "bold"))
        self.model_header.pack(pady=2)
        
        # Create a frame to hold the image with specific dimensions
        self.image_frame = tk.Frame(q1, bg='white')
        self.image_frame.pack(fill="both", expand=True, padx=0, pady=0)
        self.image_frame.pack_propagate(False)
        
        # Set size for the image frame - increasing width to 550 while keeping height at 300
        self.image_frame.config(width=527, height=340)
        
        # Create initial placeholder
        self.image_label = tk.Label(self.image_frame, 
                                   text="No image loaded",
                                   bg='white',
                                   font=('Arial', 12))
        self.image_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # Create bottom frame for status and label info
        bottom_frame = tk.Frame(q1, height=60, bg='white')
        bottom_frame.pack(fill="x", side="bottom")
        bottom_frame.pack_propagate(False)
        
        # Create status frame
        status_frame = tk.Frame(bottom_frame, bg="white")
        status_frame.pack(fill="x", pady=2)
        
        # Add HOME and AUTO status labels
        status_labels = ['HOME', 'AUTO', '1st PULL', '2nd PULL', 'TEST']
        for label_text in status_labels:
            label = tk.Label(status_frame,
                            text=label_text,
                            bg=self.get_status_label_color(label_text),
                            fg="white",
                            font=("Arial", 10, "bold"),
                            width=15,height=15,
                            relief="raised",
                            borderwidth=2)
            label.pack(side="left", padx=5,pady=5)
        
        # Add label info text
        self.label_info = tk.Label(bottom_frame,
                                  text="Placed Labels: None",
                                  bg='white',
                                  font=('Arial', 10))
        self.label_info.pack(pady=2)
        
        return q1

    def create_second_quadrant(self):
        """Create the specifications display quadrant."""
        q2 = tk.Frame(self.workspace, relief="groove", borderwidth=1)
        
        # Add header
        header = tk.Label(q2, text="TEST SPECIFICATIONS",
                         bg="#00BFFF", fg="black",
                         font=("Arial", 12, "bold"))
        header.pack(fill="x")
        
        # Create specifications table with numbered ID
        columns = (
            "Description",
            "Device",
            "Unit",
            "Min",
            "Max",
            "Actual",
            "Result"
        )
        self.spec_tree = ttk.Treeview(q2, columns=columns, show="headings", height=10)
        
        # Configure columns with specific widths
        column_widths = {
            "Description": 200,
            "Device": 100,
            "Unit": 80,
            "Min": 50,
            "Max": 50,
            "Acutal": 50,
            "Result": 50
        }
        
        # Set up each column
        for col in columns:
            self.spec_tree.heading(col, text=col)
            self.spec_tree.column(col, width=column_widths.get(col, 100), anchor='center')
        
        # Add scrollbars
        scrollbar = ttk.Scrollbar(q2, orient="vertical", command=self.spec_tree.yview)
        self.spec_tree.configure(yscrollcommand=scrollbar.set)
        
        h_scrollbar = ttk.Scrollbar(q2, orient="horizontal", command=self.spec_tree.xview)
        self.spec_tree.configure(xscrollcommand=h_scrollbar.set)
        
        # Pack the treeview and scrollbars
        self.spec_tree.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        
        return q2

    def create_third_quadrant(self):
        q3 = tk.Frame(self.workspace, relief="groove", borderwidth=1)
        
        # Add graph area directly without the labels
        self.create_graph_area(q3)
        
        return q3

    def create_fourth_quadrant(self):
        q4 = tk.Frame(self.workspace)
        
        # Header with gradient effect - reduced height to 30
        header_frame = tk.Frame(q4, bg="#1e88e5", height=30)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        columns = ["LOT NUMBER", "L1", "P1", "P2", "RESULT"]
        for col in columns:
            label = tk.Label(header_frame, 
                           text=col, 
                           bg="#1e88e5",     
                           fg="white",        
                           font=("Arial", 9, "bold"))
            label.pack(side="left", expand=True, fill="x", padx=2, pady=3)
        
        # Grid view area
        grid_frame = tk.Frame(q4, bg="#f5f5f5")
        grid_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        grid_label = tk.Label(grid_frame, 
                            text="Grid view", 
                            font=("Arial", 20),
                            bg="#f5f5f5",
                            fg="#757575")
        grid_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Bottom frame with equal spacing
        bottom_frame = tk.Frame(q4, bg="#f5f5f5", height=40)
        bottom_frame.pack(fill="x", side="bottom", pady=2)
        bottom_frame.pack_propagate(False)
        
        # Configure equal column weights
        bottom_frame.columnconfigure(0, weight=1)  # EMP CODE
        bottom_frame.columnconfigure(1, weight=1)  # NEXT LABEL button
        bottom_frame.columnconfigure(2, weight=1)  # ALC CODE
        
        # Employee Code Entry
        self.emp_entry = tk.Entry(bottom_frame,
                                 bg="white",
                                 fg="#424242",
                                 font=("Arial", 9, "bold"),
                                 justify="center",
                                 relief="flat",
                                 width=12)
        self.emp_entry.grid(row=0, column=0, padx=5, sticky="ew")
        self.emp_entry.insert(0, "EMP CODE")
        self.emp_entry.configure(highlightthickness=1,
                               highlightbackground="#e0e0e0",
                               highlightcolor="#1e88e5")
        
        # Next Label Button (centered)
        next_btn = tk.Button(bottom_frame,
                            text="NEXT LABEL ➜",
                            bg="#ffd700",
                            fg="#000000",
                            relief="flat",
                            font=("Arial", 9, "bold"),
                            cursor="hand2",
                            pady=2)
        next_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Add hover effect
        next_btn.bind('<Enter>', lambda e: next_btn.configure(bg="#ffeb3b"))
        next_btn.bind('<Leave>', lambda e: next_btn.configure(bg="#ffd700"))
        
        # ALC Code Entry (initially disabled)
        self.alc_entry = tk.Entry(bottom_frame,
                                 bg="#fff9c4",
                                 fg="#424242",
                                 font=("Arial", 9, "bold"),
                                 justify="center",
                                 relief="flat",
                                 width=12,
                                 state='disabled')  # Initially disabled
        self.alc_entry.grid(row=0, column=2, padx=5, sticky="ew")
        self.alc_entry.insert(0, "ALC CODE")
        self.alc_entry.configure(highlightthickness=1,
                               highlightbackground="#e0e0e0",
                               highlightcolor="#ffd700")
        
        # Bind events
        self.emp_entry.bind("<FocusIn>", lambda e: self.on_emp_entry_focus(True))
        self.emp_entry.bind("<FocusOut>", lambda e: self.on_emp_entry_focus(False))
        self.emp_entry.bind("<Return>", self.validate_employee_code)
        
        self.alc_entry.bind("<FocusIn>", lambda e: self.on_alc_entry_focus(True))
        self.alc_entry.bind("<FocusOut>", lambda e: self.on_alc_entry_focus(False))
        self.alc_entry.bind("<Return>", self.process_alc_code)
        
        return q4

    def create_graph_area(self, parent):
        # Create main graph container with black background
        graph_container = tk.Frame(parent, bg="black")
        graph_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure grid weights for reduced height
        graph_container.grid_rowconfigure(0, weight=0)  # Title row for Load graph
        graph_container.grid_rowconfigure(1, weight=1)  # Load graph
        graph_container.grid_rowconfigure(2, weight=0)  # Title row for Length graph
        graph_container.grid_rowconfigure(3, weight=1)  # Length graph
        graph_container.grid_columnconfigure(0, weight=1)  # Ensure full width
        
        # Load Graph Title
        tk.Label(graph_container, text="LOAD GRAPH", 
                 bg="black", fg="white", anchor="w",
                 font=("Arial", 10)).grid(row=0, column=0, sticky="w", padx=5)
        
        # Load Graph Canvas with reduced height
        self.load_canvas = tk.Canvas(graph_container, bg="black", 
                                   highlightthickness=0, height=100)  # Reduced height
        self.load_canvas.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 10))
        
        # Length Graph Title
        tk.Label(graph_container, text="LENGTH GRAPH", 
                 bg="black", fg="white", anchor="w",
                 font=("Arial", 10)).grid(row=2, column=0, sticky="w", padx=5)
        
        # Length Graph Canvas with reduced height
        self.length_canvas = tk.Canvas(graph_container, bg="black", 
                                     highlightthickness=0, height=100)  # Reduced height
        self.length_canvas.grid(row=3, column=0, sticky="ew", padx=5, pady=(0, 5))
        
        # Bind resize events
        self.load_canvas.bind('<Configure>', lambda e: self.draw_load_graph())
        self.length_canvas.bind('<Configure>', lambda e: self.draw_length_graph())

    def draw_load_graph(self):
        canvas = self.load_canvas
        canvas.delete("all")
        
        # Get dimensions
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        # Set margins
        left_margin = 40
        right_margin = 100  # Extra space for legend
        top_margin = 20
        bottom_margin = 30
        
        # Drawing area
        graph_width = width - (left_margin + right_margin)
        graph_height = height - (top_margin + bottom_margin)
        
        # Draw grid
        # Vertical lines
        for i in range(9):  # 8 divisions
            x = left_margin + (i * graph_width / 8)
            canvas.create_line(x, top_margin, x, height-bottom_margin, 
                             fill="gray", dash=(1,2))
            # X-axis labels
            canvas.create_text(x, height-bottom_margin+10, 
                             text=str(i+1), fill="white")
        
        # Horizontal lines
        for i in range(6):  # 5 divisions (0, 20, 40, 60, 80, 100)
            y = height - (bottom_margin + (i * graph_height / 5))
            canvas.create_line(left_margin, y, width-right_margin, y, 
                             fill="gray", dash=(1,2))
            # Y-axis labels
            canvas.create_text(left_margin-15, y, 
                             text=str(i*20), fill="white")
        
        # Draw legend
        legend_items = [
            ("L1", "cyan"),
            ("L2", "orange"),
            ("L3", "red"),
            ("L4", "blue")
        ]
        
        legend_x = width - right_margin + 20
        legend_y = top_margin + 20
        
        for text, color in legend_items:
            canvas.create_line(legend_x, legend_y, legend_x+20, legend_y, 
                             fill=color, width=2)
            canvas.create_text(legend_x+30, legend_y, 
                             text=text, fill="white", anchor="w")
            legend_y += 20

    def draw_length_graph(self):
        canvas = self.length_canvas
        canvas.delete("all")
        
        # Get dimensions
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        
        # Set margins
        left_margin = 40
        right_margin = 100
        top_margin = 20
        bottom_margin = 30
        
        # Drawing area
        graph_width = width - (left_margin + right_margin)
        graph_height = height - (top_margin + bottom_margin)
        
        # Draw grid
        # Vertical lines
        for i in range(9):  # 8 divisions
            x = left_margin + (i * graph_width / 8)
            canvas.create_line(x, top_margin, x, height-bottom_margin, 
                             fill="gray", dash=(1,2))
            # X-axis labels
            canvas.create_text(x, height-bottom_margin+10, 
                             text=str(i+1), fill="white")
        
        # Horizontal lines and labels
        y_labels = [-5, -3, -1, 1, 3, 5]
        for i, label in enumerate(y_labels):
            y = top_margin + (i * graph_height / (len(y_labels)-1))
            canvas.create_line(left_margin, y, width-right_margin, y, 
                             fill="gray", dash=(1,2))
            canvas.create_text(left_margin-15, y, 
                             text=str(label), fill="white")
        
        # Draw legend
        legend_items = [
            ("P1", "blue"),
            ("P2", "orange"),
            ("P3", "red"),
            ("P4", "white")
        ]
        
        legend_x = width - right_margin + 20
        legend_y = top_margin + 20
        
        for text, color in legend_items:
            canvas.create_line(legend_x, legend_y, legend_x+20, legend_y, 
                             fill=color, width=2)
            canvas.create_text(legend_x+30, legend_y, 
                             text=text, fill="white", anchor="w")
            legend_y += 20

    def create_footer(self):
        footer = tk.Label(self.main_container,
                        text="Powered By: IRACRAT TECHNOLOGIES Contact: INFO@IRACRAT.COM, (+91) 99623 46614",
                        bg="#FFB6C1", height=2)
        footer.pack(fill="x", side="bottom")

    # Label drag and drop functionality
    def enable_label_dragging(self):
        """Enable drag and drop for all labels"""
        for label in self.label_widgets.values():
            label.bind("<Button-1>", self.start_label_drag)
            label.bind("<B1-Motion>", self.on_label_drag)
            label.bind("<ButtonRelease-1>", self.stop_label_drag)
            label.configure(cursor="hand2")  # Change cursor to indicate draggable

    def disable_label_dragging(self):
        """Disable drag and drop for all labels"""
        for label in self.label_widgets.values():
            label.unbind("<Button-1>")
            label.unbind("<B1-Motion>")
            label.unbind("<ButtonRelease-1>")
            label.configure(cursor="")  # Reset cursor
            # Reset label position if it was placed on image
            if label in self.label_positions:
                label.place_forget()
                label.pack(side="left", padx=2)

    def start_label_drag(self, event):
        """Start dragging a label."""
        label = event.widget
        label._drag_start_x = event.x
        label._drag_start_y = event.y
        # Raise the label to the top of the stacking order
        label.lift()
        # Store original position
        label._original_position = (label.winfo_x(), label.winfo_y())

    def on_label_drag(self, event):
        """Handle label dragging."""
        label = event.widget
        # Calculate new position
        x = label.winfo_x() + event.x - label._drag_start_x
        y = label.winfo_y() + event.y - label._drag_start_y
        
        # Get image frame boundaries
        image_frame = self.image_frame
        frame_width = image_frame.winfo_width()
        frame_height = image_frame.winfo_height()
        
        # Keep label within image frame boundaries
        x = max(0, min(x, frame_width - label.winfo_width()))
        y = max(0, min(y, frame_height - label.winfo_height()))
        
        # Move the label
        label.place(in_=image_frame, x=x, y=y)

    def stop_label_drag(self, event):
        """Handle end of label drag."""
        label = event.widget
        
        # Get label position relative to image frame
        x = label.winfo_x()
        y = label.winfo_y()
        
        # Check if label is within image frame bounds
        if (0 <= x <= self.image_frame.winfo_width() and 
            0 <= y <= self.image_frame.winfo_height()):
            # Save the new position
            self.label_positions[label.cget('text')] = (x, y)
            print(f"Label {label.cget('text')} dropped at x={x}, y={y}")
        else:
            # Return label to label frame if dropped outside image
            label.place_forget()
            label.pack(in_=self.label_info_frame, side="left", padx=1)
            if label.cget('text') in self.label_positions:
                del self.label_positions[label.cget('text')]

    # Button command methods
    def auto_command(self):
        messagebox.showinfo("Auto", "Auto mode activated")

    def home_command(self):
        messagebox.showinfo("Home", "Returning to home position")

    def first_pull_command(self):
        messagebox.showinfo("1st Pull", "Performing load test")

    def second_pull_command(self):
        messagebox.showinfo("2nd Pull", "Performing length test")

    def test_result_command(self):
        messagebox.showinfo("Test Result", "Generating test results")

    def next_model_command(self):
        messagebox.showinfo("Next Model", "Moving to next model")

    def alc_code_command(self):
        messagebox.showinfo("ALC Code", "Opening ALC Code dialog")

    def load_image(self, file_path=None):
        """Load and display an image in the first quadrant, filling the entire frame."""
        if not file_path:
            file_path = filedialog.askopenfilename(
                filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.ico")]
            )
        
        if file_path:
            try:
                # Get the first quadrant dimensions
                frame_width = self.image_frame.winfo_width()
                frame_height = self.image_frame.winfo_height()
                
                # Load the image
                image = Image.open(file_path)
                
                # Resize image to fill the entire frame
                resized_image = image.resize((frame_width, frame_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(resized_image)
                
                # Remove old image label if it exists
                if hasattr(self, 'image_label'):
                    self.image_label.destroy()
                
                # Create new image label that fills the entire frame
                self.image_label = tk.Label(self.image_frame, image=photo, bg='white')
                self.image_label.image = photo  # Keep a reference
                self.image_label.place(x=0, y=0, relwidth=1, relheight=1)
                
                # Store image dimensions
                self.image_dimensions = {
                    'width': frame_width,
                    'height': frame_height,
                    'x_offset': 0,
                    'y_offset': 0
                }
                
                # Store the image path
                self.current_image_path = file_path
                
                print(f"Image loaded and fitted to frame: {frame_width}x{frame_height}")
                return True
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading image: {str(e)}")
                return False
        
        return False

    def setup_barcode_listener(self):
        """Alternative approach using tkinter bindings"""
        self.root.bind('<Key>', self.on_key_press)
        self.root.bind('<Return>', self.on_enter_press)

    def on_key_press(self, event):
        if event.char:
            self.barcode_data += event.char

    def on_enter_press(self, event):
        self.process_barcode_data()
        self.barcode_data = ""

    def process_barcode_data(self):
        """Process the captured barcode data."""
        part_number = self.barcode_data.strip()
        if part_number:
            self.retrieve_part_specifications(part_number)

    def retrieve_part_specifications(self, part_number):
        """Retrieve specifications and label coordinates from database."""
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="nk446420",
                database="EOL"
            )
            cursor = conn.cursor()
            
            # Get image path and label coordinates
            master_query = """
            SELECT MM_IMAGE_PATH, MM_LABEL_COORDINATES, MM_MODEL_NAME
            FROM TBL_MODEL_MASTER 
            WHERE MM_PART_NUMBER = %s
            """
            cursor.execute(master_query, (part_number,))
            result = cursor.fetchone()
            
            if result:
                image_path, label_coordinates, model_name = result
                
                # Update model header
                if model_name:
                    self.model_header.config(text=f"{model_name} - {part_number}")
                
                # Load image first
                if image_path and os.path.exists(image_path):
                    if self.load_image_with_path(image_path):
                        # After image is loaded, place labels using database coordinates
                        if label_coordinates:
                            try:
                                coordinates_data = json.loads(label_coordinates)
                                self.place_labels_from_positions(coordinates_data)
                                print(f"Label coordinates loaded: {coordinates_data}")
                            except json.JSONDecodeError as e:
                                print(f"Warning: Invalid label coordinate data: {e}")
                                messagebox.showwarning("Warning", "Invalid label coordinate data in database")
                
                # Get specifications
                spec_query = """
                SELECT 
                    MS_DESCRIPTION,
                    MS_DEVICE,
                    MS_UNIT,
                    MS_NORMAL_MIN,
                    MS_NORMAL_MAX
                FROM TBL_MODEL_SPECIFICATION 
                WHERE MS_PART_NUMBER = %s
                ORDER BY MS_DEVICE
                """
                cursor.execute(spec_query, (part_number,))
                specs = cursor.fetchall()
                
                # Update specifications tree
                self.spec_tree.delete(*self.spec_tree.get_children())
                for index, spec in enumerate(specs, start=1):
                    values = (index,) + spec
                    self.spec_tree.insert('', 'end', values=values)
            
            else:
                print(f"No data found for part number: {part_number}")
                messagebox.showwarning("Warning", f"No data found for part number: {part_number}")
            
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            messagebox.showerror("Database Error", f"Failed to retrieve data: {err}")
        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def load_image_with_path(self, image_path):
        """Load and fit image to match the exact width of the image frame."""
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Get the first quadrant dimensions
            frame_width = self.image_frame.winfo_width()
            frame_height = self.image_frame.winfo_height()
            
            # Load original image
            original_image = Image.open(image_path)
            
            # Resize image to fill the entire frame
            resized_image = original_image.resize((frame_width, frame_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(resized_image)
            
            # Remove old image label if it exists
            if self.image_label:
                self.image_label.destroy()
            
            # Create new image label that fills the entire frame
            self.image_label = tk.Label(self.image_frame, image=photo, bg='white')
            self.image_label.image = photo  # Keep a reference
            self.image_label.place(x=0, y=0, relwidth=1, relheight=1)
            
            # Store image dimensions for label positioning
            self.image_dimensions = {
                'width': frame_width,
                'height': frame_height,
                'x_offset': 0,
                'y_offset': 0
            }
            
            self.current_image_path = image_path
            return True
            
        except Exception as e:
            print(f"Error loading image: {str(e)}")
            messagebox.showerror("Error", f"Error loading image: {str(e)}")
            return False

    def place_labels_from_positions(self, coordinates_data):
        """Place labels exactly according to database coordinates without drag functionality."""
        try:
            # Clear any existing placed labels
            for label in getattr(self, 'placed_labels', {}).values():
                label.destroy()
            self.placed_labels = {}
            
            print(f"Placing labels with coordinates: {coordinates_data}")
            
            # Get image frame dimensions for validation
            frame_width = self.image_frame.winfo_width()
            frame_height = self.image_frame.winfo_height()
            
            # Create labels based on coordinates data
            for label_num, coord_data in coordinates_data.items():
                # Get coordinates from database
                x = coord_data.get('x')
                y = coord_data.get('y')
                
                if x is not None and y is not None:
                    # Validate coordinates are within frame boundaries
                    x = max(0, min(int(x), frame_width - 40))  # 40 is approximate label width
                    y = max(0, min(int(y), frame_height - 25)) # 25 is approximate label height
                    
                    # Create label with exact specifications
                    label_text = f'L{label_num}'
                    new_label = tk.Label(self.image_frame,
                                       text=label_text,
                                       bg="yellow",
                                       fg="black",
                                       font=("Arial", 10, "bold"),
                                       width=4,
                                       relief="raised",
                                       borderwidth=2)
                    
                    # Place label at exact coordinates
                    new_label.place(x=x, y=y)
                    
                    # Store the label and its position
                    self.placed_labels[label_text] = new_label
                    self.label_positions[label_text] = (x, y)
                    
                    print(f"Placed {label_text} at coordinates x={x}, y={y}")
            
            # Update label info with sorted list of placed labels
            if self.placed_labels:
                sorted_labels = sorted(self.placed_labels.keys(), key=lambda x: int(x[1:]))
                self.label_info.config(text=f"Placed Labels: {', '.join(sorted_labels)}")
            else:
                self.label_info.config(text="Placed Labels: None")

        except Exception as e:
            print(f"Error placing labels: {e}")
            messagebox.showerror("Error", f"Failed to place labels: {str(e)}")

    def get_status_label_color(self, label_text):
        """Return the color for each status label."""
        colors = {
            'HOME': '#4169E1',  # Royal Blue
            'AUTO': '#228B22',  # Forest Green
            'SEMI': '#DAA520',  # Goldenrod
            'MANU': '#B8860B',  # Dark Goldenrod
            'STOP': '#DC143C'   # Crimson
        }
        return colors.get(label_text, 'gray')

    def reset_labels(self):
        """Reset all labels to their original state"""
        # Clear any placed labels
        for label in getattr(self, 'placed_labels', {}).values():
            label.destroy()
        self.placed_labels = {}
        
        # Ensure original labels are visible in their container
        for label in self.label_widgets.values():
            label.pack(in_=self.label_info_frame, side="left", padx=2, expand=True)
        
        self.label_positions.clear()
        
        # Save the cleared positions to database
        if hasattr(self, 'current_part_number'):
            self.save_label_positions()

    # Example button command methods
    def button1_command(self):
        messagebox.showinfo("Button 1", "Button 1 pressed")

    def button2_command(self):
        messagebox.showinfo("Button 2", "Button 2 pressed")

    def button3_command(self):
        messagebox.showinfo("Button 3", "Button 3 pressed")

    def button4_command(self):
        messagebox.showinfo("Button 4", "Button 4 pressed")

    def button5_command(self):
        messagebox.showinfo("Button 5", "Button 5 pressed")

    def button6_command(self):
        messagebox.showinfo("Button 6", "Button 6 pressed")

    def save_label_positions(self):
        """Save current label positions to database."""
        if not hasattr(self, 'current_part_number') or not self.placed_labels:
            return

        positions = {}
        for label_text, label in self.placed_labels.items():
            if label_text.startswith('L'):
                label_num = label_text[1:]  # Extract number from "L1", "L2", etc.
                positions[label_num] = {
                    'x': label.winfo_x(),
                    'y': label.winfo_y(),
                    'text': label_text
                }

        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="nk446420",
                database="EOL"
            )
            cursor = conn.cursor()

            # Update the database with new positions
            positions_json = json.dumps(positions)
            update_query = """
            UPDATE TBL_MODEL_MASTER 
            SET MM_LABEL_COORDINATES = %s 
            WHERE MM_PART_NUMBER = %s
            """
            cursor.execute(update_query, (positions_json, self.current_part_number))
            conn.commit()

            cursor.close()
            conn.close()

        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
            messagebox.showerror("Database Error", f"Failed to save label positions: {err}")
        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def start_monitoring(self):
        """Start monitoring sensors and PLC status"""
        self.message_label.configure(text="Please Validate NG Cable...")
        self.starting_ng_cable_validation = True
        # Start your monitoring threads/processes here

    def on_emp_entry_focus(self, is_focused):
        """Handle employee code entry focus"""
        if is_focused:
            if self.emp_entry.get() == "EMP CODE":
                self.emp_entry.delete(0, tk.END)
            self.emp_entry.configure(bg="white")
        else:
            if not self.emp_entry.get():
                self.emp_entry.insert(0, "EMP CODE")
                self.emp_entry.configure(bg="white")

    def validate_employee_code(self, event=None):
        """Validate employee code against employecode.txt"""
        emp_code = self.emp_entry.get().strip()
        if emp_code == "EMP CODE" or not emp_code:
            messagebox.showwarning("Warning", "Please enter an employee code")
            return
        
        try:
            with open('employecode.txt', 'r') as file:
                valid_codes = [code.strip() for code in file.read().split(',')]
            
            if emp_code in valid_codes:
                self.alc_entry.configure(state='normal')
                self.emp_entry.configure(bg="lightgreen")
                messagebox.showinfo("Success", "Employee code validated. You can now enter ALC code.")
            else:
                self.alc_entry.configure(state='disabled')
                self.emp_entry.configure(bg="pink")
                messagebox.showerror("Error", "Employee code unauthorized")
                
        except FileNotFoundError:
            messagebox.showerror("Error", "Employee code file not found")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def on_alc_entry_focus(self, is_focused):
        """Handle ALC entry focus with visual feedback"""
        if is_focused:
            if self.alc_entry.get() == "ALC CODE":
                self.alc_entry.delete(0, tk.END)
            self.alc_entry.configure(bg="white")
        else:
            if not self.alc_entry.get():
                self.alc_entry.insert(0, "ALC CODE")
                self.alc_entry.configure(bg="#fff9c4")

    def process_alc_code(self, event=None):
        """Process the entered ALC code and retrieve specifications"""
        alc_code = self.alc_entry.get().strip()
        if not alc_code or alc_code == "ALC CODE":
            messagebox.showwarning("Warning", "Please enter a valid ALC code")
            return

        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="nk446420",
                database="EOL"
            )
            cursor = conn.cursor()

            # First query to get basic part details
            part_query = """
            SELECT MM_PART_NUMBER, MM_MODEL_NAME, MM_IMAGE_PATH, MM_LABEL_COORDINATES
            FROM TBL_MODEL_MASTER 
            WHERE MM_ALC_CODE = %s
            """
            cursor.execute(part_query, (alc_code,))
            part_result = cursor.fetchone()

            if part_result:
                part_number, model_name, image_path, label_coordinates = part_result
                
                # Store the current part number
                self.current_part_number = part_number

                # Update message label with part info
                self.message_label.config(
                    text=f"Model: {model_name} | Part Number: {part_number}",
                    fg="green"
                )

                # Second query to get specifications
                spec_query = """
                SELECT 
                    MS_DESCRIPTION,
                    MS_DEVICE,
                    MS_UNIT,
                    MS_NORMAL_MIN,
                    MS_NORMAL_MAX,
                    MS_SPECIAL_DATA
                FROM TBL_MODEL_SPECIFICATION 
                WHERE MS_PART_NUMBER = %s
                ORDER BY MS_DEVICE
                """
                cursor.execute(spec_query, (part_number,))
                specs = cursor.fetchall()

                # Clear existing items in specification tree
                self.spec_tree.delete(*self.spec_tree.get_children())

                # Add specifications to tree
                for i, spec in enumerate(specs, 1):
                    description, device, unit, min_val, max_val, special_data = spec
                    
                    # Format values for display
                    min_val = f"{float(min_val):.2f}" if min_val is not None else "N/A"
                    max_val = f"{float(max_val):.2f}" if max_val is not None else "N/A"
                    
                    # Insert into tree with ID number
                    values = (
                        description,
                        device,
                        unit,
                        min_val,
                        max_val,
                        "",  # Empty Actual column
                        ""   # Empty Result column
                    )
                    item_id = self.spec_tree.insert('', 'end', values=values)
                    
                    # Add special styling if needed
                    if special_data:
                        self.spec_tree.item(item_id, tags=('special',))
                        self.spec_tree.tag_configure('special', background='#fff3cd')

                # Load image if path exists
                if image_path and os.path.exists(image_path):
                    if self.load_image_with_path(image_path):
                        if label_coordinates:
                            try:
                                coordinates = json.loads(label_coordinates)
                                self.place_labels_from_positions(coordinates)
                            except json.JSONDecodeError:
                                print(f"Warning: Invalid label coordinate data for ALC code {alc_code}")

            else:
                self.message_label.config(
                    text=f"No data found for ALC code: {alc_code}",
                    fg="red"
                )
                messagebox.showwarning("Warning", "No matching ALC code found")

            cursor.close()
            conn.close()

        except mysql.connector.Error as err:
            self.message_label.config(
                text=f"Database error: {err}",
                fg="red"
            )
            messagebox.showerror("Database Error", f"Failed to retrieve data: {err}")
        except Exception as e:
            self.message_label.config(
                text=f"Error: {str(e)}",
                fg="red"
            )
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def update_specification_result(self, device, actual_value, result):
        """Update the actual value and result for a specific device in the specifications tree"""
        for item in self.spec_tree.get_children():
            if self.spec_tree.item(item)['values'][1] == device:  # Check DEVICE column
                current_values = list(self.spec_tree.item(item)['values'])
                current_values[5] = actual_value  # Update ACTUAL column
                current_values[6] = result        # Update RESULT column
                
                # Update row color based on result
                if result == "PASS":
                    self.spec_tree.tag_configure('pass', background='lightgreen')
                    self.spec_tree.item(item, values=current_values, tags=('pass',))
                elif result == "FAIL":
                    self.spec_tree.tag_configure('fail', background='pink')
                    self.spec_tree.item(item, values=current_values, tags=('fail',))
                else:
                    self.spec_tree.item(item, values=current_values)
                break

def main():
    root = tk.Tk()
    app = EOLTesterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
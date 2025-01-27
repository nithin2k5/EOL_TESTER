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
        self.root.state('zoomed')
        
        # Initialize variables
        self.image_label = None
        self.current_image = None
        self.label_positions = {}
        self.selected_label = None
        self.barcode_data = ""
        
        self.setup_gui()
        self.setup_barcode_listener()

    def setup_gui(self):
        # Main container
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)

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

        self.create_manual_entry()

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
        # Configure grid weights - equal weights for all quadrants
        self.workspace.grid_columnconfigure(0, weight=1)  # First column
        self.workspace.grid_columnconfigure(1, weight=1)  # Second column
        self.workspace.grid_rowconfigure(0, weight=1)     # First row
        self.workspace.grid_rowconfigure(1, weight=1)     # Second row
        
        # Calculate quadrant sizes
        # Get the workspace dimensions after padding
        self.workspace.update()  # Force geometry update
        total_width = self.workspace.winfo_width()
        total_height = self.workspace.winfo_height()
        
        # Calculate exact quadrant dimensions
        quadrant_width = total_width // 2 - 4   # Account for padding (2px on each side)
        quadrant_height = total_height // 2 - 4  # Account for padding (2px on each side)
        
        # Create and configure all quadrants with identical size
        self.q1 = self.create_first_quadrant()
        self.q2 = self.create_second_quadrant()
        self.q3 = self.create_third_quadrant()
        self.q4 = self.create_fourth_quadrant()
        
        # Configure all quadrants with identical settings
        quadrants = [self.q1, self.q2, self.q3, self.q4]
        positions = [(0,0), (0,1), (1,0), (1,1)]
        
        for quadrant, (row, col) in zip(quadrants, positions):
            quadrant.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            quadrant.configure(width=quadrant_width, height=quadrant_height)
            quadrant.grid_propagate(False)  # Prevent resizing
            
            # Add a minimum size constraint
            quadrant.grid_columnconfigure(0, minsize=quadrant_width)
            quadrant.grid_rowconfigure(0, minsize=quadrant_height)

    def create_first_quadrant(self):
        q1 = tk.Frame(self.workspace, relief="groove", borderwidth=1)
        
        # Model header
        model_header = tk.Label(q1, 
                              text="MODEL NAME / PART NAME - PART NUMBER",
                              bg="navy", fg="white", 
                              font=("Arial", 12, "bold"))
        model_header.pack(fill="x")
        
        # Create fixed size image area container with border
        self.image_container = tk.Frame(q1, width=500, height=400, relief="solid", borderwidth=1)
        self.image_container.pack(pady=5)
        self.image_container.pack_propagate(False)  # Prevent resizing
        
        # Image area with white background
        self.image_area = tk.Frame(self.image_container, bg="white")
        self.image_area.place(relwidth=1, relheight=1)
        
        # Add image label placeholder
        self.image_label = None
        self.image_loaded = False
        
        # Create draggable labels container at the bottom
        self.label_container = tk.Frame(q1)
        self.label_container.pack(fill="x", side="bottom", pady=5)
        
        # Create draggable labels with distinct colors
        self.label_widgets = {}
        labels_config = [
            ("HOME", "#FFB6C1"),      # Light pink
            ("AUTO", "#98FB98"),      # Light green
            ("1st PULL", "#87CEEB"),  # Sky blue
            ("2nd PULL", "#DDA0DD"),  # Plum
            ("TEST RESULT", "#F0E68C") # Khaki
        ]
        
        for text, color in labels_config:
            label = tk.Label(self.label_container, 
                            text=text,
                            bg=color, 
                            fg="black",
                            width=15, 
                            height=2,
                            relief="raised",
                            font=("Arial", 10, "bold"))
            label.pack(side="left", padx=2, expand=True)
            self.label_widgets[text] = label
            
            # Bind mouse events for dragging
            label.bind("<Button-1>", self.start_label_drag)
            label.bind("<B1-Motion>", self.on_label_drag)
            label.bind("<ButtonRelease-1>", self.stop_label_drag)
            label.configure(cursor="hand2")  # Change cursor to indicate draggable
        
        return q1

    def create_second_quadrant(self):
        q2 = tk.Frame(self.workspace, relief="groove", borderwidth=1)
        q2.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
        
        # Add header
        header = tk.Label(q2, text="TEST SPECIFICATIONS",
                         bg="#00BFFF", fg="black",
                         font=("Arial", 12, "bold"))
        header.pack(fill="x")
        
        # Create specifications table
        columns = ("DESCRIPTION", "DEVICE", "UNIT", "SPEC MIN", "SPEC MAX", "ACTUAL", "RESULT")
        self.spec_tree = ttk.Treeview(q2, columns=columns, show="headings", height=10)
        
        # Configure columns with center alignment
        for col in columns:
            self.spec_tree.heading(col, text=col)
            self.spec_tree.column(col, width=100, anchor='center')  # Set center alignment
            
        self.spec_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create camera panel container with fixed height
        camera_panel = tk.Frame(q2, height=120)  # Fixed height
        camera_panel.pack(fill="x", padx=5, pady=(0, 5))
        camera_panel.pack_propagate(False)  # Prevent resizing
        
        # Create container for both cameras
        cameras_container = tk.Frame(camera_panel)
        cameras_container.pack(fill="both", expand=True)
        
        # Configure grid weights for cameras container
        cameras_container.grid_columnconfigure(0, weight=1)  # CAM 1 space
        cameras_container.grid_columnconfigure(1, weight=0)  # Separator space
        cameras_container.grid_columnconfigure(2, weight=1)  # CAM 2 space
        
        # CAM 1 Section
        cam1_frame = tk.Frame(cameras_container)
        cam1_frame.grid(row=0, column=0, sticky="nsew")
        
        tk.Label(cam1_frame, text="CAM 1", bg="white", anchor="w",
                 font=("Arial", 8)).pack(fill="x", pady=(0, 2))
        
        cam1_blocks = tk.Frame(cam1_frame)
        cam1_blocks.pack(fill="both", expand=True)
        
        # CAM 1 blocks
        cam1_block1 = tk.Frame(cam1_blocks, bg="lightyellow", relief="groove", borderwidth=1)
        cam1_block1.pack(side="left", fill="both", expand=True, padx=(0, 1))
        
        cam1_block2 = tk.Frame(cam1_blocks, bg="lightyellow", relief="groove", borderwidth=1)
        cam1_block2.pack(side="left", fill="both", expand=True, padx=(1, 0))
        
        # Separator
        separator = tk.Frame(cameras_container, width=20)
        separator.grid(row=0, column=1, sticky="ns")
        
        # CAM 2 Section
        cam2_frame = tk.Frame(cameras_container)
        cam2_frame.grid(row=0, column=2, sticky="nsew")
        
        tk.Label(cam2_frame, text="CAM 2", bg="white", anchor="w",
                 font=("Arial", 8)).pack(fill="x", pady=(0, 2))
        
        cam2_blocks = tk.Frame(cam2_frame)
        cam2_blocks.pack(fill="both", expand=True)
        
        # CAM 2 blocks
        cam2_block1 = tk.Frame(cam2_blocks, bg="lightyellow", relief="groove", borderwidth=1)
        cam2_block1.pack(side="left", fill="both", expand=True, padx=(0, 1))
        
        cam2_block2 = tk.Frame(cam2_blocks, bg="lightyellow", relief="groove", borderwidth=1)
        cam2_block2.pack(side="left", fill="both", expand=True, padx=(1, 0))
        
        # Store camera blocks for later access if needed
        self.camera_blocks = {
            'cam1_block1': cam1_block1,
            'cam1_block2': cam1_block2,
            'cam2_block1': cam2_block1,
            'cam2_block2': cam2_block2
        }
        
        return q2

    def create_third_quadrant(self):
        q3 = tk.Frame(self.workspace, relief="groove", borderwidth=1)
        
        # Add labels at the top
        label_frame = tk.Frame(q3)
        label_frame.pack(fill="x", pady=5)
        
        labels = [
            "HOME",
            "AUTO",
            "PULL 1",
            "PULL 2",
            "TEST RESULT"
        ]
        
        for text in labels:
            lbl = tk.Label(label_frame, text=text, 
                          bg="#00BFFF", fg="black",
                          width=10, height=1,
                          font=("Arial", 10, "bold"))
            lbl.pack(side="left", padx=10, pady=5, expand=True)
        
        # Add graph area
        self.create_graph_area(q3)
        
        return q3

    def create_fourth_quadrant(self):
        q4 = tk.Frame(self.workspace, relief="groove", borderwidth=1)
        
        # Header
        header_frame = tk.Frame(q4, bg="#00BFFF")
        header_frame.pack(fill="x")
        
        columns = ["LOT NUMBER", "L1", "P1", "P2", "RESULT"]
        for col in columns:
            label = tk.Label(header_frame, text=col, bg="#00BFFF", 
                            font=("Arial", 10, "bold"))
            label.pack(side="left", expand=True, fill="x", padx=2)
        
        # Grid view area
        grid_frame = tk.Frame(q4, bg="white")
        grid_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        grid_label = tk.Label(grid_frame, text="Grid view", 
                             font=("Arial", 24), bg="white")
        grid_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Bottom frame
        bottom_frame = tk.Frame(q4)
        bottom_frame.pack(fill="x", side="bottom", pady=2)
        
        # Next model button (yellow)
        next_btn = tk.Button(bottom_frame, text="CLICK TO MOVE TO NEXT LABEL",
                            bg="yellow", relief="flat",
                            font=("Arial", 10))
        next_btn.pack(side="left", fill="x", expand=True, padx=(2, 1))
        
        # ALC CODE text box
        alc_entry = tk.Entry(bottom_frame, bg="yellow", 
                            font=("Arial", 10),
                            justify="center")
        alc_entry.insert(0, "ALC CODE")
        alc_entry.pack(side="right", padx=(1, 2), ipady=1)
        
        # Store the entry widget for later access if needed
        self.alc_entry = alc_entry
        
        return q4

    def create_graph_area(self, parent):
        # Create main graph container with black background
        graph_container = tk.Frame(parent, bg="black")
        graph_container.pack(fill="both", expand=True)
        
        # Configure grid weights for equal space
        graph_container.grid_rowconfigure(0, weight=1)  # Load graph
        graph_container.grid_rowconfigure(1, weight=1)  # Length graph
        graph_container.grid_columnconfigure(0, weight=1)  # Ensure full width
        
        # Load Graph Section
        load_graph_frame = tk.Frame(graph_container, bg="black")
        load_graph_frame.grid(row=0, column=0, sticky="nsew", pady=(5, 0))
        
        # Load Graph Title
        tk.Label(load_graph_frame, text="LOAD GRAPH", 
                 bg="black", fg="white", anchor="w",
                 font=("Arial", 10)).pack(fill="x", padx=5)
        
        # Load Graph Canvas
        self.load_canvas = tk.Canvas(load_graph_frame, bg="black", 
                                   highlightthickness=0)
        self.load_canvas.pack(fill="both", expand=True, padx=5)
        
        # Length Graph Section
        length_graph_frame = tk.Frame(graph_container, bg="black")
        length_graph_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 5))
        
        # Length Graph Title
        tk.Label(length_graph_frame, text="LENGTH GRAPH", 
                 bg="black", fg="white", anchor="w",
                 font=("Arial", 10)).pack(fill="x", padx=5)
        
        # Length Graph Canvas
        self.length_canvas = tk.Canvas(length_graph_frame, bg="black", 
                                     highlightthickness=0)
        self.length_canvas.pack(fill="both", expand=True, padx=5)
        
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
        """Start dragging a label"""
        if self.image_loaded:
            widget = event.widget
            widget._drag_start_x = event.x
            widget._drag_start_y = event.y
            widget._drag_start_pos = (widget.winfo_x(), widget.winfo_y())
            widget.lift()  # Bring label to front while dragging

    def on_label_drag(self, event):
        """Handle label dragging"""
        if self.image_loaded:
            widget = event.widget
            
            # Calculate new position
            dx = event.x - widget._drag_start_x
            dy = event.y - widget._drag_start_y
            new_x = widget._drag_start_pos[0] + dx
            new_y = widget._drag_start_pos[1] + dy
            
            # Get image area boundaries
            image_x = self.image_area.winfo_x()
            image_y = self.image_area.winfo_y()
            image_width = self.image_area.winfo_width()
            image_height = self.image_area.winfo_height()
            
            # Keep label within image boundaries
            new_x = max(image_x, min(new_x, image_x + image_width - widget.winfo_width()))
            new_y = max(image_y, min(new_y, image_y + image_height - widget.winfo_height()))
            
            # Move the label
            widget.place(x=new_x, y=new_y)

    def stop_label_drag(self, event):
        """Handle the end of label dragging"""
        if self.image_loaded:
            widget = event.widget
            # Save the final position
            self.label_positions[widget.cget("text")] = (widget.winfo_x(), widget.winfo_y())
            # Save positions to database
            self.save_label_positions()

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

    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            try:
                # Reset any existing label positions
                self.disable_label_dragging()
                self.label_positions.clear()
                
                image = Image.open(file_path)
                # Get image area dimensions
                area_width = self.image_area.winfo_width()
                area_height = self.image_area.winfo_height()
                
                # Calculate scaling to fit while maintaining aspect ratio
                img_width, img_height = image.size
                scale = min(area_width/img_width, area_height/img_height)
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                if self.image_label:
                    self.image_label.destroy()
                    
                self.image_label = tk.Label(self.image_area, image=photo, bg="white")
                self.image_label.image = photo
                
                # Center the image
                x = (area_width - new_width) // 2
                y = (area_height - new_height) // 2
                self.image_label.place(x=x, y=y)
                
                # Enable label dragging only after successful image load
                self.image_loaded = True
                self.enable_label_dragging()
                
            except Exception as e:
                self.image_loaded = False
                messagebox.showerror("Error", f"Error loading image: {str(e)}")

    def create_manual_entry(self):
        """Create an entry widget and button for manual part number entry."""
        manual_entry_frame = tk.Frame(self.main_container)
        manual_entry_frame.pack(fill="x", pady=5)

        self.part_number_entry = tk.Entry(manual_entry_frame, width=20)
        self.part_number_entry.pack(side="left", padx=5)

        retrieve_button = tk.Button(manual_entry_frame, text="Retrieve Specifications", command=self.manual_retrieve_command)
        retrieve_button.pack(side="left", padx=5)

    def manual_retrieve_command(self):
        """Retrieve specifications based on manual entry."""
        part_number = self.part_number_entry.get().strip()
        if part_number:
            self.retrieve_part_specifications(part_number)

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
        """Retrieve specifications and image for a given part number."""
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="nk446420",
                database="EOL"
            )
            cursor = conn.cursor()
            
            # Store the current part number
            self.current_part_number = part_number
            
            # First, get the image path and label positions from TBL_MODEL_MASTER
            master_query = """
            SELECT MM_IMAGE_PATH, MM_LABEL_POSITIONS 
            FROM TBL_MODEL_MASTER 
            WHERE MM_PART_NUMBER = %s
            """
            cursor.execute(master_query, (part_number,))
            result = cursor.fetchone()
            
            if result:
                image_path, label_positions = result
                if image_path:
                    self.load_image_with_path(image_path)
                    
                # Load saved label positions if they exist
                if label_positions:
                    self.load_label_positions(json.loads(label_positions))
            
            # Get the specifications
            spec_query = """
            SELECT MS_DESCRIPTION, MS_DEVICE, MS_UNIT, 
                   MS_MASTER_MIN, MS_MASTER_MAX, 
                   MS_NORMAL_MIN, MS_NORMAL_MAX
            FROM TBL_MODEL_SPECIFICATION 
            WHERE MS_PART_NUMBER = %s
            """
            
            cursor.execute(spec_query, (part_number,))
            
            # Clear existing entries in treeview
            self.spec_tree.delete(*self.spec_tree.get_children())
            
            # Insert retrieved data into treeview
            for row in cursor.fetchall():
                display_row = list(row) + ['', '']  # Add empty ACTUAL and RESULT values
                self.spec_tree.insert('', 'end', values=display_row)
            
            if not self.spec_tree.get_children():
                messagebox.showinfo("No Data", f"No specifications found for part number: {part_number}")
            
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to retrieve specifications: {err}")

    def load_image_with_path(self, image_path):
        """Load image from path and enable label dragging"""
        if os.path.exists(image_path):
            try:
                # Reset any existing label positions
                self.reset_labels()
                
                image = Image.open(image_path)
                # Get image container dimensions
                container_width = self.image_container.winfo_width()
                container_height = self.image_container.winfo_height()
                
                # Calculate scaling to fit while maintaining aspect ratio
                img_width, img_height = image.size
                scale = min(container_width/img_width, container_height/img_height)
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                # Resize image
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                if self.image_label:
                    self.image_label.destroy()
                    
                self.image_label = tk.Label(self.image_area, image=photo, bg="white")
                self.image_label.image = photo
                
                # Center the image in the container
                x = (container_width - new_width) // 2
                y = (container_height - new_height) // 2
                self.image_label.place(x=x, y=y)
                
                # Enable label dragging
                self.image_loaded = True
                
                # Make labels visually indicate they're draggable
                for label in self.label_widgets.values():
                    label.configure(cursor="hand2")
                
            except Exception as e:
                self.image_loaded = False
                messagebox.showerror("Error", f"Error loading image: {str(e)}")
        else:
            messagebox.showerror("Error", f"Image file not found: {image_path}")

    def position_saved_labels(self):
        """Position labels according to saved positions"""
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="nk446420",
                database="EOL"
            )
            cursor = conn.cursor()
            
            # Get label positions from database
            query = """
            SELECT MM_LABEL_POSITIONS 
            FROM TBL_MODEL_MASTER 
            WHERE MM_PART_NUMBER = %s
            """
            cursor.execute(query, (self.current_part_number,))
            result = cursor.fetchone()
            
            if result and result[0]:
                label_positions = json.loads(result[0])
                
                for label_name, position in label_positions.items():
                    if label_name in self.label_widgets:
                        label = self.label_widgets[label_name]
                        label.place(x=position['x'], y=position['y'])
                        self.label_positions[label_name] = (position['x'], position['y'])
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error positioning labels: {str(e)}")

    def load_label_positions(self, positions):
        """Load saved label positions onto the image"""
        if not self.image_loaded:
            return
        
        for label_text, coords in positions.items():
            if label_text in self.label_widgets:
                label = self.label_widgets[label_text]
                label.place(in_=self.image_area, x=coords['x'], y=coords['y'])
                self.label_positions[label_text] = (coords['x'], coords['y'])

    def save_label_positions(self):
        """Save current label positions to database"""
        if not self.current_part_number or not self.label_positions:
            return
        
        try:
            positions_json = json.dumps({
                text: {'x': x, 'y': y} 
                for text, (x, y) in self.label_positions.items()
            })
            
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="nk446420",
                database="EOL"
            )
            cursor = conn.cursor()
            
            update_query = """
            UPDATE TBL_MODEL_MASTER 
            SET MM_LABEL_POSITIONS = %s 
            WHERE MM_PART_NUMBER = %s
            """
            cursor.execute(update_query, (positions_json, self.current_part_number))
            conn.commit()
            
            cursor.close()
            conn.close()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to save label positions: {err}")

    def reset_labels(self):
        """Reset all labels to their original positions"""
        for label in self.label_widgets.values():
            label.place_forget()  # Remove from image area
            label.pack(in_=self.label_container, side="left", padx=2, expand=True)  # Return to bottom container
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

def main():
    root = tk.Tk()
    app = EOLTesterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
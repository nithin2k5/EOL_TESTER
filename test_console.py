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
        # Configure grid weights for equal space
        self.workspace.grid_columnconfigure(0, weight=1)  # First column
        self.workspace.grid_columnconfigure(1, weight=1)  # Second column
        self.workspace.grid_rowconfigure(0, weight=1)     # First row
        self.workspace.grid_rowconfigure(1, weight=1)     # Second row
        
        # Set minimum size for workspace
        min_quadrant_size = (500, 400)  # Match model_settings.py dimensions
        
        # Create and configure all quadrants with minimum size
        self.q1 = self.create_first_quadrant()
        self.q2 = self.create_second_quadrant()
        self.q3 = self.create_third_quadrant()
        self.q4 = self.create_fourth_quadrant()
        
        # Place quadrants with equal spacing and minimum size
        quadrants = [self.q1, self.q2, self.q3, self.q4]
        positions = [(0,0), (0,1), (1,0), (1,1)]
        
        for quadrant, (row, col) in zip(quadrants, positions):
            quadrant.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
            quadrant.grid_propagate(False)  # Prevent resizing
            quadrant.configure(width=min_quadrant_size[0], height=min_quadrant_size[1])

    def create_first_quadrant(self):
        """Create the first quadrant with layout matching the image."""
        # Set exact size to match model_settings.py
        q1 = tk.Frame(self.workspace, relief="groove", borderwidth=1)
        q1.grid_propagate(False)  # Prevent frame from resizing
        q1.pack_propagate(False)  # Prevent pack from resizing
        q1.configure(width=500, height=400)  # Fixed size
        
        # Model header (reduced height to match model_settings.py)
        self.model_header = tk.Label(q1, 
                              text="MODEL NAME / PART NAME - PART NUMBER",
                              bg="navy", fg="white", 
                              font=("Arial", 12, "bold"),
                              height=1)  # Fixed height
        self.model_header.pack(fill="x")
        
        # Create image container with white background and fixed size
        self.image_container = tk.Frame(q1, bg="white")
        self.image_container.pack(fill="both", expand=True, padx=2, pady=2)
        self.image_container.pack_propagate(False)  # Prevent resizing
        
        # Create frame to hold the image with fixed size
        self.image_frame = tk.Frame(self.image_container, bg='white')
        self.image_frame.place(relwidth=1, relheight=1)
        
        # Create image label with fixed size
        self.image_label = tk.Label(self.image_frame, bg="white")
        self.image_label.pack(fill="both", expand=True)
        
        # Create frame for L1-L15 labels with fixed height
        self.label_frame = tk.Frame(q1, height=30)  # Fixed height
        self.label_frame.pack(fill="x", side="bottom", pady=(0, 2))
        self.label_frame.pack_propagate(False)  # Prevent resizing
        
        # Create bottom status frame with fixed height
        status_frame = tk.Frame(q1, height=40)  # Fixed height
        status_frame.pack(fill="x", side="bottom", pady=(0, 2))
        status_frame.pack_propagate(False)  # Prevent resizing
        
        # Create status buttons
        buttons = [
            ("AUTO", "#00BFFF"),
            ("HOME", "#00BFFF"),
            ("1st PULL\n(Load Test)", "#00BFFF"),
            ("2nd PULL\n(Length Test)", "#00BFFF"),
            ("TEST\nRESULT", "#00BFFF")
        ]
        
        for text, color in buttons:
            btn = tk.Label(status_frame,
                          text=text,
                          bg=color,
                          fg="black",
                          font=("Arial", 10, "bold"),
                          relief="raised",
                          borderwidth=1,
                          padx=5,
                          pady=3)
            btn.pack(side="left", fill="x", expand=True, padx=2)
        
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
            "No",
            "Description",
            "Device",
            "Unit",
            "Normal Min",
            "Normal Max"
        )
        self.spec_tree = ttk.Treeview(q2, columns=columns, show="headings", height=10)
        
        # Configure columns with specific widths
        column_widths = {
            "No": 50,
            "Description": 200,
            "Device": 100,
            "Unit": 80,
            "Normal Min": 100,
            "Normal Max": 100
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
        self.alc_entry = tk.Entry(bottom_frame, bg="yellow", 
                            font=("Arial", 10),
                            justify="center")
        self.alc_entry.insert(0, "ALC CODE")
        self.alc_entry.pack(side="right", padx=(1, 2), ipady=1)
        
        # Clear default text on focus
        self.alc_entry.bind("<FocusIn>", self.clear_alc_entry)
        # Bind Enter key to process ALC code
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

    def on_label_drag(self, event):
        """Handle label dragging."""
        label = event.widget
        x = label.winfo_x() + event.x - label._drag_start_x
        y = label.winfo_y() + event.y - label._drag_start_y
        label.place(x=x, y=y)

    def stop_label_drag(self, event):
        """Handle end of label drag."""
        label = event.widget
        # Save the new position
        print(f"Label {label.cget('text')} dropped at x={label.winfo_x()}, y={label.winfo_y()}")

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
                area_width = self.image_label.winfo_width()
                area_height = self.image_label.winfo_height()
                
                # Calculate scaling to fit while maintaining aspect ratio
                img_width, img_height = image.size
                scale = min(area_width/img_width, area_height/img_height)
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                if self.image_label:
                    self.image_label.destroy()
                    
                self.image_label = tk.Label(self.image_container, image=photo, bg="white")
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
                
                # Store current part number
                self.current_part_number = part_number
                
                # Load image if path exists
                if image_path and os.path.exists(image_path):
                    if self.load_image_with_path(image_path):
                        if label_coordinates:
                            try:
                                # Parse the JSON coordinates data
                                coordinates_data = json.loads(label_coordinates)
                                # Place labels according to exact coordinates
                                self.place_labels_from_positions(coordinates_data)
                            except json.JSONDecodeError as e:
                                print(f"Warning: Invalid label coordinate data: {e}")
                
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
                
                # Clear and populate treeview
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
        """Load image from path with exact sizing to match model_settings.py"""
        try:
            # Reset any existing label positions
            self.reset_labels()
            
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            image = Image.open(image_path)
            
            # Get exact container dimensions
            container_width = 500  # Fixed width
            container_height = 300  # Fixed height for image area
            
            # Calculate scaling to fit while maintaining aspect ratio
            img_width, img_height = image.size
            scale = min(container_width/img_width, container_height/img_height)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            # Resize image
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(resized_image)
            
            if self.image_label:
                self.image_label.destroy()
            
            self.image_label = tk.Label(self.image_container, image=photo, bg="white")
            self.image_label.image = photo
            
            # Center the image in the fixed space
            x_pos = (container_width - new_width) // 2
            y_pos = (container_height - new_height) // 2
            self.image_label.place(x=x_pos, y=y_pos)
            
            self.image_loaded = True
            self.current_image_path = image_path
            print(f"Successfully loaded image: {image_path}")
            return True
            
        except Exception as e:
            self.image_loaded = False
            print(f"Error loading image: {str(e)}")
            messagebox.showerror("Error", f"Error loading image: {str(e)}")
            return False

    def place_labels_from_positions(self, coordinates_data):
        try:
            # Clear existing labels
            for label in getattr(self, 'placed_labels', {}).values():
                label.destroy()
            self.placed_labels = {}
            
            # Clear label frame
            for widget in self.label_frame.winfo_children():
                widget.destroy()
            
            # Create labels L1-L15
            for i in range(1, 16):
                label_num = str(i)
                label_text = f"L{i}"
                
                if label_num in coordinates_data:
                    # Create label with exact same properties as model_settings.py
                    new_label = tk.Label(self.image_container,  # Use same parent as model_settings
                                       text=label_text,
                                       bg="yellow",
                                       fg="black",
                                       font=("Arial", 10, "bold"),
                                       width=4,
                                       relief="raised",
                                       borderwidth=2)
                    
                    # Use exact coordinates from database
                    x = float(coordinates_data[label_num].get('x', 0))
                    y = float(coordinates_data[label_num].get('y', 0))
                    
                    # Place label at exact position
                    new_label.place(x=x, y=y)
                    
                    self.placed_labels[label_text] = new_label
                    print(f"Placed {label_text} at x={x}, y={y}")  # Debug info
                else:
                    # Bottom frame labels
                    bottom_label = tk.Label(self.label_frame,
                                          text=label_text,
                                          bg="yellow",
                                          fg="black",
                                          font=("Arial", 8, "bold"),
                                          width=4,
                                          relief="raised",
                                          borderwidth=1)
                    bottom_label.pack(side="left", padx=1)

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
            label.pack(in_=self.label_container, side="left", padx=2, expand=True)
        
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

    def clear_alc_entry(self, event):
        """Clear the default text when entry is focused"""
        if self.alc_entry.get() == "ALC CODE":
            self.alc_entry.delete(0, tk.END)

    def process_alc_code(self, event=None):
        """Process the entered ALC code"""
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

            # Query to get part details based on ALC code
            query = """
            SELECT MM_PART_NUMBER, MM_MODEL_NAME, MM_IMAGE_PATH, 
                   MM_LABEL_COORDINATES, MM_VENDOR_CODE, MM_EO_NUMBER, 
                   MM_SPECIAL_DATA, MM_INITIAL_ID, MM_SUPPLIER_SECTION
            FROM TBL_MODEL_MASTER 
            WHERE MM_ALC_CODE = %s
            """
            cursor.execute(query, (alc_code,))
            result = cursor.fetchone()

            if result:
                (part_number, model_name, image_path, label_coordinates,
                 vendor_code, eo_number, special_data, initial_id,
                 supplier_section) = result

                # Store the current part number
                self.current_part_number = part_number

                # Update message label
                self.message_label.config(
                    text=f"Model: {model_name} | Part Number: {part_number}",
                    fg="green"
                )

                # Load image if path exists
                if image_path and os.path.exists(image_path):
                    if self.load_image_with_path(image_path):
                        if label_coordinates:
                            try:
                                coordinates = json.loads(label_coordinates)
                                self.place_labels_from_positions(coordinates)
                            except json.JSONDecodeError:
                                print(f"Warning: Invalid label coordinate data for ALC code {alc_code}")

                # Retrieve and display specifications
                self.retrieve_part_specifications(part_number)

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
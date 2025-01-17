import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import mysql.connector

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
        
        self.setup_gui()

    def setup_gui(self):
        # Main container
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)

        # Title bar with INFAC logo
        self.create_title_bar()
        
        # Main workspace with reduced padding
        self.workspace = tk.Frame(self.main_container)
        self.workspace.pack(fill="both", expand=True, padx=2, pady=2)
        
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
        # Configure grid weights
        self.workspace.grid_columnconfigure(0, weight=1)
        self.workspace.grid_columnconfigure(1, weight=1)
        self.workspace.grid_rowconfigure(0, weight=1)
        self.workspace.grid_rowconfigure(1, weight=1)
        
        # Create quadrants with minimal padding
        self.q1 = self.create_first_quadrant()
        self.q1.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        
        self.q2 = self.create_second_quadrant()
        self.q2.grid(row=0, column=1, sticky="nsew", padx=1, pady=1)
        
        self.q3 = self.create_third_quadrant()
        self.q3.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)
        
        self.q4 = self.create_fourth_quadrant()
        self.q4.grid(row=1, column=1, sticky="nsew", padx=1, pady=1)

    def create_first_quadrant(self):
        q1 = tk.Frame(self.workspace, relief="groove", borderwidth=1, width=500, height=400)
        q1.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        q1.grid_propagate(False)  # Prevent resizing to ensure fixed size
        
        # Model header
        model_header = tk.Label(q1, 
                              text="MODEL NAME / PART NAME - PART NUMBER",
                              bg="navy", fg="white", 
                              font=("Arial", 12, "bold"))
        model_header.pack(fill="x")
        
        # Label strip (L0-L15)
        label_frame = tk.Frame(q1)
        label_frame.pack(fill="x", pady=5)
        
        # Store labels in a dictionary for easy access
        self.label_widgets = {}
        
        for i in range(16):
            label = tk.Label(label_frame, text=f"L{i}", width=4, 
                           relief="raised", bg="lightgray")
            label.pack(side="left", padx=2)
            self.label_widgets[f"L{i}"] = label
            # Note: Drag bindings will be added only after image upload
        
        # Image/Workspace area (white background)
        self.image_area = tk.Frame(q1, bg="white")
        self.image_area.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add image label placeholder
        self.image_label = None
        self.image_loaded = False  # Track if image is loaded
        
        # Control buttons at bottom
        button_frame = tk.Frame(q1)
        button_frame.pack(fill="x", side="bottom", pady=5)
        
        buttons = [
            ("AUTO", self.auto_command),
            ("HOME", self.home_command),
            ("1st PULL\n(Load Test)", self.first_pull_command),
            ("2nd PULL\n(Length Test)", self.second_pull_command),
            ("TEST\nRESULT", self.test_result_command)
        ]
        
        for text, command in buttons:
            btn = tk.Button(button_frame, text=text, 
                          bg="#00BFFF", fg="black",
                          width=15, height=2,
                          command=command)
            btn.pack(side="left", padx=2, expand=True)
        
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
        
        for col in columns:
            self.spec_tree.heading(col, text=col)
            self.spec_tree.column(col, width=100)
            
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
        q3.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        
        # Add graph area
        self.create_graph_area(q3)
        
        return q3

    def create_fourth_quadrant(self):
        q4 = tk.Frame(self.workspace, relief="groove", borderwidth=1)
        q4.grid(row=1, column=1, sticky="nsew", padx=1, pady=1)
        
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
        next_btn = tk.Button(bottom_frame, text="CLICK HERE TO MOVE TO NEXT MODEL",
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
        
        # Load Graph Section
        load_graph_frame = tk.Frame(graph_container, bg="black")
        load_graph_frame.pack(fill="both", expand=True, pady=(5,0))
        
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
        length_graph_frame.pack(fill="both", expand=True, pady=(5,5))
        
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
        if self.image_loaded:
            self.selected_label = event.widget
            self.selected_label.startX = event.x
            self.selected_label.startY = event.y
            self.selected_label.lift()

    def on_label_drag(self, event):
        if self.image_loaded and self.selected_label:
            x = self.selected_label.winfo_x() + event.x - self.selected_label.startX
            y = self.selected_label.winfo_y() + event.y - self.selected_label.startY
            
            # Get image area boundaries
            image_x = self.image_area.winfo_x()
            image_y = self.image_area.winfo_y()
            image_width = self.image_area.winfo_width()
            image_height = self.image_area.winfo_height()
            
            # Keep label within image area bounds
            x = max(image_x, min(x, image_x + image_width - self.selected_label.winfo_width()))
            y = max(image_y, min(y, image_y + image_height - self.selected_label.winfo_height()))
            
            self.selected_label.place(x=x, y=y)

    def stop_label_drag(self, event):
        if self.image_loaded and self.selected_label:
            self.label_positions[self.selected_label.cget("text")] = (
                self.selected_label.winfo_x(),
                self.selected_label.winfo_y()
            )
            self.selected_label = None

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

    def retrieve_part_specifications(self):
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="nk446420",
                database="EOL"
            )
            cursor = conn.cursor()
            
            query = """
            SELECT MS_DESCRIPTION, MS_DEVICE, MS_UNIT, MS_MASTER_MIN, MS_MASTER_MAX, MS_NORMAL_MIN, MS_NORMAL_MAX
            FROM TBL_MODEL_SPECIFICATION
            """
            
            cursor.execute(query)
            for row in cursor.fetchall():
                self.spec_tree.insert('', 'end', values=row)
            
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to retrieve specifications: {err}")

def main():
    root = tk.Tk()
    app = EOLTesterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
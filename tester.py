import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

class DraggableLabelBoxApp:
    def __init__(self, root):  # Corrected constructor method
        self.root = root
        self.root.title("Draggable Label Boxes")

        # Canvas for the image
        self.canvas = tk.Canvas(root, width=800, height=600, bg="white")
        self.canvas.pack(fill="both", expand=True)

        # Variables for tracking dragging
        self.current_item = None
        self.start_x = 0
        self.start_y = 0

        # Add buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack()
        tk.Button(btn_frame, text="Load Image", command=self.load_image).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Add Label Box", command=self.add_label_box).pack(side="left", padx=5)

        # Load a default image or placeholder
        self.image = None
        self.image_tk = None

    def load_image(self):
        """Load an image into the canvas."""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", ".png;.jpg;.jpeg;.bmp")])
        if not file_path:
            return

        # Load and resize the image
        self.image = Image.open(file_path)
        self.image = self.image.resize((800, 600), Image.ANTIALIAS)  # Resize to fit the canvas
        self.image_tk = ImageTk.PhotoImage(self.image)

        # Display the image on the canvas
        self.canvas.create_image(0, 0, anchor="nw", image=self.image_tk)

    def add_label_box(self):
        """Add a draggable label box with blue foreground and label 'L1'."""
        x1, y1, x2, y2 = 100, 100, 200, 150  # Default box coordinates
        label_box = self.canvas.create_rectangle(x1, y1, x2, y2, outline="black", fill="grey", width=2, tags="label_box")
        label_id = self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text="L1", fill="blue", tags="label_text")
        
        self.canvas.tag_bind(label_box, "<ButtonPress-1>", self.on_press)
        self.canvas.tag_bind(label_box, "<B1-Motion>", self.on_drag)
        self.canvas.tag_bind(label_box, "<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        """Handle the start of a drag."""
        self.start_x = event.x
        self.start_y = event.y
        self.current_item = self.canvas.find_closest(event.x, event.y)[0]

    def on_drag(self, event):
        """Handle the dragging motion."""
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.canvas.move(self.current_item, dx, dy)

        # Update label position
        text_item = self.canvas.find_withtag('label_text')[0]
        bbox = self.canvas.bbox(self.current_item)
        self.canvas.coords(text_item, (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)

        self.start_x = event.x
        self.start_y = event.y

    def on_release(self, event):
        """Handle the end of a drag."""
        self.current_item = None

# Run the application
if __name__ == "__main__":  # Corrected entry point
    root = tk.Tk()
    app = DraggableLabelBoxApp(root)
    root.mainloop()
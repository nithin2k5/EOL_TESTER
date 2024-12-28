from tkinter import Tk, Frame, Label, Button, Canvas, PhotoImage
import os

def create_eol_tester_gui():
    """Creates the GUI for the EOL (End of Line) Tester."""

    # Create the main window
    root = Tk()
    root.title("EOL (End of Line) Tester")
    root.attributes('-fullscreen', True)  # Make the window full-screen

    # Create frames for the four quadrants
    quadrant1 = Frame(root, bg="lightblue")
    quadrant2 = Frame(root, bg="lightgreen")
    quadrant3 = Frame(root, bg="lightyellow")
    quadrant4 = Frame(root, bg="pink")

    # Grid layout for the quadrants
    quadrant1.grid(row=0, column=0, sticky="nsew")
    quadrant2.grid(row=0, column=1, sticky="nsew")
    quadrant3.grid(row=1, column=0, sticky="nsew")
    quadrant4.grid(row=1, column=1, sticky="nsew")

    # Configure column and row weights for equal size
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)

    # Load and display the image in quadrant 1
    image_path = "path_to_your_image.png"  # Replace with the actual path
    image = PhotoImage(file=image_path)
    image_label = Label(quadrant1, image=image)
    image_label.pack()

    # ... (rest of the GUI elements for other quadrants) ...

    root.mainloop()

if __name__ == "__main__":
    create_eol_tester_gui()
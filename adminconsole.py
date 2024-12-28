import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class AdminConsole:
    def __init__(self, root):
        self.root = root
        self.root.title("ADMIN CONSOLE")
        
        # Make it full screen
        self.root.state('zoomed')
        
        # Configure the main background color
        self.root.configure(bg='pink')
        
        # Create and setup the UI
        self.setup_ui()

    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg='pink', height=80)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # INFAC INDIA logo placeholder (left side)
        logo_label = tk.Label(header_frame, text="INFAC\nINDIA", bg='pink', font=('Arial', 12, 'bold'))
        logo_label.pack(side=tk.LEFT, padx=20)
        
        # EOL TESTER title (center)
        title_label = tk.Label(
            header_frame, 
            text="EOL (END OF LINE) TESTER",
            bg='pink',
            font=('Arial', 24, 'bold')
        )
        title_label.pack(expand=True)

        # Main content frame
        content_frame = tk.Frame(self.root, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Top section container
        top_container = tk.Frame(content_frame, bg='white')
        top_container.pack(fill=tk.X, padx=10, pady=10)

        # Left side - Entry fields (70% of width)
        left_frame = tk.Frame(top_container, bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Fields configuration
        fields = [
            "EMPLOYEE FULL NAME :",
            "EMPLOYEE NUMBER :",
            "PASSWORD :",
            "DESIGNATION :",
            "DEPARTMENT :",
            "MOBILE NUMBER :"
        ]

        # Create a frame for organizing entry fields
        entries_frame = tk.Frame(left_frame, bg='white')
        entries_frame.pack(anchor='w', padx=20)

        self.entries = {}
        for field in fields:
            frame = tk.Frame(entries_frame, bg='white')
            frame.pack(fill=tk.X, pady=5)
            
            label = tk.Label(
                frame, 
                text=field, 
                bg='white', 
                anchor='e',
                width=20,
                font=('Arial', 10, 'bold')
            )
            label.pack(side=tk.LEFT, padx=5)
            
            entry = tk.Entry(frame, width=50)
            entry.pack(side=tk.LEFT, padx=5)
            self.entries[field] = entry

        # Right side - Image and buttons (30% of width)
        right_frame = tk.Frame(top_container, bg='white')
        right_frame.pack(side=tk.RIGHT, padx=20)

        # Image placeholder with dashed border
        self.image_frame = tk.Frame(
            right_frame, 
            bg='white', 
            relief='solid',
            borderwidth=1,
            width=150,
            height=180
        )
        self.image_frame.pack(pady=(0, 10))
        self.image_frame.pack_propagate(False)

        # Buttons container
        buttons_frame = tk.Frame(right_frame, bg='white')
        buttons_frame.pack(fill=tk.X)

        # Buttons configuration
        buttons = [
            ("➕", "green", "Add"),
            ("✏️", "orange", "Edit"),
            ("💾", "blue", "Save"),
            ("🗑️", "red", "Delete")
        ]

        # Create buttons horizontally
        for symbol, color, tooltip in buttons:
            btn = tk.Button(
                buttons_frame,
                text=symbol,
                bg='white',
                font=('Arial', 14),
                width=2,
                height=1,
                relief='raised',
                borderwidth=1
            )
            btn.pack(side=tk.LEFT, padx=2)

        # Treeview section
        tree_frame = tk.Frame(content_frame, bg='white')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(20, 10))

        # Configure columns
        columns = ('NO', 'EMPLOYEE FULL NAME', 'EMPLOYEE NUMBER', 
                  'DESIGNATION', 'DEPARTMENT', 'MOBILE NUMBER')
        
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Column widths
        widths = {
            'NO': 50,
            'EMPLOYEE FULL NAME': 200,
            'EMPLOYEE NUMBER': 150,
            'DESIGNATION': 150,
            'DEPARTMENT': 150,
            'MOBILE NUMBER': 150
        }
        
        # Configure column headings
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], anchor='center')

        # Configure treeview style
        style = ttk.Style()
        style.configure(
            "Treeview.Heading",
            background="black",
            foreground="white",
            relief="flat",
            font=('Arial', 10, 'bold')
        )
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Footer
        footer_text = "Powered By: IRACRAT TECHNOLOGIES. Contact: INFO@IRACRAT.COM, (+91) 99623 44614."
        footer = tk.Label(
            self.root,
            text=footer_text,
            bg='pink',
            font=('Arial', 8)
        )
        footer.pack(side=tk.BOTTOM, pady=5)

    def add_image_to_frame(self, image_path):
        try:
            # Open and resize image
            image = Image.open(image_path)
            image = image.resize((140, 170), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # Create label and display image
            image_label = tk.Label(self.image_frame, image=photo, bg='white')
            image_label.image = photo  # Keep a reference
            image_label.pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            print(f"Error loading image: {e}")

def main():
    root = tk.Tk()
    app = AdminConsole(root)
    root.mainloop()

if __name__ == "__main__":
    main()
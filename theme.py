import tkinter as tk
from tkinter import ttk

def apply_professional_theme(root):
    # Enhanced Professional Light Theme Colors
    BG_MAIN = '#f0f4f8'  # Soft, cool blue-gray for the app background
    BG_ALT = '#ffffff'   # Pure white for panels and inputs
    FG_MAIN = '#1e293b'  # Dark slate for text
    FG_ALT = '#0f172a'   # Almost black for emphasis
    ACCENT = '#3b82f6'   # Vibrant blue accent
    ACCENT_HOVER = '#2563eb' # Deeper blue for hover
    BORDER = '#cbd5e1'   # Soft gray border
    
    # Set the overall tk palette for a modern light theme
    root.tk_setPalette(
        background=BG_MAIN,
        foreground=FG_MAIN,
        activeBackground=BG_ALT,
        activeForeground=FG_ALT,
        selectColor=BG_ALT,
        insertBackground='#000000' # Cursor color
    )
    
    # Configure ttk styles
    style = ttk.Style()
    if 'clam' in style.theme_names():
        style.theme_use('clam')
    
    # General ttk configuration
    style.configure('.', 
                    background=BG_MAIN, 
                    foreground=FG_MAIN,
                    fieldbackground=BG_ALT,
                    troughcolor=BG_ALT,
                    selectbackground=ACCENT,
                    selectforeground='#ffffff',
                    bordercolor=BORDER,
                    lightcolor=BG_MAIN,
                    darkcolor=BG_MAIN)

    # Specific ttk widget styles (Buttons are now vibrant blue)
    style.configure('TButton', padding=6, relief='flat', background=ACCENT, foreground='#ffffff', font=('Arial', 10, 'bold'))
    style.map('TButton', 
              background=[('active', ACCENT_HOVER), ('pressed', '#1d4ed8')],
              foreground=[('active', '#ffffff')])
    
    style.configure('TFrame', background=BG_MAIN)
    style.configure('TLabelframe', background=BG_ALT, bordercolor=BORDER, borderwidth=1)
    style.configure('TLabelframe.Label', background=BG_ALT, foreground=ACCENT, font=('Arial', 10, 'bold'))
    
    style.configure('TNotebook', background=BG_MAIN, tabmargins=[2, 5, 2, 0])
    style.configure('TNotebook.Tab', background='#e2e8f0', foreground=FG_MAIN, padding=[12, 4], bordercolor=BORDER, font=('Arial', 9, 'bold'))
    style.map('TNotebook.Tab', 
              background=[('selected', ACCENT)], 
              foreground=[('selected', '#ffffff')],
              expand=[('selected', [1, 1, 1, 0])])
    
    # Monkey patch standard widgets to strip ANY background/foreground except semantic colors
    def patch_widget(widget_class):
        original_init = widget_class.__init__
        def new_init(self, master=None, cnf=None, **kw):
            if cnf is None:
                cnf = {}
            # Semantic colors to KEEP (we don't want to break red/green pass/fail buttons)
            semantic_colors = ['red', 'green', 'blue', 'orange', 'yellow', 'darkred', 'navy', '#ff0000', '#00ff00', '#0000ff']
            
            bg_val = kw.get('bg') or kw.get('background') or cnf.get('bg') or cnf.get('background')
            is_stripped = False
            # If the background is set and it's NOT a semantic color, strip it to force the modern theme
            if isinstance(bg_val, str) and bg_val.lower() not in semantic_colors:
                kw.pop('bg', None)
                kw.pop('background', None)
                if 'bg' in cnf: del cnf['bg']
                if 'background' in cnf: del cnf['background']
                is_stripped = True
                
            fg_val = kw.get('fg') or kw.get('foreground') or cnf.get('fg') or cnf.get('foreground')
            if isinstance(fg_val, str) and fg_val.lower() not in semantic_colors:
                kw.pop('fg', None)
                kw.pop('foreground', None)
                if 'fg' in cnf: del cnf['fg']
                if 'foreground' in cnf: del cnf['foreground']
                
            # If this is a standard tk.Button and we stripped its color, inject the vibrant accent!
            if widget_class.__name__ == 'Button' and (is_stripped or not bg_val):
                kw['bg'] = ACCENT
                kw['fg'] = '#ffffff'
                kw['activebackground'] = ACCENT_HOVER
                kw['activeforeground'] = '#ffffff'
                kw['relief'] = 'flat'
                kw['bd'] = 0
                
            original_init(self, master, cnf, **kw)
            
        def new_configure(self, cnf=None, **kw):
            if cnf is None: cnf = {}
            # Strip generic colors from dynamic config updates
            semantic_colors = ['red', 'green', 'blue', 'orange', 'yellow', 'darkred', 'navy', '#ff0000', '#00ff00', '#0000ff']
            
            bg_val = kw.get('bg') or kw.get('background') or cnf.get('bg') or cnf.get('background')
            if isinstance(bg_val, str) and bg_val.lower() not in semantic_colors:
                kw.pop('bg', None)
                kw.pop('background', None)
                if 'bg' in cnf: del cnf['bg']
                if 'background' in cnf: del cnf['background']
                if widget_class.__name__ == 'Button':
                    kw['bg'] = ACCENT
                
            fg_val = kw.get('fg') or kw.get('foreground') or cnf.get('fg') or cnf.get('foreground')
            if isinstance(fg_val, str) and fg_val.lower() not in semantic_colors:
                kw.pop('fg', None)
                kw.pop('foreground', None)
                if 'fg' in cnf: del cnf['fg']
                if 'foreground' in cnf: del cnf['foreground']
                if widget_class.__name__ == 'Button':
                    kw['fg'] = '#ffffff'
                
            return original_configure(self, cnf, **kw)
            
        original_configure = widget_class.configure
        widget_class.__init__ = new_init
        widget_class.configure = new_configure
        widget_class.config = new_configure

    # Apply patch to common widgets
    patch_widget(tk.Frame)
    patch_widget(tk.Label)
    patch_widget(tk.Button)
    patch_widget(tk.Checkbutton)
    patch_widget(tk.Radiobutton)
    patch_widget(tk.Entry)
    patch_widget(tk.Listbox)
    patch_widget(tk.Canvas)
    patch_widget(tk.Text)
    patch_widget(tk.Spinbox)
    patch_widget(tk.OptionMenu)
    patch_widget(tk.Tk)
    patch_widget(tk.Toplevel)

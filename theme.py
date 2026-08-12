import tkinter as tk
from tkinter import ttk

def apply_professional_theme(root):
    # Professional Light Theme Colors
    BG_MAIN = '#ffffff'
    BG_ALT = '#f3f4f6'
    FG_MAIN = '#1f2937'
    FG_ALT = '#111827'
    ACCENT = '#2563eb'
    BORDER = '#d1d5db'
    
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
                    darkcolor=BG_ALT)

    # Specific ttk widget styles
    style.configure('TButton', padding=6, relief='flat', background=BG_ALT, foreground=FG_MAIN, bordercolor=BORDER, borderwidth=1)
    style.map('TButton', 
              background=[('active', '#e5e7eb'), ('pressed', '#d1d5db')],
              foreground=[('active', FG_ALT)])
    
    style.configure('TFrame', background=BG_MAIN)
    style.configure('TLabelframe', background=BG_MAIN, bordercolor=BORDER, borderwidth=1)
    style.configure('TLabelframe.Label', background=BG_MAIN, foreground=ACCENT, font=('Arial', 10, 'bold'))
    
    style.configure('TNotebook', background=BG_MAIN, tabmargins=[2, 5, 2, 0])
    style.configure('TNotebook.Tab', background=BG_ALT, foreground=FG_MAIN, padding=[12, 4], bordercolor=BORDER)
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
            # If the background is set and it's NOT a semantic color, strip it to force the modern theme
            if isinstance(bg_val, str) and bg_val.lower() not in semantic_colors:
                kw.pop('bg', None)
                kw.pop('background', None)
                if 'bg' in cnf: del cnf['bg']
                if 'background' in cnf: del cnf['background']
                
            fg_val = kw.get('fg') or kw.get('foreground') or cnf.get('fg') or cnf.get('foreground')
            if isinstance(fg_val, str) and fg_val.lower() not in semantic_colors:
                kw.pop('fg', None)
                kw.pop('foreground', None)
                if 'fg' in cnf: del cnf['fg']
                if 'foreground' in cnf: del cnf['foreground']
                
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
                
            fg_val = kw.get('fg') or kw.get('foreground') or cnf.get('fg') or cnf.get('foreground')
            if isinstance(fg_val, str) and fg_val.lower() not in semantic_colors:
                kw.pop('fg', None)
                kw.pop('foreground', None)
                if 'fg' in cnf: del cnf['fg']
                if 'foreground' in cnf: del cnf['foreground']
                
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

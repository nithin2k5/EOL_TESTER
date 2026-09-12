"""Shared look and feel for every console.

One light, industrial palette: neutral surfaces, a single blue accent, and
colour reserved for meaning - green passes, red failures, amber warnings.

Pages were written with their own colour literals scattered through them,
so rather than rewriting thousands of call sites this module translates
those literals to palette tokens as widgets are built, and guarantees that
whatever background a control ends up with, its text stays readable on it.

    import ui
    ui.apply(root)
"""

import tkinter as tk
from tkinter import ttk

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------

APP_BG = '#eef2f6'      # page background
SURFACE = '#ffffff'     # panels and cards
SUBTLE = '#f4f7fa'      # input wells, alternating rows
BORDER = '#cbd5e1'
BORDER_STRONG = '#94a3b8'

TEXT = '#1f2933'
TEXT_MUTED = '#64748b'
TEXT_ON_ACCENT = '#ffffff'

ACCENT = '#1d4ed8'
ACCENT_HOVER = '#1e40af'
ACCENT_ACTIVE = '#1e3a8a'

SUCCESS = '#15803d'
SUCCESS_HOVER = '#166534'
DANGER = '#b91c1c'
DANGER_HOVER = '#991b1b'
WARNING = '#b45309'
INFO = '#0369a1'

# Row shading for result grids
ROW_BAND = '#fef9c3'
ROW_PLAIN = '#ffffff'

# Type scale
FONT_FAMILY = 'Segoe UI'
FONT_BODY = (FONT_FAMILY, 10)
FONT_BODY_BOLD = (FONT_FAMILY, 10, 'bold')
FONT_SMALL = (FONT_FAMILY, 9)
FONT_SECTION = (FONT_FAMILY, 11, 'bold')
FONT_TITLE = (FONT_FAMILY, 20, 'bold')

# Spacing step, so padding is consistent rather than ad hoc
PAD = 6
PAD_LARGE = 12

# --------------------------------------------------------------------------
# Translating the colour literals already in the pages
# --------------------------------------------------------------------------

# Colours that carry meaning keep it; the rest collapse onto the neutrals.
_BACKGROUND_MAP = {
    # neutrals
    'white': SURFACE, '#ffffff': SURFACE, '#fff': SURFACE,
    '#f0f0f0': SUBTLE, '#f5f5f5': SUBTLE, '#f8f9fa': SUBTLE,
    '#e0e0e0': SUBTLE, 'lightgray': SUBTLE, 'lightgrey': SUBTLE,
    'gray': SUBTLE, 'grey': SUBTLE, '#2b2b2b': SURFACE,
    'pink': SURFACE, '#ffb6c1': SUBTLE, '#f5e6e8': SURFACE,
    '#e8f6e9': SURFACE, '#e6eef5': SURFACE, '#f5f0e6': SURFACE,
    'lightyellow': ROW_BAND, '#fff9c4': ROW_BAND, '#fef9c3': ROW_BAND,
    # accent family
    'navy': ACCENT, 'darkblue': ACCENT, 'blue': ACCENT,
    'deepskyblue': ACCENT, '#00bfff': ACCENT, '#1e88e5': ACCENT,
    '#3498db': ACCENT, '#2980b9': ACCENT_HOVER, '#0d6efd': ACCENT,
    '#2c3e50': ACCENT, '#add8e6': SUBTLE,
    # success family
    'green': SUCCESS, '#2ecc71': SUCCESS, '#27ae60': SUCCESS_HOVER,
    '#4caf50': SUCCESS, '#198754': SUCCESS, '#00ff00': SUCCESS,
    '#90ee90': '#dcfce7',
    # danger family
    'red': DANGER, 'darkred': DANGER, '#e74c3c': DANGER,
    '#c0392b': DANGER_HOVER, '#f44336': DANGER, '#ff4d4d': DANGER,
    '#dc3545': DANGER, '#ffcccb': '#fee2e2',
    # warning family
    'yellow': WARNING, 'orange': WARNING, '#ffd700': WARNING,
    '#ffeb3b': WARNING, '#ff4500': WARNING,
    # purple used for the edit action
    '#9b59b6': ACCENT, '#8e44ad': ACCENT_HOVER,
    '#95a5a6': TEXT_MUTED, '#7f8c8d': TEXT_MUTED,
}

_FOREGROUND_MAP = {
    'white': TEXT_ON_ACCENT, '#ffffff': TEXT_ON_ACCENT,
    'black': TEXT, '#000000': TEXT, '#1a1a1a': TEXT, '#2b2b2b': TEXT,
    '#333333': TEXT, '#424242': TEXT, '#2c3e50': TEXT,
    '#999999': TEXT_MUTED, '#666666': TEXT_MUTED,
    'gray': TEXT_MUTED, 'grey': TEXT_MUTED, 'lightgray': TEXT_MUTED,
    'green': SUCCESS, '#00ff00': SUCCESS, '#4caf50': SUCCESS,
    'red': DANGER, 'darkred': DANGER, '#ff0000': DANGER,
    'navy': ACCENT, 'blue': ACCENT, 'darkblue': ACCENT,
    'orange': WARNING, 'yellow': WARNING,
}

# Backgrounds that must survive untouched - the chart canvases rely on them.
_KEEP_BACKGROUND = {'black', '#000000'}

_NAMED_RGB = {
    'white': (255, 255, 255), 'black': (0, 0, 0), 'red': (255, 0, 0),
    'green': (0, 128, 0), 'blue': (0, 0, 255), 'navy': (0, 0, 128),
    'darkred': (139, 0, 0), 'darkblue': (0, 0, 139), 'orange': (255, 165, 0),
    'yellow': (255, 255, 0), 'pink': (255, 192, 203), 'gray': (128, 128, 128),
    'grey': (128, 128, 128), 'lightgray': (211, 211, 211),
    'lightgrey': (211, 211, 211), 'deepskyblue': (0, 191, 255),
    'lightyellow': (255, 255, 224), 'cyan': (0, 255, 255),
}


def _rgb(color):
    """Best effort RGB for a colour literal, or None when unrecognised."""
    if not isinstance(color, str) or not color:
        return None

    value = color.strip().lower()
    if value in _NAMED_RGB:
        return _NAMED_RGB[value]

    if value.startswith('#'):
        digits = value[1:]
        if len(digits) == 3:
            digits = ''.join(c * 2 for c in digits)
        if len(digits) == 6:
            try:
                return tuple(int(digits[i:i + 2], 16) for i in (0, 2, 4))
            except ValueError:
                return None
    return None


def _channel(value):
    """One sRGB channel converted to linear light."""
    value = value / 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _luminance(color):
    """Relative luminance, gamma corrected the way contrast ratios expect."""
    rgb = _rgb(color)
    if rgb is None:
        return None
    red, green, blue = (_channel(channel) for channel in rgb)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _ratio(first, second):
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def readable_on(background, dark=TEXT, light=TEXT_ON_ACCENT):
    """Pick whichever text colour reads better on this background."""
    base = _luminance(background)
    if base is None:
        return dark

    dark_luminance = _luminance(dark)
    light_luminance = _luminance(light)
    if dark_luminance is None or light_luminance is None:
        return dark

    return dark if _ratio(base, dark_luminance) >= _ratio(base, light_luminance) else light


def mix(first, second, amount=0.5):
    """Blend two colours, amount 0 gives the first and 1 the second."""
    left, right = _rgb(first), _rgb(second)
    if left is None or right is None:
        return second
    blended = tuple(round(a + (b - a) * amount) for a, b in zip(left, right))
    return '#%02x%02x%02x' % blended


def _has_contrast(foreground, background):
    """True when these two are far enough apart to read."""
    first = _luminance(foreground)
    second = _luminance(background)
    if first is None or second is None:
        return True  # unknown colour, leave the author's choice alone
    return _ratio(first, second) >= 3.0


def map_background(color):
    if not isinstance(color, str):
        return color
    value = color.strip().lower()
    if value in _KEEP_BACKGROUND:
        return color
    return _BACKGROUND_MAP.get(value, color)


def map_foreground(color):
    if not isinstance(color, str):
        return color
    return _FOREGROUND_MAP.get(color.strip().lower(), color)


# --------------------------------------------------------------------------
# ttk styles
# --------------------------------------------------------------------------

def _configure_ttk():
    style = ttk.Style()
    if 'clam' in style.theme_names():
        style.theme_use('clam')

    style.configure('.',
                    background=APP_BG, foreground=TEXT,
                    fieldbackground=SURFACE, bordercolor=BORDER,
                    lightcolor=APP_BG, darkcolor=APP_BG,
                    troughcolor=SUBTLE, font=FONT_BODY,
                    selectbackground=ACCENT, selectforeground=TEXT_ON_ACCENT)

    style.configure('TFrame', background=APP_BG)
    style.configure('Surface.TFrame', background=SURFACE)
    style.configure('TLabel', background=APP_BG, foreground=TEXT, font=FONT_BODY)
    style.configure('Muted.TLabel', foreground=TEXT_MUTED, font=FONT_SMALL)
    style.configure('Title.TLabel', font=FONT_TITLE, foreground=TEXT)
    style.configure('Section.TLabel', font=FONT_SECTION, foreground=ACCENT)

    style.configure('TLabelframe', background=SURFACE,
                    bordercolor=BORDER, borderwidth=1, relief='solid')
    style.configure('TLabelframe.Label', background=SURFACE,
                    foreground=ACCENT, font=FONT_SECTION)

    style.configure('TButton', padding=(PAD_LARGE, PAD), relief='flat',
                    background=ACCENT, foreground=TEXT_ON_ACCENT,
                    font=FONT_BODY_BOLD, borderwidth=0)
    style.map('TButton',
              background=[('disabled', '#c7d2dd'),
                          ('pressed', ACCENT_ACTIVE),
                          ('active', ACCENT_HOVER)],
              foreground=[('disabled', '#8996a5')])

    for name, base, hover in (('Success', SUCCESS, SUCCESS_HOVER),
                              ('Danger', DANGER, DANGER_HOVER),
                              ('Neutral', SUBTLE, BORDER)):
        text_colour = readable_on(base)
        style.configure(f'{name}.TButton', background=base, foreground=text_colour)
        style.map(f'{name}.TButton',
                  background=[('disabled', '#c7d2dd'), ('active', hover)],
                  foreground=[('disabled', '#8996a5'), ('active', readable_on(hover))])

    style.configure('TEntry', fieldbackground=SURFACE, foreground=TEXT,
                    bordercolor=BORDER, padding=4)
    style.configure('TCombobox', fieldbackground=SURFACE, foreground=TEXT,
                    bordercolor=BORDER, padding=4)

    style.configure('Treeview', background=SURFACE, fieldbackground=SURFACE,
                    foreground=TEXT, rowheight=26, borderwidth=1,
                    bordercolor=BORDER, font=FONT_BODY)
    style.configure('Treeview.Heading', background=SUBTLE, foreground=TEXT,
                    font=FONT_BODY_BOLD, relief='flat', padding=(PAD, PAD))
    style.map('Treeview',
              background=[('selected', ACCENT)],
              foreground=[('selected', TEXT_ON_ACCENT)])
    style.map('Treeview.Heading', background=[('active', BORDER)])

    style.configure('TNotebook', background=APP_BG, tabmargins=[2, 5, 2, 0])
    style.configure('TNotebook.Tab', background=SUBTLE, foreground=TEXT,
                    padding=[PAD_LARGE, PAD], font=FONT_BODY_BOLD)
    style.map('TNotebook.Tab',
              background=[('selected', ACCENT)],
              foreground=[('selected', TEXT_ON_ACCENT)])

    style.configure('TScrollbar', background=SUBTLE, troughcolor=APP_BG,
                    bordercolor=BORDER, arrowcolor=TEXT_MUTED)
    return style


# --------------------------------------------------------------------------
# Normalising the classic tk widgets
# --------------------------------------------------------------------------

_BUTTON_LIKE = ('Button', 'Checkbutton', 'Radiobutton')

# Frames, canvases and toplevels have no foreground option at all, so text
# colour is only ever set on the widgets that actually draw text.
_HAS_FOREGROUND = ('Label', 'Button', 'Checkbutton', 'Radiobutton', 'Entry',
                   'Text', 'Listbox', 'Spinbox', 'LabelFrame', 'Message')

_patched = False


def _normalise(widget_class, options):
    """Translate colour options and make sure the text stays readable."""
    name = widget_class.__name__

    background = options.get('bg', options.get('background'))
    foreground = options.get('fg', options.get('foreground'))

    if isinstance(background, str):
        background = map_background(background)
        options.pop('background', None)
        options['bg'] = background

    takes_foreground = name in _HAS_FOREGROUND

    if isinstance(foreground, str):
        foreground = map_foreground(foreground)
        options.pop('foreground', None)
        if takes_foreground:
            options['fg'] = foreground
        else:
            options.pop('fg', None)

    # A control with a background but no readable text is the whole reason
    # this exists: give it one, or replace one that cannot be read.
    if takes_foreground and isinstance(background, str):
        if not isinstance(foreground, str) or not _has_contrast(foreground, background):
            options['fg'] = readable_on(background)

    if name in _BUTTON_LIKE and isinstance(background, str):
        text_colour = options.get('fg', readable_on(background))
        options.setdefault('activebackground', mix(background, text_colour, 0.15))
        options.setdefault('activeforeground', text_colour)
        options.setdefault('relief', 'flat')
        options.setdefault('borderwidth', 0)
        options.setdefault('cursor', 'hand2')
        # Tk paints a disabled label in a system grey that disappears against
        # a saturated background, so fade the real text colour instead.
        options.setdefault('disabledforeground', mix(background, text_colour, 0.45))

    # Input wells get a visible edge; without a background of their own they
    # inherit a system colour and all but vanish against a white panel.
    if name in ('Entry', 'Text', 'Listbox', 'Spinbox') and not isinstance(background, str):
        options.setdefault('bg', SURFACE)
        options.setdefault('relief', 'solid')
        options.setdefault('borderwidth', 1)
        options.setdefault('highlightthickness', 1)
        options.setdefault('highlightbackground', BORDER)
        options.setdefault('highlightcolor', ACCENT)
        options.setdefault('insertbackground', TEXT)

    return options


def _patch_tk_widgets():
    """Route classic tk widget colours through the palette, once."""
    global _patched
    if _patched:
        return
    _patched = True

    # tk.Tk is deliberately absent: its constructor takes screenName and
    # baseName rather than (master, cnf), so wrapping it breaks any window
    # created after the patch is installed.
    for widget_class in (tk.Frame, tk.LabelFrame, tk.Label, tk.Button,
                         tk.Checkbutton, tk.Radiobutton, tk.Entry, tk.Text,
                         tk.Listbox, tk.Canvas, tk.Spinbox, tk.Toplevel):
        _patch_one(widget_class)


def _patch_one(widget_class):
    original_init = widget_class.__init__
    original_configure = widget_class.configure

    def patched_init(self, master=None, cnf=None, **kw):
        if cnf:
            kw = dict(cnf, **kw)
        # ttk.Entry and ttk.Combobox subclass tkinter.Entry, but they are
        # styled through ttk.Style and reject per-widget colour options.
        if not isinstance(self, ttk.Widget):
            kw = _normalise(widget_class, kw)
        original_init(self, master, {}, **kw)

    def patched_configure(self, cnf=None, **kw):
        if cnf and isinstance(cnf, dict):
            kw = dict(cnf, **kw)
        elif cnf is not None:
            # A plain string means "read this option back"; leave it alone.
            return original_configure(self, cnf, **kw)
        if not kw:
            return original_configure(self)
        if not isinstance(self, ttk.Widget):
            kw = _normalise(widget_class, kw)
        return original_configure(self, **kw)

    widget_class.__init__ = patched_init
    widget_class.configure = patched_configure
    widget_class.config = patched_configure


def apply(root):
    """Give this window the shared look. Safe to call from every page."""
    _patch_tk_widgets()
    style = _configure_ttk()

    try:
        root.configure(bg=APP_BG)
    except tk.TclError:
        pass

    try:
        root.option_add('*Font', FONT_BODY)
    except tk.TclError:
        pass

    return style


# --------------------------------------------------------------------------
# Small building blocks pages can use directly
# --------------------------------------------------------------------------

def page_header(parent, title, right_text=''):
    """A titled bar across the top of a page, with optional right-hand text."""
    header = tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER,
                      highlightthickness=1)
    header.pack(fill='x')

    inner = tk.Frame(header, bg=SURFACE)
    inner.pack(fill='x', padx=PAD_LARGE, pady=PAD_LARGE)

    tk.Label(inner, text=title, bg=SURFACE, fg=TEXT,
             font=FONT_TITLE).pack(side='left')

    if right_text:
        tk.Label(inner, text=right_text, bg=SURFACE, fg=TEXT_MUTED,
                 font=FONT_BODY_BOLD).pack(side='right')

    return header


def section(parent, title, **kwargs):
    """A titled card. Returns the frame to put content in."""
    outer = tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER,
                     highlightthickness=1, **kwargs)

    caption = tk.Label(outer, text=title, bg=SUBTLE, fg=ACCENT,
                       font=FONT_SECTION, anchor='w', padx=PAD, pady=PAD)
    caption.pack(fill='x')

    body = tk.Frame(outer, bg=SURFACE)
    body.pack(fill='both', expand=True, padx=PAD, pady=PAD)

    outer.body = body
    return outer


def scrollable(parent, bg=APP_BG, horizontal=False):
    """A scrolling area. Returns the container; fill `container.body`.

    Pages were laid out at fixed pixel sizes, so on a smaller screen the
    lower rows and right-hand panels simply fall off and cannot be reached.
    Putting the body in one of these keeps every control available.
    """
    container = tk.Frame(parent, bg=bg)
    canvas = tk.Canvas(container, bg=bg, highlightthickness=0)
    inner = tk.Frame(canvas, bg=bg)

    window = canvas.create_window((0, 0), window=inner, anchor='nw')

    vbar = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
    canvas.configure(yscrollcommand=vbar.set)

    hbar = None
    if horizontal:
        hbar = ttk.Scrollbar(container, orient='horizontal', command=canvas.xview)
        canvas.configure(xscrollcommand=hbar.set)

    def on_inner_configure(event):
        canvas.configure(scrollregion=canvas.bbox('all'))

    def on_canvas_configure(event):
        # Stretching the body to the canvas is what lets a narrow page fill
        # the width; a page that scrolls sideways must keep its own width.
        if not horizontal:
            canvas.itemconfigure(window, width=event.width)
        elif event.width > inner.winfo_reqwidth():
            canvas.itemconfigure(window, width=event.width)

    inner.bind('<Configure>', on_inner_configure)
    canvas.bind('<Configure>', on_canvas_configure)

    def on_wheel(event):
        if canvas.winfo_exists():
            canvas.yview_scroll(-1 * (event.delta // 120), 'units')

    canvas.bind_all('<MouseWheel>', on_wheel, add='+')

    # Grid, so both bars sit outside the canvas without overlapping it.
    canvas.grid(row=0, column=0, sticky='nsew')
    vbar.grid(row=0, column=1, sticky='ns')
    if hbar is not None:
        hbar.grid(row=1, column=0, sticky='ew')
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    container.body = inner
    container.canvas = canvas
    return container

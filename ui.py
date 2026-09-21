"""Shared look and feel for every console.

One dark, industrial palette: slate surfaces, a single blue accent, and
colour reserved for meaning - green passes, red failures, amber warnings.

Pages were written with their own colour literals scattered through them,
so rather than rewriting thousands of call sites this module translates
those literals to palette tokens as widgets are built, and guarantees that
whatever background a control ends up with, its text stays readable on it.
That translation is what carries the dark theme into consoles whose own
code still says bg='white'.

    import ui
    ui.apply(root)
"""

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

import icons

# customtkinter defaults to following the OS light/dark setting, which would
# make its rounded widgets drift from this module's fixed light palette.
ctk.set_appearance_mode("dark")

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------
#
# One dark, industrial palette: slate surfaces, a single blue accent, and
# colour reserved for meaning. The status hues are brightened from their
# light-theme values - a mid green or red that reads well on white goes
# muddy against a dark panel.

APP_BG = '#12161c'      # page background
SURFACE = '#1c222b'     # panels and cards
SUBTLE = '#242b35'      # input wells, alternating rows, header strips
BORDER = '#2c3542'
BORDER_STRONG = '#3d4a5c'

TEXT = '#e6e9ee'
TEXT_MUTED = '#9aa5b4'
TEXT_ON_ACCENT = '#ffffff'
# The text colour for the rare control that is filled with a bright colour
# rather than a dark one, so `readable_on` has a genuinely dark option to
# pick when the background is light.
TEXT_ON_LIGHT = '#0f1419'

# Two tones of the one accent. On a dark theme a blue bright enough to read
# as text against a near-black panel is too light to carry white text when
# it is used as a fill, so surfaces get the deeper tone and text the
# brighter one.
ACCENT = '#3b82f6'          # text, icons and borders on dark surfaces
ACCENT_FILL = '#2563eb'     # filled surfaces, which carry TEXT_ON_ACCENT
ACCENT_HOVER = '#1d4ed8'
ACCENT_ACTIVE = '#1e40af'

# Tinted backgrounds, for marking a row as selected without filling it with
# the full accent - a whole column of solid accent reads as a wall, not a
# list, and leaves nothing to say which entry you are actually on.
ACCENT_SOFT = '#1e2d45'
DANGER_SOFT = '#3a1f22'
SUCCESS_SOFT = '#16301f'

# Disabled controls: dark enough to recede, light enough to still be read
# as a control rather than a hole in the panel.
DISABLED_BG = '#232a34'
DISABLED_TEXT = '#5b6775'

SUCCESS = '#22c55e'
SUCCESS_HOVER = '#16a34a'
DANGER = '#ef4444'
DANGER_HOVER = '#dc2626'
WARNING = '#f59e0b'
INFO = '#38bdf8'

# Row shading for result grids
ROW_BAND = '#2e2a1f'
ROW_PLAIN = SURFACE

# --------------------------------------------------------------------------
# Chart tokens
# --------------------------------------------------------------------------
#
# Trend charts used to be drawn on a pure black canvas with saturated
# primaries - which is how an oscilloscope looks, not how a panel in this
# app looks, and a black slab in the middle of a slate page is the one
# thing on screen that reads as broken. They now sit on the same surface
# as everything else.
#
# SERIES is a categorical palette: identity, not magnitude, so the slots
# are assigned in fixed order and never cycled. These four are validated
# against CHART_SURFACE for lightness, chroma, contrast and colour-vision
# separation - re-run the check before changing one:
#
#     node validate_palette.js "#3987e5,#d95926,#199e70,#c98500" #          --mode dark --surface "#1c222b"
#
CHART_SURFACE = SURFACE      # the canvas the plot is drawn on
CHART_GRID = BORDER          # hairline grid, one step off the surface
CHART_AXIS = BORDER_STRONG   # the axis rules themselves
SERIES = ('#3987e5', '#d95926', '#199e70', '#c98500')

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
# Every light literal has to land on something dark here, or a page that
# was written with bg='white' keeps a white panel in the middle of the
# dark theme.
_BACKGROUND_MAP = {
    # neutrals
    'white': SURFACE, '#ffffff': SURFACE, '#fff': SURFACE,
    '#f0f0f0': SUBTLE, '#f5f5f5': SUBTLE, '#f8f9fa': SUBTLE,
    '#e0e0e0': SUBTLE, '#e8e8e8': SUBTLE, 'lightgray': SUBTLE,
    'lightgrey': SUBTLE, 'gray': SUBTLE, 'grey': SUBTLE,
    '#2b2b2b': SURFACE, 'pink': SURFACE, '#ffb6c1': SUBTLE,
    'black': SURFACE, '#000000': SURFACE,
    '#f5e6e8': SURFACE, '#e8f6e9': SURFACE, '#e6eef5': SURFACE,
    '#f5f0e6': SURFACE,
    'lightyellow': ROW_BAND, '#fff9c4': ROW_BAND, '#fef9c3': ROW_BAND,
    '#ffff99': ROW_BAND,
    # accent family - as a background these are fills, so they take the
    # deeper tone and get TEXT_ON_ACCENT written over them below.
    'navy': ACCENT_FILL, 'darkblue': ACCENT_FILL, 'blue': ACCENT_FILL,
    'deepskyblue': ACCENT_FILL, '#00bfff': ACCENT_FILL, '#1e88e5': ACCENT_FILL,
    '#3498db': ACCENT_FILL, '#2980b9': ACCENT_HOVER, '#0d6efd': ACCENT_FILL,
    '#2c3e50': ACCENT_FILL, '#add8e6': SUBTLE, 'lightblue': SUBTLE,
    '#cce5ff': ACCENT_SOFT, '#e6f2ff': ACCENT_SOFT,
    # success family
    'green': SUCCESS, '#2ecc71': SUCCESS, '#27ae60': SUCCESS_HOVER,
    '#4caf50': SUCCESS, '#198754': SUCCESS, '#00ff00': SUCCESS,
    '#45a049': SUCCESS_HOVER,
    'lightgreen': SUCCESS_SOFT, '#90ee90': SUCCESS_SOFT,
    # danger family
    'red': DANGER, 'darkred': DANGER, '#e74c3c': DANGER,
    '#c0392b': DANGER_HOVER, '#f44336': DANGER, '#ff4d4d': DANGER,
    '#dc3545': DANGER, '#ff3333': DANGER, '#ff0000': DANGER,
    '#ffcccb': DANGER_SOFT, '#ffe6e6': DANGER_SOFT,
    # warning family
    'yellow': WARNING, 'orange': WARNING, '#ffd700': WARNING,
    '#ffeb3b': WARNING,
    # '#ff4500' (OrangeRed) is test_console.py's fail colour, not a warning -
    # it belongs with the danger family or a failed step reads as a caution.
    '#ff4500': DANGER,
    # purple used for the edit action
    '#9b59b6': ACCENT_FILL, '#8e44ad': ACCENT_HOVER,
    '#95a5a6': TEXT_MUTED, '#7f8c8d': TEXT_MUTED,
}

# Fills with a designated text colour, whichever way the contrast maths
# would otherwise fall. Blue is the one that needs saying: white on the
# accent is the convention everywhere else in this app.
_FILL_TEXT = {
    ACCENT_FILL: TEXT_ON_ACCENT,
    ACCENT_HOVER: TEXT_ON_ACCENT,
    ACCENT_ACTIVE: TEXT_ON_ACCENT,
}

_FOREGROUND_MAP = {
    'white': TEXT_ON_ACCENT, '#ffffff': TEXT_ON_ACCENT,
    'black': TEXT, '#000000': TEXT, '#1a1a1a': TEXT, '#2b2b2b': TEXT,
    '#333333': TEXT, '#424242': TEXT, '#2c3e50': TEXT,
    '#999999': TEXT_MUTED, '#666666': TEXT_MUTED,
    'gray': TEXT_MUTED, 'grey': TEXT_MUTED, 'lightgray': TEXT_MUTED,
    'green': SUCCESS, '#00ff00': SUCCESS, '#4caf50': SUCCESS,
    '#198754': SUCCESS, '#2ecc71': SUCCESS, '#27ae60': SUCCESS,
    'red': DANGER, 'darkred': DANGER, '#ff0000': DANGER,
    'navy': ACCENT, 'blue': ACCENT, 'darkblue': ACCENT,
    'orange': WARNING, 'yellow': WARNING,
}

# Black used to be preserved here for the chart canvases. They draw on
# CHART_SURFACE now, so a literal black background is just an unconverted
# light-theme leftover and maps onto the palette like any other.
_KEEP_BACKGROUND = set()

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


def readable_on(background, dark=TEXT_ON_LIGHT, light=TEXT):
    """Pick whichever text colour reads better on this background.

    `dark` is the option for light backgrounds and `light` the option for
    dark ones - on a dark theme the body text is itself light, so both
    defaults being TEXT would leave bright fills with unreadable text.
    """
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
                    selectbackground=ACCENT_FILL, selectforeground=TEXT_ON_ACCENT)

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
                    background=ACCENT_FILL, foreground=TEXT_ON_ACCENT,
                    font=FONT_BODY_BOLD, borderwidth=0)
    style.map('TButton',
              background=[('disabled', DISABLED_BG),
                          ('pressed', ACCENT_ACTIVE),
                          ('active', ACCENT_HOVER)],
              foreground=[('disabled', DISABLED_TEXT)])

    for name, base, hover in (('Success', SUCCESS, SUCCESS_HOVER),
                              ('Danger', DANGER, DANGER_HOVER),
                              ('Neutral', SUBTLE, BORDER)):
        text_colour = readable_on(base)
        style.configure(f'{name}.TButton', background=base, foreground=text_colour)
        style.map(f'{name}.TButton',
                  background=[('disabled', DISABLED_BG), ('active', hover)],
                  foreground=[('disabled', DISABLED_TEXT), ('active', readable_on(hover))])

    style.configure('TEntry', fieldbackground=SURFACE, foreground=TEXT,
                    bordercolor=BORDER, insertcolor=TEXT, padding=4)
    style.map('TEntry',
              fieldbackground=[('disabled', DISABLED_BG), ('readonly', SUBTLE)],
              foreground=[('disabled', DISABLED_TEXT)])

    style.configure('TCombobox', fieldbackground=SURFACE, foreground=TEXT,
                    bordercolor=BORDER, arrowcolor=TEXT_MUTED,
                    selectbackground=SURFACE, selectforeground=TEXT, padding=4)
    # Most of this app's comboboxes are state='readonly', which has its own
    # field colour - left alone it stays the system light grey.
    style.map('TCombobox',
              fieldbackground=[('readonly', SURFACE), ('disabled', DISABLED_BG)],
              foreground=[('readonly', TEXT), ('disabled', DISABLED_TEXT)],
              selectbackground=[('readonly', SURFACE)],
              selectforeground=[('readonly', TEXT)],
              background=[('readonly', SUBTLE), ('active', SUBTLE)],
              arrowcolor=[('disabled', DISABLED_TEXT)])
    # The drop-down itself is a Tk listbox rather than a ttk widget, so it
    # only answers to the option database.
    for pattern, value in (('*TCombobox*Listbox.background', SURFACE),
                           ('*TCombobox*Listbox.foreground', TEXT),
                           ('*TCombobox*Listbox.selectBackground', ACCENT_SOFT),
                           ('*TCombobox*Listbox.selectForeground', ACCENT)):
        try:
            style.master.option_add(pattern, value)
        except (AttributeError, tk.TclError):
            pass

    style.configure('Treeview', background=SURFACE, fieldbackground=SURFACE,
                    foreground=TEXT, rowheight=26, borderwidth=1,
                    bordercolor=BORDER, font=FONT_BODY)
    # A filled header band, so the column names read as a header rather
    # than as a slightly different first row. Every grid inherits this;
    # the dotted style names below it derive from this one.
    style.configure('Treeview.Heading', background=ACCENT_FILL,
                    foreground=TEXT_ON_ACCENT, font=FONT_BODY_BOLD,
                    relief='flat', borderwidth=0, padding=(PAD, PAD))
    style.map('Treeview',
              background=[('selected', ACCENT_FILL)],
              foreground=[('selected', TEXT_ON_ACCENT)])
    style.map('Treeview.Heading', background=[('active', ACCENT)])

    style.configure('TNotebook', background=APP_BG, tabmargins=[2, 5, 2, 0])
    style.configure('TNotebook.Tab', background=SUBTLE, foreground=TEXT,
                    padding=[PAD_LARGE, PAD], font=FONT_BODY_BOLD)
    style.map('TNotebook.Tab',
              background=[('selected', ACCENT_FILL)],
              foreground=[('selected', TEXT_ON_ACCENT)])

    # Both orientations have to be named: clam draws them through
    # Horizontal./Vertical. prefixed styles, which do not inherit the
    # colours set on the bare TScrollbar name.
    for scrollbar in ('TScrollbar', 'Horizontal.TScrollbar', 'Vertical.TScrollbar'):
        style.configure(scrollbar, background=BORDER, troughcolor=APP_BG,
                        bordercolor=APP_BG, arrowcolor=TEXT_MUTED,
                        darkcolor=SURFACE, lightcolor=SURFACE,
                        gripcount=0, relief='flat')
        style.map(scrollbar,
                  background=[('active', BORDER_STRONG),
                              ('disabled', APP_BG)],
                  arrowcolor=[('disabled', DISABLED_TEXT)])
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
        designated = _FILL_TEXT.get(background)
        if designated is not None:
            options['fg'] = designated
        elif not isinstance(foreground, str) or not _has_contrast(foreground, background):
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

    # A disabled or readonly Entry ignores `bg` entirely and paints itself in
    # a system light grey, which on a dark panel reads as a blank white slab.
    # Mirror whatever background it is being given into those two states, so
    # a page that colours an entry to mean something (a validated code going
    # green, say) keeps that meaning once the entry is locked.
    if name in ('Entry', 'Spinbox'):
        well = options.get('bg', SURFACE)
        options.setdefault('disabledbackground', well)
        options.setdefault('readonlybackground', well)
        options.setdefault('disabledforeground', TEXT_MUTED)

    # Classic scrollbars and sliders paint their trough and thumb from
    # their own options rather than from the background they sit on, so
    # left alone they stay a pale system grey against a dark page.
    if name in ('Scrollbar', 'Scale'):
        options.setdefault('bg', SUBTLE)
        options.setdefault('troughcolor', APP_BG)
        options.setdefault('activebackground', BORDER_STRONG)
        options.setdefault('highlightthickness', 0)
        options.setdefault('borderwidth', 0)
        if name == 'Scrollbar':
            options.setdefault('elementborderwidth', 0)

    if name == 'Menu':
        options.setdefault('bg', SURFACE)
        options.setdefault('fg', TEXT)
        options.setdefault('activebackground', ACCENT_SOFT)
        options.setdefault('activeforeground', ACCENT)
        options.setdefault('borderwidth', 0)

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
                         tk.Listbox, tk.Canvas, tk.Spinbox, tk.Toplevel,
                         tk.Scrollbar, tk.Menu, tk.Scale):
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

    # Widgets built without any colour of their own fall back to Tk's own
    # system defaults, which are light - on a dark theme those show up as
    # pale grey slabs in the middle of a page. The option database gives
    # them a dark default instead, while anything that asks for a specific
    # colour still wins.
    defaults = (
        ('*Font', FONT_BODY),
        ('*Background', APP_BG),
        ('*Foreground', TEXT),
        ('*selectBackground', ACCENT_SOFT),
        ('*selectForeground', TEXT),
        ('*troughColor', SUBTLE),
        ('*highlightBackground', APP_BG),
        ('*highlightColor', BORDER),
        ('*Entry.background', SURFACE),
        ('*Text.background', SURFACE),
        ('*Listbox.background', SURFACE),
        ('*Menu.background', SURFACE),
        ('*Menu.foreground', TEXT),
        ('*Menu.activeBackground', ACCENT_SOFT),
        ('*Menu.activeForeground', ACCENT),
    )
    for pattern, value in defaults:
        try:
            root.option_add(pattern, value)
        except tk.TclError:
            pass

    return style


# --------------------------------------------------------------------------
# Small building blocks pages can use directly
# --------------------------------------------------------------------------

def page_header(parent, title, right_text='', compact=False, icon=None):
    """A titled bar across the top of a page, with optional right-hand text.

    `compact` trades the display-sized title for a single line of text,
    giving back most of the bar's height to whatever sits below it.
    `icon` names a glyph from icons.py to set beside the title.
    """
    pad = PAD if compact else PAD_LARGE
    font = FONT_SECTION if compact else FONT_TITLE

    header = tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER,
                      highlightthickness=1)
    header.pack(fill='x')

    inner = tk.Frame(header, bg=SURFACE)
    inner.pack(fill='x', padx=PAD_LARGE, pady=pad)

    if icon:
        badge = ctk.CTkFrame(inner, width=30, height=30, corner_radius=8,
                             fg_color=ACCENT_FILL)
        badge.pack(side='left', padx=(0, PAD))
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text='', fg_color=ACCENT_FILL,
                    image=icon_image(icon, TEXT_ON_ACCENT, 18)).pack(expand=True)

    tk.Label(inner, text=title, bg=SURFACE, fg=TEXT,
             font=font).pack(side='left')

    if right_text:
        tk.Label(inner, text=right_text, bg=SURFACE, fg=TEXT_MUTED,
                 font=FONT_SMALL if compact else FONT_BODY_BOLD).pack(side='right')

    return header


def section(parent, title, icon='', **kwargs):
    """A titled card. Returns the frame to put content in.

    `icon` is a single glyph shown before the title, for pages that want a
    little visual variety between cards without departing from the palette.
    """
    outer = tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER,
                     highlightthickness=1, **kwargs)

    caption = tk.Frame(outer, bg=SUBTLE)
    caption.pack(fill='x')

    if icon:
        tk.Label(caption, text=icon, bg=SUBTLE, fg=ACCENT,
                 font=FONT_SECTION).pack(side='left', padx=(PAD, 0), pady=PAD)

    tk.Label(caption, text=title, bg=SUBTLE, fg=ACCENT,
            font=FONT_SECTION, anchor='w', padx=PAD, pady=PAD).pack(
                side='left', fill='x', expand=True)

    body = tk.Frame(outer, bg=SURFACE)
    body.pack(fill='both', expand=True, padx=PAD, pady=PAD)

    outer.body = body
    outer.caption = caption
    return outer


def empty_state(parent, icon, title, subtitle='', bg=SURFACE):
    """A centred "nothing here yet" block: a glyph, a title and a subtitle.

    Returns the frame; callers that want it centred in an already-expanding
    parent should pack/place it with expand=True themselves.
    """
    holder = tk.Frame(parent, bg=bg)

    tk.Label(holder, text=icon, bg=bg, fg=BORDER_STRONG,
            font=(FONT_FAMILY, 28)).pack(pady=(0, PAD))
    tk.Label(holder, text=title, bg=bg, fg=TEXT_MUTED,
            font=FONT_BODY_BOLD).pack()
    if subtitle:
        tk.Label(holder, text=subtitle, bg=bg, fg=TEXT_MUTED,
                font=FONT_SMALL).pack(pady=(2, 0))

    return holder


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


# --------------------------------------------------------------------------
# Rounded widgets (customtkinter), for the pages redesigned toward rounded
# cards and real icons
# --------------------------------------------------------------------------
#
# Classic tk can only draw flat rectangles, so everything above translates
# colour literals rather than round anything. Where a page specifically
# wants the rounded look, these build on customtkinter instead - a thin
# skin over Tk with real rounded corners and real icon images. Its widgets
# are still ordinary Tk widgets underneath, so they mix freely with a plain
# tk.Tk root and classic tk siblings; nothing here requires the whole app,
# or even the whole page, to move over at once.

CORNER_RADIUS = 14
CORNER_RADIUS_SMALL = 10

# fg_color, hover_color per semantic "kind" - the same meanings as the
# palette above (primary action, success, failure, needs-attention).
_BUTTON_KINDS = {
    'primary': (ACCENT_FILL, ACCENT_HOVER),
    'success': (SUCCESS, SUCCESS_HOVER),
    'danger': (DANGER, DANGER_HOVER),
    'warning': (WARNING, mix(WARNING, '#ffffff', 0.15)),
    'neutral': (SUBTLE, BORDER),
}


def icon_image(name, color, size=28):
    """A cached icon image (see icons.py), ready for a CTk `image=` option."""
    return icons.ctk_image(name, color, size=size)


def ctk_card(parent, **kwargs):
    """A rounded white card, matching the reference design's panels."""
    kwargs.setdefault('corner_radius', CORNER_RADIUS)
    kwargs.setdefault('fg_color', SURFACE)
    kwargs.setdefault('border_width', 1)
    kwargs.setdefault('border_color', BORDER)
    return ctk.CTkFrame(parent, **kwargs)


def ctk_card_header(card, title, icon=None, height=34):
    """The inset icon+title strip along the top of a ctk_card.

    Inset a couple of pixels from the card's own edge, so the card's
    rounded corners stay visible around it rather than being squared off
    by a banner running edge to edge.
    """
    header = ctk.CTkFrame(card, corner_radius=CORNER_RADIUS_SMALL,
                          fg_color=SUBTLE, height=height)
    header.pack(fill='x', padx=6, pady=(6, 0))
    header.pack_propagate(False)

    if icon:
        ctk.CTkLabel(header, text='', image=icon_image(icon, ACCENT, 18),
                    fg_color=SUBTLE, width=18).pack(side='left', padx=(PAD_LARGE, 0))

    ctk.CTkLabel(header, text=title, fg_color=SUBTLE, text_color=ACCENT,
                font=FONT_SECTION).pack(side='left', padx=PAD)
    return header


def ctk_button(parent, text, icon=None, kind='primary', icon_size=20,
              corner_radius=CORNER_RADIUS_SMALL, compound='left', **kwargs):
    """A rounded button in one of the palette's meaningful colours."""
    fg_color, hover_color = _BUTTON_KINDS[kind]
    text_color = kwargs.pop('text_color', readable_on(fg_color))
    image = icon_image(icon, text_color, icon_size) if icon else None
    return ctk.CTkButton(parent, text=text, image=image, compound=compound,
                         fg_color=fg_color, hover_color=hover_color,
                         text_color=text_color, corner_radius=corner_radius,
                         font=FONT_BODY_BOLD, **kwargs)


# --------------------------------------------------------------------------
# Status banner
# --------------------------------------------------------------------------
#
# The one line on a machine page that says what the equipment is doing, and
# the first thing an operator looks at when something stops. As a bare
# coloured word on the page background it was easy to miss from arm's
# length; filled, iconed and set in bold it reads across the cell.
#
# Severity is passed as the colour word the pages already use, so existing
# calls keep working - "red" means a fault, not merely red text.

_LEVELS = {
    'danger':  (DANGER,  DANGER_SOFT,  'alert'),
    'warning': (WARNING, ROW_BAND,     'alert'),
    'success': (SUCCESS, SUCCESS_SOFT, 'check'),
    'info':    (ACCENT,  ACCENT_SOFT,  'info'),
    'idle':    (TEXT_MUTED, SUBTLE,    'info'),
}

_LEVEL_WORDS = {
    'red': 'danger', 'darkred': 'danger', DANGER: 'danger',
    'orange': 'warning', 'yellow': 'warning', WARNING: 'warning',
    'green': 'success', SUCCESS: 'success',
    'blue': 'info', 'navy': 'info', ACCENT: 'info',
    'black': 'idle', 'gray': 'idle', 'grey': 'idle', TEXT_MUTED: 'idle',
}


def level_for(color):
    """The severity a page means by the colour word it passed."""
    if not isinstance(color, str):
        return 'idle'
    value = color.strip().lower()
    if value in _LEVELS:
        return value
    return _LEVEL_WORDS.get(value, 'info')


class StatusBanner(ctk.CTkFrame):
    """A filled strip carrying the current machine message.

    `show(message, colour)` takes the same colour words the pages already
    pass to their message label, so it is a drop-in for one.
    """

    def __init__(self, parent, **kwargs):
        kwargs.setdefault('corner_radius', CORNER_RADIUS_SMALL)
        kwargs.setdefault('fg_color', SUBTLE)
        kwargs.setdefault('height', 34)
        super().__init__(parent, **kwargs)
        self.pack_propagate(False)

        self._icon = ctk.CTkLabel(self, text='', width=18, fg_color='transparent')
        self._icon.pack(side='left', padx=(PAD_LARGE, 0))

        self._text = ctk.CTkLabel(self, text='', fg_color='transparent',
                                  font=FONT_BODY_BOLD, anchor='w')
        self._text.pack(side='left', fill='x', expand=True, padx=PAD)

        self.show('Initializing...', 'idle')

    def show(self, message, color='info'):
        level = level_for(color)
        accent, fill, icon = _LEVELS[level]
        self.configure(fg_color=fill)
        self._icon.configure(image=icon_image(icon, accent, 16))
        self._text.configure(text=message, text_color=accent)

    # A page that still treats this as its old tk.Label keeps working.
    def config(self, cnf=None, **kw):
        if cnf:
            kw = dict(cnf, **kw)
        text = kw.pop('text', None)
        color = kw.pop('fg', kw.pop('foreground', None))
        if text is not None or color is not None:
            self.show(text if text is not None else self._text.cget('text'),
                      color or 'info')
        if kw:
            super().configure(**kw)

    configure = config


# --------------------------------------------------------------------------
# Step lamp
# --------------------------------------------------------------------------
#
# One stage of the test cycle: AUTO, HOME, the two pulls, the result. These
# are indicators, not controls - the monitoring loop recolours them as each
# stage passes or fails, and nothing happens if you click one.
#
# They used to be flat square tk.Labels with a hand cursor, which in an app
# where every real button is a rounded pill made a row of five of them read
# as a button bar. The colour now lives on a rounded frame, and the icon and
# text are redrawn in whatever reads against it.
#
# The monitoring loop addresses these as `lamp.config(bg=...)` and reads the
# colour back with `cget('bg')`, so both are kept working rather than
# rewritten across the dozen call sites that use them.

class StepLamp(ctk.CTkFrame):

    def __init__(self, parent, text, icon, color=ACCENT_FILL, icon_size=22,
                 **kwargs):
        kwargs.setdefault('corner_radius', CORNER_RADIUS_SMALL)
        super().__init__(parent, fg_color=color, **kwargs)

        self._icon_name = icon
        self._icon_size = icon_size
        self._color = color

        self._label = ctk.CTkLabel(self, text=text, compound='top',
                                   fg_color='transparent',
                                   font=FONT_BODY_BOLD)
        self._label.pack(expand=True, fill='both', padx=PAD, pady=PAD)
        self.set_color(color)

    def set_color(self, color):
        """Light this lamp in `color`, keeping icon and text legible on it."""
        color = map_background(color)
        ink = _FILL_TEXT.get(color) or readable_on(color)
        self._color = color
        self.configure(fg_color=color)
        self._label.configure(text_color=ink,
                              image=icon_image(self._icon_name, ink,
                                               self._icon_size))

    # -- the tk.Label surface the monitoring loop still speaks -------------

    def config(self, cnf=None, **kw):
        if cnf:
            kw = dict(cnf, **kw)
        background = kw.pop('bg', kw.pop('background', None))
        # fg is derived from the background, so a caller setting one is
        # telling us something we have already worked out.
        kw.pop('fg', None)
        kw.pop('foreground', None)
        kw.pop('cursor', None)
        if background is not None:
            self.set_color(background)
        if kw:
            super().configure(**kw)

    configure = config

    def cget(self, key):
        if key in ('bg', 'background'):
            return self._color
        return super().cget(key)

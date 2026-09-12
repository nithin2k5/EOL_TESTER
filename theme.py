"""Backwards compatible entry point for the shared look.

The styling itself lives in ui.py. This keeps the old call working for
anything that still imports it.
"""

import ui


def apply_professional_theme(root):
    """Apply the shared palette and widget styles to this window."""
    return ui.apply(root)

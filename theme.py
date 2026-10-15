"""Colors, fonts, resolution-aware scaling and ttk styling."""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

# Dark gray-navy surfaces, light foregrounds, near-black chrome (tab bar / status bar).
C = {
    "tabbar": "#0e111a",
    "panel": "#151a28",
    "bg": "#1b2133",
    "tree_bg": "#1e2538",
    "surface": "#283049",
    "border": "#343e5c",
    "fg": "#e8ebf5",
    "muted": "#8f98b5",
    "faint": "#5b6482",
    "accent": "#6ea8fe",
    "accent_dim": "#2c4777",
    "select": "#2f4572",
    "danger": "#ff6b7a",
    "tab_idle": "#0e111a",
    "tab_hover": "#1a2032",
    "tab_active": "#1e2538",
    # value types
    "object": "#7db4ff",
    "array": "#7fd6d0",
    "string": "#a8e6a1",
    "number": "#f5c27a",
    "boolean": "#c8a8ff",
    "null": "#8f98b5",
}

FONT_UI = "Helvetica"
FONT_MONO = "Courier"

_scale = 1.0


def px(value: float) -> int:
    """Scale a design-time pixel value to the current screen."""
    return max(1, int(round(value * _scale)))


def scale_factor() -> float:
    return _scale


def init_scaling(root: tk.Tk) -> float:
    """Pick a UI scale from the real DPI, falling back to the screen resolution."""
    global _scale
    dpi_scale = root.winfo_fpixels("1i") / 96.0
    res_scale = root.winfo_screenheight() / 1080.0
    if abs(dpi_scale - 1.0) > 0.05:
        scale = dpi_scale
    else:
        scale = min(max(res_scale, 0.9), 2.0)
    _scale = max(0.8, min(scale, 3.0))
    # points -> pixels, so every point-sized font scales with the screen
    root.tk.call("tk", "scaling", 96.0 * _scale / 72.0)
    return _scale


def _pick(root: tk.Tk, candidates: tuple[str, ...]) -> str | None:
    available = set(tkfont.families(root))
    for name in candidates:
        if name in available:
            return name
    return None


def apply_theme(root: tk.Tk) -> None:
    global FONT_UI, FONT_MONO
    FONT_UI = _pick(root, ("Segoe UI", "Inter", "Noto Sans", "Ubuntu", "Cantarell", "DejaVu Sans")) or "Helvetica"
    FONT_MONO = _pick(root, ("Cascadia Mono", "Consolas", "JetBrains Mono", "DejaVu Sans Mono",
                             "Liberation Mono", "Courier New")) or "Courier"

    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont"):
        tkfont.nametofont(name).configure(family=FONT_UI, size=10)
    tkfont.nametofont("TkFixedFont").configure(family=FONT_MONO, size=10)

    root.configure(bg=C["bg"])
    s = ttk.Style(root)
    s.theme_use("clam")

    s.configure(".", background=C["bg"], foreground=C["fg"], bordercolor=C["border"],
                lightcolor=C["bg"], darkcolor=C["bg"], focuscolor=C["bg"],
                troughcolor=C["panel"], font=(FONT_UI, 10))

    # Buttons: flat, slightly padded
    s.configure("TButton", background=C["surface"], foreground=C["fg"], bordercolor=C["surface"],
                lightcolor=C["surface"], darkcolor=C["surface"], borderwidth=0,
                focusthickness=0, relief="flat", padding=(px(14), px(6)))
    s.map("TButton",
          background=[("pressed", C["accent_dim"]), ("active", C["border"])],
          bordercolor=[("pressed", C["accent_dim"]), ("active", C["border"])],
          lightcolor=[("pressed", C["accent_dim"]), ("active", C["border"])],
          darkcolor=[("pressed", C["accent_dim"]), ("active", C["border"])])

    s.configure("Accent.TButton", background=C["accent"], foreground="#0d1220",
                bordercolor=C["accent"], lightcolor=C["accent"], darkcolor=C["accent"],
                font=(FONT_UI, 10, "bold"))
    s.map("Accent.TButton",
          background=[("pressed", "#5a93ea"), ("active", "#8bbaff")],
          bordercolor=[("pressed", "#5a93ea"), ("active", "#8bbaff")],
          lightcolor=[("pressed", "#5a93ea"), ("active", "#8bbaff")],
          darkcolor=[("pressed", "#5a93ea"), ("active", "#8bbaff")],
          foreground=[("active", "#0d1220")])

    # Entry
    s.configure("TEntry", fieldbackground=C["tabbar"], foreground=C["fg"], insertcolor=C["fg"],
                bordercolor=C["border"], lightcolor=C["border"], darkcolor=C["border"],
                padding=(px(8), px(5)))
    s.map("TEntry",
          bordercolor=[("focus", C["accent"])],
          lightcolor=[("focus", C["accent"])],
          darkcolor=[("focus", C["accent"])])

    # Treeview
    s.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    s.configure("Treeview", background=C["tree_bg"], fieldbackground=C["tree_bg"],
                foreground=C["fg"], bordercolor=C["tree_bg"], lightcolor=C["tree_bg"],
                darkcolor=C["tree_bg"], borderwidth=0, rowheight=px(26), relief="flat")
    s.map("Treeview",
          background=[("selected", C["select"])],
          foreground=[("selected", C["fg"])])
    s.configure("Treeview.Heading", background=C["panel"], foreground=C["muted"],
                bordercolor=C["border"], lightcolor=C["panel"], darkcolor=C["panel"],
                relief="flat", padding=(px(10), px(6)), font=(FONT_UI, 9, "bold"))
    s.map("Treeview.Heading", background=[("active", C["surface"])],
          foreground=[("active", C["fg"])])

    # Scrollbars
    for orient in ("Vertical", "Horizontal"):
        name = f"{orient}.TScrollbar"
        s.configure(name, background=C["surface"], troughcolor=C["bg"], bordercolor=C["bg"],
                    lightcolor=C["surface"], darkcolor=C["surface"], arrowcolor=C["muted"],
                    relief="flat", gripcount=0, arrowsize=px(14))
        s.map(name, background=[("pressed", C["accent_dim"]), ("active", C["border"])])

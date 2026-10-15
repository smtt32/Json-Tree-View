"""JSON Tree Viewer — entry point.

Run:    python main.py [file.json ...]
Build:  pyinstaller --noconsole --onefile --name JsonTreeViewer main.py
"""
from __future__ import annotations

import sys


def _enable_dpi_awareness() -> None:
    """Must run before Tk is created, otherwise Windows bitmap-scales (blurry) the UI."""
    if sys.platform != "win32":
        return
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main() -> None:
    _enable_dpi_awareness()
    sys.setrecursionlimit(5000)  # deeply nested JSON
    from app import App
    App(sys.argv[1:]).mainloop()


if __name__ == "__main__":
    main()

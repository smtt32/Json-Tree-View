"""Path helpers that behave the same from source, on Windows/Linux, and inside a
PyInstaller bundle (--onefile or --onedir)."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def bundle_dir() -> Path:
    """Folder that holds bundled read-only resources (PyInstaller's temp dir when frozen)."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent


def app_dir() -> Path:
    """Folder that contains the program itself (next to the .exe when frozen)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_path(*parts: str) -> Path:
    """Path to a bundled resource, e.g. resource_path("assets", "icon.png")."""
    return bundle_dir().joinpath(*parts)


def user_config_dir() -> Path:
    """Per-user writable folder for settings (never the install/bundle folder)."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "JsonTreeViewer"

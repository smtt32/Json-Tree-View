<div align="center">

# 🌳 JSON Tree Viewer

**A fast, free and fully offline JSON viewer for Windows and Linux.**
Explore any JSON file as a collapsible tree, in Notepad++-style tabs, with a modern dark interface.

![Python](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)
![Platforms](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-6ea8fe)
![GUI](https://img.shields.io/badge/GUI-Tkinter-f5c27a)
![Runtime deps](https://img.shields.io/badge/runtime%20dependencies-none-7fd6d0)
![Offline](https://img.shields.io/badge/works-100%25%20offline-c8a8ff)
![License](https://img.shields.io/badge/license-MIT-a8e6a1)

[Features](#-features) · [Installation](#-installation) · [Usage](#-usage) · [Shortcuts](#-keyboard-shortcuts) · [FAQ](#-faq) · [Build](#-build-from-source)

</div>

---

## ✨ What is JSON Tree Viewer?

**JSON Tree Viewer** is a lightweight desktop **JSON viewer** and **JSON explorer** written in pure Python (Tkinter).
Open one or many `.json` files, browse them as a clean, collapsible **tree**, search keys and values, and copy the exact **JSON path** of any node, all without sending a single byte over the network.

It has **no runtime dependencies**, starts instantly, and runs on **Windows and Linux**.

```text
┌────────────────────────────────────────────────────────────────────┐
│ [ Open File ] [ Expand All ] [ Collapse All ]      Find [______] ‹ › │
├────────────────────────────────────────────────────────────────────┤
│ ▌config.json  ✕ │ users.json  ✕ │ response.json  ✕                  │
├────────────────────────────────────────────────────────────────────┤
│ Key              Value                                   Type       │
│ ▾ root           { 4 keys }                              object     │
│   ├ name         "demo"                                  string     │
│   ├ version      1.5                                     number     │
│   ├ tags         [ 3 items ]                             array      │
│   └ nested       { 2 keys }                              object     │
├────────────────────────────────────────────────────────────────────┤
│ PATH  $.nested.deep.list[1].title                                   │
│ Second item                                                         │
└────────────────────────────────────────────────────────────────────┘
```

<!-- Add a real screenshot: save it as docs/screenshot.png and uncomment the next line -->
<!-- ![JSON Tree Viewer screenshot](docs/screenshot.png) -->

## 🚀 Features

| | Feature | Details |
|---|---|---|
| 🌲 | **Collapsible JSON tree** | Objects and arrays are collapsed by default. Open only what you need. |
| 🗂️ | **Tabbed interface** | Open many files at once. Close tabs with ✕, middle-click or `Ctrl+W`, like Notepad++. |
| ⚡ | **Lazy loading** | Child nodes are created only when a branch is expanded, so big files open without freezing the UI. |
| 🔎 | **Search keys and values** | Jump through matches with `Enter` / `Shift+Enter`. Branches expand automatically to reveal each hit. |
| 📋 | **Copy JSON path / value** | Right-click any node. Paths look like `$.users[0].address["zip code"]`. |
| 🎨 | **Modern dark UI** | Dark gray-navy background, light text, color-coded value types (string, number, boolean, null, object, array). |
| 🖥️ | **Resolution-aware scaling** | The interface adapts to your screen DPI and resolution. |
| 🧾 | **Value inspector** | A bottom pane shows the selected node's path and its full value, pretty-printed. |
| 🚫 | **100% offline and private** | No network code, no telemetry, no accounts. |
| 📦 | **Easy to ship** | Plain Python, a standalone Windows `.exe`, or a Debian/Ubuntu `.deb`. |

## 📥 Installation

### Option 1: Run from source (Windows, Linux, macOS with Tk)

```bash
git clone https://github.com/YOUR_USERNAME/json-tree-viewer.git
cd json-tree-viewer
python main.py                 # or: python3 main.py
```

Requires **Python 3.9+** with Tkinter. No `pip install` is needed to run it.

> **Linux:** Tkinter comes from your distro (`sudo apt install python3-tk`). See [`requirements-linux.txt`](requirements-linux.txt).

### Option 2: Windows `.exe` and installer

Build a single-file `JsonTreeViewer.exe` with PyInstaller and, optionally, a proper Windows installer (Start Menu entry, uninstaller, right-click "Open with JSON Tree Viewer"). Step by step in [`SETUP.txt`](SETUP.txt).

### Option 3: Debian / Ubuntu / Mint `.deb` (system package)

Build a `.deb`, then install it system-wide with `sudo apt install ./json-tree-viewer_1.0.0_all.deb`. It adds a menu launcher and a `json-tree-viewer` command. Full guide in [`SETUP.txt`](SETUP.txt).

## 🧭 Usage

```bash
python main.py                      # start empty, then press Ctrl+O
python main.py data.json            # open one file
python main.py a.json b.json        # open several files, one tab each
```

1. Click **Open File** (or press `Ctrl+O`) and pick one or more `.json` files.
2. Expand branches with the arrow, a double-click, or **Expand All**.
3. Type in **Find**, press `Enter` to jump to the next match.
4. Right-click a node to **copy its path or value**, or expand/collapse its subtree.

Invalid JSON is reported with the exact **line and column** of the error.

## ⌨️ Keyboard shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Open file(s) |
| `Ctrl+W` | Close current tab |
| `Ctrl+Tab` / `Ctrl+Shift+Tab` | Next / previous tab |
| `Ctrl+F` | Focus the Find box |
| `Enter` / `Shift+Enter` | Next / previous match |
| Middle-click on a tab | Close that tab |
| Right-click on a node | Copy path, copy value, expand/collapse subtree |

## 🧬 JSON path format

Every node has a JSONPath-style address, shown in the status bar and copyable from the context menu:

| JSON | Path |
|---|---|
| `{"name": "demo"}` | `$.name` |
| `{"tags": ["a", "b"]}` → second item | `$.tags[1]` |
| `{"my key": 1}` | `$["my key"]` |
| `{"users": [{"id": 7}]}` | `$.users[0].id` |

## ❓ FAQ

<details>
<summary><b>How do I open a large JSON file?</b></summary>

Use **Open File**. The file is parsed once with Python's `json` module, but tree rows are created lazily, only for branches you expand, so the interface stays responsive. Memory use grows with file size, since the parsed data is kept in RAM.
</details>

<details>
<summary><b>Is my data uploaded anywhere?</b></summary>

No. The app contains no network code and no telemetry. Files are read locally and nothing leaves your machine.
</details>

<details>
<summary><b>Can I edit JSON with it?</b></summary>

Not currently. JSON Tree Viewer is a read-only viewer and explorer.
</details>

<details>
<summary><b>How do I copy the path to a JSON value?</b></summary>

Right-click the node and choose **Copy Path**. The path of the selected node is also shown in the status bar and in the inspector pane.
</details>

<details>
<summary><b>Which Linux desktops work?</b></summary>

It runs wherever Tk runs (X11, and Wayland through XWayland) on GNOME, KDE, XFCE, Cinnamon, MATE and others. On Debian-based systems install `python3-tk`.
</details>

<details>
<summary><b>Windows SmartScreen warns about the .exe. Why?</b></summary>

Self-built executables are unsigned, and SmartScreen is cautious with unsigned apps. Build it yourself from this source, or sign the installer with your own code-signing certificate.
</details>

<details>
<summary><b>Where are settings stored?</b></summary>

Only the last-used folder is remembered:
`%APPDATA%\JsonTreeViewer\settings.json` on Windows, `~/.config/JsonTreeViewer/settings.json` on Linux.
</details>

## ⚠️ Limits

- **Expand All** opens at most 30,000 nodes, so very large files do not freeze the window.
- Search collects at most 5,000 matches.
- The inspector pane truncates values longer than 100,000 characters (**Copy Value** still copies the full text).
- A row uses one color for the whole line, because `ttk.Treeview` does not support per-cell colors.

## 🧱 Project structure

```text
json-tree-viewer/
├── main.py                    # entry point (DPI awareness, starts the app)
├── app.py                     # main window: toolbar, tabs, panes, status bar
├── tree_view.py               # lazy-loading JSON tree widget + search
├── tabs.py                    # Notepad++-style closable tab bar
├── theme.py                   # colors, fonts, resolution-aware scaling, ttk styles
├── paths.py                   # Windows/Linux/PyInstaller-safe path helpers
├── settings.py                # tiny per-user settings store
├── requirements-windows.txt   # build-time deps for the Windows .exe
├── requirements-linux.txt     # system packages + build-time deps for Linux
└── SETUP.txt                  # .deb packaging, .exe build, Windows installer
```

## 🛠️ Build from source

- **Windows `.exe`:** `pyinstaller --noconsole --onefile --name JsonTreeViewer main.py`
- **Linux `.deb`:** see `build_deb.sh` in [`SETUP.txt`](SETUP.txt)
- **Windows installer:** Inno Setup script in [`SETUP.txt`](SETUP.txt)

Paths are resolved through `paths.py` (`sys._MEIPASS`, `pathlib`, per-user config dirs), so the app keeps working after packaging.

## 🤝 Contributing

Issues and pull requests are welcome. Ideas that would fit well: drag-and-drop to open files, a recent-files list, a light theme, per-cell value coloring with a custom canvas tree.

## 📄 License

Released under the **Apache 2.0 License**. Add a `LICENSE` file with your name before publishing.



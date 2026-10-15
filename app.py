"""Main window: toolbar, tab bar, tree area, details pane, status bar."""
from __future__ import annotations

import json
import os
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import settings
import theme
from paths import resource_path
from tabs import TabBar
from theme import C, apply_theme, init_scaling, px
from tree_view import JsonTreeView, count_nodes, value_text

APP_NAME = "JSON Tree Viewer"


@dataclass
class Doc:
    path: Path
    view: JsonTreeView
    nodes: int
    size: int


def human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{n} B"


class App(tk.Tk):
    def __init__(self, files: list[str] | None = None):
        super().__init__()
        init_scaling(self)
        apply_theme(self)
        self.title(APP_NAME)

        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = int(sw * 0.70), int(sh * 0.75)
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 3}")
        self.minsize(px(720), px(460))
        self._set_icon()

        self._docs: dict[str, Doc] = {}
        self._current: str | None = None
        self.query = tk.StringVar()

        self._build()
        self._bind_keys()
        for f in files or []:
            self.open_path(f)

    # ------------------------------------------------------------------ UI
    def _set_icon(self) -> None:
        try:
            ico, png = resource_path("assets", "icon.ico"), resource_path("assets", "icon.png")
            if sys.platform == "win32" and ico.exists():
                self.iconbitmap(str(ico))
            elif png.exists():
                self._icon = tk.PhotoImage(file=str(png))
                self.iconphoto(True, self._icon)
        except tk.TclError:
            pass

    def _build(self) -> None:
        ui, mono = theme.FONT_UI, theme.FONT_MONO

        # Toolbar
        top = tk.Frame(self, bg=C["panel"])
        top.pack(side="top", fill="x")
        row = tk.Frame(top, bg=C["panel"])
        row.pack(fill="x", padx=px(10), pady=px(8))
        ttk.Button(row, text="Open File", style="Accent.TButton", command=self.open_dialog).pack(side="left")
        ttk.Button(row, text="Expand All", command=self.expand_all).pack(side="left", padx=(px(8), 0))
        ttk.Button(row, text="Collapse All", command=self.collapse_all).pack(side="left", padx=(px(6), 0))

        ttk.Button(row, text="›", width=3, command=lambda: self.find(False)).pack(side="right")
        ttk.Button(row, text="‹", width=3, command=lambda: self.find(True)).pack(side="right", padx=(0, px(4)))
        self.match_lbl = tk.Label(row, text="", width=11, anchor="e", bg=C["panel"], fg=C["muted"],
                                  font=(ui, 9))
        self.match_lbl.pack(side="right", padx=(0, px(6)))
        self.entry = ttk.Entry(row, textvariable=self.query, width=28)
        self.entry.pack(side="right", padx=(0, px(6)))
        tk.Label(row, text="Find", bg=C["panel"], fg=C["muted"], font=(ui, 9)).pack(side="right", padx=(0, px(8)))
        self.entry.bind("<Return>", lambda _e: self.find(False))
        self.entry.bind("<Shift-Return>", lambda _e: self.find(True))
        self.query.trace_add("write", lambda *_: self.match_lbl.configure(text=""))

        tk.Frame(self, height=1, bg=C["border"]).pack(side="top", fill="x")

        # Tabs
        self.tabbar = TabBar(self, on_select=self.select_tab, on_close=self.close_tab)
        self.tabbar.pack(side="top", fill="x")

        # Status bar (packed before the paned area so it keeps its space)
        status = tk.Frame(self, bg=C["tabbar"])
        status.pack(side="bottom", fill="x")
        self.status_left = tk.Label(status, text="Ready", anchor="w", bg=C["tabbar"], fg=C["muted"],
                                    font=(mono, 9))
        self.status_left.pack(side="left", padx=px(12), pady=px(4))
        self.status_right = tk.Label(status, text="", anchor="e", bg=C["tabbar"], fg=C["muted"],
                                     font=(ui, 9))
        self.status_right.pack(side="right", padx=px(12), pady=px(4))

        # Tree area + details pane
        paned = tk.PanedWindow(self, orient="vertical", bg=C["border"], bd=0, sashwidth=px(4),
                               sashrelief="flat", opaqueresize=True)
        paned.pack(side="top", fill="both", expand=True)

        self.body = tk.Frame(paned, bg=C["tree_bg"])
        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, weight=1)

        self.empty = tk.Frame(self.body, bg=C["tree_bg"])
        self.empty.grid(row=0, column=0, sticky="nsew")
        center = tk.Frame(self.empty, bg=C["tree_bg"])
        center.place(relx=0.5, rely=0.45, anchor="center")
        tk.Label(center, text="{ }", font=(mono, 40, "bold"), fg=C["accent"], bg=C["tree_bg"]).pack()
        tk.Label(center, text="No file open", font=(ui, 16), fg=C["fg"], bg=C["tree_bg"]).pack(pady=(px(6), 0))
        tk.Label(center, text="Open a JSON file to explore it as a tree   ·   Ctrl+O", font=(ui, 10),
                 fg=C["muted"], bg=C["tree_bg"]).pack(pady=px(4))
        ttk.Button(center, text="Open File", style="Accent.TButton", command=self.open_dialog).pack(pady=(px(14), 0))

        details = tk.Frame(paned, bg=C["panel"])
        head = tk.Frame(details, bg=C["panel"])
        head.pack(fill="x", padx=px(12), pady=(px(6), px(2)))
        tk.Label(head, text="PATH", font=(ui, 8, "bold"), fg=C["muted"], bg=C["panel"]).pack(side="left")
        self.path_lbl = tk.Label(head, text="—", font=(mono, 10), fg=C["accent"], bg=C["panel"], anchor="w")
        self.path_lbl.pack(side="left", padx=px(8))

        wrap = tk.Frame(details, bg=C["panel"])
        wrap.pack(fill="both", expand=True)
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        self.detail = tk.Text(wrap, height=6, wrap="word", bg=C["panel"], fg=C["fg"], relief="flat", bd=0,
                              highlightthickness=0, insertbackground=C["fg"], selectbackground=C["select"],
                              padx=px(12), pady=px(6), font=(mono, 10), state="disabled")
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.detail.yview)
        self.detail.configure(yscrollcommand=vsb.set)
        self.detail.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        paned.add(self.body, stretch="always", minsize=px(140))
        paned.add(details, stretch="never", minsize=px(70), height=px(150))

    def _bind_keys(self) -> None:
        self.bind("<Control-o>", lambda _e: self.open_dialog())
        self.bind("<Control-w>", lambda _e: self._current and self.close_tab(self._current))
        self.bind("<Control-f>", lambda _e: (self.entry.focus_set(), self.entry.selection_range(0, "end")))
        self.bind("<Control-Tab>", lambda _e: self._cycle(1))
        for seq in ("<Control-Shift-Tab>", "<Control-ISO_Left_Tab>"):
            try:
                self.bind(seq, lambda _e: self._cycle(-1))
            except tk.TclError:
                pass

    # ------------------------------------------------------------ documents
    def open_dialog(self) -> None:
        last = settings.get("last_dir")
        initial = last if last and os.path.isdir(last) else str(Path.home())
        chosen = filedialog.askopenfilenames(
            parent=self, title="Open JSON file", initialdir=initial,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        for p in self.tk.splitlist(chosen):
            self.open_path(p)

    def open_path(self, raw: str) -> None:
        path = Path(raw).expanduser()
        try:
            path = path.resolve()
        except OSError:
            pass
        key = os.path.normcase(str(path))
        if key in self._docs:
            self.select_tab(key)
            return

        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            raw_bytes = path.read_bytes()
            text = raw_bytes.decode("utf-8-sig", errors="replace")
            data = json.loads(text)
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"{path.name}\n\nLine {e.lineno}, column {e.colno}: {e.msg}",
                                 parent=self)
            return
        except RecursionError:
            messagebox.showerror("Error", f"{path.name}\n\nThe JSON is nested too deeply.", parent=self)
            return
        except OSError as e:
            messagebox.showerror("Cannot open file", f"{path}\n\n{e.strerror or e}", parent=self)
            return
        finally:
            self.configure(cursor="")

        view = JsonTreeView(self.body, data, on_select=self._on_node_selected)
        view.grid(row=0, column=0, sticky="nsew")
        self._docs[key] = Doc(path=path, view=view, nodes=count_nodes(data), size=len(raw_bytes))
        self.tabbar.add(key, path.name)
        settings.put("last_dir", str(path.parent))
        self.select_tab(key)

    def select_tab(self, key: str) -> None:
        doc = self._docs.get(key)
        if doc is None:
            return
        self._current = key
        self.tabbar.set_active(key)
        doc.view.tkraise()
        self.title(f"{doc.path.name} — {APP_NAME}")
        self.status_left.configure(text=str(doc.path))
        self.status_right.configure(text=f"{doc.nodes:,} nodes   ·   {human_size(doc.size)}")
        self._show_details("—", "")
        self.match_lbl.configure(text="")

    def close_tab(self, key: str) -> None:
        doc = self._docs.pop(key, None)
        if doc is None:
            return
        was_active = key == self._current
        doc.view.destroy()
        neighbour = self.tabbar.remove(key)
        if not was_active:
            return
        if neighbour:
            self.select_tab(neighbour)
        else:
            self._current = None
            self.empty.tkraise()
            self.title(APP_NAME)
            self.status_left.configure(text="Ready")
            self.status_right.configure(text="")
            self._show_details("—", "")

    def _cycle(self, step: int):
        nxt = self.tabbar.cycle(step)
        if nxt:
            self.select_tab(nxt)
        return "break"

    def _view(self) -> JsonTreeView | None:
        doc = self._docs.get(self._current) if self._current else None
        return doc.view if doc else None

    # --------------------------------------------------------------- actions
    def expand_all(self) -> None:
        view = self._view()
        if view is None:
            return
        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            capped = view.expand_all()
        finally:
            self.configure(cursor="")
        if capped:
            self.status_left.configure(text="Expanded the first 30,000 nodes (file is very large)")

    def collapse_all(self) -> None:
        view = self._view()
        if view is not None:
            view.collapse_all()

    def find(self, backwards: bool) -> None:
        view = self._view()
        if view is None:
            return
        self.configure(cursor="watch")
        self.update_idletasks()
        try:
            cur, total = view.search(self.query.get(), backwards)
        finally:
            self.configure(cursor="")
        if not self.query.get().strip():
            self.match_lbl.configure(text="")
        elif total == 0:
            self.match_lbl.configure(text="No matches", fg=C["danger"])
        else:
            self.match_lbl.configure(text=f"{cur} / {total}", fg=C["muted"])

    def _on_node_selected(self, path: str, value) -> None:
        self._show_details(path, value_text(value))
        self.status_left.configure(text=path)

    def _show_details(self, path: str, text: str) -> None:
        self.path_lbl.configure(text=path)
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", text)
        self.detail.configure(state="disabled")

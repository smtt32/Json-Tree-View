"""Lazy-loading JSON tree widget (children are created only when a node is opened)."""
from __future__ import annotations

import json
import re
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Iterator

from theme import C, px

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def child_path(parent: str, key: str | int) -> str:
    if isinstance(key, int):
        return f"{parent}[{key}]"
    if _IDENT.match(key):
        return f"{parent}.{key}"
    return f"{parent}[{json.dumps(key, ensure_ascii=False)}]"


def describe(value: Any) -> tuple[str, str, str]:
    """Return (kind, preview text, type label) for a JSON value."""
    if isinstance(value, dict):
        n = len(value)
        return "object", f"{{ {n} {'key' if n == 1 else 'keys'} }}", "object"
    if isinstance(value, list):
        n = len(value)
        return "array", f"[ {n} {'item' if n == 1 else 'items'} ]", "array"
    if isinstance(value, str):
        flat = value.replace("\r", "").replace("\n", " ⏎ ")
        if len(flat) > 240:
            flat = flat[:240] + "…"
        return "string", f'"{flat}"', "string"
    if isinstance(value, bool):
        return "boolean", "true" if value else "false", "boolean"
    if value is None:
        return "null", "null", "null"
    return "number", json.dumps(value), "number"


def count_nodes(data: Any) -> int:
    total, stack = 0, [data]
    while stack:
        v = stack.pop()
        total += 1
        if isinstance(v, dict):
            stack.extend(v.values())
        elif isinstance(v, list):
            stack.extend(v)
    return total


def value_text(value: Any, limit: int = 100_000) -> str:
    text = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False, default=str)
    if len(text) > limit:
        text = text[:limit] + f"\n… truncated ({len(text):,} characters in total)"
    return text


class JsonTreeView(ttk.Frame):
    MAX_EXPAND_NODES = 30_000
    MAX_MATCHES = 5_000

    def __init__(self, master, data: Any, on_select: Callable[[str, Any], None]):
        super().__init__(master)
        self._data = data
        self._on_select = on_select
        self._nodes: dict[str, tuple[Any, str]] = {}   # iid -> (value, path)
        self._pending: dict[str, str] = {}             # iid -> placeholder child iid
        self._matches: list[tuple[int, ...]] = []
        self._match_query: str | None = None
        self._match_idx = -1

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(self, columns=("value", "type"), selectmode="browse")
        self.tree.heading("#0", text="Key", anchor="w")
        self.tree.heading("value", text="Value", anchor="w")
        self.tree.heading("type", text="Type", anchor="w")
        self.tree.column("#0", width=px(360), minwidth=px(160), stretch=False)
        self.tree.column("value", width=px(480), minwidth=px(120), stretch=True, anchor="w")
        self.tree.column("type", width=px(90), minwidth=px(60), stretch=False, anchor="w")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        for kind in ("object", "array", "string", "number", "boolean", "null"):
            self.tree.tag_configure(kind, foreground=C[kind])

        self.menu = tk.Menu(self, tearoff=0, bg=C["surface"], fg=C["fg"], bd=0, relief="flat",
                            activebackground=C["select"], activeforeground=C["fg"],
                            activeborderwidth=0)
        self.menu.add_command(label="Copy Path", command=self.copy_path)
        self.menu.add_command(label="Copy Value", command=self.copy_value)
        self.menu.add_separator()
        self.menu.add_command(label="Expand Subtree", command=self.expand_selected)
        self.menu.add_command(label="Collapse Subtree", command=self.collapse_selected)

        self.tree.bind("<<TreeviewOpen>>", self._on_open)
        self.tree.bind("<<TreeviewSelect>>", self._on_select_event)
        self.tree.bind("<Button-3>", self._popup)

        self._root = self._add("", "root", data, "$")  # collapsed by default

    # -- building ---------------------------------------------------------
    def _add(self, parent: str, key_text: str, value: Any, path: str) -> str:
        kind, preview, type_label = describe(value)
        iid = self.tree.insert(parent, "end", text=key_text, values=(preview, type_label), tags=(kind,))
        self._nodes[iid] = (value, path)
        if kind in ("object", "array") and len(value):
            self._pending[iid] = self.tree.insert(iid, "end", text="")
        return iid

    def _populate(self, iid: str) -> None:
        placeholder = self._pending.pop(iid, None)
        if placeholder is None:
            return
        self.tree.delete(placeholder)
        value, path = self._nodes[iid]
        if isinstance(value, dict):
            for k, v in value.items():
                self._add(iid, str(k), v, child_path(path, str(k)))
        else:
            for i, v in enumerate(value):
                self._add(iid, f"[{i}]", v, child_path(path, i))

    def _on_open(self, _event) -> None:
        iid = self.tree.focus()
        if iid:
            self._populate(iid)

    def _on_select_event(self, _event) -> None:
        iid = self.selected_iid()
        if iid in self._nodes:
            value, path = self._nodes[iid]
            self._on_select(path, value)

    # -- selection / clipboard -------------------------------------------
    def selected_iid(self) -> str | None:
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _clip(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)

    def copy_path(self) -> None:
        iid = self.selected_iid()
        if iid in self._nodes:
            self._clip(self._nodes[iid][1])

    def copy_value(self) -> None:
        iid = self.selected_iid()
        if iid in self._nodes:
            self._clip(value_text(self._nodes[iid][0], limit=10_000_000))

    def _popup(self, event) -> None:
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        self.tree.selection_set(iid)
        self.tree.focus(iid)
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    # -- expand / collapse ------------------------------------------------
    def _expand(self, start: str) -> bool:
        """Expand a subtree; returns True if the node cap stopped it early."""
        count, stack = 0, [start]
        while stack and count < self.MAX_EXPAND_NODES:
            iid = stack.pop()
            if iid not in self._nodes:
                continue
            self._populate(iid)
            kids = self.tree.get_children(iid)
            if kids:
                self.tree.item(iid, open=True)
                count += len(kids)
                stack.extend(kids)
        return bool(stack)

    def _collapse(self, start: str) -> None:
        stack = [start]
        while stack:
            iid = stack.pop()
            if iid not in self._nodes:
                continue
            self.tree.item(iid, open=False)
            if iid not in self._pending:
                stack.extend(self.tree.get_children(iid))

    def expand_all(self) -> bool:
        return self._expand(self._root)

    def collapse_all(self) -> None:
        self._collapse(self._root)
        self.tree.see(self._root)

    def expand_selected(self) -> None:
        iid = self.selected_iid() or self._root
        self._expand(iid)

    def collapse_selected(self) -> None:
        iid = self.selected_iid() or self._root
        self._collapse(iid)

    # -- search -----------------------------------------------------------
    def search(self, query: str, backwards: bool = False) -> tuple[int, int]:
        """Jump to the next/previous match. Returns (current, total)."""
        q = query.strip().lower()
        if not q:
            self._matches, self._match_query = [], None
            return (0, 0)
        if q != self._match_query:
            self._matches = list(self._collect(q))
            self._match_query = q
            self._match_idx = 0 if backwards else -1
        if not self._matches:
            return (0, 0)
        step = -1 if backwards else 1
        self._match_idx = (self._match_idx + step) % len(self._matches)
        self._reveal(self._matches[self._match_idx])
        return (self._match_idx + 1, len(self._matches))

    def _collect(self, q: str) -> Iterator[tuple[int, ...]]:
        found = 0
        stack: list[tuple[tuple[int, ...], str | None, Any]] = [((), None, self._data)]
        while stack and found < self.MAX_MATCHES:
            route, key, val = stack.pop()
            if key is not None:
                if q in key.lower():
                    found += 1
                    yield route
                elif not isinstance(val, (dict, list)):
                    text = val if isinstance(val, str) else json.dumps(val)
                    if q in text.lower():
                        found += 1
                        yield route
            if isinstance(val, dict):
                items = [(str(k), v) for k, v in val.items()]
            elif isinstance(val, list):
                items = [("", v) for v in val]
            else:
                continue
            for i in range(len(items) - 1, -1, -1):
                k, v = items[i]
                stack.append((route + (i,), k, v))

    def _reveal(self, route: tuple[int, ...]) -> None:
        iid = self._root
        for pos in route:
            self._populate(iid)
            self.tree.item(iid, open=True)
            iid = self.tree.get_children(iid)[pos]
        self.tree.selection_set(iid)
        self.tree.focus(iid)
        self.tree.see(iid)
        self.tree.focus_set()

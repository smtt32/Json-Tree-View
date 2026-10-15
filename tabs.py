"""Notepad++-style tab bar: closable, middle-click to close, scrolls when crowded."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

import theme
from theme import C, px


def _short(title: str, limit: int = 26) -> str:
    return title if len(title) <= limit else title[: limit - 1] + "…"


class _Tab(tk.Frame):
    def __init__(self, bar: "TabBar", key: str, title: str):
        super().__init__(bar.inner, bg=C["tab_idle"], cursor="hand2")
        self.bar, self.key = bar, key
        self.active = False
        self.hover = False
        self.close_hover = False

        self.strip = tk.Frame(self, height=px(2), bg=C["tab_idle"])
        self.strip.pack(side="top", fill="x")
        self.row = tk.Frame(self, bg=C["tab_idle"])
        self.row.pack(fill="both", expand=True, padx=(px(12), px(4)), pady=(px(6), px(7)))
        self.label = tk.Label(self.row, text=_short(title), font=(theme.FONT_UI, 10),
                              bg=C["tab_idle"], fg=C["muted"])
        self.label.pack(side="left")
        self.close = tk.Label(self.row, text="✕", font=(theme.FONT_UI, 8), bg=C["tab_idle"],
                              fg=C["faint"], padx=px(6), cursor="hand2")
        self.close.pack(side="left", padx=(px(6), 0))

        self.parts = (self, self.row, self.label, self.close)
        for w in (self, self.row, self.label):
            w.bind("<Button-1>", lambda _e: bar._clicked(key))
            w.bind("<Button-2>", lambda _e: bar._close(key))
        self.close.bind("<Button-1>", lambda _e: bar._close(key))
        for w in self.parts:
            w.bind("<Enter>", self._schedule_poll, add="+")
            w.bind("<Leave>", self._schedule_poll, add="+")

    def _schedule_poll(self, _e=None) -> None:
        self.after(1, self._poll)

    def _poll(self) -> None:
        if not self.winfo_exists():
            return
        try:
            w = self.winfo_containing(*self.winfo_pointerxy())
        except (KeyError, tk.TclError):
            w = None
        inside, x = False, w
        while x is not None:
            if x is self:
                inside = True
                break
            x = getattr(x, "master", None)
        self.hover = inside
        self.close_hover = w is self.close
        self.paint()

    def set_active(self, active: bool) -> None:
        self.active = active
        self.paint()

    def paint(self) -> None:
        bg = C["tab_active"] if self.active else (C["tab_hover"] if self.hover else C["tab_idle"])
        for w in self.parts:
            w.configure(bg=bg)
        self.strip.configure(bg=C["accent"] if self.active else bg)
        self.label.configure(fg=C["fg"] if (self.active or self.hover) else C["muted"])
        if self.close_hover:
            self.close.configure(fg=C["danger"])
        else:
            self.close.configure(fg=C["muted"] if (self.active or self.hover) else C["faint"])


class TabBar(tk.Frame):
    def __init__(self, master, on_select: Callable[[str], None], on_close: Callable[[str], None]):
        super().__init__(master, bg=C["tabbar"])
        self._on_select, self._on_close = on_select, on_close
        self._tabs: dict[str, _Tab] = {}
        self._order: list[str] = []
        self._active: str | None = None

        self.canvas = tk.Canvas(self, bg=C["tabbar"], highlightthickness=0, bd=0,
                                height=px(34), xscrollincrement=px(30))
        self.canvas.pack(side="top", fill="x")
        tk.Frame(self, height=1, bg=C["border"]).pack(side="top", fill="x")

        self.inner = tk.Frame(self.canvas, bg=C["tabbar"])
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._on_inner_configure)
        self._bind_wheel(self.canvas)
        self._bind_wheel(self.inner)

    # -- public API -------------------------------------------------------
    @property
    def active(self) -> str | None:
        return self._active

    def add(self, key: str, title: str) -> None:
        tab = _Tab(self, key, title)
        tab.pack(side="left", fill="y", padx=(0, px(2)))
        for w in tab.parts:
            self._bind_wheel(w)
        self._tabs[key] = tab
        self._order.append(key)

    def set_active(self, key: str | None) -> None:
        if self._active in self._tabs:
            self._tabs[self._active].set_active(False)
        self._active = key
        if key in self._tabs:
            self._tabs[key].set_active(True)
            self.after_idle(lambda: self._ensure_visible(key))

    def remove(self, key: str) -> str | None:
        """Remove a tab; returns the neighbouring tab key (or None if none left)."""
        if key not in self._tabs:
            return None
        idx = self._order.index(key)
        self._tabs.pop(key).destroy()
        self._order.remove(key)
        if self._active == key:
            self._active = None
        if not self._order:
            return None
        return self._order[min(idx, len(self._order) - 1)]

    def cycle(self, step: int) -> str | None:
        if not self._order:
            return None
        if self._active not in self._order:
            return self._order[0]
        return self._order[(self._order.index(self._active) + step) % len(self._order)]

    # -- internals --------------------------------------------------------
    def _clicked(self, key: str) -> None:
        self._on_select(key)

    def _close(self, key: str) -> None:
        self._on_close(key)

    def _on_inner_configure(self, event) -> None:
        self.canvas.configure(scrollregion=(0, 0, event.width, event.height),
                              height=max(px(34), event.height))

    def _bind_wheel(self, widget) -> None:
        widget.bind("<MouseWheel>", self._on_wheel, add="+")
        widget.bind("<Button-4>", self._on_wheel, add="+")
        widget.bind("<Button-5>", self._on_wheel, add="+")

    def _on_wheel(self, event) -> None:
        if self.inner.winfo_width() <= self.canvas.winfo_width():
            return
        up = getattr(event, "num", 0) == 4 or getattr(event, "delta", 0) > 0
        self.canvas.xview_scroll(-3 if up else 3, "units")

    def _ensure_visible(self, key: str) -> None:
        tab = self._tabs.get(key)
        total = self.inner.winfo_width()
        if tab is None or total <= 1:
            return
        x0 = tab.winfo_x()
        x1 = x0 + tab.winfo_width()
        left = self.canvas.canvasx(0)
        width = self.canvas.winfo_width()
        if x0 < left:
            self.canvas.xview_moveto(x0 / total)
        elif x1 > left + width:
            self.canvas.xview_moveto((x1 - width) / total)

"""
PASSMAN - Password & Passphrase Security Toolkit (GUI layer)

Thin CustomTkinter front-end over the existing project logic.
All calculations are delegated to project.py and the generators package;
this module only collects input, validates it and displays results.

Run from anywhere:
    python gui.py
"""

import os
import sys
import threading
import tkinter as tk
from pathlib import Path

import customtkinter as ctk

# A PyInstaller --windowed build has no console, so sys.stdout/stderr are
# None. project.py and generators/password_checker.py print() a lot (CLI
# output re-used here); without this guard the first print() would crash
# with AttributeError: 'NoneType' object has no attribute 'write'.
# encoding="utf-8" matters: on Windows the default would be cp1252, and the
# first print("✓ ...") would raise UnicodeEncodeError (silently, no console).
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

# Make project modules importable no matter where gui.py is started from
PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from project import (  # noqa: E402
    evaluate_entropy,
    rate_strength,
    calculate_crack_time,
    calculate_quantum_crack_time,
    check_length_policy,
)
from generators import PasswordGenerator, DicewareGenerator, PasswordChecker  # noqa: E402


# ============================================
# Brand system - Deep Ocean
# ============================================

C = {
    "bg": "#F5F7FA",
    "card": "#FFFFFF",
    "ink": "#0F172A",
    "ink_soft": "#475569",
    "accent": "#0891B2",
    "accent_soft": "#E0F2FE",
    "border": "#E2E8F0",
    "bad": "#DC2626",
    "header": "#0F172A",
    "brand_text": "#7DD3FC",
    "tagline": "#94A3B8",
    "surface_light": "#F8FAFC",
    "btn_border": "#334155",
    "warm": "#ff8c00",
    "deep_navy": "#0C4A6E",
    "mid_blue": "#0369A1",
    "teal": "#0E7490",
}

# Rating -> bar / badge colour (red -> orange -> ocean blues, no green by design)
RATING_COLORS = {
    "CRITICAL": C["bad"],
    "VERY WEAK": C["bad"],
    "WEAK": C["bad"],
    "MODERATE": C["warm"],
    "GOOD": C["warm"],
    "STRONG": C["accent"],
    "VERY STRONG": C["teal"],
    "EXCEPTIONAL": C["mid_blue"],
    "MAXIMUM": C["deep_navy"],
}

HIBP_LABELS = {
    "found": ("Breached", C["bad"]),
    "clean": ("Not found", C["accent"]),
    "rate_limited": ("Rate limited", C["warm"]),
    "timeout": ("Timeout", C["warm"]),
    "connection_error": ("No connection", C["warm"]),
    "service_unavailable": ("Unavailable", C["warm"]),
    "bad_request": ("Bad request", C["warm"]),
}

ONLINE_RATE = 7200 / 86400   # 7.2k attempts/day (same as CLI)
GPU_RATE = 1e15              # 10^15 guesses/s  (same as CLI)
MAX_BAR_BITS = 128           # progress bar is full at AES-128 strength

# Business rules mirrored from the CLI input functions in project.py
MIN_PASSWORD_LENGTH = 8
MIN_CHARSET_TYPES = 2
MIN_WORDS = 4
WARN_WORDS = 10
CLIPBOARD_CLEAR_MS = 30_000


def font(size=13, weight="normal", mono=False):
    family = "Consolas" if mono else "Segoe UI"
    return ctk.CTkFont(family=family, size=size, weight=weight)


def clean(text: str) -> str:
    """Drop emoji variation selectors (U+FE0F) - Tk 8.6 on Windows renders them as boxes."""
    return text.replace("\ufe0f", "").replace("  ", " ")


def card(master, **kwargs):
    return ctk.CTkFrame(master, fg_color=C["card"], border_color=C["border"],
                        border_width=1, corner_radius=10, **kwargs)


WINDOW_WIDTH = 450
SIDE_WIDTH = 150      # left settings card
TEXT_WRAP = 236       # wrap width inside right-hand cards


# ============================================
# Reusable widgets
# ============================================

class NumberInput(ctk.CTkFrame):
    """Slider + typed entry kept in sync. Typed values are clamped to [lo, hi]."""

    def __init__(self, master, lo: int, hi: int, value: int, on_change=None):
        super().__init__(master, fg_color="transparent")
        self.lo, self.hi, self.on_change = lo, hi, on_change
        self.var = ctk.IntVar(value=value)

        self.slider = ctk.CTkSlider(self, from_=lo, to=hi, number_of_steps=hi - lo,
                                    variable=self.var, width=SIDE_WIDTH - 28,
                                    progress_color=C["accent"], button_color=C["accent"],
                                    button_hover_color=C["teal"], fg_color=C["border"],
                                    command=self._from_slider)
        self.slider.pack(anchor="w")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(anchor="w", pady=(6, 0))
        self.entry = ctk.CTkEntry(row, width=52, height=28, font=font(13, "bold"),
                                  justify="center", border_color=C["border"],
                                  fg_color=C["card"], text_color=C["ink"])
        self.entry.insert(0, str(value))
        self.entry.pack(side="left")
        ctk.CTkLabel(row, text=f"{lo}–{hi}", font=font(11), text_color=C["tagline"]
                     ).pack(side="left", padx=8)
        for event in ("<Return>", "<FocusOut>", "<KP_Enter>"):
            self.entry.bind(event, self._from_entry)

    def get(self) -> int:
        self._from_entry()  # accept a value typed without pressing Enter
        return int(self.var.get())

    def _set(self, n: int):
        self.var.set(n)
        self.entry.delete(0, "end")
        self.entry.insert(0, str(n))
        if self.on_change:
            self.on_change(n)

    def _from_slider(self, value):
        self._set(int(round(value)))

    def _from_entry(self, _event=None):
        try:
            n = int(self.entry.get().strip())
        except ValueError:
            n = int(self.var.get())  # not a number -> restore last valid value
        self._set(max(self.lo, min(self.hi, n)))


class VScroll(ctk.CTkFrame):
    """Vertical-only scroll area for the whole app body, so a card that doesn't
    fit the current window height is reachable by scrolling instead of being
    silently cut off (previously only visible when the window was maximized).

    Uses a plain tkinter.Canvas for the wheel bindings: CustomTkinter widgets
    disable bind_all/unbind_all on themselves (it raises AttributeError), but
    a stock tk.Canvas still has the real Tkinter method.
    """

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, bg=C["bg"], highlightthickness=0, bd=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vsb = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview,
                               button_color=C["border"], button_hover_color=C["tagline"])
        vsb.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=vsb.set)

        self.inner = ctk.CTkFrame(self.canvas, fg_color="transparent")
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.refresh())
        # Keep the inner frame exactly as wide as the visible canvas (no horizontal scroll here)
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfigure(self.window_id, width=e.width))

        # Wheel / touchpad scrolling anywhere over the app body.
        # Bound once and permanently (no <Enter>/<Leave> toggling): moving the
        # pointer onto a card or label sends the canvas a <Leave>, which used
        # to switch scrolling off everywhere except empty space.
        self.canvas.configure(yscrollincrement=20)
        self._acc = 0
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)
        self.canvas.bind_all("<Button-4>", lambda e: self._scroll_units(-1, e))  # Linux
        self.canvas.bind_all("<Button-5>", lambda e: self._scroll_units(1, e))   # Linux

    def refresh(self):
        """Recompute the scrollable height from the content's requested size."""
        self.update_idletasks()
        height = max(self.inner.winfo_reqheight(), self.inner.winfo_height())
        self.canvas.configure(scrollregion=(0, 0, self.canvas.winfo_width(), height))

    def _pointer_inside(self, event) -> bool:
        w = self.winfo_containing(event.x_root, event.y_root)
        return w is not None and str(w).startswith(str(self))

    def _content_fits(self) -> bool:
        return self.inner.winfo_reqheight() <= self.canvas.winfo_height()

    def _on_wheel(self, event):
        # Precision touchpads send many small deltas (e.g. 10-30) instead of
        # 120 per notch; int(delta / 120) rounded those to 0, so accumulate.
        if not self._pointer_inside(event) or self._content_fits():
            return
        self._acc += event.delta
        units = int(self._acc / 40)  # 120 (one mouse notch) = 3 units = 60 px
        if units:
            self._acc -= units * 40
            self.canvas.yview_scroll(-units, "units")

    def _scroll_units(self, units, event):
        if self._pointer_inside(event) and not self._content_fits():
            self.canvas.yview_scroll(units * 3, "units")


class HScrollTable(ctk.CTkFrame):
    """Card with a grid of labels, scrollable horizontally only.

    Vertical scrolling is handled by the outer VScroll around the whole app
    body, so this card is never height-clipped: its canvas height always
    matches its content (see _on_inner_configure).
    """

    def __init__(self, master):
        super().__init__(master, fg_color=C["card"], border_color=C["border"],
                         border_width=1, corner_radius=10)
        self.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self, bg=C["card"], highlightthickness=0, bd=0)
        self.canvas.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 0))
        hsb = ctk.CTkScrollbar(self, orientation="horizontal", command=self.canvas.xview,
                               button_color=C["border"], button_hover_color=C["tagline"])
        hsb.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 6))
        self.canvas.configure(xscrollcommand=hsb.set)

        self.inner = ctk.CTkFrame(self.canvas, fg_color=C["card"])
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._on_inner_configure)

        # Horizontal: Shift + wheel, or a horizontal touchpad swipe (Tk on
        # Windows reports that as Shift-MouseWheel). Only while the pointer
        # is over this table; bound once, same reasoning as in VScroll.
        self.canvas.configure(xscrollincrement=20)
        self._acc = 0
        self.canvas.bind_all("<Shift-MouseWheel>", self._on_wheel)

    def _on_inner_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"),
                              height=self.inner.winfo_reqheight())

    def _on_wheel(self, event):
        w = self.winfo_containing(event.x_root, event.y_root)
        if w is None or not str(w).startswith(str(self)):
            return
        self._acc += event.delta
        units = int(self._acc / 40)
        if units:
            self._acc -= units * 40
            self.canvas.xview_scroll(-units, "units")

    def clear(self):
        for w in self.inner.winfo_children():
            w.destroy()
        self.canvas.xview_moveto(0)


# ============================================
# Generator views (password + passphrase)
#
#  +-----------+------------------+
#  | settings  | secret card      |
#  | (same     +------------------+
#  |  height   | Online           |
#  |  as right | GPU farm         |
#  |  column)  | Quantum          |
#  +-----------+------------------+
#  | summary (full width)         |
#  +------------------------------+
# ============================================

class GeneratorView(ctk.CTkFrame):
    TITLE = "Your secret"

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self._secret = ""
        self.grid_columnconfigure(0, minsize=SIDE_WIDTH)
        self.grid_columnconfigure(1, weight=1)

        # Left settings card spans the 4 right-hand rows -> identical height
        self.side = card(self, width=SIDE_WIDTH)
        self.side.grid(row=0, column=0, rowspan=4, sticky="nsew", padx=(0, 8))
        self.build_settings(self.side)
        self.gen_btn = ctk.CTkButton(self.side, text="Generate", height=34,
                                     font=font(13, "bold"), fg_color=C["accent"],
                                     hover_color=C["teal"], text_color=C["surface_light"],
                                     command=self.generate)
        self.gen_btn.pack(side="bottom", fill="x", padx=12, pady=12)

        # --- secret card ---
        top = card(self)
        top.grid(row=0, column=1, sticky="ew")
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text=self.TITLE, font=font(12), text_color=C["ink_soft"]
                     ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 0))
        self.copy_btn = ctk.CTkButton(top, text="Copy", width=56, height=24, font=font(11),
                                      fg_color=C["card"], hover_color=C["accent_soft"],
                                      text_color=C["teal"], border_color=C["border"],
                                      border_width=1, command=self._copy)
        self.copy_btn.grid(row=0, column=1, padx=10, pady=(8, 0))
        self.secret_label = ctk.CTkLabel(top, text="—", font=font(14, mono=True),
                                         text_color=C["ink"], anchor="w", justify="left",
                                         wraplength=TEXT_WRAP)
        self.secret_label.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 6))
        self.badge = ctk.CTkLabel(top, text="  —  ", font=font(11, "bold"),
                                  fg_color=C["accent_soft"], text_color=C["deep_navy"],
                                  corner_radius=6, height=22)
        self.badge.grid(row=2, column=0, columnspan=2, sticky="w", padx=12)
        self.meta = ctk.CTkLabel(top, text="", font=font(11), text_color=C["ink_soft"])
        self.meta.grid(row=3, column=0, columnspan=2, sticky="w", padx=12)
        self.bar = ctk.CTkProgressBar(top, height=6, fg_color=C["border"],
                                      progress_color=C["accent"], corner_radius=3)
        self.bar.set(0)
        self.bar.grid(row=4, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 12))

        # --- crack time cards, stacked vertically ---
        self.time_values = {}
        for i, (key, label) in enumerate([
            ("online", "Online · 7.2k/day"),
            ("gpu", "GPU farm · 10^15 guesses/s"),
            ("quantum", "Quantum · Grover"),
        ], start=1):
            c = card(self)
            c.grid(row=i, column=1, sticky="ew", pady=(8, 0))
            ctk.CTkLabel(c, text=label, font=font(11), text_color=C["ink_soft"]
                         ).pack(anchor="w", padx=12, pady=(6, 0))
            v = ctk.CTkLabel(c, text="—", font=font(14, "bold"),
                             text_color=C["warm"] if key == "quantum" else C["ink"])
            v.pack(anchor="w", padx=12, pady=(0, 6))
            self.time_values[key] = v

        # --- summary, full width under everything ---
        notes = card(self)
        notes.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.notes = ctk.CTkLabel(notes, text="Generate to see the analysis.",
                                  font=font(11), text_color=C["ink_soft"], justify="left",
                                  anchor="w", wraplength=WINDOW_WIDTH - 60)
        self.notes.pack(fill="x", padx=12, pady=10)

    # --- to be provided by subclasses ---
    def build_settings(self, side):
        raise NotImplementedError

    def generate(self):
        raise NotImplementedError

    # --- shared helpers ---
    @staticmethod
    def label(master, text, hint=False, **pack):
        lbl = ctk.CTkLabel(master, text=text, font=font(11 if hint else 12),
                           text_color=C["tagline"] if hint else C["ink_soft"],
                           justify="left", wraplength=SIDE_WIDTH - 24)
        lbl.pack(anchor="w", padx=12, **pack)
        return lbl

    def show(self, secret: str, entropy: float, meta: str, length: int):
        strength = rate_strength(entropy)
        color = RATING_COLORS.get(strength["rating"], C["accent"])
        self._secret = secret

        self.secret_label.configure(text=secret)
        self.copy_btn.configure(text="Copy")
        self.badge.configure(text=f"  {strength['rating']}  ", text_color=C["card"], fg_color=color)
        self.meta.configure(text=f"{entropy:.1f} bits · {meta}")
        self.bar.configure(progress_color=color)
        self.bar.set(min(entropy / MAX_BAR_BITS, 1.0))

        self.time_values["online"].configure(text=calculate_crack_time(entropy, ONLINE_RATE))
        self.time_values["gpu"].configure(text=calculate_crack_time(entropy, GPU_RATE))
        self.time_values["quantum"].configure(text=calculate_quantum_crack_time(entropy))

        lines = [strength["description"], f"Recommendation: {strength['recommendation']}", ""]
        if strength["standards"]:
            lines.append("Reference points")
            lines += [f"   {clean(s)}" for s in strength["standards"]]
            lines.append("")
        lines.append(f"Standards (length {length} characters)")
        lines += [f"   {clean(s)}" for s in check_length_policy(length)]
        self.notes.configure(text="\n".join(lines), text_color=C["ink"])

    def _copy(self):
        if not self._secret:
            return
        root = self.winfo_toplevel()
        root.clipboard_clear()
        root.clipboard_append(self._secret)
        copied = self._secret
        self.copy_btn.configure(text="Copied")

        def clear_if_unchanged():
            try:
                if root.clipboard_get() == copied:
                    root.clipboard_clear()
            except Exception:
                pass  # clipboard empty or unavailable
        root.after(CLIPBOARD_CLEAR_MS, clear_if_unchanged)


class PasswordView(GeneratorView):
    TITLE = "Your password"

    def build_settings(self, side):
        self.generator = PasswordGenerator()
        self.label(side, "Length", pady=(10, 4))
        self.length = NumberInput(side, MIN_PASSWORD_LENGTH, 64, 16)
        self.length.pack(anchor="w", padx=12)
        self.label(side, "15+ recommended", hint=True, pady=(2, 0))

        self.label(side, f"Characters (min. {MIN_CHARSET_TYPES} types)", pady=(10, 2))
        self.opts = {}
        for key, text in [("upper", "Upper A-Z"), ("lower", "Lower a-z"),
                          ("digits", "Digits 0-9"), ("special", "Symbols")]:
            var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(side, text=text, variable=var, font=font(12),
                            text_color=C["ink"], fg_color=C["accent"],
                            hover_color=C["teal"], border_color=C["ink_soft"],
                            checkbox_width=16, checkbox_height=16
                            ).pack(anchor="w", padx=12, pady=2)
            self.opts[key] = var
        self.label(side, f"   {PasswordGenerator.SPECIAL_CHARS}", hint=True)
        self.error = ctk.CTkLabel(side, text="", font=font(11), text_color=C["bad"],
                                  wraplength=SIDE_WIDTH - 24, justify="left")
        self.error.pack(anchor="w", padx=12)

    def generate(self):
        upper, lower = self.opts["upper"].get(), self.opts["lower"].get()
        digits, special = self.opts["digits"].get(), self.opts["special"].get()
        if sum([upper, lower, digits, special]) < MIN_CHARSET_TYPES:
            self.error.configure(text=f"Select at least {MIN_CHARSET_TYPES} character types.")
            return
        self.error.configure(text="")

        length = self.length.get()
        password = self.generator.generate(length, upper, lower, digits, special)
        charset = self.generator.get_charset_size(upper, lower, digits, special)
        entropy = evaluate_entropy(length, charset)
        self.show(password, entropy, f"charset {charset}", length)


class PassphraseView(GeneratorView):
    TITLE = "Your passphrase"

    def build_settings(self, side):
        self.generator = None  # wordlist is loaded on first use
        self.label(side, "Number of words", pady=(10, 4))
        self.words = NumberInput(side, MIN_WORDS, 12, 6, on_change=self._on_words)
        self.words.pack(anchor="w", padx=12)
        self.label(side, "EFF recommends 6+", hint=True, pady=(2, 0))

        self.label(side, "Separator", pady=(10, 4))
        self.separator = ctk.CTkSegmentedButton(
            side, values=["space", "-", "."], font=font(11), width=SIDE_WIDTH - 24,
            selected_color=C["accent"], selected_hover_color=C["teal"],
            unselected_color=C["card"], unselected_hover_color=C["accent_soft"],
            text_color=C["ink"], fg_color=C["border"])
        self.separator.set("space")
        self.separator.pack(anchor="w", padx=12)

        self.label(side, "EFF Large Wordlist\n7,776 words · ~12.9 bits/word", hint=True, pady=(10, 0))
        self.info = ctk.CTkLabel(side, text="", font=font(11), text_color=C["warm"],
                                 wraplength=SIDE_WIDTH - 24, justify="left")
        self.info.pack(anchor="w", padx=12, pady=(4, 0))

    def _on_words(self, n: int):
        self.info.configure(text="Very long, but very secure." if n > WARN_WORDS else "",
                            text_color=C["warm"])

    def generate(self):
        try:
            if self.generator is None:
                self.generator = DicewareGenerator()
        except FileNotFoundError:
            self.info.configure(text="eff_largelist.csv not found next to project.py.",
                                text_color=C["bad"])
            return

        num_words = self.words.get()
        sep = self.separator.get()
        passphrase = self.generator.generate(num_words, " " if sep == "space" else sep)
        entropy = evaluate_entropy(num_words, DicewareGenerator.WORDLIST_SIZE)
        self.show(passphrase, entropy, f"{num_words} words", len(passphrase))


# ============================================
# Mode 3 - CSV checker (HIBP)
# ============================================

class CheckerView(ctk.CTkFrame):
    COLUMNS = [("Service", 130), ("Password", 120), ("Rating", 100), ("Entropy", 60),
               ("GPU farm", 110), ("Length (NIST)", 110), ("HIBP", 110)]

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        # No row is stretched: the table takes its natural height and the
        # app-wide VScroll (see App) handles anything taller than the window.
        self.csv_path = PROJECT_DIR / "passwords.csv"
        self.results = []
        self.running = False

        # --- toolbar (two rows to fit 450 px) ---
        bar = card(self)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_columnconfigure(0, weight=1)
        self.file_label = ctk.CTkLabel(bar, text=f"File: {self.csv_path.name}", font=font(12),
                                       text_color=C["ink_soft"], anchor="w")
        self.file_label.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))
        ctk.CTkButton(bar, text="Choose CSV", width=96, height=28, font=font(12),
                      fg_color=C["card"], hover_color=C["accent_soft"], text_color=C["teal"],
                      border_color=C["border"], border_width=1, command=self.choose_file
                      ).grid(row=0, column=1, padx=12, pady=(10, 4))
        self.show_pw = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(bar, text="Show passwords", variable=self.show_pw, font=font(12),
                      text_color=C["ink_soft"], progress_color=C["accent"],
                      command=self.render).grid(row=1, column=0, sticky="w", padx=12, pady=(4, 10))
        self.run_btn = ctk.CTkButton(bar, text="Run check", width=96, height=30,
                                     font=font(12, "bold"), fg_color=C["accent"],
                                     hover_color=C["teal"], text_color=C["surface_light"],
                                     command=self.run)
        self.run_btn.grid(row=1, column=1, padx=12, pady=(4, 10))

        # --- HIBP / NIST explanation: a tagged row per term (same badge style as
        # the rating badges elsewhere), dark ink text - not the muted tagline
        # colour, so it doesn't read as decorative filler that can be ignored ---
        info = card(self)
        info.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self._info_row(info, "HIBP", "Have I Been Pwned. Only the first 5 characters of "
                       "the password's SHA-1 hash are sent - never the password itself.",
                       top_pad=(12, 8))
        ctk.CTkFrame(info, fg_color=C["border"], height=1).pack(fill="x", padx=12)
        self._info_row(info, "NIST", "NIST SP 800-63B-4. Regulates length only: 15+ "
                       "characters recommended, no composition rules required.",
                       top_pad=(8, 12))

        self.status = ctk.CTkLabel(self, text="", font=font(11), text_color=C["ink_soft"],
                                   anchor="w", justify="left", wraplength=WINDOW_WIDTH - 30)
        self.status.grid(row=2, column=0, sticky="ew", pady=(8, 4))

        # --- table, horizontal scrollbar only (vertical scroll is app-wide, see VScroll) ---
        self.table = HScrollTable(self)
        self.table.grid(row=3, column=0, sticky="ew")

        # --- alerts ---
        self.alerts = ctk.CTkLabel(self, text="", font=font(11), text_color=C["bad"],
                                   justify="left", anchor="w", wraplength=WINDOW_WIDTH - 70)
        # Bottom padding: the last alert line used to sit flush on the window
        # edge and got cut in half on Windows (larger font metrics / DPI scaling).
        self.alerts.grid(row=4, column=0, sticky="ew", pady=(6, 16))
        self.render()

    def _info_row(self, master, tag, text, top_pad):
        row = ctk.CTkFrame(master, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=top_pad)
        ctk.CTkLabel(row, text=f"  {tag}  ", font=font(11, "bold"), corner_radius=6,
                     fg_color=C["accent_soft"], text_color=C["deep_navy"], height=20
                     ).pack(side="left", anchor="n")
        ctk.CTkLabel(row, text=text, font=font(12), text_color=C["ink"], anchor="w",
                     justify="left", wraplength=WINDOW_WIDTH - 110
                     ).pack(side="left", padx=(8, 0))

    def choose_file(self):
        path = ctk.filedialog.askopenfilename(
            initialdir=str(self.csv_path.parent), filetypes=[("CSV files", "*.csv")])
        if path:
            self.csv_path = Path(path)
            self.file_label.configure(text=f"File: {self.csv_path.name}")

    def run(self):
        if self.running:
            return
        try:
            checker = PasswordChecker(str(self.csv_path))
        except Exception as e:
            self.status.configure(text=f"Couldn't read the file. {e}", text_color=C["bad"])
            return
        if not checker.passwords:
            self.status.configure(text="No passwords found (expected columns: Service,Password).",
                                  text_color=C["bad"])
            return

        self.running = True
        self.run_btn.configure(state="disabled", text="Checking…")
        self.status.configure(text=f"Checking {len(checker.passwords)} passwords "
                              f"(about {len(checker.passwords) * 0.7:.0f} s)…",
                              text_color=C["ink_soft"])

        def worker():
            try:
                results = checker.analyze_all()
                self.after(0, self._done, results, None)
            except Exception as e:  # keep the GUI alive whatever happens
                self.after(0, self._done, [], e)

        threading.Thread(target=worker, daemon=True).start()

    def _done(self, results, error):
        self.running = False
        self.run_btn.configure(state="normal", text="Run check")
        if error:
            self.status.configure(text=f"Check failed. {error}", text_color=C["bad"])
            return
        self.results = results
        if {r["hibp_status"] for r in results} - {"found", "clean"}:
            self.status.configure(text="Done, but some HIBP lookups failed (see HIBP column).",
                                  text_color=C["warm"])
        else:
            self.status.configure(text=f"Done · {len(results)} passwords checked.",
                                  text_color=C["ink_soft"])
        self.render()

    def render(self):
        self.table.clear()
        grid = self.table.inner
        for col, (name, width) in enumerate(self.COLUMNS):
            ctk.CTkLabel(grid, text=name, font=font(12, "bold"), text_color=C["ink_soft"],
                         width=width, anchor="w").grid(row=0, column=col, padx=4, pady=(2, 4),
                                                       sticky="w")
        if not self.results:
            ctk.CTkLabel(grid, text="Run the check to see results.", font=font(12),
                         text_color=C["tagline"]).grid(row=1, column=0, columnspan=3,
                                                       padx=4, pady=8, sticky="w")
            self.alerts.configure(text="")
            self.alerts.grid_remove()
            return

        for i, r in enumerate(self.results, start=1):
            rating_color = RATING_COLORS.get(r["rating"], C["ink"])
            pw = r["password"] if self.show_pw.get() else "•" * min(len(r["password"]), 12)
            length = len(r["password"])
            nist = "15+ ✓" if length >= 15 else ("MFA only" if length >= 8 else "too short")
            hibp_text, hibp_color = HIBP_LABELS.get(r["hibp_status"], ("Unknown", C["warm"]))
            if r["hibp_status"] == "found":
                hibp_text = f"Breached {r['hibp_count']:,}×"
            cells = [
                (r["service"], C["ink"], font(12)),
                (pw, C["ink"], font(12, mono=True)),
                (r["rating"], rating_color, font(12, "bold")),
                (f"{r['entropy']:.1f}", C["ink"], font(12)),
                (calculate_crack_time(r["entropy"], GPU_RATE), C["ink"], font(12)),
                (f"{length} · {nist}", C["ink_soft"] if length >= 15 else C["warm"], font(12)),
                (hibp_text, hibp_color, font(12, "bold" if r["hibp_status"] == "found" else "normal")),
            ]
            for col, (text, color, f) in enumerate(cells):
                ctk.CTkLabel(grid, text=text, text_color=color, font=f,
                             width=self.COLUMNS[col][1], anchor="w"
                             ).grid(row=i, column=col, padx=4, pady=0, sticky="w")

        # Same alert rules as PasswordChecker._print_security_warnings
        breached = [r["service"] for r in self.results if r["hibp_breached"] is True]
        weak_ratings = ("CRITICAL", "VERY WEAK", "WEAK", "MODERATE")
        weak = [r["service"] for r in self.results if r["rating"] in weak_ratings]
        lines = []
        if breached:
            lines.append(f"In known breaches ({len(breached)}), change now: {', '.join(breached)}")
        if weak:
            lines.append(f"GPU farm cracks in ≤ ~1 hour ({len(weak)}): {', '.join(weak)}")
        if lines:
            self.alerts.configure(text="\n".join(lines))
            self.alerts.grid()
            # The wrapped label can settle its final height after this frame's
            # <Configure> already ran; re-measure the scroll area once idle.
            self.after_idle(self.winfo_toplevel().scroll.refresh)
        else:
            self.alerts.configure(text="")
            self.alerts.grid_remove()


# ============================================
# Main window
# ============================================

class App(ctk.CTk):
    MODES = [("password", "Password"), ("passphrase", "Passphrase"), ("checker", "Check CSV")]

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        self.title("PASSMAN")
        # Without a console (--windowed .exe) a failing button callback would
        # just do nothing. Show the error in a dialog instead.
        self.report_callback_exception = self._show_error
        # 640px opens comfortably even on a 768px-tall laptop screen with the
        # Windows taskbar and DPI scaling eating into it; 520 is the minimum at
        # which the settings card and its Generate button both stay usable.
        # Anything taller is reachable via the app-wide VScroll either way.
        self.geometry(f"{WINDOW_WIDTH}x590")
        self.minsize(WINDOW_WIDTH, 470)
        self.configure(fg_color=C["bg"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- header: brand row + navigation row ---
        header = ctk.CTkFrame(self, fg_color=C["header"], corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkLabel(brand, text="PASSMAN", font=font(18, "bold"), text_color=C["brand_text"]
                     ).pack(side="left")
        ctk.CTkLabel(brand, text="Password security toolkit", font=font(11),
                     text_color=C["tagline"]).pack(side="left", padx=10, pady=(4, 0))

        nav = ctk.CTkFrame(header, fg_color="transparent")
        nav.pack(fill="x", padx=14, pady=(0, 10))
        self.nav = {}
        for i, (key, label) in enumerate(self.MODES):
            nav.grid_columnconfigure(i, weight=1, uniform="nav")
            b = ctk.CTkButton(nav, text=label, height=30, font=font(12), corner_radius=6,
                              border_width=1, command=lambda k=key: self.show(k))
            b.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 6, 0))
            self.nav[key] = b

        # --- views, inside a vertical scroll area so nothing is ever cut off ---
        self.scroll = VScroll(self)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=12)
        body = self.scroll.inner
        body.grid_columnconfigure(0, weight=1)
        self.views = {
            "password": PasswordView(body),
            "passphrase": PassphraseView(body),
            "checker": CheckerView(body),
        }
        # Views are created but not yet placed - show() grids exactly one at a
        # time. (Views have different natural heights now that none of them
        # is stretched to fill a fixed cell, so stacking all three with
        # tkraise() would let a taller hidden view peek out under a shorter
        # visible one; only ever gridding one avoids that.)
        self.current_view = None
        self.show("password")

    def show(self, key):
        if self.current_view is not None:
            self.views[self.current_view].grid_remove()
        # "new": natural height, stretched to the body's width. The body's own
        # height is not stretched, so content taller than the window is
        # reachable by scrolling instead of being clipped.
        self.views[key].grid(row=0, column=0, sticky="new")
        self.current_view = key
        self.scroll.canvas.yview_moveto(0)  # start each view at the top
        for k, b in self.nav.items():
            if k == key:
                b.configure(fg_color=C["accent"], hover_color=C["accent"],
                            text_color=C["surface_light"], border_color=C["accent"])
            else:
                b.configure(fg_color=C["header"], hover_color=C["btn_border"],
                            text_color=C["tagline"], border_color=C["btn_border"])

    def _show_error(self, exc_type, exc_value, exc_tb):
        import traceback
        from tkinter import messagebox
        detail = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        messagebox.showerror("PASSMAN - unexpected error",
                             f"{exc_type.__name__}: {exc_value}\n\n{detail[-1500:]}")


def main():
    App().mainloop()


if __name__ == "__main__":
    main()

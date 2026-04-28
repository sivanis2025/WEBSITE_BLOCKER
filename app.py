import customtkinter as ctk
from tkinter import messagebox, simpledialog
import hashlib
import json
import os
from datetime import datetime, date
import threading

# Matplotlib imports for stats chart
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from models.site_model import add_site, get_all_sites, analyze_website
from core.blocker import block_sites, unblock_sites

# ── Theme ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Cyberpunk Palette ──────────────────────────────────────────────────────────
BG_APP        = "#07080f"
BG_CARD       = "#0b0c17"
BG_PANEL      = "#0e1020"
BG_INPUT      = "#090b15"
BG_ITEM       = "#0e1020"
BG_ITEM_SEL   = "#131628"
BG_STATUS     = "#090b15"
BORDER        = "#1c1f3a"
BORDER_BRIGHT = "#2a2f5a"

CYAN          = "#00e5ff"
CYAN_DIM      = "#007a99"
RED_NEON      = "#ff2d55"
RED_DIM       = "#7a0020"
GREEN_NEON    = "#00ff88"
GREEN_DIM     = "#00552e"
ORANGE_NEON   = "#ff6b00"
PURPLE_NEON   = "#bf00ff"

TEXT_PRI      = "#e0e8ff"
TEXT_SEC      = "#4a5280"
TEXT_MUT      = "#252847"

ACCENT        = CYAN
ACCENT_HOVER  = "#00c4db"
BTN_GHOST     = "#0e1020"

PIN_FILE   = "pin.json"
STATS_FILE = "block_stats.json"

CATEGORY_COLORS = {
    "adult":        RED_NEON,
    "gambling":     ORANGE_NEON,
    "violence":     "#ff4444",
    "drugs":        PURPLE_NEON,
    "social_media": CYAN,
    "safe":         GREEN_NEON,
    "unknown":      TEXT_SEC,
}

FAVICON_COLORS = {
    "facebook":  ("#0a1a3a", "#4080ff"),
    "twitter":   ("#0a1f2e", "#38bdf8"),
    "instagram": ("#2a0a1e", "#ff4488"),
    "youtube":   ("#2a0a0a", "#ff3333"),
    "reddit":    ("#2a1500", "#ff6b00"),
    "tiktok":    ("#001020", "#00e5ff"),
    "casino":    ("#1a0a00", "#ff6b00"),
    "poker":     ("#1a0a00", "#ff6b00"),
    "default":   ("#0e1020", "#4a5280"),
}

def get_favicon_colors(url: str):
    for key, colors in FAVICON_COLORS.items():
        if key in url.lower():
            return colors
    return FAVICON_COLORS["default"]

def get_initial(url: str) -> str:
    domain = url.replace("www.", "").replace("https://", "").replace("http://", "")
    return domain[0].upper() if domain else "?"


# ── PIN Helpers ────────────────────────────────────────────────────────────────

def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()

def load_pin():
    if os.path.exists(PIN_FILE):
        with open(PIN_FILE, "r") as f:
            return json.load(f).get("pin_hash")
    return None

def save_pin(pin: str):
    with open(PIN_FILE, "w") as f:
        json.dump({"pin_hash": _hash_pin(pin)}, f)

def verify_pin(pin: str) -> bool:
    stored = load_pin()
    if stored is None:
        return True
    return _hash_pin(pin) == stored


# ── Stats Helpers ──────────────────────────────────────────────────────────────

def load_stats() -> dict:
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_stats(stats: dict):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)

def record_block_event():
    stats = load_stats()
    today = str(date.today())
    if today not in stats:
        stats[today] = {"blocks": 0, "unblocks": 0}
    stats[today]["blocks"] += 1
    save_stats(stats)

def record_unblock_event():
    stats = load_stats()
    today = str(date.today())
    if today not in stats:
        stats[today] = {"blocks": 0, "unblocks": 0}
    stats[today]["unblocks"] += 1
    save_stats(stats)


# ══════════════════════════════════════════════════════════════════════════════
class PinDialog(ctk.CTkToplevel):

    def __init__(self, master, title="Enter PIN",
                 prompt="Enter your 4-digit PIN:", confirm=False):
        super().__init__(master)
        self.title(title)
        self.geometry("360x320")
        self.resizable(False, False)
        self.configure(fg_color=BG_APP)
        self.grab_set()

        self._result   = None
        self._confirm  = confirm
        self._pin_var  = ctk.StringVar()
        self._conf_var = ctk.StringVar()

        hdr = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=0, height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text=f"◈ {title.upper()}",
            text_color=CYAN,
            font=ctk.CTkFont(family="Courier New", size=12, weight="bold")
        ).pack(side="left", padx=16, pady=14)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=16)

        ctk.CTkLabel(
            body, text=prompt,
            text_color=TEXT_SEC,
            font=ctk.CTkFont(family="Courier New", size=10)
        ).pack(anchor="w", pady=(0, 6))

        self._pin_entry = ctk.CTkEntry(
            body, textvariable=self._pin_var,
            placeholder_text="● ● ● ●", show="●",
            fg_color=BG_INPUT, border_color=BORDER_BRIGHT, border_width=1,
            text_color=CYAN, corner_radius=8, height=42,
            font=ctk.CTkFont(family="Courier New", size=18)
        )
        self._pin_entry.pack(fill="x", pady=(0, 10))

        if confirm:
            ctk.CTkLabel(
                body, text="CONFIRM PIN:",
                text_color=TEXT_SEC,
                font=ctk.CTkFont(family="Courier New", size=10)
            ).pack(anchor="w", pady=(0, 6))
            self._conf_entry = ctk.CTkEntry(
                body, textvariable=self._conf_var,
                placeholder_text="● ● ● ●", show="●",
                fg_color=BG_INPUT, border_color=BORDER_BRIGHT, border_width=1,
                text_color=CYAN, corner_radius=8, height=42,
                font=ctk.CTkFont(family="Courier New", size=18)
            )
            self._conf_entry.pack(fill="x", pady=(0, 10))

        self._err = ctk.CTkLabel(
            body, text="",
            text_color=RED_NEON,
            font=ctk.CTkFont(family="Courier New", size=10)
        )
        self._err.pack()

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            btn_row, text="CANCEL",
            fg_color=BTN_GHOST, hover_color=BG_ITEM_SEL,
            text_color=TEXT_SEC, corner_radius=8, height=38,
            border_width=1, border_color=BORDER_BRIGHT,
            font=ctk.CTkFont(family="Courier New", size=11),
            command=self.destroy
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btn_row, text="CONFIRM",
            fg_color=CYAN, hover_color=CYAN_DIM,
            text_color=BG_APP, corner_radius=8, height=38,
            font=ctk.CTkFont(family="Courier New", size=11, weight="bold"),
            command=self._on_confirm
        ).pack(side="left", fill="x", expand=True)

        self._pin_entry.focus()
        self._pin_entry.bind("<Return>", lambda e: self._on_confirm())

    def _on_confirm(self):
        pin = self._pin_var.get().strip()
        if len(pin) < 4:
            self._err.configure(text="⚠ PIN must be at least 4 digits")
            return
        if self._confirm:
            if pin != self._conf_var.get().strip():
                self._err.configure(text="⚠ PINs do not match!")
                return
        self._result = pin
        self.destroy()

    def get_result(self):
        self.wait_window()
        return self._result


# ══════════════════════════════════════════════════════════════════════════════
class StatsWindow(ctk.CTkToplevel):

    def __init__(self, master):
        super().__init__(master)
        self.title("Usage Statistics")
        self.geometry("780x500")
        self.resizable(True, True)
        self.configure(fg_color=BG_APP)

        hdr = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=0, height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(
            hdr, text="◈ USAGE STATISTICS  —  DAILY BLOCK HISTORY",
            text_color=CYAN,
            font=ctk.CTkFont(family="Courier New", size=12, weight="bold")
        ).pack(side="left", padx=16, pady=14)

        ctk.CTkButton(
            hdr, text="↻ REFRESH",
            fg_color=BTN_GHOST, hover_color=BG_ITEM_SEL,
            text_color=CYAN, corner_radius=6, height=28,
            border_width=1, border_color=CYAN_DIM,
            font=ctk.CTkFont(family="Courier New", size=10),
            width=90, command=self._draw_chart
        ).pack(side="right", padx=16)

        self._chart_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0)
        self._chart_frame.pack(fill="both", expand=True, padx=16, pady=16)

        self._draw_chart()

    def _draw_chart(self):
        for w in self._chart_frame.winfo_children():
            w.destroy()

        stats = load_stats()

        if not stats:
            ctk.CTkLabel(
                self._chart_frame,
                text="No data yet.\nStart blocking sites to see stats here!",
                text_color=TEXT_SEC,
                font=ctk.CTkFont(family="Courier New", size=13)
            ).pack(expand=True)
            return

        dates       = sorted(stats.keys())
        blocks      = [stats[d].get("blocks", 0)   for d in dates]
        unblocks    = [stats[d].get("unblocks", 0) for d in dates]
        x           = list(range(len(dates)))
        date_labels = [d[5:] for d in dates]

        fig, ax = plt.subplots(figsize=(7.2, 3.8))
        fig.patch.set_facecolor("#0b0c17")
        ax.set_facecolor("#090b15")

        bar_w = 0.35
        bars1 = ax.bar([i - bar_w/2 for i in x], blocks,
                       width=bar_w, label="Blocks",
                       color="#ff2d55", alpha=0.9, zorder=3)
        bars2 = ax.bar([i + bar_w/2 for i in x], unblocks,
                       width=bar_w, label="Unblocks",
                       color="#00ff88", alpha=0.9, zorder=3)

        for bar in bars1:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width()/2, h + 0.05,
                        str(int(h)), ha="center", va="bottom",
                        color="#ff2d55", fontsize=8, fontfamily="monospace")
        for bar in bars2:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width()/2, h + 0.05,
                        str(int(h)), ha="center", va="bottom",
                        color="#00ff88", fontsize=8, fontfamily="monospace")

        ax.set_xticks(x)
        ax.set_xticklabels(date_labels, color="#4a5280",
                           fontsize=9, fontfamily="monospace")
        ax.tick_params(axis="y", colors="#4a5280", labelsize=9)
        ax.spines["bottom"].set_color("#1c1f3a")
        ax.spines["left"].set_color("#1c1f3a")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
        ax.grid(axis="y", color="#1c1f3a", linestyle="--", linewidth=0.8, zorder=0)
        ax.set_xlabel("DATE", color="#4a5280",
                      fontsize=9, fontfamily="monospace", labelpad=8)
        ax.set_ylabel("COUNT", color="#4a5280",
                      fontsize=9, fontfamily="monospace", labelpad=8)
        ax.set_title("DAILY BLOCK / UNBLOCK HISTORY",
                     color="#00e5ff", fontsize=11,
                     fontfamily="monospace", pad=12)
        ax.legend(facecolor="#0e1020", edgecolor="#2a2f5a",
                  labelcolor="#e0e8ff", fontsize=9)
        fig.tight_layout(pad=1.5)

        canvas = FigureCanvasTkAgg(fig, master=self._chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
class StatCard(ctk.CTkFrame):
    def __init__(self, master, icon, label, value="0", accent=CYAN, **kwargs):
        super().__init__(master, fg_color=BG_PANEL, corner_radius=10,
                         border_width=1, border_color=BORDER_BRIGHT, **kwargs)
        self.configure(height=80)
        ctk.CTkLabel(
            self, text=icon, width=36, height=36,
            fg_color=BG_APP, corner_radius=8,
            text_color=accent, font=ctk.CTkFont(size=17)
        ).pack(pady=(14, 2))
        self._val_label = ctk.CTkLabel(
            self, text=value, text_color=accent,
            font=ctk.CTkFont(family="Courier New", size=18, weight="bold")
        )
        self._val_label.pack()
        ctk.CTkLabel(
            self, text=label.upper(), text_color=TEXT_SEC,
            font=ctk.CTkFont(family="Courier New", size=8)
        ).pack(pady=(0, 10))

    def set_value(self, v):
        self._val_label.configure(text=str(v))


# ══════════════════════════════════════════════════════════════════════════════
class SiteRow(ctk.CTkFrame):
    # ── CHANGED: added on_unblock parameter ───────────────────────────────────
    def __init__(self, master, url: str, on_remove, on_unblock,
                 category="unknown", confidence=0, **kwargs):
        super().__init__(master, fg_color=BG_ITEM, corner_radius=0, **kwargs)
        self.url  = url
        self._sep = None
        self.configure(height=58)

        bg, fg = get_favicon_colors(url)
        badge = ctk.CTkLabel(
            self, text=get_initial(url), width=30, height=30,
            fg_color=bg, text_color=fg, corner_radius=8,
            font=ctk.CTkFont(family="Courier New", size=13, weight="bold")
        )
        badge.pack(side="left", padx=(14, 10), pady=10)

        mid = ctk.CTkFrame(self, fg_color="transparent")
        mid.pack(side="left", fill="x", expand=True)

        lbl = ctk.CTkLabel(
            mid, text=url, text_color=TEXT_PRI,
            font=ctk.CTkFont(family="Courier New", size=12), anchor="w"
        )
        lbl.pack(anchor="w")

        cat_color = CATEGORY_COLORS.get(category, TEXT_SEC)
        cat_text  = f"◈ {category.upper()}  {confidence}%" if category != "unknown" else ""
        self._cat_label = ctk.CTkLabel(
            mid, text=cat_text, text_color=cat_color,
            font=ctk.CTkFont(family="Courier New", size=9), anchor="w"
        )
        self._cat_label.pack(anchor="w")

        # ── CHANGED: ✕ remove button (right-most) ─────────────────────────
        ctk.CTkButton(
            self, text="✕", width=28, height=28,
            fg_color="transparent", hover_color="#2a0a0a",
            text_color=TEXT_SEC, font=ctk.CTkFont(size=13),
            corner_radius=6, command=lambda: on_remove(url)
        ).pack(side="right", padx=(4, 12))

        # ── NEW: 🔓 Unblock button (next to ✕) ────────────────────────────
        ctk.CTkButton(
            self, text="🔓 UNBLOCK", width=90, height=28,
            fg_color="transparent", hover_color="#003320",
            text_color=GREEN_NEON,
            font=ctk.CTkFont(family="Courier New", size=9, weight="bold"),
            corner_radius=6, border_width=1, border_color=GREEN_NEON,
            command=lambda: on_unblock(url)
        ).pack(side="right", padx=(0, 4))

        for w in (self, badge, lbl, mid):
            w.bind("<Enter>", lambda e: self.configure(fg_color=BG_ITEM_SEL))
            w.bind("<Leave>", lambda e: self.configure(fg_color=BG_ITEM))


# ══════════════════════════════════════════════════════════════════════════════
class WebsiteBlockerApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Website Blocker")
        self.geometry("860x800")
        self.minsize(760, 700)
        self.resizable(True, True)
        self.configure(fg_color=BG_APP)

        self._blocking_active  = False
        self._site_rows: dict  = {}
        self._unblocked_today  = 0

        self._build_ui()
        self._load_sites()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        card = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=16,
                            border_width=1, border_color=BORDER)
        card.pack(fill="both", expand=True, padx=14, pady=14)
        self._build_header(card)
        self._build_stats_row(card)
        self._build_main_panels(card)
        self._build_footer(card)

    def _build_header(self, parent):
        hdr = ctk.CTkFrame(parent, fg_color=BG_PANEL, corner_radius=0, height=62)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        inner = ctk.CTkFrame(hdr, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=12)

        ctk.CTkLabel(
            inner, text="⬡", width=36, height=36,
            fg_color=BG_APP, corner_radius=10,
            text_color=CYAN, font=ctk.CTkFont(size=20)
        ).pack(side="left", padx=(0, 14))

        col = ctk.CTkFrame(inner, fg_color="transparent")
        col.pack(side="left")
        ctk.CTkLabel(
            col, text="WEBSITE BLOCKER",
            font=ctk.CTkFont(family="Courier New", size=16, weight="bold"),
            text_color=CYAN
        ).pack(anchor="w")
        ctk.CTkLabel(
            col, text="[ Network Access Control Interface v2.0 ]",
            font=ctk.CTkFont(family="Courier New", size=9),
            text_color=TEXT_SEC
        ).pack(anchor="w")

        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right")

        pin_exists = load_pin() is not None
        self._pin_btn = ctk.CTkButton(
            right,
            text="🔑 PIN SET" if pin_exists else "🔓 SET PIN",
            fg_color=BTN_GHOST, hover_color=BG_ITEM_SEL,
            text_color=ORANGE_NEON if pin_exists else TEXT_SEC,
            corner_radius=6, height=28, width=100,
            border_width=1,
            border_color=ORANGE_NEON if pin_exists else BORDER_BRIGHT,
            font=ctk.CTkFont(family="Courier New", size=9),
            command=self._manage_pin
        )
        self._pin_btn.pack(side="right", padx=(8, 0))

        self._status_pill = ctk.CTkLabel(
            right, text="◉  BLOCKING INACTIVE",
            fg_color=BG_APP, text_color=TEXT_SEC,
            corner_radius=6,
            font=ctk.CTkFont(family="Courier New", size=10, weight="bold"),
            padx=12, pady=5
        )
        self._status_pill.pack(side="right")

    def _build_stats_row(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(14, 0))

        self._stat_blocked = StatCard(row, "⬛", "Blocked Sites", "0", RED_NEON)
        self._stat_blocked.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._stat_timers = StatCard(row, "◷", "Active Timers", "0", CYAN)
        self._stat_timers.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._stat_unblocked = StatCard(row, "✦", "Unblocked Today", "0", GREEN_NEON)
        self._stat_unblocked.pack(side="left", fill="x", expand=True)

    def _build_main_panels(self, parent):
        panels = ctk.CTkFrame(parent, fg_color="transparent")
        panels.pack(fill="both", expand=True, padx=16, pady=12)

        # ── LEFT panel ────────────────────────────────────────────────────
        left = ctk.CTkFrame(panels, fg_color=BG_PANEL, corner_radius=12,
                            border_width=1, border_color=BORDER_BRIGHT)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self._panel_label(left, "◈ BLOCK WEBSITE", RED_NEON)

        self._field_label(left, "TARGET URL")
        url_row = ctk.CTkFrame(left, fg_color="transparent")
        url_row.pack(fill="x", padx=14, pady=(0, 10))

        self._url_entry = ctk.CTkEntry(
            url_row, placeholder_text="e.g. youtube.com",
            fg_color=BG_INPUT, border_color=BORDER_BRIGHT, border_width=1,
            text_color=TEXT_PRI, placeholder_text_color=TEXT_MUT,
            corner_radius=8, height=38,
            font=ctk.CTkFont(family="Courier New", size=12)
        )
        self._url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._url_entry.bind("<Return>", lambda e: self._add_site())

        ctk.CTkButton(
            url_row, text="+", width=38, height=38,
            fg_color=RED_NEON, hover_color="#cc0033",
            text_color="#ffffff", corner_radius=8,
            font=ctk.CTkFont(size=20, weight="bold"),
            command=self._add_site
        ).pack(side="left")

        self._nlp_result_label = ctk.CTkLabel(
            left, text="", text_color=TEXT_SEC,
            font=ctk.CTkFont(family="Courier New", size=10), anchor="w"
        )
        self._nlp_result_label.pack(fill="x", padx=14, pady=(0, 8))

        self._block_btn = ctk.CTkButton(
            left, text="▶  BLOCK NOW",
            fg_color=RED_NEON, hover_color="#cc0033",
            text_color="#ffffff", corner_radius=8, height=40,
            font=ctk.CTkFont(family="Courier New", size=12, weight="bold"),
            command=self._on_block
        )
        self._block_btn.pack(fill="x", padx=14, pady=(0, 8))

        self._block_timer_btn = ctk.CTkButton(
            left, text="◷  BLOCK WITH TIMER",
            fg_color=BTN_GHOST, hover_color=BG_ITEM_SEL,
            text_color=CYAN, corner_radius=8, height=40,
            border_width=1, border_color=CYAN_DIM,
            font=ctk.CTkFont(family="Courier New", size=12),
            command=self._on_block
        )
        self._block_timer_btn.pack(fill="x", padx=14, pady=(0, 12))

        self._field_label(left, "BLOCKED SITES")
        self._list_frame = ctk.CTkScrollableFrame(
            left, fg_color=BG_INPUT, corner_radius=8,
            border_width=1, border_color=BORDER,
            scrollbar_button_color=BORDER_BRIGHT,
            scrollbar_button_hover_color=ACCENT
        )
        self._list_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self._empty_label = ctk.CTkLabel(
            self._list_frame, text="No sites blocked",
            text_color=TEXT_MUT,
            font=ctk.CTkFont(family="Courier New", size=12)
        )
        self._empty_label.pack(pady=20)

        # ── RIGHT panel — outer frame holds border + header ───────────────
        right_outer = ctk.CTkFrame(panels, fg_color=BG_PANEL, corner_radius=12,
                                   border_width=1, border_color=BORDER_BRIGHT)
        right_outer.pack(side="left", fill="both", expand=True)

        self._panel_label(right_outer, "◈ SCHEDULE BLOCK", ORANGE_NEON)

        # Scrollable inner frame — all widgets go inside here
        right = ctk.CTkScrollableFrame(
            right_outer, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=BORDER_BRIGHT,
            scrollbar_button_hover_color=CYAN
        )
        right.pack(fill="both", expand=True)

        self._field_label(right, "TARGET URL")
        self._sched_url_entry = ctk.CTkEntry(
            right, placeholder_text="e.g. instagram.com",
            fg_color=BG_INPUT, border_color=BORDER_BRIGHT, border_width=1,
            text_color=TEXT_PRI, placeholder_text_color=TEXT_MUT,
            corner_radius=8, height=38,
            font=ctk.CTkFont(family="Courier New", size=12)
        )
        self._sched_url_entry.pack(fill="x", padx=14, pady=(0, 10))

        self._field_label(right, "TIMER DURATION (MINUTES)")
        self._timer_entry = ctk.CTkEntry(
            right, placeholder_text="leave empty for permanent",
            fg_color=BG_INPUT, border_color=BORDER_BRIGHT, border_width=1,
            text_color=TEXT_PRI, placeholder_text_color=TEXT_MUT,
            corner_radius=8, height=38,
            font=ctk.CTkFont(family="Courier New", size=12)
        )
        self._timer_entry.pack(fill="x", padx=14, pady=(0, 10))

        self._field_label(right, "START & END TIME")
        time_row = ctk.CTkFrame(right, fg_color="transparent")
        time_row.pack(fill="x", padx=14, pady=(0, 10))

        self._start_time = ctk.CTkEntry(
            time_row, placeholder_text="--:--",
            fg_color=BG_INPUT, border_color=BORDER_BRIGHT, border_width=1,
            text_color=TEXT_PRI, placeholder_text_color=TEXT_MUT,
            corner_radius=8, height=38,
            font=ctk.CTkFont(family="Courier New", size=12)
        )
        self._start_time.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._end_time = ctk.CTkEntry(
            time_row, placeholder_text="--:--",
            fg_color=BG_INPUT, border_color=BORDER_BRIGHT, border_width=1,
            text_color=TEXT_PRI, placeholder_text_color=TEXT_MUT,
            corner_radius=8, height=38,
            font=ctk.CTkFont(family="Courier New", size=12)
        )
        self._end_time.pack(side="left", fill="x", expand=True)

        self._field_label(right, "DAYS")
        days_row = ctk.CTkFrame(right, fg_color="transparent")
        days_row.pack(fill="x", padx=14, pady=(0, 10))

        self._day_vars = {}
        for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            var = ctk.BooleanVar()
            self._day_vars[day] = var
            ctk.CTkCheckBox(
                days_row, text=day, variable=var,
                fg_color=CYAN, hover_color=CYAN_DIM,
                text_color=TEXT_SEC, checkmark_color=BG_APP,
                font=ctk.CTkFont(family="Courier New", size=9),
                width=14, corner_radius=4
            ).pack(side="left", padx=2)

        self._field_label(right, "AUTO-UNBLOCK AFTER")
        self._schedule_var = ctk.StringVar(value="Never")
        sched_row = ctk.CTkFrame(right, fg_color=BG_INPUT, corner_radius=8,
                                 border_width=1, border_color=BORDER, height=44)
        sched_row.pack(fill="x", padx=14, pady=(0, 10))
        sched_row.pack_propagate(False)

        ctk.CTkLabel(
            sched_row, text="◷",
            text_color=CYAN, font=ctk.CTkFont(size=16)
        ).pack(side="left", padx=12)

        ctk.CTkOptionMenu(
            sched_row,
            values=["Never", "25 min (Pomodoro)", "1 hour", "2 hours", "4 hours"],
            variable=self._schedule_var,
            fg_color=BTN_GHOST, button_color=BORDER_BRIGHT,
            button_hover_color=CYAN_DIM,
            text_color=TEXT_PRI, dropdown_fg_color=BG_CARD,
            dropdown_hover_color=BG_ITEM_SEL, dropdown_text_color=TEXT_PRI,
            corner_radius=8, font=ctk.CTkFont(family="Courier New", size=11),
            width=180, height=30
        ).pack(side="right", padx=10)

        ctk.CTkButton(
            right, text="◈  SET SCHEDULE",
            fg_color=BTN_GHOST, hover_color=BG_ITEM_SEL,
            text_color=ORANGE_NEON, corner_radius=8, height=40,
            border_width=1, border_color=ORANGE_NEON,
            font=ctk.CTkFont(family="Courier New", size=12, weight="bold"),
            command=lambda: messagebox.showinfo("Schedule", "Schedule feature coming soon!")
        ).pack(fill="x", padx=14, pady=(0, 8))

        self._nlp_pill = ctk.CTkLabel(
            right, text="◈ NLP READY",
            fg_color=BG_APP, text_color=CYAN,
            corner_radius=6, font=ctk.CTkFont(family="Courier New", size=10),
            padx=10, pady=5
        )
        self._nlp_pill.pack(padx=14, pady=(0, 6), anchor="w")

        # ── Usage Stats button ─────────────────────────────────────────────
        ctk.CTkButton(
            right, text="📊  VIEW USAGE STATS",
            fg_color=BTN_GHOST, hover_color=BG_ITEM_SEL,
            text_color=PURPLE_NEON, corner_radius=8, height=38,
            border_width=1, border_color=PURPLE_NEON,
            font=ctk.CTkFont(family="Courier New", size=11, weight="bold"),
            command=self._open_stats
        ).pack(fill="x", padx=14, pady=(0, 10))

    def _build_footer(self, parent):
        footer = ctk.CTkFrame(parent, fg_color=BG_PANEL, corner_radius=0, height=36)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        row = ctk.CTkFrame(footer, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=16)

        ctk.CTkLabel(row, text="◉  FLASK SERVER ONLINE",
                     text_color=GREEN_NEON,
                     font=ctk.CTkFont(family="Courier New", size=9)
                     ).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(row, text="◉  MONGODB CONNECTED",
                     text_color=GREEN_NEON,
                     font=ctk.CTkFont(family="Courier New", size=9)
                     ).pack(side="left", padx=(0, 20))
        ctk.CTkLabel(row, text="◉  HOSTS FILE ACTIVE",
                     text_color=GREEN_NEON,
                     font=ctk.CTkFont(family="Courier New", size=9)
                     ).pack(side="left")

        ctk.CTkButton(
            row, text="⬡  UNBLOCK ALL",
            fg_color=BTN_GHOST, hover_color="#1a1f3a",
            text_color=TEXT_SEC, corner_radius=6, height=26,
            border_width=1, border_color=BORDER_BRIGHT,
            font=ctk.CTkFont(family="Courier New", size=10),
            command=self._on_unblock
        ).pack(side="right")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _panel_label(self, parent, text, color=CYAN):
        hdr = ctk.CTkFrame(parent, fg_color=BG_APP, corner_radius=0, height=36)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text=text, text_color=color,
            font=ctk.CTkFont(family="Courier New", size=11, weight="bold")
        ).pack(side="left", padx=14, pady=10)

    def _field_label(self, parent, text):
        ctk.CTkLabel(
            parent, text=text, text_color=TEXT_SEC,
            font=ctk.CTkFont(family="Courier New", size=9)
        ).pack(anchor="w", padx=14, pady=(8, 2))

    # ── PIN Management ────────────────────────────────────────────────────────

    def _manage_pin(self):
        pin_exists = load_pin() is not None
        if pin_exists:
            choice = messagebox.askquestion(
                "PIN Management",
                "A PIN is already set.\n\nYES → Change PIN\nNO  → Remove PIN"
            )
            if choice == "yes":
                self._set_new_pin()
            else:
                if self._verify_pin_dialog():
                    os.remove(PIN_FILE)
                    self._pin_btn.configure(
                        text="🔓 SET PIN",
                        text_color=TEXT_SEC, border_color=BORDER_BRIGHT
                    )
                    messagebox.showinfo("PIN Removed", "PIN lock has been removed.")
        else:
            self._set_new_pin()

    def _set_new_pin(self):
        dialog = PinDialog(self, title="Set New PIN",
                           prompt="Enter a new PIN (min 4 digits):", confirm=True)
        pin = dialog.get_result()
        if pin:
            save_pin(pin)
            self._pin_btn.configure(
                text="🔑 PIN SET",
                text_color=ORANGE_NEON, border_color=ORANGE_NEON
            )
            messagebox.showinfo("PIN Activated",
                                "🔒 PIN lock is now active!\n\nYou'll need this PIN to unblock sites.")

    def _verify_pin_dialog(self) -> bool:
        if load_pin() is None:
            return True
        dialog = PinDialog(self, title="PIN Required",
                           prompt="Enter your PIN to continue:")
        pin = dialog.get_result()
        if pin is None:
            return False
        if verify_pin(pin):
            return True
        messagebox.showerror("Wrong PIN", "❌ Incorrect PIN. Access denied.")
        return False

    # ── Stats ─────────────────────────────────────────────────────────────────

    def _open_stats(self):
        StatsWindow(self).focus()

    # ── Data ──────────────────────────────────────────────────────────────────

    def _load_sites(self):
        try:
            for url in get_all_sites():
                if url:
                    self._add_row(url)
        except Exception as e:
            print(f"[App] Could not load sites: {e}")

    def _add_site(self):
        url = self._url_entry.get().strip()
        if not url:
            return
        if url in self._site_rows:
            self._flash_entry_error()
            return

        self._nlp_pill.configure(text="◈ ANALYZING...", text_color=ORANGE_NEON)
        self.update()

        try:
            result       = analyze_website(url)
            category     = result["category"]
            confidence   = int(result["confidence"] * 100)
            should_block = result["should_block"]
            reason       = result["reason"]

            cat_color = CATEGORY_COLORS.get(category, TEXT_SEC)
            self._nlp_result_label.configure(
                text=f"◈ NLP: {category.upper()}  |  Confidence: {confidence}%  |  {reason}",
                text_color=cat_color
            )
            self._nlp_pill.configure(text=f"◈ {category.upper()}", text_color=cat_color)

            if should_block:
                if not messagebox.askyesno(
                    "⚠ Harmful Site Detected",
                    f"NLP: {category.upper()}\nConfidence: {confidence}%\n"
                    f"Reason: {reason}\n\nBlock {url}?"
                ):
                    self._nlp_result_label.configure(
                        text=f"⚠ Skipped: {url}", text_color=TEXT_SEC)
                    return

        except Exception as e:
            print(f"[NLP] Analysis failed: {e}")
            category, confidence = "unknown", 0

        try:
            add_site(url)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self._add_row(url, category=category, confidence=confidence)
        self._url_entry.delete(0, "end")

    def _add_row(self, url: str, category="unknown", confidence=0):
        if url in self._site_rows:
            return
        if self._empty_label.winfo_ismapped():
            self._empty_label.pack_forget()

        sep = None
        if self._site_rows:
            sep = ctk.CTkFrame(self._list_frame, fg_color=BORDER, height=1)
            sep.pack(fill="x")

        # ── CHANGED: pass on_unblock=self._unblock_site ───────────────────
        row = SiteRow(self._list_frame, url,
                      on_remove=self._remove_site,
                      on_unblock=self._unblock_site,
                      category=category, confidence=confidence)
        row._sep = sep
        row.pack(fill="x")
        self._site_rows[url] = row
        self._update_stats()

    def _remove_site(self, url: str):
        """Remove site from UI and MongoDB only (does NOT touch hosts file)."""
        if url not in self._site_rows:
            return
        try:
            from config.db import get_db
            db = get_db()
            db["blocked_sites"].delete_one({"site": url})
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        row = self._site_rows.pop(url)
        if row._sep:
            row._sep.destroy()
        row.destroy()

        if not self._site_rows:
            self._empty_label.pack(pady=20)

        self._nlp_result_label.configure(text="")
        self._update_stats()

    # ── NEW: Unblock a single site from hosts file ────────────────────────────
    def _unblock_site(self, url: str):
        """Unblock a single site: removes it from the hosts file + DB + UI."""
        if not self._verify_pin_dialog():
            return

        # Determine hosts file path (cross-platform)
        if os.name == "nt":
            hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        else:
            hosts_path = "/etc/hosts"

        try:
            with open(hosts_path, "r") as f:
                lines = f.readlines()

            # Keep only lines that do NOT contain this url
            new_lines = [
                line for line in lines
                if url not in line
            ]

            with open(hosts_path, "w") as f:
                f.writelines(new_lines)

        except PermissionError:
            messagebox.showerror(
                "Admin Required",
                "Run the app as Administrator (Windows) or with sudo (Mac/Linux)\n"
                "to modify the hosts file."
            )
            return
        except Exception as e:
            messagebox.showerror("Hosts File Error", str(e))
            return

        # Update counters + stats
        self._unblocked_today += 1
        record_unblock_event()

        # Remove from UI and MongoDB
        self._remove_site(url)

        messagebox.showinfo("Unblocked", f"✅ {url} has been unblocked successfully!")

    # ─────────────────────────────────────────────────────────────────────────

    def _update_stats(self):
        n = len(self._site_rows)
        self._stat_blocked.set_value(n)
        active = 1 if (self._blocking_active and self._schedule_var.get() != "Never") else 0
        self._stat_timers.set_value(active)
        self._stat_unblocked.set_value(self._unblocked_today)

    def _flash_entry_error(self):
        self._url_entry.configure(border_color=RED_NEON)
        self.after(600, lambda: self._url_entry.configure(border_color=BORDER_BRIGHT))

    # ── Block / Unblock All ───────────────────────────────────────────────────

    def _on_block(self):
        if not self._site_rows:
            messagebox.showinfo("No sites", "Add at least one site first.")
            return
        try:
            block_sites()
        except PermissionError:
            messagebox.showerror("Admin Required",
                                 "Run as Administrator to modify the hosts file.")
            return
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self._blocking_active = True
        record_block_event()
        self._block_btn.configure(
            text="◉  BLOCKING ACTIVE",
            fg_color=GREEN_DIM, text_color=GREEN_NEON, hover_color=GREEN_DIM
        )
        self._status_pill.configure(
            text="◉  BLOCKING ACTIVE",
            fg_color=GREEN_DIM, text_color=GREEN_NEON
        )
        self._update_stats()
        self._schedule_auto_unblock()

    def _on_unblock(self):
        if not self._blocking_active:
            messagebox.showinfo("Not Blocking", "Sites are not currently blocked.")
            return

        if not self._verify_pin_dialog():
            return

        try:
            unblock_sites()
        except PermissionError:
            messagebox.showerror("Admin Required",
                                 "Run as Administrator to modify the hosts file.")
            return
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

        self._blocking_active  = False
        self._unblocked_today += 1
        record_unblock_event()
        self._block_btn.configure(
            text="▶  BLOCK NOW",
            fg_color=RED_NEON, text_color="#ffffff", hover_color="#cc0033"
        )
        self._status_pill.configure(
            text="◉  BLOCKING INACTIVE",
            fg_color=BG_APP, text_color=TEXT_SEC
        )
        self._update_stats()

    def _schedule_auto_unblock(self):
        mapping = {
            "25 min (Pomodoro)": 25 * 60 * 1000,
            "1 hour":            60 * 60 * 1000,
            "2 hours":       2 * 60 * 60 * 1000,
            "4 hours":       4 * 60 * 60 * 1000,
        }
        ms = mapping.get(self._schedule_var.get())
        if ms:
            self._stat_timers.set_value(1)
            self.after(ms, self._on_unblock)


# ── Entry point ────────────────────────────────────────────────────────────────
def launch():
    app = WebsiteBlockerApp()
    app.mainloop()


if __name__ == "__main__":
    launch()


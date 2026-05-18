#!/usr/bin/env python3
"""
Pinpoint - Simple screen magnifier scope overlay for Windows.
Uses the native Windows Magnification API (magnification.dll).
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import ctypes
import traceback
import sys

# Windows DPI awareness
ctypes.windll.user32.SetProcessDPIAware()

# Config defaults
DEFAULT_TOGGLE_KEY = 0x02
DEFAULT_ZOOM = 2.0
DEFAULT_SIZE = 300
DEFAULT_CROSSHAIR = True
DEFAULT_CLICK_TOGGLE = False
DEFAULT_MODE = "Follow Mouse"
MODES = ["Follow Mouse", "Center Screen"]
UPDATE_INTERVAL = 16

# Key map for UI dropdown
KEY_MAP = {
    "Right Mouse": 0x02,
    "Left Mouse": 0x01,
    "Middle Mouse": 0x04,
    "Mouse4 / X1": 0x05,
    "Mouse5 / X2": 0x06,
    "Left Shift": 0xA0,
    "Left Ctrl": 0xA2,
    "Left Alt": 0xA4,
    "F": 0x46,
    "Q": 0x51,
    "E": 0x45,
    "R": 0x52,
    "C": 0x43,
    "V": 0x56,
    "Space": 0x20,
    "1": 0x31,
    "2": 0x32,
    "3": 0x33,
    "4": 0x34,
    "5": 0x35,
}
KEY_NAMES = list(KEY_MAP.keys())
INV_KEY_MAP = {v: k for k, v in KEY_MAP.items()}

# Windows API DLLs
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# Window styles
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000
WS_CLIPCHILDREN = 0x02000000
MS_SHOWMAGNIFIEDCURSOR = 0x0001
LWA_ALPHA = 0x00000002
SWP_NOACTIVATE = 0x0010
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_FRAMECHANGED = 0x0020
SWP_NOZORDER = 0x0004

WC_MAGNIFIER = "Magnifier"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line)
    try:
        with open("pinpoint_debug.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Structs
# ---------------------------------------------------------------------------
class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class MAGTRANSFORM(ctypes.Structure):
    _fields_ = [("v", (ctypes.c_float * 3) * 3)]


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


# ---------------------------------------------------------------------------
# Load Magnification API
# ---------------------------------------------------------------------------
MAG_AVAILABLE = False
try:
    mag = ctypes.windll.Magnification
    MAG_AVAILABLE = True
except OSError:
    log("Magnification.dll not found on this system!")

if MAG_AVAILABLE:
    mag.MagInitialize.restype = ctypes.c_bool
    mag.MagUninitialize.restype = ctypes.c_bool
    mag.MagSetWindowTransform.argtypes = [ctypes.c_void_p, ctypes.POINTER(MAGTRANSFORM)]
    mag.MagSetWindowTransform.restype = ctypes.c_bool
    mag.MagSetWindowSource.argtypes = [ctypes.c_void_p, ctypes.POINTER(RECT)]
    mag.MagSetWindowSource.restype = ctypes.c_bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_async_key_state(vkey):
    return user32.GetAsyncKeyState(vkey) & 0x8000 != 0


def get_screen_size():
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def get_cursor_pos():
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def make_transform(zoom):
    t = MAGTRANSFORM()
    t.v[0][0] = zoom
    t.v[1][1] = zoom
    t.v[2][2] = 1.0
    return t


# ---------------------------------------------------------------------------
# Main App
# ---------------------------------------------------------------------------
class ScopeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pinpoint")
        self.root.geometry("440x460")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")

        # Settings state
        self.zoom = DEFAULT_ZOOM
        self.scope_size = DEFAULT_SIZE
        self.toggle_key = DEFAULT_TOGGLE_KEY
        self.show_crosshair = DEFAULT_CROSSHAIR
        self.click_to_toggle = DEFAULT_CLICK_TOGGLE
        self.mode = DEFAULT_MODE

        # Runtime state
        self.scope_active = False
        self.scope_hwnd = None
        self.mag_hwnd = None
        self.overlay = None
        self.overlay_canvas = None
        self.crosshair_items = []
        self.running = True
        self._scope_lock = threading.Lock()

        if not MAG_AVAILABLE:
            self.root.title("Pinpoint - ERROR: Magnification API unavailable")

        self.build_ui()

        if MAG_AVAILABLE:
            ok = mag.MagInitialize()
            log(f"MagInitialize() = {ok}")

        self.hk_thread = threading.Thread(target=self.hotkey_loop, daemon=True)
        self.hk_thread.start()
        log("Pinpoint started")
        log(f"Screen: {get_screen_size()}")

    # -----------------------------------------------------------------------
    # UI
    # -----------------------------------------------------------------------
    def build_ui(self):
        tk.Label(self.root, text="Pinpoint", font=("Segoe UI", 18, "bold"),
                 fg="#00ff88", bg="#1e1e1e").pack(pady=(12, 4))

        msg = "Magnification API ready" if MAG_AVAILABLE else "ERROR: Windows Magnification API not available"
        fg = "#888888" if MAG_AVAILABLE else "#ff4444"
        tk.Label(self.root, text=msg, font=("Segoe UI", 9), fg=fg, bg="#1e1e1e").pack(pady=(0, 8))

        # --- Sliders ---
        frame = tk.Frame(self.root, bg="#1e1e1e")
        frame.pack(pady=4)

        tk.Label(frame, text="Zoom:", fg="#ffffff", bg="#1e1e1e", font=("Segoe UI", 10)).grid(row=0, column=0, padx=5)
        self.zoom_var = tk.DoubleVar(value=self.zoom)
        zoom_scale = ttk.Scale(frame, from_=1.0, to=5.0, orient=tk.HORIZONTAL,
                               variable=self.zoom_var, length=150)
        zoom_scale.grid(row=0, column=1, padx=5)
        self.zoom_label = tk.Label(frame, text=f"{self.zoom:.1f}x", fg="#00ff88", bg="#1e1e1e", font=("Segoe UI", 10))
        self.zoom_label.grid(row=0, column=2, padx=5)
        zoom_scale.config(command=self.on_zoom_change)

        tk.Label(frame, text="Size:", fg="#ffffff", bg="#1e1e1e", font=("Segoe UI", 10)).grid(row=1, column=0, padx=5, pady=8)
        self.size_var = tk.IntVar(value=self.scope_size)
        size_scale = ttk.Scale(frame, from_=100, to=600, orient=tk.HORIZONTAL,
                               variable=self.size_var, length=150)
        size_scale.grid(row=1, column=1, padx=5, pady=8)
        self.size_label = tk.Label(frame, text=f"{self.scope_size}px", fg="#00ff88", bg="#1e1e1e", font=("Segoe UI", 10))
        self.size_label.grid(row=1, column=2, padx=5, pady=8)
        size_scale.config(command=self.on_size_change)

        # --- Settings ---
        settings = tk.Frame(self.root, bg="#1e1e1e")
        settings.pack(pady=4)

        # Key dropdown
        tk.Label(settings, text="Trigger Key:", fg="#ffffff", bg="#1e1e1e", font=("Segoe UI", 10)).grid(row=0, column=0, padx=5, pady=4, sticky="w")
        self.key_var = tk.StringVar(value=INV_KEY_MAP.get(self.toggle_key, "Right Mouse"))
        key_combo = ttk.Combobox(settings, textvariable=self.key_var, values=KEY_NAMES,
                                 state="readonly", width=14)
        key_combo.grid(row=0, column=1, padx=5, pady=4)
        key_combo.bind("<<ComboboxSelected>>", self.on_key_change)

        # Mode dropdown
        tk.Label(settings, text="Zoom Mode:", fg="#ffffff", bg="#1e1e1e", font=("Segoe UI", 10)).grid(row=1, column=0, padx=5, pady=4, sticky="w")
        self.mode_var = tk.StringVar(value=self.mode)
        mode_combo = ttk.Combobox(settings, textvariable=self.mode_var, values=MODES,
                                  state="readonly", width=14)
        mode_combo.grid(row=1, column=1, padx=5, pady=4)
        mode_combo.bind("<<ComboboxSelected>>", self.on_mode_change)

        # Toggle mode checkbox
        self.toggle_var = tk.BooleanVar(value=self.click_to_toggle)
        tk.Checkbutton(settings, text="Click to toggle (vs hold)", variable=self.toggle_var,
                       bg="#1e1e1e", fg="#ffffff", selectcolor="#1e1e1e",
                       activebackground="#1e1e1e", activeforeground="#ffffff",
                       font=("Segoe UI", 10), command=self.on_click_toggle_change).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        # Crosshair checkbox
        self.crosshair_var = tk.BooleanVar(value=self.show_crosshair)
        tk.Checkbutton(settings, text="Show crosshair & border", variable=self.crosshair_var,
                       bg="#1e1e1e", fg="#ffffff", selectcolor="#1e1e1e",
                       activebackground="#1e1e1e", activeforeground="#ffffff",
                       font=("Segoe UI", 10), command=self.on_crosshair_change).grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        # Reset button
        tk.Button(settings, text="Reset Defaults", command=self.reset_defaults,
                  bg="#555555", fg="#ffffff", font=("Segoe UI", 9),
                  width=14, relief=tk.FLAT, cursor="hand2").grid(row=4, column=0, columnspan=2, pady=6)

        # --- Action buttons ---
        btn_frame = tk.Frame(self.root, bg="#1e1e1e")
        btn_frame.pack(pady=4)
        tk.Button(btn_frame, text="Test Scope (3s)", command=self.test_scope,
                  bg="#00aa88", fg="#ffffff", font=("Segoe UI", 10, "bold"),
                  width=16, relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Force Show Scope", command=self.manual_show_scope,
                  bg="#0088cc", fg="#ffffff", font=("Segoe UI", 10, "bold"),
                  width=16, relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Exit", command=self.exit_app,
                  bg="#ff4444", fg="#ffffff", font=("Segoe UI", 10, "bold"),
                  width=10, relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=5)

        # --- Status ---
        self.debug_label = tk.Label(self.root, text="Debug: Ready", font=("Segoe UI", 9),
                                     fg="#888888", bg="#1e1e1e")
        self.debug_label.pack(pady=2)

        self.status_label = tk.Label(self.root, text="Status: Idle", font=("Segoe UI", 10, "bold"),
                                     fg="#ffaa00", bg="#1e1e1e")
        self.status_label.pack(pady=4)

    # -----------------------------------------------------------------------
    # Settings callbacks
    # -----------------------------------------------------------------------
    def on_key_change(self, event=None):
        name = self.key_var.get()
        new_key = KEY_MAP.get(name, DEFAULT_TOGGLE_KEY)
        if new_key != self.toggle_key:
            self.toggle_key = new_key
            log(f"Key rebound to {name} (0x{new_key:02X})")

    def on_mode_change(self, event=None):
        self.mode = self.mode_var.get()
        log(f"Zoom mode changed to {self.mode}")

    def on_click_toggle_change(self):
        self.click_to_toggle = self.toggle_var.get()
        mode = "click-to-toggle" if self.click_to_toggle else "hold"
        log(f"Trigger mode changed to {mode}")

    def on_crosshair_change(self):
        self.show_crosshair = self.crosshair_var.get()
        self.refresh_crosshair()
        log(f"Crosshair set to {self.show_crosshair}")

    def reset_defaults(self):
        self.zoom_var.set(DEFAULT_ZOOM)
        self.on_zoom_change(DEFAULT_ZOOM)
        self.size_var.set(DEFAULT_SIZE)
        self.on_size_change(DEFAULT_SIZE)
        self.key_var.set(INV_KEY_MAP[DEFAULT_TOGGLE_KEY])
        self.toggle_key = DEFAULT_TOGGLE_KEY
        self.mode_var.set(DEFAULT_MODE)
        self.mode = DEFAULT_MODE
        self.toggle_var.set(DEFAULT_CLICK_TOGGLE)
        self.click_to_toggle = DEFAULT_CLICK_TOGGLE
        self.crosshair_var.set(DEFAULT_CROSSHAIR)
        self.show_crosshair = DEFAULT_CROSSHAIR
        self.refresh_crosshair()
        log("Settings reset to defaults")

    # -----------------------------------------------------------------------
    # Sliders
    # -----------------------------------------------------------------------
    def on_zoom_change(self, val):
        self.zoom = float(val)
        self.zoom_label.config(text=f"{self.zoom:.1f}x")
        if self.mag_hwnd and MAG_AVAILABLE:
            t = make_transform(self.zoom)
            mag.MagSetWindowTransform(self.mag_hwnd, ctypes.byref(t))
            log(f"Zoom updated to {self.zoom:.1f}x")

    def on_size_change(self, val):
        self.scope_size = int(float(val))
        self.size_label.config(text=f"{self.scope_size}px")
        if self.scope_hwnd:
            sw, sh = get_screen_size()
            x = (sw - self.scope_size) // 2
            y = (sh - self.scope_size) // 2
            user32.SetWindowPos(
                self.scope_hwnd, 0, x, y, self.scope_size, self.scope_size,
                SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED
            )
            if self.mag_hwnd:
                user32.SetWindowPos(
                    self.mag_hwnd, 0, 0, 0, self.scope_size, self.scope_size,
                    SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED
                )
            hrgn = gdi32.CreateEllipticRgn(0, 0, self.scope_size, self.scope_size)
            user32.SetWindowRgn(self.scope_hwnd, hrgn, True)
            if self.overlay:
                self.overlay.geometry(f"{self.scope_size}x{self.scope_size}+{x}+{y}")

    def test_scope(self):
        self.manual_show_scope()
        self.root.after(3000, self.hide_scope)

    def manual_show_scope(self):
        if not self.scope_active:
            self.show_scope()

    # -----------------------------------------------------------------------
    # Scope creation
    # -----------------------------------------------------------------------
    def create_scope_window(self):
        sw, sh = get_screen_size()
        x = (sw - self.scope_size) // 2
        y = (sh - self.scope_size) // 2

        log(f"Creating scope host at {x},{y} size={self.scope_size}")

        hwnd = user32.CreateWindowExW(
            WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE,
            "Static",
            "ScopeX",
            WS_POPUP | WS_CLIPCHILDREN | WS_VISIBLE,
            x, y, self.scope_size, self.scope_size,
            None, None, None, None
        )
        if not hwnd:
            log("CreateWindowExW failed for host")
            return None, None

        user32.SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)
        hrgn = gdi32.CreateEllipticRgn(0, 0, self.scope_size, self.scope_size)
        user32.SetWindowRgn(hwnd, hrgn, True)
        log(f"Host created: hwnd={hwnd}")

        mag_hwnd = None
        if MAG_AVAILABLE:
            mag_hwnd = user32.CreateWindowExW(
                0, WC_MAGNIFIER, None,
                WS_CHILD | WS_VISIBLE | MS_SHOWMAGNIFIEDCURSOR,
                0, 0, self.scope_size, self.scope_size,
                hwnd, None, None, None
            )
            if not mag_hwnd:
                log("Magnifier child creation failed")
                return hwnd, None
            log(f"Magnifier created: hwnd={mag_hwnd}")
            t = make_transform(self.zoom)
            ok = mag.MagSetWindowTransform(mag_hwnd, ctypes.byref(t))
            log(f"MagSetWindowTransform = {ok}")

        return hwnd, mag_hwnd

    def create_overlay(self, x, y):
        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.attributes("-topmost", True)
        overlay.attributes("-transparentcolor", "#000001")
        overlay.configure(bg="#000001")
        overlay.geometry(f"{self.scope_size}x{self.scope_size}+{x}+{y}")
        overlay.deiconify()
        overlay.lift()
        overlay.update_idletasks()

        canvas = tk.Canvas(overlay, width=self.scope_size, height=self.scope_size,
                           highlightthickness=0, bg="#000001")
        canvas.pack(fill=tk.BOTH, expand=True)

        self.overlay_canvas = canvas
        self.crosshair_items = []

        r = self.scope_size // 2
        self.crosshair_items.append(
            canvas.create_oval(2, 2, self.scope_size - 2, self.scope_size - 2, outline="#00ff88", width=3))
        self.crosshair_items.append(
            canvas.create_line(r, 10, r, self.scope_size - 10, fill="#00ff88", width=1))
        self.crosshair_items.append(
            canvas.create_line(10, r, self.scope_size - 10, r, fill="#00ff88", width=1))
        self.crosshair_items.append(
            canvas.create_oval(r - 4, r - 4, r + 4, r + 4, outline="#00ff88", width=1))

        self.refresh_crosshair()
        log("Overlay created")
        return overlay

    def refresh_crosshair(self):
        state = tk.NORMAL if self.show_crosshair else tk.HIDDEN
        for item in self.crosshair_items:
            if self.overlay_canvas:
                self.overlay_canvas.itemconfig(item, state=state)

    # -----------------------------------------------------------------------
    # Update loop
    # -----------------------------------------------------------------------
    def update_source(self):
        if not self.scope_active or not self.mag_hwnd:
            return

        try:
            capture_w = max(1, int(self.scope_size / self.zoom))
            capture_h = max(1, int(self.scope_size / self.zoom))
            sw, sh = get_screen_size()

            if self.mode == "Follow Mouse":
                mx, my = get_cursor_pos()
                x1 = mx - capture_w // 2
                y1 = my - capture_h // 2
            else:  # Center Screen
                x1 = (sw - capture_w) // 2
                y1 = (sh - capture_h) // 2

            x2 = x1 + capture_w
            y2 = y1 + capture_h

            x1 = max(0, x1); y1 = max(0, y1)
            x2 = min(sw, x2); y2 = min(sh, y2)

            rect = RECT()
            rect.left = x1; rect.top = y1; rect.right = x2; rect.bottom = y2

            ok = mag.MagSetWindowSource(self.mag_hwnd, ctypes.byref(rect))
            if not ok:
                self.debug_label.config(text="Debug: MagSetWindowSource failed")
                log("MagSetWindowSource failed")
            else:
                self.debug_label.config(text=f"Debug: {self.mode} | source {x1},{y1} {capture_w}x{capture_h}")

            user32.InvalidateRect(self.mag_hwnd, None, True)

            if self.overlay:
                try:
                    hwnd_overlay = self.overlay.winfo_id()
                    user32.SetWindowPos(hwnd_overlay, -1, 0, 0, 0, 0,
                                        SWP_NOACTIVATE | SWP_NOMOVE | SWP_NOSIZE)
                except Exception:
                    self.overlay.lift()

            if self.scope_hwnd:
                user32.SetWindowPos(
                    self.scope_hwnd, 0, 0, 0, 0, 0,
                    SWP_NOACTIVATE | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER
                )

        except Exception as e:
            self.debug_label.config(text=f"Debug: update error {e}")
            log(f"Update source error: {e}")

        if self.scope_active:
            self.root.after(UPDATE_INTERVAL, self.update_source)

    # -----------------------------------------------------------------------
    # Show / hide
    # -----------------------------------------------------------------------
    def show_scope(self):
        with self._scope_lock:
            if self.scope_active or self.scope_hwnd is not None:
                return

            try:
                self.scope_hwnd, self.mag_hwnd = self.create_scope_window()
            except Exception as e:
                log(f"Failed to create scope: {e}\n{traceback.format_exc()}")
                return

            if not self.scope_hwnd:
                return

            sw, sh = get_screen_size()
            x = (sw - self.scope_size) // 2
            y = (sh - self.scope_size) // 2
            self.overlay = self.create_overlay(x, y)

            self.scope_active = True
            self.status_label.config(text="Status: Active", fg="#00ff88")
            log("Scope shown")
            self.update_source()

    def hide_scope(self):
        with self._scope_lock:
            self.scope_active = False
            self.status_label.config(text="Status: Idle", fg="#ffaa00")

            if self.overlay:
                try:
                    self.overlay.destroy()
                except Exception:
                    pass
                self.overlay = None
                self.overlay_canvas = None
                self.crosshair_items.clear()

            if self.mag_hwnd:
                try:
                    user32.DestroyWindow(self.mag_hwnd)
                except Exception as e:
                    log(f"DestroyWindow(mag) error: {e}")
                self.mag_hwnd = None

            if self.scope_hwnd:
                try:
                    user32.DestroyWindow(self.scope_hwnd)
                    log("Scope destroyed")
                except Exception as e:
                    log(f"DestroyWindow(host) error: {e}")
                self.scope_hwnd = None

    # -----------------------------------------------------------------------
    # Hotkey
    # -----------------------------------------------------------------------
    def hotkey_loop(self):
        log("Hotkey thread started")
        last_state = False
        toggled_on = False
        while self.running:
            try:
                pressed = get_async_key_state(self.toggle_key)

                if self.click_to_toggle:
                    # Edge-triggered toggle
                    if pressed and not last_state:
                        if self.scope_active:
                            self.root.after(0, self.hide_scope)
                        else:
                            self.root.after(0, self.show_scope)
                else:
                    # Hold mode
                    if pressed and not last_state and not self.scope_active:
                        self.root.after(0, self.show_scope)
                    elif not pressed and last_state and self.scope_active:
                        self.root.after(0, self.hide_scope)

                last_state = pressed
            except Exception as e:
                log(f"Hotkey error: {e}")
            time.sleep(0.01)
        log("Hotkey thread exited")

    # -----------------------------------------------------------------------
    # Exit
    # -----------------------------------------------------------------------
    def exit_app(self):
        log("Exiting...")
        self.running = False
        self.hide_scope()
        if MAG_AVAILABLE:
            mag.MagUninitialize()
            log("MagUninitialize() called")
        self.root.destroy()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    log("=" * 40)
    log("Pinpoint starting up")
    log(f"Python: {sys.version}")
    log(f"Screen: {get_screen_size()}")
    log(f"Magnification API available: {MAG_AVAILABLE}")
    root = tk.Tk()
    app = ScopeApp(root)
    root.protocol("WM_DELETE_WINDOW", app.exit_app)
    root.mainloop()
    log("Pinpoint exited")


if __name__ == "__main__":
    main()

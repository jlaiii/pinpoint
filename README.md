# Pinpoint

A lightweight, customizable screen magnifier overlay for Windows.

## About

Pinpoint is a simple yet powerful Windows utility that creates a circular magnified scope overlay on your screen. Unlike the built-in Windows Magnifier, it gives you instant toggle control, cursor tracking, and full customization — all without slowing down your system.

## What is Pinpoint?

- **Instant toggle** — hold a key (or click to toggle) to show/hide the scope
- **Two zoom modes** — follow your mouse cursor or lock to center-screen
- **Multi-monitor support** — pick which monitor to magnify
- **Fully customizable** — change zoom, size, trigger key, refresh rate, crosshair, and behavior
- **Zero screen capture lag** — uses the native Windows Magnification API for smooth GPU-accelerated performance
- **Click-through** — the overlay doesn't block your mouse from interacting with games or apps underneath
- **Persistent settings** — every change auto-saves to a JSON file so your preferences stick

## Use Cases

- **Gaming** — zoom in on distant targets, read small UI text, or inspect fine details
- **Design & Editing** — precise pixel-level work without straining your eyes
- **Accessibility** — quick magnification wherever your cursor goes
- **Streaming** — show zoomed-in highlights to your audience

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer

## Installation

1. Clone or download this repository
2. Install the single dependency:
   ```bash
   pip install Pillow
   ```
3. Run Pinpoint:
   ```bash
   python pinpoint.py
   ```
   Or double-click `run.bat`

## Controls

| Action | Default |
|--------|---------|
| Show scope | Hold **Right Mouse Button** |
| Zoom | 2.0x (adjustable 1x-5x) |
| Scope size | 300px (adjustable 100-600px) |

All controls can be changed from the settings panel.

## Settings

| Setting | Description |
|---------|-------------|
| **Zoom** | 1.0x to 5.0x magnification |
| **Size** | Scope diameter from 100px to 600px |
| **Zoom Mode** | Follow Mouse (tracks cursor) or Center Screen (locked to monitor center) |
| **Target Monitor** | Choose which monitor to magnify (multi-monitor setups) |
| **Trigger Key** | Right Mouse, Left Mouse, Middle Mouse, Mouse4/5, Shift, Ctrl, Alt, F, Q, E, R, C, V, Space, 1-5 |
| **Click to toggle** | Click once to open, click again to close (instead of hold) |
| **Refresh Rate** | 144 FPS, 120 FPS, 60 FPS, or 30 FPS — pick the smoothness you want |
| **Crosshair & border** | Toggle the green circle and crosshair lines on or off |
| **Reset Defaults** | One-click restore to factory settings |

Changes take effect immediately and auto-save — no restart needed.

## Settings Persistence

Pinpoint auto-saves every change to `settings.json` in the same folder. The next time you launch the app, your zoom, size, key bindings, mode, monitor, refresh rate, and crosshair preference are all restored automatically. Click **Reset Defaults** to clear the file and start fresh.

## How It Works

Pinpoint uses the **Windows Magnification API** (`magnification.dll`), the same low-level API that powers the built-in Windows Magnifier. This means:

- No slow screen capture / screenshot loops
- Native GPU-accelerated magnification
- Works with games, browsers, and any application

## Troubleshooting

If the scope appears but shows a black or white screen, the Windows Magnification API may not be available on your system. Check `pinpoint_debug.log` in the same folder for details.

## License

MIT License — free to use, modify, and share.

---

**Website:** [https://jlaiii.github.io/pinpoint](https://jlaiii.github.io/pinpoint)  
**Repo:** [https://github.com/jlaiii/pinpoint](https://github.com/jlaiii/pinpoint)

# Pinpoint

A lightweight, customizable screen magnifier overlay for Windows.

## About

Pinpoint is a simple yet powerful Windows utility that creates a circular magnified scope overlay on your screen. Unlike the built-in Windows Magnifier, it gives you instant toggle control, cursor tracking, and full customization — all without slowing down your system.

## What is Pinpoint?

- **Instant toggle** — hold a key (or click to toggle) to show/hide the scope
- **Follows your cursor** — the magnified view tracks your mouse in real time
- **Fully customizable** — change zoom level, scope size, trigger key, crosshair, and behavior
- **Zero screen capture lag** — uses the native Windows Magnification API for smooth performance
- **Click-through** — the overlay doesn't block your mouse from interacting with games or apps underneath

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
| Zoom | 2.0x (adjustable) |
| Scope size | 300px (adjustable) |

All controls can be changed from the settings panel.

## Settings

| Setting | Description |
|---------|-------------|
| **Zoom** | 1.0x to 5.0x magnification |
| **Size** | Scope diameter from 100px to 600px |
| **Trigger Key** | Right Mouse, Left Mouse, Middle Mouse, Mouse4/5, Shift, Ctrl, Alt, F, Q, E, R, C, V, Space, 1-5 |
| **Click to toggle** | Click once to open, click again to close (instead of hold) |
| **Crosshair & border** | Toggle the green circle and crosshair lines on or off |

Changes take effect immediately — no restart needed.

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

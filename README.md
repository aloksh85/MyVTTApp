# NeuroType

A premium, fully offline, privacy-first Voice-to-Text daemon for macOS. Speak naturally and your words are transcribed by an on-device AI model and injected directly at your cursor — no cloud, no clipboard, no data leaves your machine.

## Features

- **100% Offline & Private**: All transcriptions run locally via `mlx-whisper` (Apple Silicon) or `faster-whisper` (Intel/Linux). No network requests, no telemetry.
- **Native macOS Daemon**: Compiles into a signed `.app` bundle that runs invisibly in the background with a Menu Bar status indicator (⚫🔴🟠).
- **Zero Focus Stealing**: Uses a native `QSystemTrayIcon` to avoid macOS Window Manager conflicts. Your cursor never moves from the target app.
- **Direct Keyboard Injection**: Bypasses the system clipboard entirely using `pynput`, protecting sensitive dictated content from clipboard managers.
- **Authenticated Socket API**: The daemon listens on `localhost:9999` secured by a per-session cryptographic token (`secrets.token_hex`). Only your user account can trigger the microphone.
- **Pinned AI Model**: The HuggingFace Whisper model revision is SHA-1 pinned to prevent supply chain attacks.

## Quick Start

### 1. Install Dependencies
```bash
cd /path/to/MyVTTApp
./install.sh
```

### 2. Build the Native App
```bash
source venv/bin/activate
./build.sh
```
This compiles two `.app` bundles into the `dist/` folder:
- **`NeuroType.app`** — The background AI transcription daemon.
- **`StartDictation.app`** — A lightweight trigger client.

### 3. Launch
```bash
open dist/NeuroType.app
```
Or simply double-click `NeuroType.app` in Finder. A small **black dot (⚫)** will appear in your Mac Menu Bar (top-right, near WiFi/Battery).

### 4. Dictate
1. Focus on any app (Notion, Safari, Messages, etc.).
2. Trigger your macOS Shortcut (or run `python3 client.py toggle` from the terminal).
3. The dot turns **red (🔴)** — speak naturally.
4. Trigger the shortcut again to stop.
5. The dot turns **orange (🟠)** while the AI processes, then your text appears at the cursor. The dot returns to **black (⚫)**.

### 5. Quit
Right-click the dot in the Menu Bar → **"Quit NeuroType"**.

## Project Structure

| File | Purpose |
|---|---|
| `app.py` | Main daemon entry point (PyQt6 event loop, socket server, transcription orchestration) |
| `client.py` | Lightweight CLI to send authenticated `toggle` commands to the daemon |
| `build.sh` | PyInstaller compilation script for native `.app` bundles |
| `core/audio.py` | In-memory microphone recording via `sounddevice` |
| `core/transcribe.py` | MLX Whisper / faster-whisper inference engine (SHA-1 pinned) |
| `integration/clipboard.py` | Direct keyboard injection via `pynput` (no clipboard) |
| `ui/widget.py` | Native `QSystemTrayIcon` Menu Bar status indicator |

## Security

All identified vulnerabilities have been resolved. See the full [Security Analysis](security_analysis.md) for details.

| Risk | Status |
|---|---|
| Clipboard data leakage | ✅ Resolved (direct `pynput` injection) |
| Temp file exposure | ✅ Resolved (in-memory `numpy` arrays) |
| Supply chain tampering | ✅ Resolved (SHA-1 model pinning + frozen deps) |
| Permission spoofing | ✅ Resolved (signed `.app` bundle) |
| Memory overflow | ✅ Resolved (queue size cap) |
| Unauthenticated socket | ✅ Resolved (per-session token auth) |

## Requirements

- macOS with Apple Silicon (M1/M2/M3/M4) for `mlx-whisper`
- Python 3.11+
- Microphone permission granted to the `.app` bundle

# NeuroType: Codebase Architecture & Design Decisions

This document breaks down the entire codebase of the NeuroType Voice-to-Text application. It explains what each module does and, more importantly, **why** specific engineering decisions were made during development to navigate severe macOS security restrictions and performance bottlenecks.

---

## 1. The Entry Points (`app.py` & `client.py`)

### `app.py` (The Background Daemon)
**What it does:** This is the main engine. It initializes the UI (System Tray), loads the AI model into memory, and spins up a background `socketserver.TCPServer` listening on `localhost:9999` for commands.
**Why it was written this way:**
* **Socket Server over Global Hotkeys:** Originally, the app used `pynput` to listen for a global `Cmd+Shift+R` hotkey. However, Python global keyboard hooks on macOS require deep Accessibility permissions, trigger thread-locking deadlocks when combined with UI frameworks like PyQt, and pose theoretical security risks (keylogging). 
* **The Fix:** By moving to a Socket-Daemon architecture, `app.py` does zero keyboard listening. It just waits passively for a network ping. This offloads the hotkey detection entirely to the native macOS operating system (via Apple Shortcuts).

### `client.py` (The Trigger Utility)
**What it does:** A tiny, 10-line script that connects to `localhost:9999` and sends the string `"toggle"`.
**Why it was written this way:**
* **Focus Stealing Prevention:** Connecting an Apple Shortcut directly to a massive Python application often causes macOS to instantly shift window focus away from the app you are trying to type into. By having the shortcut run this tiny, lightning-fast `client.py` ping, the OS window manager never realizes an external script was executed, preserving the user's focus on their current editor.

---

## 2. Core Processing (`core/audio.py` & `core/transcribe.py`)

### `core/audio.py` (Memory-Safe Recording)
**What it does:** Uses `sounddevice` and `soundfile` to capture microphone input on a background thread and store it directly into a NumPy memory array.
**Why it was written this way:**
* **No Temporary Files:** Many basic VTT apps save a temporary `.wav` file to the hard drive, transcribe it, and delete it. This destroys SSD lifespans over time due to constant read/writes and leaves fragments of sensitive voice data on the disk. Storing the audio stream purely in RAM (NumPy array) guarantees total privacy and instantaneous handoff to the AI model.

### `core/transcribe.py` (Hardware Accelerated AI)
**What it does:** Feeds the NumPy audio array into the Whisper AI model and returns the decoded text string.
**Why it was written this way:**
* **Apple Silicon MLX:** We explicitly chose `mlx-whisper` over the standard OpenAI `whisper` library or `whisper.cpp`. MLX is Apple's native machine learning framework designed specifically for the unified memory architecture of M-series chips (M1/M2/M3). It avoids copying memory between the CPU and GPU, making transcription exponentially faster and cooler (thermally) than traditional PyTorch implementations.
* **Fallback Architecture:** It retains a fallback to `faster-whisper` (CTranslate2) strictly so the codebase remains portable to Intel Macs or Linux machines if needed.

---

## 3. The macOS Injection Challenge (`integration/clipboard.py`)

### `integration/clipboard.py` (Secure Text Pasting)
**What it does:** Securely takes the final transcribed text and forces it to appear where the user's text cursor is currently blinking.
**Why it was written this way:**
This file underwent the most iteration of the entire project due to macOS security constraints.
* **Why not `pynput.keyboard.type()`:** We tried simulating typing character-by-character. It was slow for long paragraphs, interleaved with the user's actual typing if their hands were on the keyboard, and failed silently without explicit OS permissions.
* **Why not `osascript` keystrokes:** We tried native AppleScript to simulate `Cmd+V`. macOS blocked it entirely (Error 1002) because it views command-line AppleScript execution as an inherently untrusted capability for Accessibility automation.
* **The Final Masterpiece Approach:** The code copies the text to the clipboard (`pyperclip.copy()`). It then uses `ctypes` (`AXIsProcessTrusted`) to hook directly into Apple's C-level API to natively check if it has Accessibility permission. 
    * If `True`: It briefly taps `Cmd+V` using `pynput`, instantly pasting the text safely.
    * If `False`: It fires a native, unblockable UI dialog warning the user and opens System Settings for them. This entirely prevents the "silent failure" bugs that plague macOS automation tools.

---

## 4. The User Interface (`ui/widget.py`)

### `ui/widget.py` (Zero-Intrusion Menu Bar)
**What it does:** Renders the small black/red/orange dot in the macOS menu bar near the WiFi icon and manages the pulsing animation.
**Why it was written this way:**
* **Menu Bar vs Floating Node:** We initially built a beautiful, translucent floating bubble that appeared on the screen when recording. However, forcing a floating PyQt widget to NEVER steal keyboard focus on macOS is nearly impossible. If the focus is stolen even for a microsecond, the final text injection has nowhere to paste.
* **`QSystemTrayIcon`:** Shifting to the Menu Bar solved all focus issues instantly because the Menu Bar lives outside the standard window manager Z-index. The user maintains 100% focus on their word processor.
* **The `QTimer` Pulse:** The red pulsing animation uses a pure PyQt Event Loop timer (`QTimer`) rather than Python's `time.sleep()`. This ensures the animation never blocks or freezes the background socket server, allowing it to instantly receive the "stop recording" ping.

---

## 5. Security and Packaging (`build.sh`)

### `build.sh` (The PyInstaller Freeze)
**What it does:** Packages the raw Python scripts into native macOS `.app` bundles so the user doesn't have to keep a terminal window permanently open.
**Why it was written this way:**
* **`Info.plist` & The Microphone:** macOS possesses a feature where if an `.app` bundle tries to access the microphone *without* explicitly stating why in its `Info.plist` file, macOS will not warn you. It will **silently feed the app pure zeros** (absolute silence). The build script manually injects `<key>NSMicrophoneUsageDescription</key>` to force macOS to display the native "NeuroType would like to access the microphone" permission prompt.
* **The `LSUIElement` Flag:** The script injects this flag to tell macOS that `NeuroType.app` is a strict background daemon. This hides the app from the Dock, prevents it from manifesting a top menu bar (File/Edit/View), and explicitly prevents it from becoming the active application.
* **`codesign` and `xattr -cr`:** Strips Apple's Gatekeeper "Quarantine" tags downloaded files get, and forcibly signs the new bundle so macOS lets it run locally without developer certificates.

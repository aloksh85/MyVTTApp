# Project Lessons & Context (lessons.md)

**Purpose:** This document is maintained by the Maintainer Agent. It records critical observations, architectural decisions, mistakes made, and best practices. The Code Writer and Code Reviewer agents MUST read this file before implementing new features to avoid repeating past mistakes.

## 1. Environment & Packaging
* **PyInstaller and Apple MLX:** PyInstaller routinely fails to automatically collect Apple's native C++ `mlx` and `mlx_whisper` framework binaries. 
  * *Fix / Best Practice:* Always explicitly pass `--collect-all mlx` and `--collect-all mlx_whisper` to the PyInstaller build script to prevent silent crashes on startup.
* **PyInstaller Multiprocessing Fork Bomb:** If any underlying library (like `torch` or `mlx`) utilizes Python's `multiprocessing` module, frozen PyInstaller apps on Windows/macOS will spawn infinite instances of the application until the OS crashes.
  * *Fix / Best Practice:* The absolute first line executed under `if __name__ == "__main__":` must be `import multiprocessing; multiprocessing.freeze_support()`.
* **PyInstaller Raw Folder Confusion:** Even when using `--windowed`, PyInstaller will generate both a `.app` bundle and a raw folder containing the UNIX executable in the `dist/` directory. If a user double-clicks the raw UNIX executable, it will force-open Terminal.app.
  * *Fix / Best Practice:* Always add `rm -rf dist/AppName` to the end of your `build.sh` script to delete the raw UNIX folders, leaving only the `.app` bundles for the user.
* **macOS Gatekeeper Quarantine (Spotlight failure):** Newly built PyInstaller `.app` bundles will have hidden Apple Quarantine extended attributes attached to them. Attempting to launch them via Spotlight (`Cmd+Space`) or Finder will fail silently.
  * *Fix / Best Practice:* Always run `xattr -cr dist/AppName.app` and `chmod -R 755 dist/AppName.app` after compilation to strip these tags so the user can execute them normally.
* **macOS Silent Microphone Blocking:** macOS strictly prohibits any compiled `.app` bundle from reading the microphone unless the `NSMicrophoneUsageDescription` key is explicitly present in its `Info.plist`. Without it, macOS will NOT crash the app or throw an error; it will silently feed it pure zeros (digital silence), causing Whisper to transcribe nothing.
  * *Fix / Best Practice:* Always inject the `NSMicrophoneUsageDescription` key into the `<dict>` of the `.app` bundle's `Info.plist` using `sed` in your build script to successfully trigger the macOS Privacy popup.

## 2. Desktop UI & Focus Management
* **Focus Stealing via Apple Shortcuts:** Binding a shell script to an Apple Shortcut causes a momentary window-switch to the invisible Shortcuts Engine, stealing typing focus from the user's active application (e.g., Notion).
  * *Fix / Best Practice:* Never use the Shortcuts app for hidden terminal commands. Instead, compile the trigger script into a native `.app` bundle using PyInstaller and explicitly inject the `<key>LSUIElement</key><string>1</string>` flag into its `Info.plist`. This forces macOS to treat it as a true background app that never steals focus.
* **PyQt6 Background Daemons:** A PyQt6 `QApplication` designed to run invisibly without a primary window will automatically terminate itself.
  * *Fix / Best Practice:* Always set `app.setQuitOnLastWindowClosed(False)` when building daemonized PyQt applications.

## 3. Keyboard Hooks & Security
* **macOS Global Hotkeys (`pynput`):** Relying on `pynput` or global keyboard listeners in Python on modern macOS architectures triggers thread-handle bugs, requires invasive Accessibility permissions, and poses keylogger security risks.
  * *Fix / Best Practice:* Do NOT use `pynput` for application hotkeys. Use a **Socket-Daemon Architecture**. Run a local TCP socket in the background (`app.py`), and use native OS shortcuts to ping the port (via a `client.py` payload).

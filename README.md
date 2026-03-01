# Offline Voice-to-Text Setup and Verification

Your offline, privacy-first Voice-to-Text transcription app MVP is complete! It now features **Cross-Platform Support** for macOS and Linux.

## How to Install and Use the App

1. Open your terminal to `/Users/aloksh/Documents/sandbox/myVTT/` and simply run the new smart installer. This will download dependencies and download the offline AI models so they are ready before you even run the app!
```bash
./install.sh
```

2. Start the App:
```bash
./run.sh
```

3. Ensure your OS grants the necessary permissions:
   - **macOS**: System Settings > Privacy & Security > Accessibility
   - **Linux**: Wayland users may need to run on X11 or grant specific input recording permissions depending on their compositor.


4. An icon should appear in your System Tray:
   - On macOS: The Menu Bar at the top of the screen (🎙️).
   - On Linux: The right-side system tray.

5. Focus on any application you want to type into (e.g. Notion, Browser). 
6. Hit the Global Hotkey:
   - **macOS**: `Cmd+Shift+R`
   - **Linux**: `Ctrl+Shift+R`
7. Speak your mind. Hit the hotkey again to stop recording.
8. Wait a few moments. It will use the offline model to transcribe your audio and it will automatically paste your speech wherever your cursor currently is located!

### Features
- **Starts Fast**: Using lightweight `rumps`/`pystray`, `pynput`, and `sounddevice`.
- **Fully Offline**: All transcriptions happen locally leveraging `mlx-whisper` on Apple Silicon, and `faster-whisper` on Linux/Intel architectures. The models download at install time.
- **Global Injection**: Pastes naturally using `osascript` on Mac and `pyautogui` on Linux.

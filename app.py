"""
Offline Voice-to-Text Application.

This module provides a cross-platform (macOS and Linux) application that:
1. Records audio from the microphone directly into memory.
2. Transcribes the audio locally using Apple Silicon's MLX (mlx-whisper)
   or faster-whisper on other platforms.
3. Securely pastes the transcribed text into the user's active application.

Production hardened and PEP-8 compliant.
"""

import logging
import platform
import queue
import subprocess
import threading
import time
from typing import Optional

import numpy as np
import pyperclip
import sounddevice as sd
from pynput import keyboard

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Platform Detection ---
OS_NAME: str = platform.system()
ARCH_NAME: str = platform.machine()
IS_MAC_SILICON: bool = (OS_NAME == "Darwin" and ARCH_NAME == "arm64")

if IS_MAC_SILICON:
    import mlx_whisper
else:
    from faster_whisper import WhisperModel

if OS_NAME == "Darwin":
    import rumps
else:
    import pystray
    from PIL import Image, ImageDraw

# --- Configuration Constants ---
SAMPLE_RATE: int = 16000
CHANNELS: int = 1
# Approximately 10 minutes of audio buffers max
MAX_QUEUE_SIZE: int = 6000

if IS_MAC_SILICON:
    MODEL_PATH: str = "mlx-community/whisper-base-mlx"
else:
    MODEL_PATH: str = "base"

HOTKEY: str = "<cmd>+<shift>+r" if OS_NAME == "Darwin" else "<ctrl>+<shift>+r"


class AppState:
    """Manages the application's global state and threads."""

    def __init__(self) -> None:
        """Initialize the application state."""
        self.is_recording: bool = False
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue(
            maxsize=MAX_QUEUE_SIZE)
        self.record_thread: Optional[threading.Thread] = None
        self.whisper_model_instance = None

        if not IS_MAC_SILICON:
            logger.info("Loading faster-whisper model into memory...")
            self.whisper_model_instance = WhisperModel(
                MODEL_PATH, device="cpu", compute_type="int8"
            )


# Initialize global state
state = AppState()


def audio_callback(
    indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags
) -> None:
    """
    Callback function invoked by sounddevice for each audio block.

    Args:
        indata: The recorded audio data as a NumPy array.
        frames: The number of frames in the block.
        time_info: Dictionary containing timing information.
        status: Status flags indicating errors or warnings.
    """
    if status:
        logger.warning("Audio input status warning: %s", status)

    if state.is_recording:
        try:
            # Drop chunks if the queue is full to prevent unbounded memory
            # growth
            state.audio_queue.put_nowait(indata.copy())
        except queue.Full:
            logger.error(
                "Audio queue full! Dropping frames to prevent memory leak.")


def start_recording() -> None:
    """Start the microphone recording thread."""
    state.is_recording = True

    # Clear lingering data from previous recordings
    with state.audio_queue.mutex:
        state.audio_queue.queue.clear()

    def record_process() -> None:
        """Inner function to run the sounddevice InputStream."""
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                callback=audio_callback,
            ):
                while state.is_recording:
                    time.sleep(0.1)
        except Exception as e:
            logger.error("Error during recording: %s", e)

    state.record_thread = threading.Thread(target=record_process, daemon=True)
    state.record_thread.start()
    logger.info("Recording started. Microphone active.")


def stop_recording() -> None:
    """Stop the microphone recording thread and trigger processing."""
    if not state.is_recording:
        return

    state.is_recording = False
    if state.record_thread:
        state.record_thread.join(timeout=2.0)

    logger.info("Recording stopped. Processing audio...")
    process_audio()


def process_audio() -> None:
    """Extract audio from the queue and transcribe it entirely in-memory."""
    audio_data_list = []
    while not state.audio_queue.empty():
        audio_data_list.append(state.audio_queue.get())

    if not audio_data_list:
        logger.info("No audio frames recorded.")
        return

    # Combine array chunks into a single contiguous flat 1D array
    # ML models generally require a 1D float32 array normalized between -1.0
    # and 1.0
    audio_array = np.concatenate(audio_data_list, axis=0).flatten()

    logger.info(
        "Audio processed (shape: %s). Transcribing in-memory...",
        audio_array.shape)

    try:
        text: str = ""
        if IS_MAC_SILICON:
            # MLX whisper accepts ndarray directly
            result = mlx_whisper.transcribe(
                audio_array, path_or_hf_repo=MODEL_PATH
            )
            text = result.get("text", "").strip()
        else:
            # Faster-whisper accepts ndarray directly
            segments, _ = state.whisper_model_instance.transcribe(
                audio_array, beam_size=5
            )
            text = " ".join([segment.text for segment in segments]).strip()

        logger.info("Transcription Result: %s", text)

        if text:
            type_text(text)

    except Exception as e:
        logger.error("Transcriber inference failed: %s", e)


def type_text(text: str) -> None:
    """
    Securely inject text into the active user window.

    Temporarily uses the clipboard, simulating a 'paste' shortcut,
    then restores the prior clipboard value to prevent data leakage.

    Args:
        text: The transcribed text string to be pasted.
    """
    # 1. Back up current clipboard state
    try:
        original_clipboard = pyperclip.paste()
    except Exception as e:
        logger.warning("Could not read original clipboard: %s", e)
        original_clipboard = ""

    # 2. Inject transcription to clipboard
    try:
        pyperclip.copy(text)
        time.sleep(0.05)  # Let clipboard subsystem settle
    except Exception as e:
        logger.error("Clipboard write failed: %s", e)
        return

    # 3. Trigger Paste automation
    if OS_NAME == "Darwin":
        apple_script = """
        tell application "System Events"
            keystroke "v" using command down
        end tell
        """
        try:
            subprocess.run(["osascript", "-e", apple_script], check=True)
        except subprocess.CalledProcessError as e:
            logger.error("AppleScript paste failed: %s", e)
    else:
        # Cross-platform / Linux fallback
        try:
            import pyautogui
            pyautogui.hotkey("ctrl", "v")
        except ImportError:
            logger.warning("pyautogui not installed. Falling back to xdotool.")
            subprocess.run(["xdotool", "key", "ctrl+v"], check=False)

    logger.info("Text successfully injected.")

    # 4. Restore the clipboard to prevent privacy leaks
    time.sleep(0.1)  # Ensure paste finishes before overwriting clipboard
    try:
        pyperclip.copy(original_clipboard)
        logger.debug("Clipboard state restored automatically.")
    except Exception as e:
        logger.error("Failed to restore clipboard state: %s", e)


def on_activate_h() -> None:
    """Toggle logic triggered by the global hotkey."""
    if not state.is_recording:
        start_recording()
    else:
        stop_recording()


def setup_hotkeys() -> keyboard.GlobalHotKeys:
    """
    Initialize global hotkey listener.

    Returns:
        The instantiated global hotkey listener object.
    """
    listener = keyboard.GlobalHotKeys({HOTKEY: on_activate_h})
    listener.start()
    return listener


if OS_NAME == "Darwin":

    class VTTApp(rumps.App):
        """macOS menu bar application interface."""

        def __init__(self) -> None:
            """Initialize the menu bar application."""
            super().__init__("🎙️")
            self.menu = [f"Toggle Recording ({HOTKEY})"]
            self.hotkey_listener = setup_hotkeys()

        @rumps.timer(0.5)
        def update_ui(self, sender: rumps.Timer) -> None:
            """Poll and update the menu bar icon based on recording state."""
            self.title = "🔴" if state.is_recording else "🎙️"

        @rumps.clicked(f"Toggle Recording ({HOTKEY})")
        def on_toggle(self, sender: rumps.MenuItem) -> None:
            """Handle manual click on the tray toggle button."""
            on_activate_h()

    def run_ui() -> None:
        """Start the macOS application loop."""
        app = VTTApp()
        app.run()

else:
    # Linux Tray Icon Logic
    def create_image(color1: str, color2: str) -> Image.Image:
        """Create a dynamic tray icon placeholder."""
        image = Image.new("RGB", (64, 64), color1)
        dc = ImageDraw.Draw(image)
        dc.rectangle((16, 16, 48, 48), fill=color2)
        return image

    def run_ui() -> None:
        """Start the Linux system tray application loop."""
        setup_hotkeys()

        icon = pystray.Icon("VTT")
        icon.icon = create_image("black", "white")

        def on_clicked(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
            """Handle manual click on the tray toggle button."""
            on_activate_h()

        def updater() -> None:
            """Update the system tray icon based on recording state."""
            while True:
                icon.icon = (
                    create_image("red", "white")
                    if state.is_recording
                    else create_image("black", "white")
                )
                time.sleep(0.5)

        threading.Thread(target=updater, daemon=True).start()

        menu = pystray.Menu(
            pystray.MenuItem(f"Toggle Recording ({HOTKEY})", on_clicked)
        )
        icon.menu = menu
        icon.run()


if __name__ == "__main__":
    logger.info("Initializing Offline Voice-to-Text VTT App...")
    logger.info("System Trigger: Press %s to toggle recording.", HOTKEY)

    if IS_MAC_SILICON:
        logger.info("Warming up MLX Whisper model memory buffers...")
        try:
            # Emit a blank 1s float32 audio signature to ensure memory
            # initializes.
            dummy_audio = np.zeros(16000, dtype=np.float32)
            mlx_whisper.transcribe(dummy_audio, path_or_hf_repo=MODEL_PATH)
            logger.info("Local MLX model ready!")
        except Exception as e:
            logger.error("Model warmup failed: %s", e)

    run_ui()

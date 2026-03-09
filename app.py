"""
Main Application Entry Point.

Wires the PyQt6 GUI with the microphone and AI transcription layers.
"""

import sys
import logging
import platform
import signal

import numpy as np
import socket
from PyQt6.QtCore import pyqtSignal, QObject, QThread, QTimer
from PyQt6.QtWidgets import QApplication

from core.audio import AudioRecorder
from core.transcribe import Transcriber
from integration.clipboard import ClipboardManager
from ui.widget import StatusTrayIcon

# --- Configure Logging ---
import os
log_dir = os.path.expanduser("~/Library/Logs/MyVTTApp")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "daemon.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=log_file
)
logger = logging.getLogger(__name__)

OS_NAME = platform.system()
DAEMON_PORT = 9999

class CommandListener(QThread):
    """Background listener for socket commands (e.g., 'toggle')."""
    toggle_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.keep_running = True

    def run(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('127.0.0.1', DAEMON_PORT))
                s.listen()
                s.settimeout(1.0)
                logger.info("Daemon listening on localhost:%s", DAEMON_PORT)
                
                while self.keep_running:
                    try:
                        conn, addr = s.accept()
                        with conn:
                            data = conn.recv(1024)
                            if data:
                                cmd = data.decode('utf-8').strip()
                                if cmd == 'toggle':
                                    self.toggle_signal.emit()
                    except socket.timeout:
                        continue
        except Exception as e:
            logger.error("Command listener failed: %s", e)

    def stop(self):
        self.keep_running = False
        self.wait()

class TranscribeThread(QThread):
    """Background thread to run inference without freezing the UI."""
    finished_signal = pyqtSignal(str)

    def __init__(self, transcriber, audio_data):
        super().__init__()
        self.transcriber = transcriber
        self.audio_data = audio_data

    def run(self):
        try:
            text = self.transcriber.transcribe(self.audio_data)
            self.finished_signal.emit(text)
        except Exception as e:
            logger.error("Transcription thread failed: %s", e)
            self.finished_signal.emit("")

class AppController(QObject):
    """
    Coordinates between the GUI Thread, the Audio Thread,
    and transcription models.
    """

    # Signals to safely update the GUI from the background hotkey thread
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    transcription_ready = pyqtSignal(str)
    
    # Internal signal to transfer audio processing to the Main Thread
    _process_audio = pyqtSignal(np.ndarray)

    def __init__(self, widget: StatusTrayIcon):
        super().__init__()
        self.widget = widget
        self.recorder = AudioRecorder()

        # Wire signals to the widget UI safely across threads
        self.recording_started.connect(lambda: self.widget.set_listening(True))
        self.recording_stopped.connect(lambda: self.widget.set_listening(False))
        self.transcription_ready.connect(self._auto_inject_text)

        # The ML Transcriber is heavy, loaded asynchronously or lazily
        self.transcriber = Transcriber()
        
        # Connect the background audio signal to the main-thread execution
        self._process_audio.connect(self._do_transcribe)

        # Start the socket Command Listener
        self.command_listener = CommandListener()
        self.command_listener.toggle_signal.connect(self._toggle_recording)
        self.command_listener.start()

    def _toggle_recording(self) -> None:
        """
        Triggered by global hotkey (runs in a background pynput thread).
        Emits signals to the main GUI thread.
        """
        if not self.recorder.is_recording:
            # Widget isn't active, start recording
            self.recording_started.emit()
            self.recorder.start()
        else:
            # Widget is active, stop and process
            self.recording_stopped.emit()
            audio_data = self.recorder.stop()

            if audio_data is not None and len(audio_data) > 0:
                # Emit to main thread to avoid Metal/GPU cross-thread crash
                self._process_audio.emit(audio_data)
            else:
                self.transcription_ready.emit("[No audio recorded]")

    def _do_transcribe(self, audio_data: np.ndarray) -> None:
        """Executes transcription on a background QThread to keep UI fluid."""
        logger.info("Executing transcription on a dedicated QThread...")
        
        self.transcribe_thread = TranscribeThread(self.transcriber, audio_data)
        self.transcribe_thread.finished_signal.connect(self._on_transcription_finished)
        self.transcribe_thread.start()

    def _on_transcription_finished(self, text: str) -> None:
        """Emit the returned text back to the main thread."""
        self.transcription_ready.emit(text)

    def _auto_inject_text(self, final_text: str) -> None:
        """Automatically called upon successful transcription."""
        self.widget.reset_idle()
        
        if not final_text or final_text.strip() == "[No audio recorded]":
            logger.info("Nothing to inject. Reset to idle.")
            return
            
        logger.info("Auto-Injecting Text: %s", final_text)
        
        # Because we are now using a native macOS Menu Bar icon (QSystemTrayIcon),
        # we bypass the macOS Window Manager entirely. There is no need for hacky
        # hide() or processEvents() loops to juggle keyboard focus!
        ClipboardManager.type_text(final_text)

    def cleanup(self) -> None:
        """Gracefully close background processing threads before exit."""
        logger.info("Cleaning up application resources...")
        if self.recorder.is_recording:
            self.recorder.stop()
        if hasattr(self, 'command_listener'):
            self.command_listener.stop()
        if hasattr(self, 'transcribe_thread') and self.transcribe_thread.isRunning():
            self.transcribe_thread.wait()


def main():
    """Start the PyQt6 event loop and application."""
    logger.info("Starting Premium VTT Application...")

    app = QApplication(sys.argv)
    
    # Needs to stay resident in memory even when no windows are open
    app.setQuitOnLastWindowClosed(False)

    # Bind Ctrl+C to gracefully terminate the application
    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())
    
    # PyQt6 event loop blocks Python signals. A dummy timer is required to let Python 
    # process the Ctrl+C interrupt gracefully.
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    widget = StatusTrayIcon()
    widget.show()
    _controller = AppController(widget)
    
    app.aboutToQuit.connect(_controller.cleanup)

    logger.info("Ready! Send 'toggle' via client.py to begin dictation.")

    sys.exit(app.exec())


import multiprocessing

if __name__ == "__main__":
    # CRITICAL: Required for PyInstaller to not fork bomb when spawning background 
    # child processes for MLX/Whisper inference.
    multiprocessing.freeze_support()
    main()

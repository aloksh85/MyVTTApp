"""
Audio Capture Module.

Handles continuous microphone streaming into a NumPy memory queue
using sounddevice.
"""

import logging
import queue
import threading
import time
from typing import Optional

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)

SAMPLE_RATE: int = 16000
CHANNELS: int = 1
MAX_QUEUE_SIZE: int = 6000  # ~10 minutes of buffer


class AudioRecorder:
    """Manages the microphone and audio frame queue."""

    def __init__(self) -> None:
        """Initialize the recording state."""
        self.is_recording: bool = False
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        self.record_thread: Optional[threading.Thread] = None

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags
    ) -> None:
        """Sounddevice stream callback."""
        if status:
            logger.warning("Audio input status warning: %s", status)

        if self.is_recording:
            try:
                self.audio_queue.put_nowait(indata.copy())
            except queue.Full:
                logger.error("Audio queue full! Dropping frames.")

    def start(self) -> None:
        """Start recording from the microphone."""
        self.is_recording = True

        # Flush any old audio
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()

        def record_process() -> None:
            try:
                with sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype="float32",
                    blocksize=int(SAMPLE_RATE * 0.1),
                    callback=self._audio_callback,
                ):
                    while self.is_recording:
                        time.sleep(0.1)
            except Exception as e:
                logger.error("CRITICAL ERROR opening Microphone: %s", e)
                logger.error("Please grant Terminal/App Microphone permissions in Mac System Settings!")
                self.is_recording = False

        self.record_thread = threading.Thread(target=record_process, daemon=True)
        self.record_thread.start()
        logger.info("Microphone active.")

    def stop(self) -> Optional[np.ndarray]:
        """
        Stop recording and return the flattened audio queue.

        Returns:
            A 1D numpy array of audio samples, or None if no audio.
        """
        if not self.is_recording:
            return None

        self.is_recording = False
        if self.record_thread:
            self.record_thread.join(timeout=2.0)

        logger.info("Microphone stopped.")

        audio_data_list = []
        while not self.audio_queue.empty():
            audio_data_list.append(self.audio_queue.get())

        if not audio_data_list:
            logger.info("No audio recorded.")
            return None

        return np.concatenate(audio_data_list, axis=0).flatten()

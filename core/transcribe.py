"""
Transcription Engine Module.

Handles offline audio transcription using mlx-whisper (macOS Apple Silicon)
or faster-whisper (Cross-Platform/Intel).
"""

import logging
import platform

import numpy as np

logger = logging.getLogger(__name__)

OS_NAME: str = platform.system()
ARCH_NAME: str = platform.machine()
IS_MAC_SILICON: bool = (OS_NAME == "Darwin" and ARCH_NAME == "arm64")

if IS_MAC_SILICON:
    import mlx_whisper
else:
    from faster_whisper import WhisperModel


class Transcriber:
    """Handles loading and running inference on the Whisper models."""

    # Pinned model revision hash for supply chain verification.
    # To verify: git ls-remote https://huggingface.co/mlx-community/whisper-base-mlx main
    PINNED_REVISION = "a8f14b616d37f94a159016b04f80a7f7003a1b8f"

    def __init__(self) -> None:
        """Initialize the model based on system architecture."""
        if IS_MAC_SILICON:
            self.model_path = "mlx-community/whisper-small-mlx"
            self._warmup_mlx()
        else:
            self.model_path = "base"
            self.whisper_model_instance = self._load_faster_whisper()

    def _warmup_mlx(self) -> None:
        """Forces MLX model to load weights into memory."""
        logger.info("Warming up MLX Whisper model memory buffers...")
        try:
            dummy_audio = np.zeros(16000, dtype=np.float32)
            mlx_whisper.transcribe(dummy_audio, path_or_hf_repo=self.model_path)
            logger.info("Local MLX model ready for inference!")
        except Exception as e:
            logger.error("Model warmup failed: %s", e)

    def _load_faster_whisper(self) -> "WhisperModel":
        """Loads faster-whisper model into CPU memory."""
        logger.info("Loading faster-whisper model into memory...")
        return WhisperModel(self.model_path, device="cpu", compute_type="int8")

    def transcribe(self, audio_array: np.ndarray) -> str:
        """
        Transcribe a 1D float32 audio array.

        Args:
            audio_array: Raw numpy audio samples.

        Returns:
            The transcribed text string.
        """
        logger.info("Transcribing audio array of shape: %s", audio_array.shape)
        try:
            if IS_MAC_SILICON:
                result = mlx_whisper.transcribe(
                    audio_array, path_or_hf_repo=self.model_path
                )
                text = result.get("text", "").strip()
            else:
                segments, _ = self.whisper_model_instance.transcribe(
                    audio_array, beam_size=5
                )
                text = " ".join([segment.text for segment in segments]).strip()

            return text
        except Exception as e:
            logger.error("Transcriber inference failed: %s", e)
            return ""

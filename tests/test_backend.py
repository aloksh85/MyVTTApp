import numpy as np
import pytest
from core.transcribe import Transcriber

@pytest.fixture(scope="session")
def transcriber():
    """Fixture to load the MLX/Faster-Whisper model once per test session."""
    return Transcriber()

def test_transcriber_initialization(transcriber):
    """Test that the transcriber initializes properly without crashing."""
    assert transcriber is not None
    assert transcriber.model_path is not None

def test_transcriber_transcribe_silence(transcriber):
    """Test that feeding pure silence does not crash or raise exceptions."""
    # 0.5 seconds of silent 16k audio
    dummy_audio = np.zeros(8000, dtype=np.float32)
    result = transcriber.transcribe(dummy_audio)
    
    # Whisper usually returns either '' or a hallucination on pure silence, 
    # but the critical check is that it returns a string and doesn't hit Abort Trap.
    assert isinstance(result, str)

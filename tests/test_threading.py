import pytest
import numpy as np
from app import TranscribeThread
from core.transcribe import Transcriber

@pytest.fixture(scope="session")
def transcriber():
    return Transcriber()

def test_transcribe_thread(qtbot, transcriber):
    """Test that the QThread processes audio and emits the finished signal."""
    # Dummy empty audio chunk
    dummy_audio = np.zeros(8000, dtype=np.float32)
    
    thread = TranscribeThread(transcriber, dummy_audio)
    
    with qtbot.waitSignal(thread.finished_signal, timeout=5000) as blocker:
        thread.start()
        
    assert blocker.args is not None
    # Depending on model fallback, empty audio might be "" or hallucination, 
    # but we just care it emitted a string safely without crashing Qt.
    assert isinstance(blocker.args[0], str)

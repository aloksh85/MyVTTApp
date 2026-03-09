import pytest
import numpy as np
import time
from unittest.mock import patch, MagicMock
from core.audio import AudioRecorder

def test_audio_recorder_initialization():
    recorder = AudioRecorder()
    assert getattr(recorder, 'is_recording', None) is False
    assert not recorder.is_recording
    assert recorder.audio_queue.empty()

@patch('core.audio.sd.InputStream')
def test_audio_recorder_start_stop(mock_input_stream):
    """Test that start() opens an InputStream and stop() returns data."""
    recorder = AudioRecorder()
    
    # Mock the InputStream
    mock_stream_instance = MagicMock()
    mock_input_stream.return_value = mock_stream_instance
    
    recorder.start()
    assert recorder.is_recording
    assert recorder.record_thread is not None
    assert recorder.record_thread.is_alive()
    
    # Simulate the callback pushing data
    dummy_data = np.ones((512, 1), dtype=np.float32)
    recorder._audio_callback(dummy_data, frames=512, time_info=None, status=None)
    
    # Ensure queue actually received the data
    assert not recorder.audio_queue.empty()
    
    # Stop recording
    result_audio = recorder.stop()
    
    assert not recorder.is_recording
    assert result_audio is not None
    assert len(result_audio) == 512
    assert np.all(result_audio == 1.0)
    
    # Clean up the thread
    if recorder.record_thread:
        recorder.record_thread.join(timeout=1.0)

import pytest
import socket
import time
from app import CommandListener, DAEMON_PORT

def test_command_listener_toggle(qtbot):
    """Test that the CommandListener properly receives socket payloads and fires PyQt signals."""
    listener = CommandListener()
    
    # Track if the signal was emitted across thread boundaries
    signal_emitted = False
    def on_toggle():
        nonlocal signal_emitted
        signal_emitted = True

    listener.toggle_signal.connect(on_toggle)
    listener.start()
    
    # Give the background QThread a moment to bind to the port
    time.sleep(0.5)

    # Simulate the client.py trigger script
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Short timeout so tests fail fast if port isn't bound
            s.settimeout(2.0)
            s.connect(('127.0.0.1', DAEMON_PORT))
            s.sendall(b'toggle')
    except Exception as e:
        listener.stop()
        pytest.fail(f"Could not connect to test daemon on port {DAEMON_PORT}: {e}")

    # Wait up to 2 seconds for the Qt Event Loop to receive and process the background signal
    try:
        qtbot.waitUntil(lambda: signal_emitted is True, timeout=2000)
    finally:
        # Guarantee cleanup even if the assertion fails
        listener.stop()

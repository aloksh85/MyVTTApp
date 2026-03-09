import pytest
from PyQt6.QtCore import Qt
from ui.widget import FloatingDictationWidget

@pytest.fixture
def floating_widget(qtbot):
    """Fixture to provide a clean FloatingDictationWidget instance."""
    widget = FloatingDictationWidget()
    qtbot.addWidget(widget)
    return widget

def test_ui_initialization(floating_widget):
    """Test the widget initializes correctly with click-through flags."""
    assert not floating_widget.is_listening
    assert floating_widget.status_label.text() == "Ready"
    assert floating_widget.pulse_state is False
    
    # Assert it has the new transparent flags
    flags = floating_widget.windowFlags()
    assert flags & Qt.WindowType.WindowTransparentForInput
    assert flags & Qt.WindowType.WindowDoesNotAcceptFocus

def test_ui_listening_state(floating_widget, qtbot):
    """Test UI changes when listening state toggles."""
    floating_widget.set_listening(True)
    
    assert floating_widget.is_listening
    assert floating_widget.status_label.text() == "Listening..."
    assert floating_widget.pulse_timer.isActive()
    assert floating_widget.isVisible()
    
    floating_widget.set_listening(False)
    assert not floating_widget.pulse_timer.isActive()
    assert floating_widget.status_label.text() == "Transcribing..."

def test_ui_flash_success(floating_widget, qtbot):
    """Test that the widget updates status to Paste and schedules a hide."""
    floating_widget.show()
    floating_widget.flash_success()
    
    assert "Pasted!" in floating_widget.status_label.text()
    
    # The hide is scheduled for 1000ms later via singleShot.
    # We can use qtbot to wait for it.
    qtbot.wait(1100)
    assert not floating_widget.isVisible()

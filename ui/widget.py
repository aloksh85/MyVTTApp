"""
PyQt6 Custom Floating User Interface.

Provides a tiny, non-interactive, click-through status bubble that 
does not steal OS focus from the user's active application.
"""

import logging
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class FloatingDictationWidget(QWidget):
    """A frameless, floating dictation status bubble."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the non-interactive bubble."""
        super().__init__(parent)

        # CRITICAL UX FIX: WindowTransparentForInput makes the widget "click-through"
        # Tool and WindowStaysOnTopHint prevent it from showing on the dock or falling behind apps
        # WindowDoesNotAcceptFocus prevents it from stealing keyboard focus from Notion/Word
        # WindowDoesNotAcceptFocus prevents it from stealing keyboard focus from Notion/Word
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow |  # Critical: SubWindow prevents secondary focus stealing
            Qt.WindowType.WindowDoesNotAcceptFocus |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Mac-specific flag to entirely decouple from the OS Window Manager focus loop
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)

        # Dimensions & position
        self.resize(250, 60)
        self._center_on_screen()

        self._init_ui()
        self._setup_animations()

        self.is_listening: bool = False

    def _center_on_screen(self) -> None:
        """Center the widget on the primary screen (lower half)."""
        screen_geo = QApplication.primaryScreen().geometry()
        x = (screen_geo.width() - self.width()) // 2
        y = int(screen_geo.height() * 0.8)  # Place very low on screen
        self.move(x, y)

    def _init_ui(self) -> None:
        """Build the internal layouts and styling."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Main background frame
        self.bg_frame = QFrame(self)
        self.bg_frame.setObjectName("BgFrame")
        self.bg_frame.setStyleSheet(
            """
            #BgFrame {
                background-color: rgba(20, 20, 20, 200);
                border-radius: 30px;
                border: 1px solid rgba(255, 255, 255, 20);
            }
            """
        )
        frame_layout = QHBoxLayout(self.bg_frame)
        frame_layout.setContentsMargins(20, 10, 20, 10)

        self.mic_icon = QLabel("🎙️")
        self.mic_icon.setFont(QFont("Arial", 16))
        
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.status_label.setStyleSheet("color: #FFFFFF;")

        frame_layout.addStretch()
        frame_layout.addWidget(self.mic_icon)
        frame_layout.addWidget(self.status_label)
        frame_layout.addStretch()

        main_layout.addWidget(self.bg_frame)

    def _setup_animations(self) -> None:
        """Setup the pulsing animation for the microphone."""
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._toggle_pulse)
        self.pulse_state = False

    def _toggle_pulse(self) -> None:
        """Toggle the microphone icon color to simulate pulsing."""
        if self.pulse_state:
            self.status_label.setStyleSheet("color: #FF4444;")  # Red
        else:
            self.status_label.setStyleSheet("color: #FFFFFF;")  # White
        self.pulse_state = not self.pulse_state

    def set_listening(self, active: bool) -> None:
        """Update UI to reflect listening state."""
        self.is_listening = active
        if active:
            self.status_label.setText("Listening...")
            self.status_label.setStyleSheet("color: #FF4444;")
            self.pulse_timer.start(500)
            self._toggle_pulse()
            
            # Use WA_ShowWithoutActivating trick
            self.show()
            self.raise_()
        else:
            self.pulse_timer.stop()
            self.status_label.setText("Transcribing...")
            self.status_label.setStyleSheet("color: #FFAA00;")

    def flash_success(self) -> None:
        """Briefly show a success state before hiding."""
        self.status_label.setText("Pasted!")
        self.status_label.setStyleSheet("color: #00FF00;")
        
        # Hide the widget completely after 1 second
        QTimer.singleShot(1000, self.hide)

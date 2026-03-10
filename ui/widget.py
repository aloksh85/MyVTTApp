"""
PyQt6 Native System Tray Interface.

Provides a native macOS Menu Bar icon. This completely bypasses the macOS Window Manager 
focus hierarchy, permanently solving the "invisible bubble" and "focus stealing" bugs
inherent to LSUIElement background dictation daemons.
"""

import logging
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtWidgets import (
    QSystemTrayIcon,
    QMenu,
    QApplication
)

logger = logging.getLogger(__name__)


class StatusTrayIcon(QSystemTrayIcon):
    """A native macOS Menu Bar status icon with pulsing recording animation."""

    # Animation interval in milliseconds
    _PULSE_INTERVAL_MS: int = 500

    def __init__(self, parent=None) -> None:
        """Initialize the tray icon with dynamic states."""
        super().__init__(parent)
        self.is_listening: bool = False
        self._pulse_state: bool = False

        # Create dynamically drawn colored circle icons
        self.idle_icon = self._create_icon(QColor("black"))
        self.recording_bright_icon = self._create_icon(QColor(220, 30, 30))
        self.recording_dim_icon = self._create_icon(QColor(120, 15, 15))
        self.transcribing_icon = self._create_icon(QColor("orange"))

        self.setIcon(self.idle_icon)
        self.setToolTip("NeuroType - Idle")

        # Provide a context menu so the user can easily quit the invisible background app
        self.menu = QMenu()
        quit_action = self.menu.addAction("Quit NeuroType")
        quit_action.triggered.connect(QApplication.instance().quit)
        self.setContextMenu(self.menu)

        # Pulse timer runs on the PyQt6 main thread event loop (no threading needed)
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._toggle_pulse)

    def _create_icon(self, color: QColor) -> QIcon:
        """Draw a simple 16x16 circle indicator."""
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor("transparent"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(color)
        painter.setPen(QColor("transparent"))
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()
        return QIcon(pixmap)

    def _toggle_pulse(self) -> None:
        """Alternate the recording icon between bright and dim red."""
        if self._pulse_state:
            self.setIcon(self.recording_bright_icon)
        else:
            self.setIcon(self.recording_dim_icon)
        self._pulse_state = not self._pulse_state

    def set_listening(self, active: bool) -> None:
        """Update system tray icon to reflect listening state."""
        self.is_listening = active
        if active:
            self._pulse_state = False
            self.setIcon(self.recording_bright_icon)
            self.setToolTip("Listening...")
            self._pulse_timer.start(self._PULSE_INTERVAL_MS)
        else:
            self._pulse_timer.stop()
            self.setIcon(self.transcribing_icon)
            self.setToolTip("Transcribing...")

    def reset_idle(self) -> None:
        """Return the icon to the black idle state."""
        self._pulse_timer.stop()
        self.setIcon(self.idle_icon)
        self.setToolTip("NeuroType - Idle")


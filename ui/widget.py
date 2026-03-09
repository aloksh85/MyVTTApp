"""
PyQt6 Native System Tray Interface.

Provides a native macOS Menu Bar icon. This completely bypasses the macOS Window Manager 
focus hierarchy, permanently solving the "invisible bubble" and "focus stealing" bugs
inherent to LSUIElement background dictation daemons.
"""

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtWidgets import (
    QSystemTrayIcon,
    QMenu,
    QApplication
)

logger = logging.getLogger(__name__)


class StatusTrayIcon(QSystemTrayIcon):
    """A native macOS Menu Bar status icon."""

    def __init__(self, parent=None) -> None:
        """Initialize the tray icon with dynamic states."""
        super().__init__(parent)
        self.is_listening = False

        # Create dynamically drawn colored circle icons
        self.idle_icon = self._create_icon(QColor("black"))
        self.recording_icon = self._create_icon(QColor("red"))
        self.transcribing_icon = self._create_icon(QColor("orange"))

        self.setIcon(self.idle_icon)
        self.setToolTip("NeuroType - Idle")

        # Provide a context menu so the user can easily quit the invisible background app
        self.menu = QMenu()
        quit_action = self.menu.addAction("Quit NeuroType")
        quit_action.triggered.connect(QApplication.instance().quit)
        self.setContextMenu(self.menu)

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

    def set_listening(self, active: bool) -> None:
        """Update system tray icon to reflect listening state."""
        self.is_listening = active
        if active:
            self.setIcon(self.recording_icon)
            self.setToolTip("Listening...")
        else:
            self.setIcon(self.transcribing_icon)
            self.setToolTip("Transcribing...")

    def reset_idle(self) -> None:
        """Return the icon to the black idle state."""
        self.setIcon(self.idle_icon)
        self.setToolTip("NeuroType - Idle")

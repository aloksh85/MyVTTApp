"""
Platform / Clipboard Integration Module.

Handles securely typing/pasting text into the active user window
while maintaining clipboard privacy state.
"""

import logging
import platform
import subprocess
import time

import pyperclip

logger = logging.getLogger(__name__)

OS_NAME: str = platform.system()


class ClipboardManager:
    """Manages secure text injection into other applications."""

    @staticmethod
    def type_text(text: str) -> None:
        """
        Securely paste text into the active user window.

        Args:
            text: The text to inject.
        """
        if not text:
            return

        # Disabled original clipboard backup to prevent macOS AppleScript race conditions.
        # try:
        #     original_clipboard = pyperclip.paste()
        # except Exception as e:
        #     logger.warning("Could not read original clipboard: %s", e)
        #     original_clipboard = ""

        try:
            pyperclip.copy(text)
            # Give macOS enough time to visibly restore focus to the underlying app 
            # after the PyQt6 window hides itself.
            time.sleep(0.4) 
        except Exception as e:
            logger.error("Clipboard write failed: %s", e)
            return

        if OS_NAME == "Darwin":
            try:
                from pynput.keyboard import Key, Controller
                keyboard = Controller()
                
                # Small delay to ensure the OS has shifted focus back to Notion
                # after the PyQt6 ToolTip bubble hides itself.
                time.sleep(0.3)
                
                # Simulate Cmd+V at the OS driver level
                keyboard.press(Key.cmd)
                keyboard.press('v')
                keyboard.release('v')
                keyboard.release(Key.cmd)
            except Exception as e:
                logger.error("pynput paste failed: %s", e)
        else:
            try:
                import pyautogui
                pyautogui.hotkey("ctrl", "v")
            except ImportError:
                logger.warning("pyautogui not installed. Using xdotool.")
                subprocess.run(["xdotool", "key", "ctrl+v"], check=False)

        logger.info("Text injected via clipboard.")

        # Disabling aggressive restoration. macOS needs time to async process Cmd+V.
        # Leaving the text in the pasteboard also acts as a great UX fallback!
        # time.sleep(0.1)  
        # try:
        #     pyperclip.copy(original_clipboard)
        # except Exception as e:
        #     logger.error("Failed to restore clipboard state: %s", e)

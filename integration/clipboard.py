"""
Platform / Text Injection Module.

Handles pasting transcribed text into the active user window
using the system clipboard and a simulated Cmd+V keystroke.
"""

import logging
import platform
import subprocess
import time

import pyperclip

logger = logging.getLogger(__name__)

OS_NAME: str = platform.system()


class ClipboardManager:
    """Manages text injection into other applications."""

    @staticmethod
    def type_text(text: str) -> None:
        """
        Inject text into the active user window via clipboard paste.

        Copies the text to the system clipboard, then simulates
        Cmd+V (macOS) or Ctrl+V (Linux) to paste it at the cursor.

        Args:
            text: The text to inject.
        """
        if not text:
            return

        try:
            pyperclip.copy(text)
        except Exception as e:
            logger.error("Clipboard write failed: %s", e)
            return

        # Brief delay to let macOS settle focus on the target app
        time.sleep(0.3)

        if OS_NAME == "Darwin":
            # Check native macOS Accessibility permissions explicitly before simulating keys
            has_access = False
            try:
                import ctypes
                app_services = ctypes.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
                app_services.AXIsProcessTrusted.restype = ctypes.c_bool
                has_access = app_services.AXIsProcessTrusted()
            except Exception as e:
                logger.error("Failed to check accessibility permissions: %s", e)
            
            if has_access:
                try:
                    from pynput.keyboard import Key, Controller
                    keyboard = Controller()
                    keyboard.press(Key.cmd)
                    keyboard.press('v')
                    keyboard.release('v')
                    keyboard.release(Key.cmd)
                    logger.info("Text injected via clipboard (pynput Cmd+V).")
                except Exception as e:
                    logger.error("pynput paste failed: %s", e)
            else:
                logger.error("Accessibility permission missing. Cannot simulate Cmd+V.")
                subprocess.run([
                    "osascript", "-e",
                    'display alert "Accessibility Required" message "NeuroType needs Accessibility permission to automatically paste text. The text is in your clipboard, but please enable NeuroType in System Settings -> Privacy & Security -> Accessibility." buttons {"OK"} default button "OK"'
                ])
                subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])
        else:
            try:
                import pyautogui
                pyautogui.hotkey("ctrl", "v")
                logger.info("Text injected via clipboard (pyautogui Ctrl+V).")
            except ImportError:
                logger.warning("pyautogui not installed. Using xdotool.")
                subprocess.run(["xdotool", "key", "ctrl+v"], check=False)
                logger.info("Text injected via clipboard (xdotool Ctrl+V).")



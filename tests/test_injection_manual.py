import time
import subprocess
import platform
import ctypes
import CoreFoundation

print("=== Text Injection Test ===")

def check_accessibility():
    """Check if the current process has macOS Accessibility permissions using ctypes."""
    try:
        app_services = ctypes.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        # AXIsProcessTrusted returns a boolean (1 or 0)
        app_services.AXIsProcessTrusted.restype = ctypes.c_bool
        is_trusted = app_services.AXIsProcessTrusted()
        return is_trusted
    except Exception as e:
        print(f"Error checking accessibility: {e}")
        return False

def prompt_accessibility():
    """Trigger the native macOS accessibility prompt using ctypes."""
    try:
        app_services = ctypes.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        app_services.AXIsProcessTrustedWithOptions.restype = ctypes.c_bool
        app_services.AXIsProcessTrustedWithOptions.argtypes = [ctypes.c_void_p]
        
        # We need to pass a CFDictionary with kAXTrustedCheckOptionPrompt = kCFBooleanTrue
        # This is complex in pure ctypes, so let's use PyObjC if available, or fallback to an osascript dialog.
        try:
            from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt
            options = {kAXTrustedCheckOptionPrompt: True}
            return AXIsProcessTrustedWithOptions(options)
        except ImportError:
            # Fallback to osascript dialog
            subprocess.run([
                "osascript", "-e",
                'display alert "Accessbility Required" message "NeuroType needs Accessibility permission to type text. Please enable it in System Settings -> Privacy & Security -> Accessibility." buttons {"OK"} default button "OK"'
            ])
            # Open System Settings
            subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])
            return False
            
    except Exception as e:
        print(f"Error prompting accessibility: {e}")
        return False

has_access = check_accessibility()
print(f"Has macOS Accessibility Permission: {has_access}")

if not has_access:
    print("Prompting for access...")
    prompt_accessibility()

print("Attempting to type 'Hello via pynput!'")
try:
    from pynput.keyboard import Controller
    keyboard = Controller()
    keyboard.type("Hello via pynput!")
    print("pynput succeeded.")
except Exception as e:
    print(f"pynput failed: {e}")


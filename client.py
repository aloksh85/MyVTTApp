#!/usr/bin/env python3
"""
client.py

A simple CLI utility to interact with the background MyVTTApp daemon.
Can be used by external macros, Shortcuts, or script wrappers
to trigger dictation cleanly without global keyboard listeners.
"""

import socket
import sys
import os
import logging

log_dir = os.path.expanduser("~/Library/Logs/MyVTTApp")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "client.log")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", filename=log_file)

DAEMON_PORT = 9999

def ping_daemon(command: str = "toggle") -> None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # Set a very tight timeout. We aren't waiting for a response, just sending a ping.
            s.settimeout(2.0)
            s.connect(('127.0.0.1', DAEMON_PORT))
            s.sendall(command.encode('utf-8'))
            print(f"Sent '{command}' command to VTT daemon successfully.")
    except ConnectionRefusedError:
        print("Error: The VTT daemon is not running on port 9999. Start it first with './run.sh'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error communicating with VTT daemon: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "toggle"
    ping_daemon(cmd)

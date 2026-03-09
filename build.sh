#!/bin/bash
# build.sh
# Compiles the Python scripts into standalone native applications.

echo "Cleaning old builds..."
rm -rf build/ dist/

# 1. Build the Main Background Daemon
# --noconsole hides the terminal window
# --windowed ensures it compiles as a correct macOS .app bundle
echo "Building MyVTTApp Daemon..."
pyinstaller --noconfirm \
            --windowed \
            --noconsole \
            --collect-all "mlx" \
            --collect-all "mlx_whisper" \
            --hidden-import "mlx_whisper" \
            --hidden-import "PyQt6" \
            --hidden-import "numpy" \
            --name "MyVTTApp" \
            app.py

# 2. Build the Trigger Client
# We MUST use --windowed to create an .app bundle
# and we MUST patch its Info.plist to be LSBackgroundOnly later
echo "Building StartDictation Client..."
pyinstaller --noconfirm \
            --windowed \
            --noconsole \
            --name "StartDictation" \
            client.py

echo "Build complete! Setting LSBackgroundOnly flag on StartDictation..."

echo "Build complete! Setting LSBackgroundOnly flag on Apps..."

# Patch the Info.plist explicitly to prevent focus stealing and dock icons
for APP_NAME in "StartDictation" "MyVTTApp"; do
    PLIST_PATH="dist/${APP_NAME}.app/Contents/Info.plist"
    if [ -f "$PLIST_PATH" ]; then
        # Add LSUIElement to the plist so it never steals focus and hides from Dock
        # Add NSMicrophoneUsageDescription so macOS knows to ask the user for permission instead of silently blocking
        sed -i '' '/<dict>/a\
        <key>LSUIElement</key>\
        <string>1</string>\
        <key>NSMicrophoneUsageDescription</key>\
        <string>This app requires microphone access to record your voice for dictation.</string>\
        ' "$PLIST_PATH"
        echo "Focus-stealing prevention active for ${APP_NAME}."
        
        # AGENT 3 MAINTAINER FIX: Strip Apple Gatekeeper Quarantine attrs 
        # so Spotlight and Finder don't silently block execution of the new binary.
        chmod -R 755 "dist/${APP_NAME}.app"
        xattr -cr "dist/${APP_NAME}.app"
    fi
done

# Clean up the raw UNIX executable folders that PyInstaller generates, 
# which cause users to accidentally open them and spawn Terminal windows.
rm -rf dist/MyVTTApp dist/StartDictation

echo "Done! You can find the native .app bundles in the dist/ folder."

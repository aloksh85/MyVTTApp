# Voice-To-Text (VTT) UX Research & Executive Summary

## Executive Summary
The current "Floating Widget" approach in our application inherently suffers from **Focus Stealing**. By spawning a fully interactive PyQt6 `QTextEdit` window, the macOS window manager forces the user's active context (e.g., Notion, Microsoft Word, Chrome) into the background. While manageable with workarounds (like the simulated `time.sleep` delay before AppleScript injection), this introduces race conditions and breaks the user's "flow state."

A competitive analysis of the most widely used and highly-rated modern VTT applications (such as **Superwhisper**, **Wispr Flow**, and **Apple Native Dictation**) reveals a stark consensus in the industry: **VTT tools should never commandeer user focus.** Modern tools prioritize "invisible" or "non-intrusive" interfaces that act as background daemons, injecting text directly into the user's original active window without requiring an intermediate review step.

---

## Industry Research: How Top Apps Handle UI & Text Injection

### 1. Superwhisper
* **Workflow:** Users trigger dictation via a hotkey (e.g., `Option+Space`).
* **UI Design:** Operates primarily as a discreet macOS Menu Bar icon. 
* **Focus Management:** Superwhisper NEVER spawns an interactive text box that steals focus. Instead, it features an optional "live transcript" overlay that is completely click-through and non-focusable. 
* **Injection Strategy:** Once the hotkey is released, the AI processes the audio and injects the text precisely at the cursor's current position within the target application. It even uses a "Super Mode" that reads the user's clipboard to understand the context of the application they are typing in.

### 2. Wispr Flow
* **Workflow:** Push-to-talk dictation.
* **UI Design:** Extremely minimalistic. When activated, a tiny, non-intrusive bubble appears at the absolute bottom of the screen merely to indicate that the microphone is hot.
* **Focus Management:** No focus stealing. The user's cursor never formally leaves their target application (Slack, Email, Code Editor).
* **Injection Strategy:** Relies entirely on AI post-processing (removing "ums", adding punctuation, applying tone) to guarantee accuracy *before* injection. Because the AI is highly accurate, they bypass the "user review window" entirely. Users simply hit `Backspace` in their own app if a mistake is made.

### 3. Apple Native Dictation (macOS)
* **Workflow:** Triggered by hitting `F5` or the microphone key.
* **UI Design:** A small floating microphone icon appears immediately next to the user's blinking cursor inside the target application.
* **Focus Management:** Zero focus loss. The dictation is technically a sub-process of the active text field.
* **Injection Strategy:** Live streaming text injection.

---

## Conclusion & Proposed Pivot

Our initial hypothesis—that a user would want a dedicated staging window to review text before pasting—is actually considered an anti-pattern in modern VTT design because of the focus-stealing friction it introduces. 

If we want to match the "Production Quality" tier of apps like Superwhisper and Wispr Flow, we should pivot our UI architecture:

**The Path Forward:**
Remove the interactive PyQt6 `QTextEdit` window. Replace it with a tiny, non-focusable "Status Bubble" (or simply a system tray notification) that appears in the corner of the screen when listening. When the hotkey is pressed to stop, the application simply transcribes and instantly injects the text into the active window. This guarantees 100% reliability for the paste action and removes the need for `Enter`/`Escape` key acrobatics.

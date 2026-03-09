import pytest
from unittest.mock import patch, MagicMock
from integration.clipboard import ClipboardManager

@patch('integration.clipboard.OS_NAME', 'Darwin')
@patch('integration.clipboard.pyperclip')
@patch('integration.clipboard.subprocess.run')
@patch('integration.clipboard.time.sleep')
def test_type_text_mac(mock_sleep, mock_run, mock_pyperclip):
    """Test macOS osascript injection via ClipboardManager."""
    mock_pyperclip.paste.return_value = "OldClipboardContext"
    
    ClipboardManager.type_text("Hello User")
    
    # Verify it backed up and replaced the clipboard
    mock_pyperclip.copy.assert_any_call("Hello User")
    
    # Verify the script executed 'Cmd+V'
    mock_run.assert_called_once()
    args, kwargs = mock_run.call_args
    assert "osascript" in args[0]
    assert "keystroke \"v\" using command down" in args[0][-1]
    
    # Verify it restored the old board context
    mock_pyperclip.copy.assert_any_call("OldClipboardContext")

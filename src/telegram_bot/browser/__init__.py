"""Browser module with basic and enhanced browser support."""

# Import TelegramBrowser from parent directory (browser.py)
import sys
from pathlib import Path

parent_dir = Path(__file__).parent.parent
browser_file = parent_dir / "browser.py"

if browser_file.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("telegram_bot_browser", browser_file)
    browser_module = importlib.util.module_from_spec(spec)
    sys.modules['telegram_bot_browser'] = browser_module
    spec.loader.exec_module(browser_module)
    TelegramBrowser = browser_module.TelegramBrowser
else:
    # Fallback: try relative import (won't work but prevents error)
    TelegramBrowser = None

from .browser_adapter import EnhancedBrowserAdapter
from .enhanced_browser import EnhancedBrowserInstance

__all__ = ["TelegramBrowser", "EnhancedBrowserInstance", "EnhancedBrowserAdapter"]


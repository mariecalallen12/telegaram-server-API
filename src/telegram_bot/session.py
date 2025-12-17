"""Session management for Telegram automation."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages session storage for Telegram Web."""

    def __init__(self, sessions_dir: str = "sessions"):
        """
        Initialize session manager.

        Args:
            sessions_dir: Directory to store session files
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)

    def _get_session_path(self, phone: str) -> Path:
        """
        Get session file path for a phone number.

        Args:
            phone: Phone number

        Returns:
            Path to session file
        """
        # Sanitize phone number for filename
        safe_phone = phone.replace("+", "").replace("-", "").replace(" ", "")
        return self.sessions_dir / f"session_{safe_phone}.json"

    def save_session(
        self, phone: str, storage_state: dict[str, Any], metadata: Optional[dict] = None
    ) -> None:
        """
        Save session to file.

        Args:
            phone: Phone number
            storage_state: Browser storage state (cookies, localStorage, etc.)
            metadata: Additional metadata to store
        """
        session_path = self._get_session_path(phone)
        session_data = {
            "phone": phone,
            "storage_state": storage_state,
            "metadata": metadata or {},
        }

        try:
            with open(session_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2)
            logger.info(f"Session saved for {phone}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            raise

    def load_session(self, phone: str) -> Optional[dict[str, Any]]:
        """
        Load session from file.

        Args:
            phone: Phone number

        Returns:
            Session data dictionary or None if not found
        """
        session_path = self._get_session_path(phone)

        if not session_path.exists():
            logger.info(f"No saved session found for {phone}")
            return None

        try:
            with open(session_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            logger.info(f"Session loaded for {phone}")
            return session_data
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None

    def session_exists(self, phone: str) -> bool:
        """
        Check if session exists for a phone number.

        Args:
            phone: Phone number

        Returns:
            True if session exists, False otherwise
        """
        session_path = self._get_session_path(phone)
        return session_path.exists()

    def delete_session(self, phone: str) -> bool:
        """
        Delete session file.

        Args:
            phone: Phone number

        Returns:
            True if deleted, False if not found
        """
        session_path = self._get_session_path(phone)

        if not session_path.exists():
            logger.info(f"No session to delete for {phone}")
            return False

        try:
            session_path.unlink()
            logger.info(f"Session deleted for {phone}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    def list_sessions(self) -> list[str]:
        """
        List all saved sessions.

        Returns:
            List of phone numbers with saved sessions
        """
        sessions = []
        for session_file in self.sessions_dir.glob("session_*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)
                    if "phone" in session_data:
                        sessions.append(session_data["phone"])
            except Exception as e:
                logger.warning(f"Failed to read session file {session_file}: {e}")
        return sessions


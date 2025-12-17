"""Notes management for tracking operations and findings."""

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class NotesManager:
    """Manages notes for operations and findings."""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize notes manager.

        Args:
            storage_path: Path to store notes (default: ./notes)
        """
        self.storage_path = storage_path or Path.cwd() / "notes"
        self.storage_path.mkdir(exist_ok=True)

        self.notes_file = self.storage_path / "notes.json"
        self._notes: dict[str, dict[str, Any]] = {}
        self._load_notes()

    def _load_notes(self) -> None:
        """Load notes from file."""
        if self.notes_file.exists():
            try:
                with open(self.notes_file, "r", encoding="utf-8") as f:
                    self._notes = json.load(f)
                logger.info(f"Loaded {len(self._notes)} notes")
            except Exception as e:
                logger.warning(f"Failed to load notes: {e}")
                self._notes = {}

    def _save_notes(self) -> None:
        """Save notes to file."""
        try:
            with open(self.notes_file, "w", encoding="utf-8") as f:
                json.dump(self._notes, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save notes: {e}")

    def create_note(
        self,
        title: str,
        content: str,
        category: str = "general",
        tags: Optional[list[str]] = None,
        priority: str = "normal",
    ) -> str:
        """
        Create a new note.

        Args:
            title: Note title
            content: Note content
            category: Note category
            tags: List of tags
            priority: Priority level

        Returns:
            Note ID
        """
        note_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now(UTC).isoformat()

        note = {
            "id": note_id,
            "title": title.strip(),
            "content": content.strip(),
            "category": category,
            "tags": tags or [],
            "priority": priority,
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        self._notes[note_id] = note
        self._save_notes()

        logger.info(f"Note created: {note_id} - {title}")
        return note_id

    def list_notes(
        self,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        List notes with optional filtering.

        Args:
            category: Filter by category
            tags: Filter by tags
            priority: Filter by priority
            search: Search in title and content

        Returns:
            List of notes
        """
        filtered_notes = []

        for note in self._notes.values():
            if category and note.get("category") != category:
                continue

            if priority and note.get("priority") != priority:
                continue

            if tags:
                note_tags = note.get("tags", [])
                if not any(tag in note_tags for tag in tags):
                    continue

            if search:
                search_lower = search.lower()
                title_match = search_lower in note.get("title", "").lower()
                content_match = search_lower in note.get("content", "").lower()
                if not (title_match or content_match):
                    continue

            filtered_notes.append(note)

        filtered_notes.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return filtered_notes

    def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[list[str]] = None,
        priority: Optional[str] = None,
    ) -> bool:
        """
        Update a note.

        Args:
            note_id: Note ID
            title: New title
            content: New content
            tags: New tags
            priority: New priority

        Returns:
            True if updated successfully
        """
        if note_id not in self._notes:
            logger.warning(f"Note not found: {note_id}")
            return False

        note = self._notes[note_id]

        if title is not None:
            note["title"] = title.strip()
        if content is not None:
            note["content"] = content.strip()
        if tags is not None:
            note["tags"] = tags
        if priority is not None:
            note["priority"] = priority

        note["updated_at"] = datetime.now(UTC).isoformat()
        self._save_notes()

        logger.info(f"Note updated: {note_id}")
        return True

    def delete_note(self, note_id: str) -> bool:
        """
        Delete a note.

        Args:
            note_id: Note ID

        Returns:
            True if deleted successfully
        """
        if note_id not in self._notes:
            logger.warning(f"Note not found: {note_id}")
            return False

        del self._notes[note_id]
        self._save_notes()

        logger.info(f"Note deleted: {note_id}")
        return True

    def get_note(self, note_id: str) -> Optional[dict[str, Any]]:
        """
        Get a note by ID.

        Args:
            note_id: Note ID

        Returns:
            Note dictionary or None
        """
        return self._notes.get(note_id)


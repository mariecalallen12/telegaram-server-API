"""Notes schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NoteCreateRequest(BaseModel):
    title: str
    content: str
    category: str = "general"
    tags: list[str] | None = None
    priority: str = "normal"


class NoteCreateResponse(BaseModel):
    note_id: str


class NotesListResponse(BaseModel):
    notes: list[dict] = Field(default_factory=list)


class NoteUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    priority: str | None = None


class NoteUpdateResponse(BaseModel):
    updated: bool


class NoteDeleteResponse(BaseModel):
    deleted: bool


class NoteGetResponse(BaseModel):
    note: dict | None



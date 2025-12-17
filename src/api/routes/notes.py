"""Notes endpoints (CRUD over local notes storage)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from telegram_bot.notes import NotesManager

from ..schemas.notes import (
    NoteCreateRequest,
    NoteCreateResponse,
    NoteDeleteResponse,
    NoteGetResponse,
    NotesListResponse,
    NoteUpdateRequest,
    NoteUpdateResponse,
)

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteCreateResponse)
async def create_note(req: NoteCreateRequest) -> NoteCreateResponse:
    mgr = NotesManager()
    note_id = mgr.create_note(req.title, req.content, req.category, req.tags, req.priority)
    return NoteCreateResponse(note_id=note_id)


@router.get("", response_model=NotesListResponse)
async def list_notes(
    category: str | None = Query(default=None),
    tags: str | None = Query(default=None, description="Comma-separated tags"),
    priority: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> NotesListResponse:
    mgr = NotesManager()
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    notes = mgr.list_notes(category=category, tags=tag_list, priority=priority, search=search)
    return NotesListResponse(notes=notes)


@router.get("/{note_id}", response_model=NoteGetResponse)
async def get_note(note_id: str) -> NoteGetResponse:
    mgr = NotesManager()
    return NoteGetResponse(note=mgr.get_note(note_id))


@router.patch("/{note_id}", response_model=NoteUpdateResponse)
async def update_note(note_id: str, req: NoteUpdateRequest) -> NoteUpdateResponse:
    mgr = NotesManager()
    updated = mgr.update_note(
        note_id,
        title=req.title,
        content=req.content,
        tags=req.tags,
        priority=req.priority,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="note_not_found")
    return NoteUpdateResponse(updated=True)


@router.delete("/{note_id}", response_model=NoteDeleteResponse)
async def delete_note(note_id: str) -> NoteDeleteResponse:
    mgr = NotesManager()
    deleted = mgr.delete_note(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="note_not_found")
    return NoteDeleteResponse(deleted=True)



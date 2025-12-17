"""Session schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SessionListResponse(BaseModel):
    sessions: list[str] = Field(default_factory=list, description="List of phone numbers with saved sessions")


class SessionDeleteResponse(BaseModel):
    deleted: bool



"""Contacts schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CheckPhoneRequest(BaseModel):
    phone: str = Field(..., description="Phone to check")
    session_phone: str = Field(..., description="Phone number of a logged-in session to use")
    headless: bool | None = None
    proxy: str | None = None


class CheckPhoneResponse(BaseModel):
    exists: bool


class AddContactRequest(BaseModel):
    phone: str
    first_name: str
    last_name: str | None = ""
    session_phone: str
    headless: bool | None = None
    proxy: str | None = None


class AddContactResponse(BaseModel):
    success: bool



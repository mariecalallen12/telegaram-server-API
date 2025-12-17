"""Groups schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateGroupRequest(BaseModel):
    name: str
    members: list[str] | None = Field(default=None, description="Optional list of member phones to add")
    session_phone: str
    headless: bool | None = None
    proxy: str | None = None


class CreateGroupResponse(BaseModel):
    success: bool


class AddMembersRequest(BaseModel):
    group_name: str
    phones: list[str]
    session_phone: str
    headless: bool | None = None
    proxy: str | None = None


class AddMembersResponse(BaseModel):
    success: bool


class ListGroupsResponse(BaseModel):
    groups: list[str] = Field(default_factory=list)


class GroupInfoResponse(BaseModel):
    info: dict



"""Runs/reports schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RunsListResponse(BaseModel):
    runs: list[str] = Field(default_factory=list)


class RunDataResponse(BaseModel):
    run_name: str
    data: dict


class ReportsListResponse(BaseModel):
    reports: list[str] = Field(default_factory=list, description="Report filenames under ./reports")



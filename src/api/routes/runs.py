"""Runs and reports endpoints."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..schemas.runs import ReportsListResponse, RunDataResponse, RunsListResponse

router = APIRouter(tags=["runs"])


@router.get("/runs", response_model=RunsListResponse)
async def list_runs() -> RunsListResponse:
    runs_dir = Path.cwd() / "telegram_runs"
    if not runs_dir.exists():
        return RunsListResponse(runs=[])
    runs = sorted([p.name for p in runs_dir.iterdir() if p.is_dir()])
    return RunsListResponse(runs=runs)


@router.get("/runs/{run_name}", response_model=RunDataResponse)
async def get_run(run_name: str) -> RunDataResponse:
    run_file = Path.cwd() / "telegram_runs" / run_name / "run_data.json"
    if not run_file.exists():
        raise HTTPException(status_code=404, detail="run_not_found")
    try:
        data = json.loads(run_file.read_text(encoding="utf-8"))
        return RunDataResponse(run_name=run_name, data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports", response_model=ReportsListResponse)
async def list_reports() -> ReportsListResponse:
    reports_dir = Path.cwd() / "reports"
    if not reports_dir.exists():
        return ReportsListResponse(reports=[])
    reports = sorted([p.name for p in reports_dir.iterdir() if p.is_file()])
    return ReportsListResponse(reports=reports)



"""Auth endpoints (job-based login with OTP/2FA submission)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..config import get_settings
from ..schemas.auth import (
    AuthStartRequest,
    AuthStartResponse,
    AuthStatusResponse,
    AuthSubmit2FARequest,
    AuthSubmitOtpRequest,
)
from ..services.job_manager import JobManager

router = APIRouter(prefix="/auth", tags=["auth"])

_jobs = JobManager()


@router.post("/start", response_model=AuthStartResponse)
async def start(req: AuthStartRequest) -> AuthStartResponse:
    settings = get_settings()
    headless = req.headless if req.headless is not None else settings.default_headless

    job = await _jobs.create_login_job(
        phone=req.phone,
        force=req.force,
        headless=headless,
        proxy=req.proxy,
        use_enhanced_browser=settings.use_enhanced_browser,
        run_name=req.run_name,
    )
    return AuthStartResponse(job_id=job.job_id, status=job.status)


@router.get("/status/{job_id}", response_model=AuthStatusResponse)
async def status(job_id: str) -> AuthStatusResponse:
    job = await _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job_not_found")
    return AuthStatusResponse(
        job_id=job.job_id,
        status=job.status,
        phone=job.phone,
        run_name=job.run_name,
        error=job.error,
    )


@router.post("/submit-otp", response_model=AuthStatusResponse)
async def submit_otp(req: AuthSubmitOtpRequest) -> AuthStatusResponse:
    try:
        job = await _jobs.submit_otp(req.job_id, req.otp)
        return AuthStatusResponse(
            job_id=job.job_id,
            status=job.status,
            phone=job.phone,
            run_name=job.run_name,
            error=job.error,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="job_not_found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit-2fa", response_model=AuthStatusResponse)
async def submit_2fa(req: AuthSubmit2FARequest) -> AuthStatusResponse:
    try:
        job = await _jobs.submit_2fa(req.job_id, req.password)
        return AuthStatusResponse(
            job_id=job.job_id,
            status=job.status,
            phone=job.phone,
            run_name=job.run_name,
            error=job.error,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="job_not_found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



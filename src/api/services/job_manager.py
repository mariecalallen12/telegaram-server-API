"""In-process job manager for long-running automation operations.

Why jobs?
- Playwright browser sessions are expensive.
- Login requires multiple client round-trips (start -> submit OTP -> optional submit 2FA).

This module keeps job state in memory. For production, this can be swapped out for
Redis/DB-backed storage plus a proper worker.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal, Optional

from telegram_bot.browser import TelegramBrowser
from telegram_bot.browser.browser_adapter import EnhancedBrowserAdapter
from telegram_bot.login import TelegramLogin
from telegram_bot.reporting import ReportGenerator
from telegram_bot.session import SessionManager
from telegram_bot.telemetry import Tracer, set_global_tracer
from telegram_bot.utils import extract_phone_number

logger = logging.getLogger(__name__)

JobStatus = Literal[
    "queued",
    "running",
    "waiting_for_otp",
    "waiting_for_2fa",
    "completed",
    "failed",
]


@dataclass
class LoginJob:
    job_id: str
    status: JobStatus = "queued"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    phone: Optional[str] = None
    run_name: Optional[str] = None
    error: Optional[str] = None

    # Runtime objects (kept in-process)
    tracer: Optional[Tracer] = None
    browser: Any | None = None  # TelegramBrowser or EnhancedBrowserAdapter
    session_manager: Optional[SessionManager] = None
    login_handler: Optional[TelegramLogin] = None

    task: Optional[asyncio.Task] = None

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC).isoformat()


class JobManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._jobs: dict[str, LoginJob] = {}

    async def get(self, job_id: str) -> Optional[LoginJob]:
        async with self._lock:
            return self._jobs.get(job_id)

    async def create_login_job(
        self,
        *,
        phone: str,
        force: bool,
        headless: bool,
        proxy: str | None,
        use_enhanced_browser: bool,
        run_name: str | None,
    ) -> LoginJob:
        job_id = str(uuid.uuid4())
        phone = extract_phone_number(phone)
        resolved_run_name = run_name or f"api_login_{phone}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        tracer = Tracer(run_name=resolved_run_name)
        set_global_tracer(tracer)

        browser = (
            EnhancedBrowserAdapter(headless=headless, proxy=proxy)
            if use_enhanced_browser
            else TelegramBrowser(headless=headless)
        )
        session_manager = SessionManager()
        login_handler = TelegramLogin(browser, session_manager)

        job = LoginJob(
            job_id=job_id,
            status="queued",
            phone=phone,
            run_name=resolved_run_name,
            tracer=tracer,
            browser=browser,
            session_manager=session_manager,
            login_handler=login_handler,
        )

        async with self._lock:
            self._jobs[job_id] = job

        job.task = asyncio.create_task(self._run_login_start(job, force=force), name=f"login:{job_id}")
        return job

    async def submit_otp(self, job_id: str, otp: str) -> LoginJob:
        job = await self._require_job(job_id)
        if job.status != "waiting_for_otp":
            raise ValueError(f"Job {job_id} is not waiting for OTP (status={job.status})")
        if not job.login_handler:
            raise RuntimeError("Job is missing login handler")

        job.status = "running"
        job.touch()

        try:
            await job.login_handler.enter_otp(otp)
            if await job.login_handler._check_2fa_required():
                job.status = "waiting_for_2fa"
                job.touch()
                return job

            await self._finalize_login(job)
            return job
        except Exception as e:
            await self._fail_job(job, str(e))
            return job

    async def submit_2fa(self, job_id: str, password: str) -> LoginJob:
        job = await self._require_job(job_id)
        if job.status != "waiting_for_2fa":
            raise ValueError(f"Job {job_id} is not waiting for 2FA (status={job.status})")
        if not job.login_handler:
            raise RuntimeError("Job is missing login handler")

        job.status = "running"
        job.touch()

        try:
            ok = await job.login_handler.handle_2fa(password)
            if not ok:
                raise RuntimeError("2FA verification failed")
            await self._finalize_login(job)
            return job
        except Exception as e:
            await self._fail_job(job, str(e))
            return job

    async def _require_job(self, job_id: str) -> LoginJob:
        job = await self.get(job_id)
        if not job:
            raise KeyError(f"Job not found: {job_id}")
        return job

    async def _run_login_start(self, job: LoginJob, *, force: bool) -> None:
        job.status = "running"
        job.touch()
        assert job.login_handler is not None
        assert job.browser is not None

        try:
            # Launch browser and attempt saved session unless forcing a fresh login.
            await job.browser.launch()
            success = await job.login_handler.login_with_phone(
                job.phone or "",
                use_saved_session=not force,
                force_new=force,
                # API flow: do NOT block waiting for OTP. We will stop at OTP screen.
                stop_at_otp=True,
            )

            # login_with_phone returns True only if completed using saved session.
            if success:
                await self._finalize_login(job, used_saved_session=True, close_browser=True)
                return

            job.status = "waiting_for_otp"
            job.touch()
        except Exception as e:
            await self._fail_job(job, str(e))

    async def _finalize_login(
        self,
        job: LoginJob,
        *,
        used_saved_session: bool = False,
        close_browser: bool = True,
    ) -> None:
        assert job.login_handler is not None
        assert job.browser is not None
        assert job.session_manager is not None

        if not await job.login_handler.check_login_success():
            raise RuntimeError("Login verification failed")

        # Save session (for saved session flows, storage_state may still be valid to refresh on disk).
        storage_state = await job.browser.get_storage_state()
        job.session_manager.save_session(job.phone or "", storage_state)

        job.status = "completed"
        job.error = None
        job.touch()

        # Finish tracer + generate report.
        if job.tracer:
            job.tracer.finish()
            report_gen = ReportGenerator()
            summary = job.tracer.get_summary()
            report_gen.generate_markdown_report(
                job.run_name or job.tracer.run_name,
                summary["statistics"],
                job.tracer.operations,
                job.tracer.errors,
            )

        if close_browser:
            await job.browser.close()

    async def _fail_job(self, job: LoginJob, error: str) -> None:
        job.status = "failed"
        job.error = error
        job.touch()
        logger.exception("Job failed: %s", job.job_id)
        try:
            if job.tracer:
                job.tracer.log_error("api", "login_job", error)
                job.tracer.finish()
            if job.browser:
                await job.browser.close()
        except Exception:
            # best effort
            pass



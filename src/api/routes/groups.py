"""Groups endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from telegram_bot.groups import GroupManager

from ..config import get_settings
from ..schemas.groups import (
    AddMembersRequest,
    AddMembersResponse,
    CreateGroupRequest,
    CreateGroupResponse,
    GroupInfoResponse,
    ListGroupsResponse,
)
from ..services.browser_runner import browser_with_session

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("/create", response_model=CreateGroupResponse)
async def create_group(req: CreateGroupRequest) -> CreateGroupResponse:
    settings = get_settings()
    headless = req.headless if req.headless is not None else settings.default_headless
    try:
        async with browser_with_session(
            session_phone=req.session_phone,
            headless=headless,
            proxy=req.proxy,
            use_enhanced_browser=settings.use_enhanced_browser,
        ) as browser:
            mgr = GroupManager(browser)
            ok = await mgr.create_group(req.name, req.members)
            return CreateGroupResponse(success=ok)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="session_not_found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-members", response_model=AddMembersResponse)
async def add_members(req: AddMembersRequest) -> AddMembersResponse:
    settings = get_settings()
    headless = req.headless if req.headless is not None else settings.default_headless
    try:
        async with browser_with_session(
            session_phone=req.session_phone,
            headless=headless,
            proxy=req.proxy,
            use_enhanced_browser=settings.use_enhanced_browser,
        ) as browser:
            mgr = GroupManager(browser)
            ok = await mgr.add_members_to_group(req.group_name, req.phones)
            return AddMembersResponse(success=ok)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="session_not_found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=ListGroupsResponse)
async def list_groups(
    session_phone: str = Query(..., description="Phone number of a logged-in session to use"),
    headless: bool | None = Query(default=None),
    proxy: str | None = Query(default=None),
) -> ListGroupsResponse:
    settings = get_settings()
    resolved_headless = headless if headless is not None else settings.default_headless
    try:
        async with browser_with_session(
            session_phone=session_phone,
            headless=resolved_headless,
            proxy=proxy,
            use_enhanced_browser=settings.use_enhanced_browser,
        ) as browser:
            mgr = GroupManager(browser)
            groups = await mgr.list_groups()
            return ListGroupsResponse(groups=groups)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="session_not_found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info", response_model=GroupInfoResponse)
async def group_info(
    session_phone: str = Query(...),
    group_name: str = Query(...),
    headless: bool | None = Query(default=None),
    proxy: str | None = Query(default=None),
) -> GroupInfoResponse:
    settings = get_settings()
    resolved_headless = headless if headless is not None else settings.default_headless
    try:
        async with browser_with_session(
            session_phone=session_phone,
            headless=resolved_headless,
            proxy=proxy,
            use_enhanced_browser=settings.use_enhanced_browser,
        ) as browser:
            mgr = GroupManager(browser)
            info = await mgr.get_group_info(group_name)
            return GroupInfoResponse(info=info or {"name": group_name})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="session_not_found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



"""Campaign endpoints.

Thin HTTP layer over :class:`CampaignRepository`. The session is injected per
request; the route never builds its own database connection.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from brandpulse.api.deps import get_session
from brandpulse.api.schemas import CampaignCreate, CampaignResponse
from brandpulse.db.repository import CampaignRepository

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(payload: CampaignCreate, session: SessionDep) -> CampaignResponse:
    repo = CampaignRepository(session)
    try:
        campaign = await repo.create(payload.name, payload.terms, payload.description)
        await session.flush()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Campaign {payload.name!r} already exists.",
        ) from None
    return CampaignResponse.from_orm_campaign(campaign)


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(session: SessionDep) -> list[CampaignResponse]:
    repo = CampaignRepository(session)
    return [CampaignResponse.from_orm_campaign(c) for c in await repo.list()]


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: int, session: SessionDep) -> CampaignResponse:
    campaign = await CampaignRepository(session).get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    return CampaignResponse.from_orm_campaign(campaign)

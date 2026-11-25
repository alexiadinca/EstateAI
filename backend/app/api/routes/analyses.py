"""Endpoints for supported cities, property entry and the user's saved analyses."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.db.session import get_db_session
from app.schemas.property_analysis import (
    AnalysisDetail,
    AnalysisSummary,
    CityResponse,
    PropertyAnalysisCreate,
)
from app.services.property_analyses import (
    CityNotFoundError,
    create_property_analysis,
    get_user_analysis,
    list_cities,
    list_user_analyses,
    to_analysis_detail,
    to_analysis_summary,
)

router = APIRouter(tags=["analyses"])

DatabaseSession = Annotated[Session, Depends(get_db_session)]


@router.get("/cities", response_model=list[CityResponse])
def read_supported_cities(_: CurrentUser, session: DatabaseSession) -> list[CityResponse]:
    """Cities covered by the valuation data scope."""
    return [CityResponse.model_validate(city) for city in list_cities(session)]


@router.post("/analyses", response_model=AnalysisDetail, status_code=status.HTTP_201_CREATED)
def create_analysis(
    request: PropertyAnalysisCreate, current_user: CurrentUser, session: DatabaseSession
) -> AnalysisDetail:
    """Save a confirmed property and run the valuation available at this moment."""
    try:
        analysis = create_property_analysis(session, current_user, request)
    except CityNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Choose one of the supported cities.",
        ) from error
    return to_analysis_detail(analysis)


@router.get("/analyses", response_model=list[AnalysisSummary])
def read_my_analyses(current_user: CurrentUser, session: DatabaseSession) -> list[AnalysisSummary]:
    """The signed-in user's analyses, newest first."""
    return [
        to_analysis_summary(analysis)
        for analysis in list_user_analyses(session, current_user.user_id)
    ]


@router.get("/analyses/{analysis_id}", response_model=AnalysisDetail)
def read_analysis(
    analysis_id: uuid.UUID, current_user: CurrentUser, session: DatabaseSession
) -> AnalysisDetail:
    """One saved analysis, exactly as it was stored. Other users' analyses are not found."""
    analysis = get_user_analysis(session, current_user.user_id, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")
    return to_analysis_detail(analysis)

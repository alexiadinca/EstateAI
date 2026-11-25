"""Endpoint that proposes property details from a listing link or pasted listing text."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.db.session import get_db_session
from app.extraction.fetcher import ListingUnavailableError, UnsupportedListingUrlError
from app.extraction.service import extract_from_text, extract_from_url
from app.schemas.extraction import ExtractionRequest, ExtractionResponse

router = APIRouter(tags=["extraction"])


@router.post("/extractions", response_model=ExtractionResponse)
def extract_listing(
    request: ExtractionRequest,
    _: CurrentUser,
    session: Annotated[Session, Depends(get_db_session)],
) -> ExtractionResponse:
    """Read a listing and return proposed values for review. Nothing is saved."""
    try:
        if request.url:
            return extract_from_url(session, request.url)
        return extract_from_text(session, request.text or "")
    except UnsupportedListingUrlError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    except ListingUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error

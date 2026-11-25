"""Saving properties with their analysis snapshot, and reading a user's own analyses."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.auth.token_verifier import AuthenticatedUser
from app.models import Analysis, City, Neighborhood, Property
from app.schemas.property_analysis import (
    AnalysisDetail,
    AnalysisSummary,
    ConfirmedPropertyInputs,
    PropertyAnalysisCreate,
    ValuationResponse,
)
from app.services.pricing import price_per_m2
from app.services.user_profiles import get_or_create_profile
from app.services.valuation import estimate_reference_price

SNAPSHOT_SCHEMA_VERSION = 1
MANUAL_ENTRY = "manual_entry"


class CityNotFoundError(Exception):
    """The requested city is not one of the supported cities."""


def list_cities(session: Session) -> list[City]:
    return list(session.scalars(select(City).order_by(City.name)))


def _get_or_create_neighborhood(session: Session, city: City, name: str) -> Neighborhood:
    """Reuse a neighborhood of the same city regardless of letter case, or create it."""
    existing = session.scalars(
        select(Neighborhood).where(
            Neighborhood.city_id == city.city_id,
            func.lower(Neighborhood.name) == name.lower(),
        )
    ).first()
    if existing is not None:
        return existing

    session.execute(
        insert(Neighborhood)
        .values(city_id=city.city_id, name=name)
        .on_conflict_do_nothing(constraint="uq_neighborhood_city_id_name")
    )
    return session.scalars(
        select(Neighborhood).where(Neighborhood.city_id == city.city_id, Neighborhood.name == name)
    ).one()


def create_property_analysis(
    session: Session, owner: AuthenticatedUser, request: PropertyAnalysisCreate
) -> Analysis:
    """Save the property and its analysis in one transaction.

    The valuation result is stored with the snapshot. If no estimate can be produced,
    the analysis is still saved with status "unavailable" and the reason.
    """
    get_or_create_profile(session, owner)

    city = session.get(City, request.city_id)
    if city is None:
        raise CityNotFoundError
    neighborhood = _get_or_create_neighborhood(session, city, request.neighborhood)

    characteristics = request.model_dump(
        exclude={"city_id", "neighborhood", "asking_price", "currency"}
    )
    saved_property = Property(neighborhood_id=neighborhood.neighborhood_id, **characteristics)
    session.add(saved_property)
    session.flush()

    confirmed_inputs = ConfirmedPropertyInputs(
        city=city.name, county=city.county, neighborhood=neighborhood.name, **characteristics
    )
    # The asking price is deliberately not passed to the model; it is compared afterwards.
    valuation = estimate_reference_price(confirmed_inputs)

    analysis = Analysis(
        user_id=owner.user_id,
        property_id=saved_property.property_id,
        confirmed_inputs={
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "input_source": MANUAL_ENTRY,
            "property": confirmed_inputs.model_dump(mode="json"),
        },
        asking_price=request.asking_price,
        currency=request.currency,
        asking_price_per_m2=price_per_m2(request.asking_price, request.usable_area_m2),
        status=valuation.status,
        error_message=valuation.reason,
    )
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    return analysis


def list_user_analyses(session: Session, user_id: uuid.UUID) -> list[Analysis]:
    return list(
        session.scalars(
            select(Analysis).where(Analysis.user_id == user_id).order_by(Analysis.created_at.desc())
        )
    )


def get_user_analysis(
    session: Session, user_id: uuid.UUID, analysis_id: uuid.UUID
) -> Analysis | None:
    """Return the analysis only if it belongs to the user.

    Another user's analysis is reported exactly like a missing one, so its existence
    is not revealed.
    """
    return session.scalars(
        select(Analysis).where(Analysis.analysis_id == analysis_id, Analysis.user_id == user_id)
    ).first()


def _snapshot_property(analysis: Analysis) -> ConfirmedPropertyInputs:
    return ConfirmedPropertyInputs.model_validate(analysis.confirmed_inputs["property"])


def to_analysis_summary(analysis: Analysis) -> AnalysisSummary:
    confirmed = _snapshot_property(analysis)
    return AnalysisSummary(
        analysis_id=analysis.analysis_id,
        created_at=analysis.created_at,
        status=analysis.status,
        city=confirmed.city,
        neighborhood=confirmed.neighborhood,
        property_type=confirmed.property_type,
        rooms=confirmed.rooms,
        usable_area_m2=confirmed.usable_area_m2,
        asking_price=analysis.asking_price,
        currency=analysis.currency,
    )


def to_analysis_detail(analysis: Analysis) -> AnalysisDetail:
    confirmed = _snapshot_property(analysis)
    return AnalysisDetail(
        analysis_id=analysis.analysis_id,
        created_at=analysis.created_at,
        input_source=analysis.confirmed_inputs.get("input_source", MANUAL_ENTRY),
        property=confirmed,
        asking_price=analysis.asking_price,
        currency=analysis.currency,
        asking_price_per_m2=analysis.asking_price_per_m2,
        # Estimates are stored in the prediction table, added with the baseline model.
        # Until then the stored status and its reason are the complete valuation result.
        valuation=ValuationResponse(status=analysis.status, reason=analysis.error_message),
    )

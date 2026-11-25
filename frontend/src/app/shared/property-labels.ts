import {
  AnalysisStatus,
  BuildingStructure,
  PropertyCondition,
  PropertyType,
} from '../core/api/analyses.service';

// Display text for stored codes. The codes stay in English in the database and the API.

export const STRUCTURE_LABELS: Record<BuildingStructure, string> = {
  concrete: 'Reinforced concrete',
  brick: 'Brick',
  aerated_concrete: 'Aerated concrete (BCA)',
  wood: 'Wood',
  metal: 'Metal',
  other: 'Other',
};

export const CONDITION_LABELS: Record<PropertyCondition, string> = {
  new: 'New',
  renovated: 'Renovated',
  good: 'Good',
  needs_renovation: 'Needs renovation',
};

export const STATUS_LABELS: Record<AnalysisStatus, string> = {
  completed: 'Valuation ready',
  unavailable: 'Valuation unavailable',
  failed: 'Valuation failed',
  pending: 'Valuation in progress',
};

export const NOT_STATED = 'Not stated';

/** For example "2-room apartment" or "1-room apartment". */
export function propertyHeadline(propertyType: PropertyType, rooms: number): string {
  return `${rooms}-room ${propertyType}`;
}

/** Yes, No, or Not stated when the listing did not mention it. */
export function amenityLabel(value: boolean | null): string {
  if (value === null) {
    return NOT_STATED;
  }
  return value ? 'Yes' : 'No';
}

/** The apartment floor, which does not apply to a house. */
export function floorLabel(propertyType: PropertyType, floor: number | null): string {
  if (propertyType === 'house') {
    return 'Not applicable';
  }
  if (floor === null) {
    return NOT_STATED;
  }
  if (floor === 0) {
    return 'Ground floor';
  }
  if (floor === -1) {
    return 'Semi-basement';
  }
  return `Floor ${floor}`;
}

/** Plain-language reading of the signed difference between asking price and estimate. */
export function describePriceDifference(differencePct: number): string {
  const magnitude = Math.abs(differencePct).toFixed(2);
  if (differencePct > 0) {
    return `The asking price is ${magnitude}% above the estimated reference price.`;
  }
  if (differencePct < 0) {
    return `The asking price is ${magnitude}% below the estimated reference price.`;
  }
  return 'The asking price is equal to the estimated reference price.';
}

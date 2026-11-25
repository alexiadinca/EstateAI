import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

import {
  BuildingStructure,
  PropertyAnalysisRequest,
  PropertyCondition,
  PropertyType,
} from '../../../core/api/analyses.service';

// Limits match the backend validation in backend/app/schemas/property_analysis.py.
export const LIMITS = {
  minUsableArea: 10,
  maxUsableArea: 1000,
  maxRooms: 20,
  minFloor: -1,
  maxFloors: 60,
  minConstructionYear: 1800,
  maxConstructionYear: new Date().getFullYear() + 5,
  neighborhoodMaxLength: 100,
};

/** Three answers for an amenity: the listing may not mention it at all. */
export type AmenityChoice = 'unknown' | 'yes' | 'no';

export interface PropertyFormValue {
  cityId: number | null;
  neighborhood: string;
  propertyType: PropertyType;
  usableArea: number | null;
  rooms: number | null;
  floor: number | null;
  totalFloors: number | null;
  constructionYear: number | null;
  structure: BuildingStructure | '';
  condition: PropertyCondition | '';
  hasElevator: AmenityChoice;
  hasBalcony: AmenityChoice;
  hasParking: AmenityChoice;
  askingPrice: number | null;
}

export function toAmenityValue(choice: AmenityChoice): boolean | null {
  if (choice === 'unknown') {
    return null;
  }
  return choice === 'yes';
}

/**
 * Converts the confirmed form into the API request.
 * For a house, the apartment floor and the lift are not applicable and are sent as null.
 */
export function toAnalysisRequest(value: PropertyFormValue): PropertyAnalysisRequest {
  const isHouse = value.propertyType === 'house';
  return {
    city_id: value.cityId as number,
    neighborhood: value.neighborhood.trim().replace(/\s+/g, ' '),
    property_type: value.propertyType,
    usable_area_m2: value.usableArea as number,
    rooms: value.rooms as number,
    floor: isHouse ? null : value.floor,
    total_floors: value.totalFloors,
    construction_year: value.constructionYear,
    structure: value.structure || null,
    condition: value.condition || null,
    has_elevator: isHouse ? null : toAmenityValue(value.hasElevator),
    has_balcony: toAmenityValue(value.hasBalcony),
    has_parking: toAmenityValue(value.hasParking),
    asking_price: value.askingPrice as number,
    currency: 'EUR',
  };
}

/** Whole numbers only, for rooms, floors and years. */
export const wholeNumber: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
  const value = control.value;
  if (value === null || value === '') {
    return null;
  }
  return Number.isInteger(Number(value)) ? null : { wholeNumber: true };
};

/** At most two decimals, which is the precision stored for areas and prices. */
export const atMostTwoDecimals: ValidatorFn = (
  control: AbstractControl,
): ValidationErrors | null => {
  const value = control.value;
  if (value === null || value === '') {
    return null;
  }
  // Checked on the text form, because floating-point multiplication can misjudge decimals.
  return /^-?\d+(\.\d{1,2})?$/.test(String(value)) ? null : { tooManyDecimals: true };
};

/** Group validator: an apartment cannot be above the top floor of its building. */
export const floorWithinBuilding: ValidatorFn = (
  group: AbstractControl,
): ValidationErrors | null => {
  const floor = group.get('floor')?.value;
  const totalFloors = group.get('totalFloors')?.value;
  if (floor === null || totalFloors === null || floor === undefined || totalFloors === undefined) {
    return null;
  }
  return floor > totalFloors ? { floorAboveBuilding: true } : null;
};

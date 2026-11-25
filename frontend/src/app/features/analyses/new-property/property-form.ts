import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

import {
  BuildingStructure,
  ExtractedValues,
  FieldOrigin,
  InputSource,
  ListingSource,
  PropertyAnalysisRequest,
  PropertyCondition,
  PropertyType,
  ProvenanceField,
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

export function toAmenityChoice(value: boolean | null): AmenityChoice {
  if (value === null) {
    return 'unknown';
  }
  return value ? 'yes' : 'no';
}

/** Form control name for each API field whose origin is tracked. */
export const FORM_FIELD_FOR: Record<ProvenanceField, keyof PropertyFormValue> = {
  city_id: 'cityId',
  neighborhood: 'neighborhood',
  property_type: 'propertyType',
  usable_area_m2: 'usableArea',
  rooms: 'rooms',
  floor: 'floor',
  total_floors: 'totalFloors',
  construction_year: 'constructionYear',
  structure: 'structure',
  condition: 'condition',
  has_balcony: 'hasBalcony',
  has_elevator: 'hasElevator',
  has_parking: 'hasParking',
  asking_price: 'askingPrice',
};

/** Where the form's details came from, sent with the analysis when it is saved. */
export interface ImportContext {
  inputSource: InputSource;
  source: ListingSource | null;
  fieldProvenance: Partial<Record<ProvenanceField, FieldOrigin>>;
}

export const MANUAL_ENTRY: ImportContext = {
  inputSource: 'manual_entry',
  source: null,
  fieldProvenance: {},
};

/** Converts proposed values into form values. Values the listing does not state are left out. */
export function extractionToFormValue(values: ExtractedValues): Partial<PropertyFormValue> {
  const formValue: Partial<PropertyFormValue> = {};
  const set = <K extends keyof PropertyFormValue>(key: K, value: PropertyFormValue[K] | null) => {
    if (value !== null) {
      formValue[key] = value;
    }
  };
  set('cityId', values.city_id);
  set('neighborhood', values.neighborhood);
  set('propertyType', values.property_type);
  set('usableArea', values.usable_area_m2);
  set('rooms', values.rooms);
  set('floor', values.floor);
  set('totalFloors', values.total_floors);
  set('constructionYear', values.construction_year);
  set('structure', values.structure);
  set('condition', values.condition);
  set('askingPrice', values.asking_price);
  if (values.has_balcony !== null) formValue.hasBalcony = toAmenityChoice(values.has_balcony);
  if (values.has_elevator !== null) formValue.hasElevator = toAmenityChoice(values.has_elevator);
  if (values.has_parking !== null) formValue.hasParking = toAmenityChoice(values.has_parking);
  return formValue;
}

/**
 * Origin of each imported field at this moment: unchanged values keep their origin, and
 * values the user changed or cleared become "corrected". Fields that were not imported are
 * not listed, which means they were entered manually.
 */
export function currentFieldProvenance(
  importedOrigins: Partial<Record<ProvenanceField, 'listing' | 'description'>>,
  importedValues: Partial<PropertyFormValue>,
  currentValue: PropertyFormValue,
): Partial<Record<ProvenanceField, FieldOrigin>> {
  const provenance: Partial<Record<ProvenanceField, FieldOrigin>> = {};
  for (const [apiField, origin] of Object.entries(importedOrigins) as [
    ProvenanceField,
    'listing' | 'description',
  ][]) {
    const formField = FORM_FIELD_FOR[apiField];
    provenance[apiField] =
      importedValues[formField] === currentValue[formField] ? origin : 'corrected';
  }
  return provenance;
}

/**
 * Converts the confirmed form into the API request.
 * For a house, the apartment floor and the lift are not applicable and are sent as null.
 */
export function toAnalysisRequest(
  value: PropertyFormValue,
  importContext: ImportContext = MANUAL_ENTRY,
): PropertyAnalysisRequest {
  const isHouse = value.propertyType === 'house';
  return {
    input_source: importContext.inputSource,
    source: importContext.source,
    field_provenance: importContext.fieldProvenance,
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

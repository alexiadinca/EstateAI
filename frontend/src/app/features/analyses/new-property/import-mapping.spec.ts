import { ExtractedValues } from '../../../core/api/analyses.service';
import {
  currentFieldProvenance,
  extractionToFormValue,
  PropertyFormValue,
  toAnalysisRequest,
} from './property-form';

const emptyValues: ExtractedValues = {
  city_id: null,
  neighborhood: null,
  property_type: null,
  usable_area_m2: null,
  rooms: null,
  floor: null,
  total_floors: null,
  construction_year: null,
  structure: null,
  condition: null,
  has_balcony: null,
  has_elevator: null,
  has_parking: null,
  asking_price: null,
};

const formDefaults: PropertyFormValue = {
  cityId: null,
  neighborhood: '',
  propertyType: 'apartment',
  usableArea: null,
  rooms: null,
  floor: null,
  totalFloors: null,
  constructionYear: null,
  structure: '',
  condition: '',
  hasElevator: 'unknown',
  hasBalcony: 'unknown',
  hasParking: 'unknown',
  askingPrice: null,
};

describe('extractionToFormValue', () => {
  it('fills only the details the listing states', () => {
    const formValue = extractionToFormValue({ ...emptyValues, rooms: 3, has_parking: false });

    expect(formValue).toEqual({ rooms: 3, hasParking: 'no' });
  });

  it('keeps a stated amenity distinct from an unstated one', () => {
    const formValue = extractionToFormValue({ ...emptyValues, has_elevator: true });

    expect(formValue.hasElevator).toBe('yes');
    expect(formValue.hasBalcony).toBeUndefined();
  });
});

describe('currentFieldProvenance', () => {
  const imported = { rooms: 3, usableArea: 54 };
  const origins = { rooms: 'listing', usable_area_m2: 'description' } as const;

  it('keeps the origin of unchanged values', () => {
    const current = { ...formDefaults, rooms: 3, usableArea: 54 };

    expect(currentFieldProvenance(origins, imported, current)).toEqual({
      rooms: 'listing',
      usable_area_m2: 'description',
    });
  });

  it('marks changed and cleared values as corrected', () => {
    const current = { ...formDefaults, rooms: 2, usableArea: null };

    expect(currentFieldProvenance(origins, imported, current)).toEqual({
      rooms: 'corrected',
      usable_area_m2: 'corrected',
    });
  });

  it('does not list values the user typed in empty fields', () => {
    const current = { ...formDefaults, rooms: 3, usableArea: 54, constructionYear: 1985 };

    expect(currentFieldProvenance(origins, imported, current)).not.toHaveProperty(
      'construction_year',
    );
  });
});

describe('toAnalysisRequest with an import', () => {
  it('sends the listing source and field origins', () => {
    const value = {
      ...formDefaults,
      cityId: 2,
      neighborhood: 'Rogerius',
      usableArea: 54,
      rooms: 2,
      askingPrice: 92000,
    };
    const source = {
      site: 'storia.ro' as const,
      url: 'https://www.storia.ro/ro/oferta/x',
      title: null,
      observed_at: '2026-11-25T10:00:00Z',
      latitude: null,
      longitude: null,
    };

    const request = toAnalysisRequest(value, {
      inputSource: 'listing_url',
      source,
      fieldProvenance: { rooms: 'listing' },
    });

    expect(request.input_source).toBe('listing_url');
    expect(request.source).toBe(source);
    expect(request.field_provenance).toEqual({ rooms: 'listing' });
  });

  it('defaults to manual entry without a source', () => {
    const request = toAnalysisRequest({ ...formDefaults, cityId: 2, rooms: 2 });

    expect(request.input_source).toBe('manual_entry');
    expect(request.source).toBeNull();
    expect(request.field_provenance).toEqual({});
  });
});

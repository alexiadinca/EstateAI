import { FormControl, FormGroup } from '@angular/forms';

import {
  atMostTwoDecimals,
  floorWithinBuilding,
  PropertyFormValue,
  toAnalysisRequest,
  wholeNumber,
} from './property-form';

const apartment: PropertyFormValue = {
  cityId: 2,
  neighborhood: '  Rogerius   Nord ',
  propertyType: 'apartment',
  usableArea: 54,
  rooms: 2,
  floor: 3,
  totalFloors: 4,
  constructionYear: null,
  structure: '',
  condition: 'good',
  hasElevator: 'yes',
  hasBalcony: 'no',
  hasParking: 'unknown',
  askingPrice: 92000,
};

describe('toAnalysisRequest', () => {
  it('keeps unknown, yes and no amenities distinct', () => {
    const request = toAnalysisRequest(apartment);

    expect(request.has_elevator).toBe(true);
    expect(request.has_balcony).toBe(false);
    expect(request.has_parking).toBeNull();
  });

  it('sends empty optional choices as unknown', () => {
    const request = toAnalysisRequest(apartment);

    expect(request.structure).toBeNull();
    expect(request.construction_year).toBeNull();
    expect(request.condition).toBe('good');
  });

  it('tidies the neighborhood name', () => {
    expect(toAnalysisRequest(apartment).neighborhood).toBe('Rogerius Nord');
  });

  it('marks floor and lift as not applicable for a house', () => {
    const request = toAnalysisRequest({ ...apartment, propertyType: 'house' });

    expect(request.floor).toBeNull();
    expect(request.has_elevator).toBeNull();
  });

  it('always analyzes prices in euro', () => {
    expect(toAnalysisRequest(apartment).currency).toBe('EUR');
  });
});

describe('property form validators', () => {
  it('rejects a floor above the top floor of the building', () => {
    const group = new FormGroup({ floor: new FormControl(5), totalFloors: new FormControl(4) });

    expect(floorWithinBuilding(group)).toEqual({ floorAboveBuilding: true });
  });

  it('accepts a missing floor', () => {
    const group = new FormGroup({ floor: new FormControl(null), totalFloors: new FormControl(4) });

    expect(floorWithinBuilding(group)).toBeNull();
  });

  it('requires whole numbers for rooms and floors', () => {
    expect(wholeNumber(new FormControl(2.5))).toEqual({ wholeNumber: true });
    expect(wholeNumber(new FormControl(2))).toBeNull();
  });

  it('limits areas and prices to two decimals', () => {
    expect(atMostTwoDecimals(new FormControl(54.555))).toEqual({ tooManyDecimals: true });
    expect(atMostTwoDecimals(new FormControl(54.55))).toBeNull();
  });
});

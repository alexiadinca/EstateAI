import {
  amenityLabel,
  describePriceDifference,
  floorLabel,
  propertyHeadline,
} from './property-labels';

describe('property labels', () => {
  it('describes a property by rooms and type', () => {
    expect(propertyHeadline('apartment', 2)).toBe('2-room apartment');
  });

  it('keeps unknown amenities distinct from a stated absence', () => {
    expect(amenityLabel(null)).toBe('Not stated');
    expect(amenityLabel(false)).toBe('No');
    expect(amenityLabel(true)).toBe('Yes');
  });

  it('marks the apartment floor as not applicable for a house', () => {
    expect(floorLabel('house', null)).toBe('Not applicable');
  });

  it('distinguishes an unknown floor from the ground floor', () => {
    expect(floorLabel('apartment', null)).toBe('Not stated');
    expect(floorLabel('apartment', 0)).toBe('Ground floor');
    expect(floorLabel('apartment', 3)).toBe('Floor 3');
  });
});

describe('describePriceDifference', () => {
  it('reads the requirements example as above the estimate', () => {
    expect(describePriceDifference(13.64)).toBe(
      'The asking price is 13.64% above the estimated reference price.',
    );
  });

  it('reads a negative difference as below the estimate', () => {
    expect(describePriceDifference(-9.09)).toBe(
      'The asking price is 9.09% below the estimated reference price.',
    );
  });

  it('reads a zero difference as equal', () => {
    expect(describePriceDifference(0)).toBe(
      'The asking price is equal to the estimated reference price.',
    );
  });
});

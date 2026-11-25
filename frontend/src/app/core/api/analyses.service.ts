import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

// Types mirror the FastAPI contract in backend/app/schemas/property_analysis.py.

export type PropertyType = 'apartment' | 'house';
export type BuildingStructure =
  'concrete' | 'brick' | 'aerated_concrete' | 'wood' | 'metal' | 'other';
export type PropertyCondition = 'new' | 'renovated' | 'good' | 'needs_renovation';
export type AnalysisStatus = 'pending' | 'completed' | 'unavailable' | 'failed';

export interface City {
  city_id: number;
  name: string;
  county: string;
}

/** Property characteristics. For amenities, null means "not stated" and false means "no". */
export interface PropertyCharacteristics {
  property_type: PropertyType;
  usable_area_m2: number;
  rooms: number;
  floor: number | null;
  total_floors: number | null;
  construction_year: number | null;
  structure: BuildingStructure | null;
  condition: PropertyCondition | null;
  has_balcony: boolean | null;
  has_elevator: boolean | null;
  has_parking: boolean | null;
}

/** How the details reached the form. */
export type InputSource = 'manual_entry' | 'listing_url' | 'listing_text';

/** Where a confirmed value came from. Fields without an origin were entered manually. */
export type FieldOrigin = 'listing' | 'description' | 'corrected';

export type ProvenanceField =
  | 'city_id'
  | 'neighborhood'
  | 'property_type'
  | 'usable_area_m2'
  | 'rooms'
  | 'floor'
  | 'total_floors'
  | 'construction_year'
  | 'structure'
  | 'condition'
  | 'has_balcony'
  | 'has_elevator'
  | 'has_parking'
  | 'asking_price';

export interface ListingSource {
  site: 'storia.ro' | 'olx.ro' | null;
  url: string | null;
  title: string | null;
  observed_at: string;
  latitude: number | null;
  longitude: number | null;
}

export interface PropertyAnalysisRequest extends PropertyCharacteristics {
  city_id: number;
  neighborhood: string;
  asking_price: number;
  currency: 'EUR';
  input_source: InputSource;
  source: ListingSource | null;
  field_provenance: Partial<Record<ProvenanceField, FieldOrigin>>;
}

/** Values proposed from a listing. Any of them may be missing. */
export interface ExtractedValues {
  city_id: number | null;
  neighborhood: string | null;
  property_type: PropertyType | null;
  usable_area_m2: number | null;
  rooms: number | null;
  floor: number | null;
  total_floors: number | null;
  construction_year: number | null;
  structure: BuildingStructure | null;
  condition: PropertyCondition | null;
  has_balcony: boolean | null;
  has_elevator: boolean | null;
  has_parking: boolean | null;
  asking_price: number | null;
}

export interface ExtractionResult {
  input_source: 'listing_url' | 'listing_text';
  source: ListingSource;
  transaction_type: 'sale' | 'rent' | null;
  monthly_rent: number | null;
  monthly_rent_currency: string | null;
  values: ExtractedValues;
  provenance: Partial<Record<ProvenanceField, 'listing' | 'description'>>;
  notices: string[];
}

export type ExtractionRequest = { url: string } | { text: string };

export interface ConfirmedProperty extends PropertyCharacteristics {
  city: string;
  county: string;
  neighborhood: string;
}

export interface Valuation {
  status: AnalysisStatus;
  estimated_reference_price: number | null;
  estimated_price_per_m2: number | null;
  price_difference_eur: number | null;
  price_difference_pct: number | null;
  price_closeness_pct: number | null;
  model_version: string | null;
  reason: string | null;
}

export interface AnalysisSummary {
  analysis_id: string;
  created_at: string;
  status: AnalysisStatus;
  city: string;
  neighborhood: string;
  property_type: PropertyType;
  rooms: number;
  usable_area_m2: number;
  asking_price: number;
  currency: string;
}

export interface AnalysisDetail {
  analysis_id: string;
  created_at: string;
  input_source: InputSource;
  source: ListingSource | null;
  field_provenance: Partial<Record<ProvenanceField, FieldOrigin>>;
  property: ConfirmedProperty;
  asking_price: number;
  currency: string;
  asking_price_per_m2: number;
  valuation: Valuation;
}

@Injectable({ providedIn: 'root' })
export class AnalysesService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiBaseUrl;

  getSupportedCities(): Observable<City[]> {
    return this.http.get<City[]>(`${this.baseUrl}/cities`);
  }

  /** Proposes property details from a listing link or pasted text. Nothing is saved. */
  extractListing(request: ExtractionRequest): Observable<ExtractionResult> {
    return this.http.post<ExtractionResult>(`${this.baseUrl}/extractions`, request);
  }

  createAnalysis(request: PropertyAnalysisRequest): Observable<AnalysisDetail> {
    return this.http.post<AnalysisDetail>(`${this.baseUrl}/analyses`, request);
  }

  listMyAnalyses(): Observable<AnalysisSummary[]> {
    return this.http.get<AnalysisSummary[]>(`${this.baseUrl}/analyses`);
  }

  getAnalysis(analysisId: string): Observable<AnalysisDetail> {
    return this.http.get<AnalysisDetail>(
      `${this.baseUrl}/analyses/${encodeURIComponent(analysisId)}`,
    );
  }
}

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

export interface PropertyAnalysisRequest extends PropertyCharacteristics {
  city_id: number;
  neighborhood: string;
  asking_price: number;
  currency: 'EUR';
}

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
  input_source: 'manual_entry';
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

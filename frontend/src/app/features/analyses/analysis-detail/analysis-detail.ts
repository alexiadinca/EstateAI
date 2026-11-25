import { CurrencyPipe, DatePipe, DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, input, OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { describeApiError } from '../../../core/api/api-errors';
import { AnalysesService, AnalysisDetail as Analysis } from '../../../core/api/analyses.service';
import {
  amenityLabel,
  CONDITION_LABELS,
  describePriceDifference,
  floorLabel,
  NOT_STATED,
  propertyHeadline,
  STATUS_LABELS,
  STRUCTURE_LABELS,
} from '../../../shared/property-labels';

type DetailState =
  | { status: 'loading' }
  | { status: 'loaded'; analysis: Analysis }
  | { status: 'error'; message: string };

/** One saved analysis, shown exactly as it was stored when it was created. */
@Component({
  selector: 'app-analysis-detail',
  imports: [RouterLink, CurrencyPipe, DatePipe, DecimalPipe],
  templateUrl: './analysis-detail.html',
  styleUrl: './analysis-detail.scss',
})
export class AnalysisDetail implements OnInit {
  private readonly analysesService = inject(AnalysesService);

  /** Route parameter :analysisId. */
  readonly analysisId = input.required<string>();

  protected readonly state = signal<DetailState>({ status: 'loading' });

  protected readonly propertyHeadline = propertyHeadline;
  protected readonly amenityLabel = amenityLabel;
  protected readonly floorLabel = floorLabel;
  protected readonly describePriceDifference = describePriceDifference;
  protected readonly structureLabels = STRUCTURE_LABELS;
  protected readonly conditionLabels = CONDITION_LABELS;
  protected readonly statusLabels = STATUS_LABELS;
  protected readonly notStated = NOT_STATED;

  ngOnInit(): void {
    this.loadAnalysis();
  }

  protected loadAnalysis(): void {
    this.state.set({ status: 'loading' });
    this.analysesService.getAnalysis(this.analysisId()).subscribe({
      next: (analysis) => this.state.set({ status: 'loaded', analysis }),
      error: (error: HttpErrorResponse) =>
        this.state.set({
          status: 'error',
          message:
            error.status === 404
              ? 'This analysis was not found in your account.'
              : describeApiError(error),
        }),
    });
  }
}

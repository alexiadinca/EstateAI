import { CurrencyPipe, DatePipe, DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { describeApiError } from '../../../core/api/api-errors';
import { AnalysesService, AnalysisSummary } from '../../../core/api/analyses.service';
import { propertyHeadline, STATUS_LABELS } from '../../../shared/property-labels';

type ListState =
  | { status: 'loading' }
  | { status: 'loaded'; analyses: AnalysisSummary[] }
  | { status: 'error'; message: string };

@Component({
  selector: 'app-my-analyses',
  imports: [RouterLink, CurrencyPipe, DatePipe, DecimalPipe],
  templateUrl: './my-analyses.html',
  styleUrl: './my-analyses.scss',
})
export class MyAnalyses {
  private readonly analysesService = inject(AnalysesService);

  protected readonly state = signal<ListState>({ status: 'loading' });
  protected readonly statusLabels = STATUS_LABELS;
  protected readonly propertyHeadline = propertyHeadline;

  constructor() {
    this.loadAnalyses();
  }

  protected loadAnalyses(): void {
    this.state.set({ status: 'loading' });
    this.analysesService.listMyAnalyses().subscribe({
      next: (analyses) => this.state.set({ status: 'loaded', analyses }),
      // A failed request is shown as an error, never as an empty workspace.
      error: (error: HttpErrorResponse) =>
        this.state.set({ status: 'error', message: describeApiError(error) }),
    });
  }
}

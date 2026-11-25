import { CurrencyPipe, DatePipe, DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';

import { describeApiError } from '../../../core/api/api-errors';
import { AnalysesService, AnalysisSummary } from '../../../core/api/analyses.service';
import { LiveUpdates } from '../../../core/live/live-updates';
import { propertyHeadline, STATUS_LABELS } from '../../../shared/property-labels';

type ListState =
  | { status: 'loading' }
  | { status: 'loaded'; analyses: AnalysisSummary[]; loadedAt: Date }
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
  /** Set when an automatic refresh failed while an earlier list is still on screen. */
  protected readonly refreshFailed = signal(false);
  protected readonly statusLabels = STATUS_LABELS;
  protected readonly propertyHeadline = propertyHeadline;

  private pendingRequest: Subscription | null = null;

  constructor() {
    this.loadAnalyses();
    inject(LiveUpdates)
      .refreshTriggers('analyses')
      .pipe(takeUntilDestroyed())
      .subscribe(() => this.refreshInBackground());
  }

  /** First load and "Try again": shows the loading state. */
  protected loadAnalyses(): void {
    this.state.set({ status: 'loading' });
    this.fetchAnalyses();
  }

  /** Automatic refresh: the current list stays on screen until the new one arrives. */
  private refreshInBackground(): void {
    const requestInProgress = this.pendingRequest !== null && !this.pendingRequest.closed;
    if (this.state().status === 'loading' || requestInProgress) {
      return;
    }
    this.fetchAnalyses();
  }

  private fetchAnalyses(): void {
    this.pendingRequest?.unsubscribe();
    this.pendingRequest = this.analysesService.listMyAnalyses().subscribe({
      next: (analyses) => {
        this.refreshFailed.set(false);
        this.state.set({ status: 'loaded', analyses, loadedAt: new Date() });
      },
      error: (error: HttpErrorResponse) => {
        if (this.state().status === 'loaded') {
          // Keep the list the user is reading and say that it may be out of date.
          this.refreshFailed.set(true);
        } else {
          // A failed request is shown as an error, never as an empty workspace.
          this.state.set({ status: 'error', message: describeApiError(error) });
        }
      },
    });
  }
}

import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { Observable, of, Subject, throwError } from 'rxjs';

import { AnalysesService, AnalysisSummary } from '../../../core/api/analyses.service';
import { LiveUpdates } from '../../../core/live/live-updates';
import { MyAnalyses } from './my-analyses';

function summary(analysisId: string): AnalysisSummary {
  return {
    analysis_id: analysisId,
    created_at: '2026-11-25T10:00:00Z',
    status: 'unavailable',
    city: 'Craiova',
    neighborhood: 'Rogerius',
    property_type: 'apartment',
    usable_area_m2: 54,
    rooms: 2,
    asking_price: 92000,
    currency: 'EUR',
  };
}

function renderList(responses: Observable<AnalysisSummary[]>[]) {
  const refresh = new Subject<void>();
  TestBed.configureTestingModule({
    imports: [MyAnalyses],
    providers: [
      provideRouter([]),
      { provide: AnalysesService, useValue: { listMyAnalyses: () => responses.shift()! } },
      { provide: LiveUpdates, useValue: { refreshTriggers: () => refresh } },
    ],
  });
  const fixture = TestBed.createComponent(MyAnalyses);
  fixture.detectChanges();
  const page = fixture.nativeElement as HTMLElement;
  return {
    page,
    rows: () => page.querySelectorAll('.analysis-row').length,
    refreshNow: () => {
      refresh.next();
      fixture.detectChanges();
    },
  };
}

describe('MyAnalyses live updates', () => {
  it('shows an analysis saved elsewhere without a manual reload', () => {
    const list = renderList([of([summary('a')]), of([summary('b'), summary('a')])]);
    expect(list.rows()).toBe(1);

    list.refreshNow();

    expect(list.rows()).toBe(2);
  });

  it('keeps the list on screen and says so when an automatic refresh fails', () => {
    const failure = throwError(() => new HttpErrorResponse({ status: 0 }));
    const list = renderList([of([summary('a')]), failure]);

    list.refreshNow();

    expect(list.rows()).toBe(1);
    expect(list.page.querySelector('.alert--notice')?.textContent).toContain(
      'could not be updated automatically',
    );
  });

  it('recovers from a failed first load on the next automatic refresh', () => {
    const failure = throwError(() => new HttpErrorResponse({ status: 0 }));
    const list = renderList([failure, of([summary('a')])]);
    expect(list.page.querySelector('.alert--error')).not.toBeNull();

    list.refreshNow();

    expect(list.page.querySelector('.alert--error')).toBeNull();
    expect(list.rows()).toBe(1);
  });
});

import { DestroyRef, inject, Injectable } from '@angular/core';
import { auditTime, EMPTY, filter, fromEvent, interval, map, merge, Observable } from 'rxjs';

/** Kinds of data a page can display and keep up to date. */
export type DataTopic = 'analyses';

/** Browser channel shared by the EstateAI tabs of one browser. */
export const DATA_CHANGES_CHANNEL = 'estateai.data-changes';

/** How often a visible page checks for changes made on another device. */
export const BACKGROUND_REFRESH_INTERVAL_MS = 30_000;

/** Window focus and visibility events often arrive together; they cause a single refresh. */
const TRIGGER_COALESCE_MS = 300;

/**
 * Tells pages when their data may have changed, so they can refresh without a manual reload:
 * - immediately, when another EstateAI tab in this browser saves a change;
 * - when the user returns to the tab or window;
 * - every 30 seconds while the page is visible, for changes made on another device.
 *
 * Messages between tabs contain only the topic name, never user data.
 */
@Injectable({ providedIn: 'root' })
export class LiveUpdates {
  private readonly channel =
    typeof BroadcastChannel === 'undefined' ? null : new BroadcastChannel(DATA_CHANGES_CHANNEL);

  constructor() {
    inject(DestroyRef).onDestroy(() => this.channel?.close());
  }

  /** Called after this tab saved a change, so that other open tabs refresh at once. */
  announceChange(topic: DataTopic): void {
    this.channel?.postMessage(topic);
  }

  /** Emits each time a page showing this topic should fetch it again. */
  refreshTriggers(topic: DataTopic): Observable<void> {
    const changedInAnotherTab = this.channel
      ? fromEvent<MessageEvent>(this.channel, 'message').pipe(
          filter((event) => event.data === topic),
        )
      : EMPTY;
    const userReturned = merge(fromEvent(window, 'focus'), fromEvent(document, 'visibilitychange'));
    const periodicCheck = interval(BACKGROUND_REFRESH_INTERVAL_MS);

    return merge(changedInAnotherTab, userReturned, periodicCheck).pipe(
      // A hidden tab does not poll; it refreshes when the user comes back to it.
      filter(() => document.visibilityState === 'visible'),
      auditTime(TRIGGER_COALESCE_MS),
      map(() => undefined),
    );
  }
}

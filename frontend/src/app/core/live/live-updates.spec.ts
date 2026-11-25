import { TestBed } from '@angular/core/testing';
import { Subscription } from 'rxjs';

import { DATA_CHANGES_CHANNEL, LiveUpdates } from './live-updates';

const COALESCE_WAIT_MS = 400;

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

describe('LiveUpdates', () => {
  let liveUpdates: LiveUpdates;
  let subscription: Subscription | undefined;
  let triggers: number;

  beforeEach(() => {
    liveUpdates = TestBed.inject(LiveUpdates);
    triggers = 0;
    subscription = liveUpdates.refreshTriggers('analyses').subscribe(() => triggers++);
  });

  afterEach(() => subscription?.unsubscribe());

  it('asks for a refresh when the user returns to the window', async () => {
    window.dispatchEvent(new Event('focus'));
    await wait(COALESCE_WAIT_MS);

    expect(triggers).toBe(1);
  });

  it('refreshes once when focus and visibility events arrive together', async () => {
    window.dispatchEvent(new Event('focus'));
    document.dispatchEvent(new Event('visibilitychange'));
    await wait(COALESCE_WAIT_MS);

    expect(triggers).toBe(1);
  });

  it('refreshes when another tab announces a change to the same data', async () => {
    const otherTab = new BroadcastChannel(DATA_CHANGES_CHANNEL);
    otherTab.postMessage('analyses');
    otherTab.postMessage('something-else');
    await wait(COALESCE_WAIT_MS);
    otherTab.close();

    expect(triggers).toBe(1);
  });

  it('tells other tabs about a change made in this tab, without any user data', async () => {
    const otherTab = new BroadcastChannel(DATA_CHANGES_CHANNEL);
    const received: unknown[] = [];
    otherTab.onmessage = (event) => received.push(event.data);

    liveUpdates.announceChange('analyses');
    await wait(50);
    otherTab.close();

    expect(received).toEqual(['analyses']);
  });
});

import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';
import { Home, START_ANALYSIS_URL } from './home';
import { INTRO_PLAYED_KEY, shouldPlayIntro } from './intro-splash';

function renderHome(signedIn: boolean): HTMLElement {
  // The intro is covered by its own tests; here it is marked as already played.
  sessionStorage.setItem(INTRO_PLAYED_KEY, 'true');
  TestBed.configureTestingModule({
    imports: [Home],
    providers: [
      provideRouter([]),
      { provide: AuthService, useValue: { isSignedIn: signal(signedIn) } },
    ],
  });
  const fixture = TestBed.createComponent(Home);
  fixture.detectChanges();
  return fixture.nativeElement as HTMLElement;
}

function linkByText(page: HTMLElement, text: string): HTMLAnchorElement | undefined {
  return [...page.querySelectorAll('a')].find((link) => link.textContent?.trim() === text);
}

describe('Home', () => {
  afterEach(() => sessionStorage.clear());

  it('sends a visitor towards Analyze a property, which asks for sign-in first', () => {
    const page = renderHome(false);

    expect(linkByText(page, 'Start analyzing')?.getAttribute('href')).toBe(START_ANALYSIS_URL);
    expect(linkByText(page, 'Create an account')?.getAttribute('href')).toBe(
      '/register?returnUrl=%2Fanalyses%2Fnew',
    );
    expect(page.textContent).toContain('You will be asked to sign in');
  });

  it('offers a signed-in user Analyze a property and their saved analyses', () => {
    const page = renderHome(true);

    expect(linkByText(page, 'Start analyzing')?.getAttribute('href')).toBe(START_ANALYSIS_URL);
    expect(linkByText(page, 'My analyses')?.getAttribute('href')).toBe('/analyses');
    expect(linkByText(page, 'Create an account')).toBeUndefined();
  });

  it('shows the six tutorial steps in order', () => {
    const page = renderHome(false);

    const titles = [...page.querySelectorAll('.steps__title')].map((title) => title.textContent);
    expect(titles).toHaveLength(6);
    expect(titles[0]).toBe('Sign in or create an account');
    expect(titles[5]).toBe('Come back at any time');
  });

  it('labels the example figures as illustrative, not a live estimate', () => {
    const page = renderHome(false);

    expect(page.querySelector('.preview__badge')?.textContent).toBe('Illustrative example');
    expect(page.querySelector('.preview__caption')?.textContent).toContain('not a live');
  });

  it('does not show the opening animation once it has played in this tab', () => {
    const page = renderHome(false);

    expect(page.querySelector('app-intro-splash')).toBeNull();
  });
});

describe('shouldPlayIntro', () => {
  const originalMatchMedia = window.matchMedia;

  function preferReducedMotion(reduce: boolean): void {
    window.matchMedia = ((query: string) => ({ matches: reduce, media: query })) as never;
  }

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
    sessionStorage.clear();
  });

  it('plays on the first visit in a tab', () => {
    preferReducedMotion(false);

    expect(shouldPlayIntro()).toBe(true);
  });

  it('does not play again in the same tab', () => {
    preferReducedMotion(false);
    sessionStorage.setItem(INTRO_PLAYED_KEY, 'true');

    expect(shouldPlayIntro()).toBe(false);
  });

  it('never plays when the visitor asks to reduce motion', () => {
    preferReducedMotion(true);

    expect(shouldPlayIntro()).toBe(false);
  });
});

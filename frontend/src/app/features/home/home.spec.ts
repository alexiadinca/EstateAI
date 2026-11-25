import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';
import { Home, START_ANALYSIS_URL } from './home';
import { isFirstPageLoad, shouldPlayIntro } from './intro-splash';

// Components created by TestBed are not part of a navigation, so the intro does not play here.
function renderHome(signedIn: boolean): HTMLElement {
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

  it('does not show the opening animation when reached from inside the application', () => {
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
  });

  it('plays every time the home page is loaded or refreshed', () => {
    preferReducedMotion(false);

    expect(shouldPlayIntro(true)).toBe(true);
  });

  it('does not play after a navigation inside the application', () => {
    preferReducedMotion(false);

    expect(shouldPlayIntro(false)).toBe(false);
  });

  it('never plays when the visitor asks to reduce motion', () => {
    preferReducedMotion(true);

    expect(shouldPlayIntro(true)).toBe(false);
  });
});

describe('isFirstPageLoad', () => {
  function routerDuring(navigation: unknown): Router {
    return { currentNavigation: signal(navigation) } as unknown as Router;
  }

  it('recognises the first navigation after a page load or refresh', () => {
    expect(isFirstPageLoad(routerDuring({ previousNavigation: null }))).toBe(true);
  });

  it('recognises a later navigation, such as a click on the logo', () => {
    expect(isFirstPageLoad(routerDuring({ previousNavigation: {} }))).toBe(false);
  });

  it('is false outside a navigation', () => {
    expect(isFirstPageLoad(routerDuring(null))).toBe(false);
  });
});

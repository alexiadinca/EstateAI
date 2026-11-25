import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';

import { App } from './app';
import { requireSignIn } from './core/auth/auth.guards';
import { AuthService } from './core/auth/auth.service';

function renderShell(signedIn: boolean): HTMLElement {
  TestBed.configureTestingModule({
    imports: [App],
    providers: [
      provideRouter([]),
      {
        provide: AuthService,
        useValue: {
          isSignedIn: signal(signedIn),
          userEmail: signal(signedIn ? 'demo1@estateai.test' : null),
          signOut: async () => undefined,
        },
      },
    ],
  });
  const fixture = TestBed.createComponent(App);
  fixture.detectChanges();
  return fixture.nativeElement as HTMLElement;
}

describe('App shell', () => {
  it('shows the EstateAI wordmark in the header and footer', () => {
    const page = renderShell(false);

    expect(page.querySelector('.site-header .wordmark')?.textContent).toContain('EstateAI');
    expect(page.querySelector('.site-footer')?.textContent).toContain('EstateAI');
  });

  it('links the wordmark to the home page', () => {
    const page = renderShell(true);

    expect(page.querySelector('.site-header .wordmark')?.getAttribute('href')).toBe('/');
  });

  it('shows sign-in and registration links instead of sign-out for visitors', () => {
    const page = renderShell(false);

    expect(page.querySelector('.session__sign-out')).toBeNull();
    expect(page.querySelector('.session__link')?.getAttribute('href')).toBe('/sign-in');
    expect(page.querySelector('.session__register')?.getAttribute('href')).toBe('/register');
  });

  it('shows navigation, the signed-in email and a sign-out button', () => {
    const page = renderShell(true);

    expect(page.querySelector('.site-nav__link')?.textContent).toContain('My analyses');
    expect(page.querySelector('.session__account')?.textContent).toContain('demo1@estateai.test');
    expect(page.querySelector('.session__sign-out')).not.toBeNull();
  });

  it('leaves a private page when the session ends, for example in another tab', async () => {
    const signedIn = signal(true);
    TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideRouter([
          { path: '', children: [] },
          { path: 'analyses', canActivate: [requireSignIn], children: [] },
        ]),
        {
          provide: AuthService,
          useValue: {
            ready: Promise.resolve(),
            isSignedIn: signedIn,
            userEmail: signal('demo1@estateai.test'),
          },
        },
      ],
    });
    const fixture = TestBed.createComponent(App);
    const router = TestBed.inject(Router);
    await router.navigateByUrl('/analyses');
    await fixture.whenStable();
    expect(router.url).toBe('/analyses');

    signedIn.set(false);
    await fixture.whenStable();

    expect(router.url).toBe('/');
  });

  it('makes the header translucent from the first scroll', async () => {
    TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideRouter([]),
        {
          provide: AuthService,
          useValue: { isSignedIn: signal(false), userEmail: signal(null), signOut: async () => {} },
        },
      ],
    });
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const header = (fixture.nativeElement as HTMLElement).querySelector('.site-header')!;
    expect(header.classList).not.toContain('site-header--scrolled');

    Object.defineProperty(window, 'scrollY', { value: 1, configurable: true });
    window.dispatchEvent(new Event('scroll'));
    await fixture.whenStable();

    expect(header.classList).toContain('site-header--scrolled');
    Object.defineProperty(window, 'scrollY', { value: 0, configurable: true });
  });
});

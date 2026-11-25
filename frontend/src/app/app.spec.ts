import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { App } from './app';
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

  it('hides the sign-out button for visitors', () => {
    const page = renderShell(false);

    expect(page.querySelector('.session__sign-out')).toBeNull();
  });

  it('shows navigation, the signed-in email and a sign-out button', () => {
    const page = renderShell(true);

    expect(page.querySelector('.site-nav__link')?.textContent).toContain('My analyses');
    expect(page.querySelector('.session__account')?.textContent).toContain('demo1@estateai.test');
    expect(page.querySelector('.session__sign-out')).not.toBeNull();
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

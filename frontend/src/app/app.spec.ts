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

  it('shows the signed-in email and a sign-out button', () => {
    const page = renderShell(true);

    expect(page.querySelector('.session__email')?.textContent).toContain('demo1@estateai.test');
    expect(page.querySelector('.session__sign-out')).not.toBeNull();
  });
});

import { TestBed } from '@angular/core/testing';
import {
  ActivatedRouteSnapshot,
  provideRouter,
  Router,
  RouterStateSnapshot,
  UrlTree,
} from '@angular/router';

import { redirectSignedInUser, requireSignIn, safeReturnUrl, SIGNED_IN_HOME } from './auth.guards';
import { AuthService } from './auth.service';

function runGuard(guard: typeof requireSignIn, signedIn: boolean, url = '/account') {
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      { provide: AuthService, useValue: { ready: Promise.resolve(), isSignedIn: () => signedIn } },
    ],
  });
  return TestBed.runInInjectionContext(() =>
    guard({} as ActivatedRouteSnapshot, { url } as RouterStateSnapshot),
  ) as Promise<boolean | UrlTree>;
}

describe('requireSignIn', () => {
  it('allows a signed-in user', async () => {
    expect(await runGuard(requireSignIn, true)).toBe(true);
  });

  it('sends a visitor to sign-in and remembers the requested page', async () => {
    const result = await runGuard(requireSignIn, false, '/account');

    const router = TestBed.inject(Router);
    expect(router.serializeUrl(result as UrlTree)).toBe('/sign-in?returnUrl=%2Faccount');
  });
});

describe('redirectSignedInUser', () => {
  it('sends a signed-in user to the home page instead of the sign-in form', async () => {
    const result = await runGuard(redirectSignedInUser, true);

    expect(TestBed.inject(Router).serializeUrl(result as UrlTree)).toBe(SIGNED_IN_HOME);
  });

  it('lets a visitor open the sign-in form', async () => {
    expect(await runGuard(redirectSignedInUser, false)).toBe(true);
  });
});

describe('safeReturnUrl', () => {
  it('keeps a path inside the application', () => {
    expect(safeReturnUrl('/account')).toBe('/account');
  });

  it.each([null, '', 'https://example.com', '//example.com', 'javascript:alert(1)'])(
    'replaces the unsafe or missing value %s with the home page',
    (returnUrl) => {
      expect(safeReturnUrl(returnUrl)).toBe(SIGNED_IN_HOME);
    },
  );
});

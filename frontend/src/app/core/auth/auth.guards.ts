import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

export const SIGNED_IN_HOME = '/account';

/** Allows a route only for signed-in users; others are sent to sign-in and brought back after. */
export const requireSignIn: CanActivateFn = async (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);

  await auth.ready;
  if (auth.isSignedIn()) {
    return true;
  }
  return router.createUrlTree(['/sign-in'], { queryParams: { returnUrl: state.url } });
};

/** Keeps signed-in users away from the sign-in and registration pages. */
export const redirectSignedInUser: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  await auth.ready;
  return auth.isSignedIn() ? router.parseUrl(SIGNED_IN_HOME) : true;
};

/**
 * Accepts only paths inside this application, so a crafted link such as
 * /sign-in?returnUrl=https://example.com cannot redirect the user to another website.
 */
export function safeReturnUrl(returnUrl: string | null): string {
  if (returnUrl && returnUrl.startsWith('/') && !returnUrl.startsWith('//')) {
    return returnUrl;
  }
  return SIGNED_IN_HOME;
}

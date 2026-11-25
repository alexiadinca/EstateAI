import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { from, switchMap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';

export function isApiRequest(url: string): boolean {
  return url === environment.apiBaseUrl || url.startsWith(`${environment.apiBaseUrl}/`);
}

/**
 * Adds the Supabase access token to requests sent to the EstateAI API.
 * Requests to any other address never receive the token.
 */
export const attachAccessToken: HttpInterceptorFn = (request, next) => {
  if (!isApiRequest(request.url)) {
    return next(request);
  }

  const auth = inject(AuthService);
  return from(auth.getAccessToken()).pipe(
    switchMap((accessToken) =>
      next(
        accessToken
          ? request.clone({ setHeaders: { Authorization: `Bearer ${accessToken}` } })
          : request,
      ),
    ),
  );
};

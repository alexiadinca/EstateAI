import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { attachAccessToken } from './auth.interceptor';
import { AuthService } from './auth.service';

function setUp(accessToken: string | null) {
  TestBed.configureTestingModule({
    providers: [
      provideHttpClient(withInterceptors([attachAccessToken])),
      provideHttpClientTesting(),
      { provide: AuthService, useValue: { getAccessToken: async () => accessToken } },
    ],
  });
  return {
    http: TestBed.inject(HttpClient),
    backend: TestBed.inject(HttpTestingController),
  };
}

/** The token is read asynchronously, so the request is sent after pending promises settle. */
const settle = () => new Promise((resolve) => setTimeout(resolve));

describe('attachAccessToken', () => {
  it('adds the bearer token to EstateAI API requests', async () => {
    const { http, backend } = setUp('token-123');

    http.get(`${environment.apiBaseUrl}/me`).subscribe();
    await settle();

    const request = backend.expectOne(`${environment.apiBaseUrl}/me`);
    expect(request.request.headers.get('Authorization')).toBe('Bearer token-123');
    backend.verify();
  });

  it('never sends the token to other websites', async () => {
    const { http, backend } = setUp('token-123');

    http.get('https://example.com/data').subscribe();
    http.get(`${environment.apiBaseUrl}.example.com/me`).subscribe();
    await settle();

    expect(backend.expectOne('https://example.com/data').request.headers.has('Authorization')).toBe(
      false,
    );
    expect(
      backend
        .expectOne(`${environment.apiBaseUrl}.example.com/me`)
        .request.headers.has('Authorization'),
    ).toBe(false);
    backend.verify();
  });

  it('sends the request without a token when nobody is signed in', async () => {
    const { http, backend } = setUp(null);

    http.get(`${environment.apiBaseUrl}/me`).subscribe();
    await settle();

    expect(
      backend.expectOne(`${environment.apiBaseUrl}/me`).request.headers.has('Authorization'),
    ).toBe(false);
    backend.verify();
  });
});

import { HttpErrorResponse } from '@angular/common/http';

/** Turns a failed API request into a message that explains what the user can do next. */
export function describeApiError(error: HttpErrorResponse): string {
  if (error.status === 0) {
    return 'The EstateAI service cannot be reached. Check that the backend is running and try again.';
  }
  if (error.status === 401) {
    return 'Your session has expired. Sign in again to continue.';
  }
  const detail: unknown = error.error?.detail;
  if (error.status === 503 && typeof detail === 'string') {
    return detail;
  }
  return 'Something went wrong while loading your data. Try again.';
}

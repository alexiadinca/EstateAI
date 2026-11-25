/**
 * Translation of Supabase Auth error codes into messages a user can act on.
 * Raw provider messages are not shown, because they can be technical or inconsistent.
 */

/** An authentication operation failed with a message that is safe to display. */
export class AuthFailure extends Error {}

interface ErrorWithCode {
  code?: string;
  message: string;
}

export function describeSignInError(error: ErrorWithCode): string {
  switch (error.code) {
    case 'invalid_credentials':
      return 'The email or password is incorrect.';
    case 'email_not_confirmed':
      return 'Confirm your email address before signing in. Check your inbox for the confirmation link.';
    case 'over_request_rate_limit':
      return 'Too many attempts. Wait a moment and try again.';
    default:
      return 'Sign-in failed. Check your connection and try again.';
  }
}

export function describeRegistrationError(error: ErrorWithCode): string {
  switch (error.code) {
    case 'user_already_exists':
    case 'email_exists':
      return 'An account with this email already exists. Sign in instead.';
    case 'weak_password':
      return 'This password is too weak. Use at least 8 characters, including letters and digits.';
    case 'email_address_invalid':
      return 'Enter a valid email address.';
    case 'email_address_not_authorized':
      return 'A confirmation email cannot be sent to this address yet. Contact the EstateAI team.';
    case 'over_email_send_rate_limit':
      return 'Too many confirmation emails were sent recently. Try again later.';
    case 'signup_disabled':
      return 'Registration is currently disabled.';
    default:
      return 'Registration failed. Check your connection and try again.';
  }
}

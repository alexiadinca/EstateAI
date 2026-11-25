import { describeRegistrationError, describeSignInError } from './auth-errors';

describe('describeSignInError', () => {
  it('explains wrong credentials without revealing which field was wrong', () => {
    expect(describeSignInError({ code: 'invalid_credentials', message: 'raw' })).toBe(
      'The email or password is incorrect.',
    );
  });

  it('uses a general message for unknown errors instead of the raw provider text', () => {
    expect(describeSignInError({ code: 'unexpected', message: 'internal detail' })).not.toContain(
      'internal detail',
    );
  });
});

describe('describeRegistrationError', () => {
  it('suggests signing in when the email is already registered', () => {
    expect(describeRegistrationError({ code: 'user_already_exists', message: 'raw' })).toContain(
      'Sign in instead',
    );
  });
});

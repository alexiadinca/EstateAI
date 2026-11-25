import { FormControl, FormGroup } from '@angular/forms';

import { containsLetterAndDigit, notBlank, passwordsMatch } from './validators';

describe('notBlank', () => {
  it('rejects a value made only of spaces', () => {
    expect(notBlank(new FormControl('   '))).toEqual({ blank: true });
  });

  it('accepts a real name', () => {
    expect(notBlank(new FormControl('Ana'))).toBeNull();
  });
});

describe('containsLetterAndDigit', () => {
  it.each(['onlyletters', '12345678'])('rejects %s', (password) => {
    expect(containsLetterAndDigit(new FormControl(password))).toEqual({ letterAndDigit: true });
  });

  it('accepts letters combined with digits', () => {
    expect(containsLetterAndDigit(new FormControl('craiova2026'))).toBeNull();
  });
});

describe('passwordsMatch', () => {
  const validator = passwordsMatch('password', 'confirmPassword');

  it('reports a mismatch', () => {
    const group = new FormGroup({
      password: new FormControl('craiova2026'),
      confirmPassword: new FormControl('craiova2025'),
    });

    expect(validator(group)).toEqual({ passwordMismatch: true });
  });

  it('accepts identical passwords', () => {
    const group = new FormGroup({
      password: new FormControl('craiova2026'),
      confirmPassword: new FormControl('craiova2026'),
    });

    expect(validator(group)).toBeNull();
  });
});

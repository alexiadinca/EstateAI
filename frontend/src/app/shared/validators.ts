import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

/** Rejects values that contain only spaces, which Validators.required accepts. */
export const notBlank: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
  const value = control.value;
  return typeof value === 'string' && value.trim().length === 0 ? { blank: true } : null;
};

/** Requires at least one letter and one digit. */
export const containsLetterAndDigit: ValidatorFn = (
  control: AbstractControl,
): ValidationErrors | null => {
  const value = String(control.value ?? '');
  if (value === '') {
    return null;
  }
  return /[A-Za-z]/.test(value) && /\d/.test(value) ? null : { letterAndDigit: true };
};

/** Group validator: the password confirmation must match the password. */
export function passwordsMatch(passwordKey: string, confirmationKey: string): ValidatorFn {
  return (group: AbstractControl): ValidationErrors | null => {
    const password = group.get(passwordKey)?.value;
    const confirmation = group.get(confirmationKey)?.value;
    if (!confirmation) {
      return null;
    }
    return password === confirmation ? null : { passwordMismatch: true };
  };
}

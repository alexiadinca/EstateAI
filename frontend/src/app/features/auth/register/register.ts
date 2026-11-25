import { Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthFailure } from '../../../core/auth/auth-errors';
import { SIGNED_IN_HOME } from '../../../core/auth/auth.guards';
import { AuthService } from '../../../core/auth/auth.service';
import { containsLetterAndDigit, notBlank, passwordsMatch } from '../../../shared/validators';

export const MINIMUM_PASSWORD_LENGTH = 8;
const NAME_MAX_LENGTH = 100;

type RegisterField = 'firstName' | 'lastName' | 'email' | 'password' | 'confirmPassword';

@Component({
  selector: 'app-register',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './register.html',
  styleUrl: '../auth-page.scss',
})
export class Register {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  protected readonly minimumPasswordLength = MINIMUM_PASSWORD_LENGTH;

  // First and last name are required for every EstateAI account.
  protected readonly form = inject(NonNullableFormBuilder).group(
    {
      firstName: ['', [Validators.required, notBlank, Validators.maxLength(NAME_MAX_LENGTH)]],
      lastName: ['', [Validators.required, notBlank, Validators.maxLength(NAME_MAX_LENGTH)]],
      email: ['', [Validators.required, Validators.email]],
      password: [
        '',
        [
          Validators.required,
          Validators.minLength(MINIMUM_PASSWORD_LENGTH),
          containsLetterAndDigit,
        ],
      ],
      confirmPassword: ['', [Validators.required]],
    },
    { validators: passwordsMatch('password', 'confirmPassword') },
  );

  protected readonly submitted = signal(false);
  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal<string | null>(null);
  /** Set when Supabase requires the user to confirm the email address before signing in. */
  protected readonly confirmationSentTo = signal<string | null>(null);

  protected showError(controlName: RegisterField): boolean {
    const control = this.form.controls[controlName];
    const wasVisited = control.touched || this.submitted();
    if (controlName === 'confirmPassword') {
      return wasVisited && (control.invalid || this.form.hasError('passwordMismatch'));
    }
    return wasVisited && control.invalid;
  }

  protected async submit(): Promise<void> {
    this.submitted.set(true);
    this.errorMessage.set(null);
    if (this.form.invalid || this.submitting()) {
      return;
    }

    this.submitting.set(true);
    const { firstName, lastName, email, password } = this.form.getRawValue();
    try {
      const outcome = await this.auth.register({
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        email: email.trim(),
        password,
      });
      if (outcome === 'signed-in') {
        await this.router.navigateByUrl(SIGNED_IN_HOME);
      } else {
        this.confirmationSentTo.set(email.trim());
      }
    } catch (error) {
      this.errorMessage.set(
        error instanceof AuthFailure ? error.message : 'Registration failed. Try again.',
      );
    } finally {
      this.submitting.set(false);
    }
  }
}

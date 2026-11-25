import { Component, inject, input, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthFailure } from '../../../core/auth/auth-errors';
import { safeReturnUrl } from '../../../core/auth/auth.guards';
import { AuthService } from '../../../core/auth/auth.service';

@Component({
  selector: 'app-sign-in',
  imports: [ReactiveFormsModule, RouterLink],
  templateUrl: './sign-in.html',
  styleUrl: '../auth-page.scss',
})
export class SignIn {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  /** Page the user tried to open before being asked to sign in (from the query string). */
  readonly returnUrl = input<string | null>(null);

  protected readonly form = inject(NonNullableFormBuilder).group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required]],
  });

  protected readonly submitted = signal(false);
  protected readonly submitting = signal(false);
  protected readonly errorMessage = signal<string | null>(null);

  protected showError(controlName: 'email' | 'password'): boolean {
    const control = this.form.controls[controlName];
    return control.invalid && (control.touched || this.submitted());
  }

  protected async submit(): Promise<void> {
    this.submitted.set(true);
    this.errorMessage.set(null);
    if (this.form.invalid || this.submitting()) {
      return;
    }

    this.submitting.set(true);
    const { email, password } = this.form.getRawValue();
    try {
      await this.auth.signIn(email.trim(), password);
      await this.router.navigateByUrl(safeReturnUrl(this.returnUrl()));
    } catch (error) {
      this.errorMessage.set(
        error instanceof AuthFailure ? error.message : 'Sign-in failed. Try again.',
      );
    } finally {
      this.submitting.set(false);
    }
  }
}

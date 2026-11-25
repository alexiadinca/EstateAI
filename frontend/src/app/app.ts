import { Component, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterOutlet } from '@angular/router';

import { AuthFailure } from './core/auth/auth-errors';
import { SIGNED_IN_HOME } from './core/auth/auth.guards';
import { AuthService } from './core/auth/auth.service';

/** Application shell: espresso header, page content and footer. */
@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly router = inject(Router);
  protected readonly auth = inject(AuthService);

  protected readonly signedInHome = SIGNED_IN_HOME;
  protected readonly signOutError = signal<string | null>(null);

  protected async signOut(): Promise<void> {
    this.signOutError.set(null);
    try {
      await this.auth.signOut();
      await this.router.navigateByUrl('/sign-in');
    } catch (error) {
      this.signOutError.set(
        error instanceof AuthFailure ? error.message : 'Sign-out failed. Try again.',
      );
    }
  }
}

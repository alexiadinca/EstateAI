import { afterNextRender, Component, DestroyRef, effect, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { AuthFailure } from './core/auth/auth-errors';
import { isOnProtectedPage } from './core/auth/auth.guards';
import { AuthService } from './core/auth/auth.service';

/** Application shell: espresso header, page content and footer. */
@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly router = inject(Router);
  protected readonly auth = inject(AuthService);

  protected readonly signOutError = signal<string | null>(null);
  /** True as soon as the page is scrolled, which makes the header translucent. */
  protected readonly scrolled = signal(false);

  constructor() {
    // Supabase shares the session between tabs. When it ends here or in another tab, or can no
    // longer be refreshed, a private page must not stay on screen with the previous data.
    let wasSignedIn = false;
    effect(() => {
      const signedIn = this.auth.isSignedIn();
      if (wasSignedIn && !signedIn && isOnProtectedPage(this.router)) {
        void this.router.navigateByUrl('/');
      }
      wasSignedIn = signedIn;
    });

    const destroyRef = inject(DestroyRef);
    afterNextRender(() => {
      const updateScrolled = () => this.scrolled.set(window.scrollY > 0);
      updateScrolled();
      window.addEventListener('scroll', updateScrolled, { passive: true });
      destroyRef.onDestroy(() => window.removeEventListener('scroll', updateScrolled));
    });
  }

  protected async signOut(): Promise<void> {
    this.signOutError.set(null);
    try {
      await this.auth.signOut();
      await this.router.navigateByUrl('/');
    } catch (error) {
      this.signOutError.set(
        error instanceof AuthFailure ? error.message : 'Sign-out failed. Try again.',
      );
    }
  }
}

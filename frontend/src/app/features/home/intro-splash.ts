import { afterNextRender, Component, DestroyRef, inject, output } from '@angular/core';
import { Router } from '@angular/router';

/** Longest time the animation may stay on screen, in case the browser never reports its end. */
const INTRO_MAX_DURATION_MS = 3200;

/**
 * True while the router performs the first navigation after the page was loaded or refreshed.
 * Later navigations inside the application, such as a click on the logo, have a previous one.
 */
export function isFirstPageLoad(router: Router): boolean {
  const navigation = router.currentNavigation();
  return navigation !== null && navigation.previousNavigation === null;
}

/**
 * The opening animation plays when the home page is loaded or refreshed, and never for
 * visitors who ask their operating system to reduce motion.
 */
export function shouldPlayIntro(firstPageLoad: boolean): boolean {
  if (!firstPageLoad || typeof window === 'undefined') {
    return false;
  }
  return !window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Full-screen opening animation: a house outline with a rising price line is drawn, then the
 * EstateAI wordmark appears and the screen lifts away. A click or any key skips it.
 */
@Component({
  selector: 'app-intro-splash',
  templateUrl: './intro-splash.html',
  styleUrl: './intro-splash.scss',
  host: { '(document:keydown)': 'finish()' },
})
export class IntroSplash {
  /** Emitted once, when the animation has ended or was skipped. */
  readonly finished = output<void>();

  private hasFinished = false;

  constructor() {
    const destroyRef = inject(DestroyRef);
    afterNextRender(() => {
      const fallback = window.setTimeout(() => this.finish(), INTRO_MAX_DURATION_MS);
      destroyRef.onDestroy(() => window.clearTimeout(fallback));
    });
  }

  /** Child animations also bubble animationend, so only the overlay's own exit ends the intro. */
  protected onAnimationEnd(event: AnimationEvent): void {
    if (event.target === event.currentTarget) {
      this.finish();
    }
  }

  protected finish(): void {
    if (!this.hasFinished) {
      this.hasFinished = true;
      this.finished.emit();
    }
  }
}

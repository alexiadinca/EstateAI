import { afterNextRender, Component, DestroyRef, inject, output } from '@angular/core';

/** Session storage key that records that the opening animation already played in this tab. */
export const INTRO_PLAYED_KEY = 'estateai.introPlayed';

/** Longest time the animation may stay on screen, in case the browser never reports its end. */
const INTRO_MAX_DURATION_MS = 3200;

/**
 * The opening animation plays once per browser tab and never for visitors who ask their
 * operating system to reduce motion.
 */
export function shouldPlayIntro(): boolean {
  if (typeof window === 'undefined') {
    return false;
  }
  if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
    return false;
  }
  try {
    return window.sessionStorage.getItem(INTRO_PLAYED_KEY) === null;
  } catch {
    // Storage can be blocked by privacy settings. The animation is short, so it simply plays.
    return true;
  }
}

function rememberIntroPlayed(): void {
  try {
    window.sessionStorage.setItem(INTRO_PLAYED_KEY, 'true');
  } catch {
    // Without storage the animation may play again on the next visit, which is harmless.
  }
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
      rememberIntroPlayed();
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

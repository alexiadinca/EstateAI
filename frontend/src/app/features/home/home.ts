import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthService } from '../../core/auth/auth.service';
import { IntroSplash, shouldPlayIntro } from './intro-splash';

/**
 * Where "Start analyzing" leads. The route requires sign-in, so visitors are sent to the
 * sign-in page first and brought back here afterwards.
 */
export const START_ANALYSIS_URL = '/analyses/new';

interface TutorialStep {
  title: string;
  description: string;
}

interface ProductQuestion {
  question: string;
  answer: string;
  status: string;
}

/** Public landing page: what EstateAI does, how to use it and where to start. */
@Component({
  selector: 'app-home',
  imports: [RouterLink, IntroSplash],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {
  protected readonly auth = inject(AuthService);

  protected readonly startUrl = START_ANALYSIS_URL;
  /** Decided once, so the hero waits for the intro only when the intro actually plays. */
  protected readonly introPlayed = shouldPlayIntro();
  protected readonly introVisible = signal(this.introPlayed);

  // The status lines describe the current prototype and must be updated as features arrive.
  protected readonly questions: readonly ProductQuestion[] = [
    {
      question: 'Is the asking price reasonable?',
      answer:
        'Compare the asking price with a reference price estimated from the characteristics of similar listings.',
      status: 'Valuation model in development',
    },
    {
      question: 'How does it compare with my other options?',
      answer: 'Put the properties you are considering side by side, in the same units.',
      status: 'Planned',
    },
    {
      question: 'What return could it bring?',
      answer:
        'Explore rent, vacancy and expenses to estimate gross and net rental yield at your purchase price.',
      status: 'Planned',
    },
  ];

  protected readonly steps: readonly TutorialStep[] = [
    {
      title: 'Sign in or create an account',
      description: 'Your analyses are private and saved to your account.',
    },
    {
      title: 'Start from a listing or a blank form',
      description:
        'Paste a storia.ro or olx.ro link, or the text of any listing, and EstateAI fills in the details it finds. No listing? Fill in the form yourself.',
    },
    {
      title: 'Check every detail',
      description:
        'Each imported value shows where it came from. Correct anything that is wrong and leave unknown details as not stated.',
    },
    {
      title: 'Review and save',
      description:
        'Confirm the summary. EstateAI saves a snapshot of exactly what you confirmed, together with the date.',
    },
    {
      title: 'Read your analysis',
      description:
        'See the asking price, the price per square metre and every confirmed detail with its source. The reference estimate appears here once the valuation model supports the property.',
    },
    {
      title: 'Come back at any time',
      description:
        'My analyses keeps every saved analysis. Reopening one shows it exactly as it was saved.',
    },
  ];

  protected endIntro(): void {
    this.introVisible.set(false);
  }
}

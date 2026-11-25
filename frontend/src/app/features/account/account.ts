import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';

import { describeApiError } from '../../core/api/api-errors';
import { UserProfile, UserProfileService } from '../../core/api/user-profile.service';

type ProfileState =
  | { status: 'loading' }
  | { status: 'loaded'; profile: UserProfile }
  | { status: 'error'; message: string };

/** First signed-in page: confirms that the frontend, Supabase Auth and FastAPI work together. */
@Component({
  selector: 'app-account',
  imports: [DatePipe],
  templateUrl: './account.html',
  styleUrl: './account.scss',
})
export class Account {
  private readonly profiles = inject(UserProfileService);

  protected readonly state = signal<ProfileState>({ status: 'loading' });

  protected readonly fullName = computed(() => {
    const current = this.state();
    if (current.status !== 'loaded') {
      return null;
    }
    const { first_name, last_name } = current.profile;
    const name = [first_name, last_name].filter(Boolean).join(' ');
    return name || null;
  });

  constructor() {
    this.loadProfile();
  }

  protected loadProfile(): void {
    this.state.set({ status: 'loading' });
    this.profiles.getCurrentProfile().subscribe({
      next: (profile) => this.state.set({ status: 'loaded', profile }),
      error: (error: HttpErrorResponse) =>
        this.state.set({ status: 'error', message: describeApiError(error) }),
    });
  }
}

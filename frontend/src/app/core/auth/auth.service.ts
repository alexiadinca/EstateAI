import { computed, inject, Injectable, signal } from '@angular/core';
import { Session } from '@supabase/supabase-js';

import { SUPABASE_CLIENT } from '../supabase-client';
import { AuthFailure, describeRegistrationError, describeSignInError } from './auth-errors';

export interface RegistrationDetails {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
}

/**
 * signed-in: Supabase created a session immediately (email confirmation is disabled).
 * confirmation-required: the user must open the confirmation link sent by email first.
 */
export type RegistrationOutcome = 'signed-in' | 'confirmation-required';

/** Session state and account operations. Passwords go directly to Supabase, never to FastAPI. */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly supabase = inject(SUPABASE_CLIENT);
  private readonly sessionState = signal<Session | null>(null);

  readonly isSignedIn = computed(() => this.sessionState() !== null);
  readonly userEmail = computed(() => this.sessionState()?.user.email ?? null);

  /** Resolves once a session stored in the browser has been restored after a page load. */
  readonly ready: Promise<void>;

  constructor() {
    this.ready = this.supabase.auth.getSession().then(({ data }) => {
      this.sessionState.set(data.session);
    });
    // Keeps the state current after sign-in, sign-out and automatic token refresh.
    this.supabase.auth.onAuthStateChange((_event, session) => this.sessionState.set(session));
  }

  async signIn(email: string, password: string): Promise<void> {
    const { error } = await this.supabase.auth.signInWithPassword({ email, password });
    if (error) {
      throw new AuthFailure(describeSignInError(error));
    }
  }

  async register(details: RegistrationDetails): Promise<RegistrationOutcome> {
    const { data, error } = await this.supabase.auth.signUp({
      email: details.email,
      password: details.password,
      options: {
        // Stored by Supabase as user_metadata; FastAPI copies the names into user_profile.
        data: { first_name: details.firstName, last_name: details.lastName },
        emailRedirectTo: `${window.location.origin}/sign-in`,
      },
    });
    if (error) {
      throw new AuthFailure(describeRegistrationError(error));
    }
    return data.session ? 'signed-in' : 'confirmation-required';
  }

  async signOut(): Promise<void> {
    const { error } = await this.supabase.auth.signOut();
    if (error) {
      throw new AuthFailure('Sign-out failed. Check your connection and try again.');
    }
  }

  /** Returns a valid access token, refreshing it first if it has expired. */
  async getAccessToken(): Promise<string | null> {
    const { data } = await this.supabase.auth.getSession();
    return data.session?.access_token ?? null;
  }
}

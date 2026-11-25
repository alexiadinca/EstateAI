import { InjectionToken } from '@angular/core';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

import { environment } from '../../environments/environment';

/**
 * The single Supabase client used by the application.
 * Supabase stores the session in the browser, so a signed-in user stays signed in after a refresh.
 * Provided through a token so that tests can replace it with a fake client.
 */
export const SUPABASE_CLIENT = new InjectionToken<SupabaseClient>('SUPABASE_CLIENT', {
  providedIn: 'root',
  factory: () => createClient(environment.supabaseUrl, environment.supabasePublishableKey),
});

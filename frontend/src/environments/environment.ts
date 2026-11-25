/**
 * Frontend configuration for local development.
 *
 * The Supabase project URL and publishable key are designed to be public: they identify the
 * project, while access to data is controlled by FastAPI and the database permissions.
 * Never place the Supabase secret key (sb_secret_...) or the database password in the frontend.
 */
export const environment = {
  apiBaseUrl: 'http://127.0.0.1:8000',
  supabaseUrl: 'https://nhqyqnttynyimjhsxewn.supabase.co',
  supabasePublishableKey: 'sb_publishable_RxMZnNw-XuWz05XitjdIfw_MeWeiwMP',
};

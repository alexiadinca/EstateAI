import { Routes } from '@angular/router';

import { redirectSignedInUser, requireSignIn, SIGNED_IN_HOME } from './core/auth/auth.guards';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: SIGNED_IN_HOME },
  {
    path: 'sign-in',
    title: 'Sign in | EstateAI',
    canActivate: [redirectSignedInUser],
    loadComponent: () => import('./features/auth/sign-in/sign-in').then((m) => m.SignIn),
  },
  {
    path: 'register',
    title: 'Create account | EstateAI',
    canActivate: [redirectSignedInUser],
    loadComponent: () => import('./features/auth/register/register').then((m) => m.Register),
  },
  {
    path: 'analyses',
    canActivate: [requireSignIn],
    children: [
      {
        path: '',
        title: 'My analyses | EstateAI',
        loadComponent: () =>
          import('./features/analyses/my-analyses/my-analyses').then((m) => m.MyAnalyses),
      },
      {
        path: 'new',
        title: 'Analyze a property | EstateAI',
        loadComponent: () =>
          import('./features/analyses/new-property/new-property').then((m) => m.NewProperty),
      },
      {
        path: ':analysisId',
        title: 'Property analysis | EstateAI',
        loadComponent: () =>
          import('./features/analyses/analysis-detail/analysis-detail').then(
            (m) => m.AnalysisDetail,
          ),
      },
    ],
  },
  {
    path: 'account',
    title: 'Your account | EstateAI',
    canActivate: [requireSignIn],
    loadComponent: () => import('./features/account/account').then((m) => m.Account),
  },
  { path: '**', redirectTo: SIGNED_IN_HOME },
];

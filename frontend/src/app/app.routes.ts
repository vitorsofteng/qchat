import { Routes } from '@angular/router';

import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'lobby' },
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login.component').then((m) => m.LoginComponent),
  },
  {
    path: 'register',
    loadComponent: () =>
      import('./features/auth/register.component').then((m) => m.RegisterComponent),
  },
  {
    path: 'lobby',
    canActivate: [authGuard],
    loadComponent: () => import('./features/lobby/lobby.component').then((m) => m.LobbyComponent),
  },
  {
    path: 'chat/:sessionId',
    canActivate: [authGuard],
    loadComponent: () => import('./features/chat/chat.component').then((m) => m.ChatComponent),
  },
  {
    path: 'settings',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./features/settings/settings.component').then((m) => m.SettingsComponent),
  },
  { path: '**', redirectTo: 'lobby' },
];

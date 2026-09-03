import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from '../services/auth.service';

/** Bloqueia rotas autenticadas quando nao ha token valido (F2.7). */
export const authGuard: CanActivateFn = () => {
  const router = inject(Router);
  if (inject(AuthService).token) {
    return true;
  }
  return router.createUrlTree(['/login']);
};

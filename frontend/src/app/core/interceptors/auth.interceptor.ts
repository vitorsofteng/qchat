import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { AuthService } from '../services/auth.service';

/** Adiciona o token JWT ao header Authorization das requisicoes (F2.6). */
export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const token = inject(AuthService).token;
  if (token) {
    request = request.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    });
  }
  return next(request);
};

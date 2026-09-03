import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, switchMap, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { TokenResponse, UserProfile } from '../models/user';

/** Servico de autenticacao — login, logout e perfil do usuario (F15.1). */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly api = environment.apiBaseUrl;
  private readonly tokenKey = 'qchat_token';

  readonly currentUser = signal<UserProfile | null>(null);
  readonly isAuthenticated = computed(() => this.currentUser() !== null);

  get token(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  register(username: string, password: string): Observable<UserProfile> {
    return this.http.post<UserProfile>(`${this.api}/auth/register`, { username, password });
  }

  login(username: string, password: string): Observable<UserProfile> {
    return this.http
      .post<TokenResponse>(`${this.api}/auth/login`, { username, password })
      .pipe(
        tap((response) => localStorage.setItem(this.tokenKey, response.access_token)),
        switchMap(() => this.loadCurrentUser()),
      );
  }

  /** Revalida o token vigente e atualiza o perfil em memoria. */
  loadCurrentUser(): Observable<UserProfile> {
    return this.http
      .get<UserProfile>(`${this.api}/auth/me`)
      .pipe(tap((user) => this.currentUser.set(user)));
  }

  logout(): void {
    localStorage.removeItem(this.tokenKey);
    this.currentUser.set(null);
  }
}

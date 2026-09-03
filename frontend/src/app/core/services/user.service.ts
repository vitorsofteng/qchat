import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { UserProfile } from '../models/user';

/** Consulta de usuarios disponiveis para iniciar uma sessao. */
@Injectable({ providedIn: 'root' })
export class UserService {
  private readonly http = inject(HttpClient);
  private readonly api = environment.apiBaseUrl;

  /** Usuarios atualmente conectados (exceto o proprio). */
  listOnline(): Observable<UserProfile[]> {
    return this.http.get<UserProfile[]>(`${this.api}/users/online`);
  }
}

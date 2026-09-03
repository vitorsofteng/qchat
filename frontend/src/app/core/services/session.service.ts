import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { ProtocolMode } from '../models/protocol-mode';
import { SessionView } from '../models/session';

/** Servico de gestao de sessoes — criar, aceitar, recusar, encerrar (F15.2). */
@Injectable({ providedIn: 'root' })
export class SessionService {
  private readonly http = inject(HttpClient);
  private readonly api = environment.apiBaseUrl;

  request(bobUsername: string, mode: ProtocolMode): Observable<SessionView> {
    return this.http.post<SessionView>(`${this.api}/sessions/request`, {
      bob_username: bobUsername,
      mode,
    });
  }

  accept(sessionId: string): Observable<SessionView> {
    return this.http.post<SessionView>(`${this.api}/sessions/${sessionId}/accept`, {});
  }

  reject(sessionId: string): Observable<SessionView> {
    return this.http.post<SessionView>(`${this.api}/sessions/${sessionId}/reject`, {});
  }

  close(sessionId: string): Observable<SessionView> {
    return this.http.delete<SessionView>(`${this.api}/sessions/${sessionId}`);
  }

  list(): Observable<SessionView[]> {
    return this.http.get<SessionView[]>(`${this.api}/sessions`);
  }

  get(sessionId: string): Observable<SessionView> {
    return this.http.get<SessionView>(`${this.api}/sessions/${sessionId}`);
  }

  /** Recupera a chave de uma sessao ativa (ex.: apos recarregar a pagina). */
  getKey(sessionId: string): Observable<SessionKeyResponse> {
    return this.http.get<SessionKeyResponse>(`${this.api}/sessions/${sessionId}/key`);
  }
}

export interface SessionKeyResponse {
  key: string;
  qber: number | null;
}

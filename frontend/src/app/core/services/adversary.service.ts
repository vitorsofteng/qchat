import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AdversaryState, EveMode } from '../models/adversary';

/** Adversario simulado: leitura e troca do modo em tempo de execucao (F11.4).
 *
 * O estado e mantido num signal compartilhado para que o controle do lobby e o
 * painel de evidencias do chat exibam sempre o mesmo valor.
 */
@Injectable({ providedIn: 'root' })
export class AdversaryService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiBaseUrl}/adversary`;

  readonly state = signal<AdversaryState | null>(null);

  refresh(): void {
    this.http
      .get<AdversaryState>(this.api)
      .subscribe({ next: (state) => this.state.set(state) });
  }

  setMode(mode: EveMode) {
    return this.http
      .put<AdversaryState>(this.api, { mode })
      .pipe(tap((state) => this.state.set(state)));
  }
}

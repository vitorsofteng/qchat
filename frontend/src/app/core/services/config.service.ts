import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, shareReplay } from 'rxjs';

import { environment } from '../../../environments/environment';
import { SystemConfig } from '../models/system-config';

/** Parametros do sistema (`/config`), buscados uma unica vez e reaproveitados. */
@Injectable({ providedIn: 'root' })
export class ConfigService {
  private readonly http = inject(HttpClient);
  private config$?: Observable<SystemConfig>;

  get(): Observable<SystemConfig> {
    this.config$ ??= this.http
      .get<SystemConfig>(`${environment.apiBaseUrl}/config`)
      .pipe(shareReplay({ bufferSize: 1, refCount: false }));
    return this.config$;
  }
}

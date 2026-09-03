import { Injectable, inject, signal } from '@angular/core';

import { WebSocketService } from './websocket.service';

export interface QberAlert {
  qber: number;
  threshold: number;
  detail: string;
}

export interface EstablishedKey {
  /** Chave de sessao de 32 bytes, codificada em base64. */
  key: string;
  metrics: Record<string, unknown>;
  qber: number | null;
}

/** Recebe e expoe a chave estabelecida, metricas e alertas de QBER (F15.4).
 *
 * Mantido vivo desde o lobby, captura os eventos `key_established` de todas as
 * sessoes — assim o chat encontra a chave mesmo se entrar apos o evento.
 */
@Injectable({ providedIn: 'root' })
export class CryptoMetricsService {
  private readonly ws = inject(WebSocketService);
  private readonly established = new Map<string, EstablishedKey>();

  readonly lastQberAlert = signal<QberAlert | null>(null);

  constructor() {
    this.ws.messages$.subscribe((message) => {
      if (message.type === 'key_established' && message.session_id) {
        const metrics = (message.payload['metrics'] as Record<string, unknown>) ?? {};
        this.established.set(message.session_id, {
          key: message.payload['key'] as string,
          metrics,
          qber: (metrics['qber'] as number | null) ?? null,
        });
      } else if (message.type === 'qber_alert') {
        this.lastQberAlert.set(message.payload as unknown as QberAlert);
      }
    });
  }

  getEstablished(sessionId: string): EstablishedKey | undefined {
    return this.established.get(sessionId);
  }
}

import { Injectable, inject } from '@angular/core';

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
 * Mantido vivo desde o lobby, captura os eventos `key_established` e
 * `qber_alert` de todas as sessoes. Isso importa para quem aceita o convite:
 * o backend executa o protocolo durante o aceite, entao os dois eventos chegam
 * enquanto Bob ainda esta no lobby. Sem este cache, o chat de Bob abriria sem a
 * chave e — no caso do alerta — sem saber que houve espionagem.
 */
@Injectable({ providedIn: 'root' })
export class CryptoMetricsService {
  private readonly ws = inject(WebSocketService);
  private readonly established = new Map<string, EstablishedKey>();
  private readonly alerts = new Map<string, QberAlert>();

  constructor() {
    this.ws.messages$.subscribe((message) => {
      if (!message.session_id) {
        return;
      }
      if (message.type === 'key_established') {
        const metrics = (message.payload['metrics'] as Record<string, unknown>) ?? {};
        this.established.set(message.session_id, {
          key: message.payload['key'] as string,
          metrics,
          qber: (metrics['qber'] as number | null) ?? null,
        });
      } else if (message.type === 'qber_alert') {
        this.alerts.set(message.session_id, message.payload as unknown as QberAlert);
      }
    });
  }

  getEstablished(sessionId: string): EstablishedKey | undefined {
    return this.established.get(sessionId);
  }

  getQberAlert(sessionId: string): QberAlert | undefined {
    return this.alerts.get(sessionId);
  }
}

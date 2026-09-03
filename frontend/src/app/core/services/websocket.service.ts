import { Injectable, signal } from '@angular/core';
import { Observable, Subject } from 'rxjs';

import { environment } from '../../../environments/environment';
import { WSMessage } from '../models/ws-message';

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected';

/** Conexao WebSocket com reconexao automatica por backoff exponencial (F15.3). */
@Injectable({ providedIn: 'root' })
export class WebSocketService {
  private socket: WebSocket | null = null;
  private token: string | null = null;
  private shouldReconnect = false;
  private reconnectAttempts = 0;
  private readonly maxReconnectDelayMs = 30_000;

  private readonly messages = new Subject<WSMessage>();
  readonly messages$: Observable<WSMessage> = this.messages.asObservable();
  readonly status = signal<ConnectionStatus>('disconnected');

  connect(token: string): void {
    const alreadyConnected =
      this.socket !== null &&
      this.token === token &&
      (this.socket.readyState === WebSocket.OPEN ||
        this.socket.readyState === WebSocket.CONNECTING);
    if (alreadyConnected) {
      return;
    }
    this.token = token;
    this.shouldReconnect = true;
    this.open();
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this.socket?.close();
    this.socket = null;
    this.status.set('disconnected');
  }

  send(message: WSMessage): void {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    }
  }

  private open(): void {
    if (!this.token) {
      return;
    }
    this.status.set('connecting');
    this.socket = new WebSocket(`${this.wsBaseUrl()}/ws/${this.token}`);

    this.socket.onopen = () => {
      this.status.set('connected');
      this.reconnectAttempts = 0;
    };

    this.socket.onmessage = (event) => {
      const message = JSON.parse(event.data) as WSMessage;
      if (message.type === 'ping') {
        this.send({ type: 'pong', payload: {} });
        return;
      }
      this.messages.next(message);
    };

    this.socket.onclose = () => {
      this.status.set('disconnected');
      this.scheduleReconnect();
    };

    this.socket.onerror = () => this.socket?.close();
  }

  private scheduleReconnect(): void {
    if (!this.shouldReconnect) {
      return;
    }
    const delay = Math.min(1000 * 2 ** this.reconnectAttempts, this.maxReconnectDelayMs);
    this.reconnectAttempts += 1;
    setTimeout(() => this.open(), delay);
  }

  private wsBaseUrl(): string {
    if (environment.wsBaseUrl) {
      return environment.wsBaseUrl;
    }
    const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
    return `${protocol}://${location.host}`;
  }
}

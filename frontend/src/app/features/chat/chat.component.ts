import { DatePipe } from '@angular/common';
import {
  Component,
  ElementRef,
  OnDestroy,
  OnInit,
  computed,
  effect,
  inject,
  signal,
  viewChild,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActivatedRoute, Router } from '@angular/router';
import { Subscription } from 'rxjs';

import { ChatMessage } from '../../core/models/chat-message';
import { PROTOCOL_MODES } from '../../core/models/protocol-mode';
import { SessionView } from '../../core/models/session';
import { EncryptedEnvelope, WSMessage } from '../../core/models/ws-message';
import { AdversaryService } from '../../core/services/adversary.service';
import { AuthService } from '../../core/services/auth.service';
import { ConfigService } from '../../core/services/config.service';
import { CryptoMetricsService } from '../../core/services/crypto-metrics.service';
import { MessageCryptoService } from '../../core/services/message-crypto.service';
import { SessionService } from '../../core/services/session.service';
import { WebSocketService } from '../../core/services/websocket.service';
import { AdversaryControlComponent } from '../../shared/adversary-control/adversary-control.component';
import { QberAlertDialogComponent } from '../../shared/qber-alert-dialog/qber-alert-dialog.component';
import { ToolbarComponent } from '../../shared/toolbar/toolbar.component';

const TYPING_THROTTLE_MS = 1500;
const TYPING_CLEAR_MS = 3000;

/** Escala fixa do medidor de QBER, em fracao (0 a 30%). */
const QBER_SCALE_MAX = 0.3;

/** Uma linha do painel de evidencias: rotulo, valor e nota explicativa. */
export interface EvidenceRow {
  label: string;
  value: string;
  note?: string;
}

/** Situacao de um componente do modo hibrido. */
export interface ComponentStatus {
  name: string;
  ok: boolean;
  error: string | null;
}

/** Ultimo envelope que passou pelo canal, com a direcao em que trafegou. */
export interface WireRecord {
  envelope: EncryptedEnvelope;
  outgoing: boolean;
  plaintext: string;
}

/** Tela de chat — mensagens cifradas, métricas de QBER e status (F14.4 - F14.6). */
@Component({
  selector: 'app-chat',
  imports: [
    DatePipe,
    ToolbarComponent,
    AdversaryControlComponent,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss',
})
export class ChatComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly auth = inject(AuthService);
  private readonly ws = inject(WebSocketService);
  private readonly sessions = inject(SessionService);
  private readonly messageCrypto = inject(MessageCryptoService);
  private readonly cryptoMetrics = inject(CryptoMetricsService);
  private readonly adversary = inject(AdversaryService);
  private readonly config = inject(ConfigService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);

  readonly session = signal<SessionView | null>(null);
  readonly messages = signal<ChatMessage[]>([]);
  readonly ready = signal(false);
  readonly sessionClosed = signal(false);
  readonly peerTyping = signal(false);
  readonly qber = signal<number | null>(null);
  readonly connectionStatus = this.ws.status;

  // --- painel de evidencias (F15.4) ---
  readonly evidenceOpen = signal(true);
  readonly sessionKey = signal<string | null>(null);
  readonly keyFingerprint = signal<string | null>(null);
  readonly metrics = signal<Record<string, unknown> | null>(null);
  readonly wire = signal<WireRecord | null>(null);
  readonly qberThreshold = signal<number | null>(null);

  readonly modeLabel = computed(() => {
    const mode = this.session()?.mode;
    return PROTOCOL_MODES.find((option) => option.value === mode)?.label ?? mode ?? '—';
  });
  readonly qberDisplay = computed(() => {
    const value = this.qber();
    return value === null ? 'N/A' : `${(value * 100).toFixed(1)}%`;
  });

  readonly modeDescription = computed(() => {
    const mode = this.session()?.mode;
    return PROTOCOL_MODES.find((option) => option.value === mode)?.description ?? '';
  });

  /** Metricas do estabelecimento de chave, comuns e especificas de cada modo. */
  readonly protocolRows = computed<EvidenceRow[]>(() => {
    const metrics = this.metrics();
    if (!metrics) {
      return [];
    }
    const rows: EvidenceRow[] = [];
    const push = (label: string, value: unknown, note?: string): void => {
      if (value !== undefined && value !== null && value !== '') {
        rows.push({ label, value: String(value), note });
      }
    };

    push('Tempo de estabelecimento', this.formatMs(metrics['elapsed_ms']));
    const bytes = metrics['bytes_exchanged'];
    if (typeof bytes === 'number' && bytes > 0) {
      push('Bytes trocados no canal', bytes.toLocaleString('pt-BR'));
    }
    push('Tamanho da chave derivada', this.formatBits(metrics['key_size_bits']));

    switch (this.session()?.mode) {
      case 'RSA':
        push('Par de chaves RSA', this.formatBits(metrics['rsa_key_bits']), 'controle experimental');
        break;
      case 'MLKEM':
        push('Nível ML-KEM', metrics['mlkem_level'], 'NIST FIPS 203');
        break;
      case 'BB84':
        push('Qubits transmitidos', this.formatCount(metrics['n_qubits']));
        push('Bits após o sifting', this.formatCount(metrics['sifted_length']), 'bases coincidentes');
        push('Bits após a reconciliação', this.formatCount(metrics['reconciled_length']), 'Cascade');
        push('Bits após a amplificação', this.formatCount(metrics['amplified_length']));
        push('Bits de paridade vazados', this.formatCount(metrics['parity_bits_leaked']));
        break;
      case 'HYBRID':
        push('Componentes íntegros', this.formatSurvivors(metrics['survivors']));
        break;
    }
    return rows;
  });

  /** Situacao de cada componente do modo hibrido. */
  readonly hybridComponents = computed<ComponentStatus[]>(() => {
    const components = this.metrics()?.['components'];
    if (!components || typeof components !== 'object') {
      return [];
    }
    return Object.entries(components as Record<string, Record<string, unknown>>).map(
      ([name, detail]) => ({
        name: name === 'bb84' ? 'BB84 (quântico)' : 'ML-KEM (pós-quântico)',
        ok: detail?.['ok'] === true,
        error: (detail?.['error'] as string | null) ?? null,
      }),
    );
  });

  /** Largura da barra de QBER, em porcentagem da escala do medidor. */
  readonly qberBarWidth = computed(() => {
    const value = this.qber();
    return value === null ? 0 : Math.min(100, (value / QBER_SCALE_MAX) * 100);
  });

  /** Posicao do marcador de limiar, em porcentagem da escala do medidor. */
  readonly qberMarkerLeft = computed(() => {
    const threshold = this.qberThreshold();
    return threshold === null ? 50 : Math.min(100, (threshold / QBER_SCALE_MAX) * 100);
  });

  readonly qberExceeded = computed(() => {
    const value = this.qber();
    const threshold = this.qberThreshold();
    return value !== null && threshold !== null && value > threshold;
  });

  readonly thresholdDisplay = computed(() => {
    const threshold = this.qberThreshold();
    return threshold === null ? '—' : `${(threshold * 100).toFixed(1)}%`;
  });

  readonly scaleMaxDisplay = `${(QBER_SCALE_MAX * 100).toFixed(0)}%`;

  /** O modo em uso mede QBER? (RSA e ML-KEM nao medem.) */
  readonly hasQber = computed(() => {
    const mode = this.session()?.mode;
    return PROTOCOL_MODES.find((option) => option.value === mode)?.hasQber ?? false;
  });

  private readonly messageList = viewChild<ElementRef<HTMLDivElement>>('messageList');

  private sessionId = '';
  private cryptoKey: CryptoKey | null = null;
  private sendSequence = 0;
  private subscription?: Subscription;
  private typingTimeout?: ReturnType<typeof setTimeout>;
  private lastTypingSentAt = 0;

  constructor() {
    // Rola a lista para a ultima mensagem sempre que chega ou sai uma mensagem.
    effect(() => {
      this.messages();
      const element = this.messageList()?.nativeElement;
      if (element) {
        queueMicrotask(() => (element.scrollTop = element.scrollHeight));
      }
    });
  }

  ngOnInit(): void {
    this.sessionId = this.route.snapshot.paramMap.get('sessionId') ?? '';
    const token = this.auth.token;
    if (token) {
      this.ws.connect(token);
    }

    this.config.get().subscribe({
      next: (config) => this.qberThreshold.set(config.qber_threshold),
    });

    // O evento key_established pode ter chegado ainda no lobby, antes desta
    // tela existir; o CryptoMetricsService o mantem em cache.
    const cached = this.cryptoMetrics.getEstablished(this.sessionId);
    if (cached) {
      this.metrics.set(cached.metrics);
    }

    this.sessions.get(this.sessionId).subscribe({
      next: (session) => {
        this.session.set(session);
        this.qber.set(session.qber);
        if (['closed', 'rejected', 'aborted'].includes(session.state)) {
          this.sessionClosed.set(true);
        } else if (session.state === 'active') {
          // Sessao ja ativa (ex.: apos recarregar a pagina): recupera a chave.
          this.loadKey();
        }
        // pending/establishing: a chave chegara via WS (key_established).
      },
      error: () => this.notify('Sessão não encontrada.'),
    });

    this.subscription = this.ws.messages$.subscribe((message) => this.handle(message));
  }

  private loadKey(): void {
    this.sessions.getKey(this.sessionId).subscribe({
      next: ({ key, qber }) => void this.applyKey(key, qber),
      error: () => this.notify('Não foi possível recuperar a chave da sessão.'),
    });
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
    if (this.typingTimeout) {
      clearTimeout(this.typingTimeout);
    }
  }

  async send(input: HTMLInputElement): Promise<void> {
    const text = input.value.trim();
    if (!text || !this.cryptoKey || this.sessionClosed()) {
      return;
    }
    const timestamp = new Date().toISOString();
    const envelope = await this.messageCrypto.encrypt(
      this.cryptoKey,
      text,
      this.sessionId,
      this.sendSequence,
      timestamp,
    );
    this.sendSequence += 1;
    this.ws.send({
      type: 'chat_message',
      session_id: this.sessionId,
      payload: envelope as unknown as Record<string, unknown>,
    });
    this.wire.set({ envelope, outgoing: true, plaintext: text });
    this.appendMessage({ text, outgoing: true, timestamp });
    input.value = '';
  }

  onTyping(): void {
    const now = Date.now();
    if (now - this.lastTypingSentAt > TYPING_THROTTLE_MS) {
      this.lastTypingSentAt = now;
      this.ws.send({ type: 'typing', session_id: this.sessionId, payload: {} });
    }
  }

  closeSession(): void {
    this.sessions.close(this.sessionId).subscribe({
      next: () => void this.router.navigate(['/lobby']),
      error: () => void this.router.navigate(['/lobby']),
    });
  }

  private async applyKey(keyBase64: string, qber: number | null): Promise<void> {
    this.cryptoKey = await this.messageCrypto.importKey(keyBase64);
    this.adversary.refresh();
    this.sessionKey.set(keyBase64);
    this.keyFingerprint.set(await this.messageCrypto.fingerprint(keyBase64));
    this.ready.set(true);
    if (qber !== null) {
      this.qber.set(qber);
    }
  }

  toggleEvidence(): void {
    this.evidenceOpen.update((open) => !open);
  }

  private formatMs(value: unknown): string | null {
    return typeof value === 'number' ? `${value.toLocaleString('pt-BR')} ms` : null;
  }

  private formatBits(value: unknown): string | null {
    return typeof value === 'number' ? `${value.toLocaleString('pt-BR')} bits` : null;
  }

  private formatCount(value: unknown): string | null {
    return typeof value === 'number' ? value.toLocaleString('pt-BR') : null;
  }

  private formatSurvivors(value: unknown): string | null {
    if (!Array.isArray(value)) {
      return null;
    }
    const labels: Record<string, string> = { bb84: 'BB84', mlkem: 'ML-KEM' };
    return value.map((item) => labels[String(item)] ?? String(item)).join(' + ');
  }

  private handle(message: WSMessage): void {
    if (message.session_id && message.session_id !== this.sessionId && message.type !== 'error') {
      return; // mensagem de outra sessao
    }
    switch (message.type) {
      case 'key_established': {
        const metrics = message.payload['metrics'] as Record<string, unknown> | undefined;
        if (metrics) {
          this.metrics.set(metrics);
        }
        void this.applyKey(
          message.payload['key'] as string,
          (metrics?.['qber'] as number | null) ?? null,
        );
        break;
      }
      case 'chat_message':
        void this.receive(message.payload as unknown as EncryptedEnvelope);
        break;
      case 'qber_alert':
        this.sessionClosed.set(true);
        this.dialog.open(QberAlertDialogComponent, { data: message.payload });
        break;
      case 'session_closed':
        this.sessionClosed.set(true);
        this.notify('A sessão foi encerrada.');
        break;
      case 'typing':
        this.showPeerTyping();
        break;
      case 'error':
        this.notify((message.payload['detail'] as string) ?? 'Ocorreu um erro.');
        break;
    }
  }

  private async receive(envelope: EncryptedEnvelope): Promise<void> {
    if (!this.cryptoKey) {
      return;
    }
    try {
      const text = await this.messageCrypto.decrypt(this.cryptoKey, envelope, this.sessionId);
      this.wire.set({ envelope, outgoing: false, plaintext: text });
      this.appendMessage({ text, outgoing: false, timestamp: envelope.timestamp });
    } catch {
      this.notify('Uma mensagem recebida não pôde ser decifrada.');
    }
  }

  private appendMessage(message: ChatMessage): void {
    this.messages.update((list) => [...list, message]);
  }

  private showPeerTyping(): void {
    this.peerTyping.set(true);
    if (this.typingTimeout) {
      clearTimeout(this.typingTimeout);
    }
    this.typingTimeout = setTimeout(() => this.peerTyping.set(false), TYPING_CLEAR_MS);
  }

  private notify(text: string): void {
    this.snackBar.open(text, 'OK', { duration: 5000 });
  }
}

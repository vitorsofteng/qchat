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

import { EveMode } from '../../core/models/adversary';
import { ChatMessage } from '../../core/models/chat-message';
import { PROTOCOL_MODES } from '../../core/models/protocol-mode';
import { SessionView } from '../../core/models/session';
import { EncryptedEnvelope, WSMessage } from '../../core/models/ws-message';
import { AdversaryService } from '../../core/services/adversary.service';
import { AuthService } from '../../core/services/auth.service';
import { ConfigService } from '../../core/services/config.service';
import { CryptoMetricsService, QberAlert } from '../../core/services/crypto-metrics.service';
import { MessageCryptoService } from '../../core/services/message-crypto.service';
import { SessionService } from '../../core/services/session.service';
import { WebSocketService } from '../../core/services/websocket.service';
import { AdversaryControlComponent } from '../../shared/adversary-control/adversary-control.component';
import { formatNumber, formatPercent } from '../../shared/format';
import { FunnelStage, KeyFunnelComponent } from '../../shared/key-funnel/key-funnel.component';
import {
  QberAlertDialogComponent,
  QberAlertDialogData,
} from '../../shared/qber-alert-dialog/qber-alert-dialog.component';
import { QberGaugeComponent } from '../../shared/qber-gauge/qber-gauge.component';
import { ToolbarComponent } from '../../shared/toolbar/toolbar.component';

const TYPING_THROTTLE_MS = 1500;
const TYPING_CLEAR_MS = 3000;

/** Um numero em destaque no painel: valor grande, rotulo pequeno. */
export interface StatTile {
  label: string;
  value: string;
  unit?: string;
}

/** Uma linha de detalhe do protocolo. */
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

/** Tela de chat — mensagens cifradas e painel de evidencias (F14.4 - F14.6). */
@Component({
  selector: 'app-chat',
  imports: [
    DatePipe,
    ToolbarComponent,
    AdversaryControlComponent,
    QberGaugeComponent,
    KeyFunnelComponent,
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
  /** Bob recusou o convite: nenhuma chave chegou a existir. */
  readonly rejected = signal(false);
  /** BB84 abortado por espionagem. */
  readonly aborted = signal(false);
  /** Hibrido sob espionagem: o BB84 caiu e a sessao segue apenas com o ML-KEM. */
  readonly bb84Discarded = signal(false);
  readonly peerTyping = signal(false);
  readonly qber = signal<number | null>(null);
  readonly connectionStatus = this.ws.status;

  // --- painel de evidencias (F15.4) ---
  readonly evidenceOpen = signal(true);
  readonly sessionKey = signal<string | null>(null);
  readonly keyFingerprint = signal<string | null>(null);
  readonly keyRevealed = signal(false);
  readonly metrics = signal<Record<string, unknown> | null>(null);
  readonly wire = signal<WireRecord | null>(null);
  readonly qberThreshold = signal<number | null>(null);
  /** Modo do adversario vigente quando a chave desta sessao foi estabelecida. */
  readonly adversaryAtKey = signal<EveMode | null>(null);

  private readonly modeOption = computed(() => {
    const mode = this.session()?.mode;
    return PROTOCOL_MODES.find((option) => option.value === mode);
  });

  readonly modeLabel = computed(() => this.modeOption()?.label ?? this.session()?.mode ?? '—');
  readonly modeShort = computed(() => this.modeOption()?.short ?? '—');
  readonly modeIcon = computed(() => this.modeOption()?.icon ?? 'lock');
  readonly modeDescription = computed(() => this.modeOption()?.description ?? '');
  readonly hasQber = computed(() => this.modeOption()?.hasQber ?? false);

  readonly qberDisplay = computed(() => {
    const value = this.qber();
    return value === null ? 'N/A' : formatPercent(value);
  });

  readonly qberExceeded = computed(() => {
    const value = this.qber();
    const threshold = this.qberThreshold();
    return value !== null && threshold !== null && value > threshold;
  });

  readonly thresholdDisplay = computed(() => {
    const threshold = this.qberThreshold();
    return threshold === null ? '—' : formatPercent(threshold);
  });

  /** Estado da sessao em uma linha, para o cabecalho. */
  readonly sessionStateLabel = computed(() => {
    if (this.rejected()) {
      return 'Convite recusado';
    }
    if (this.aborted()) {
      return 'Abortada — espionagem detectada';
    }
    if (this.sessionClosed()) {
      return 'Sessão encerrada';
    }
    if (!this.ready()) {
      return 'Estabelecendo chave…';
    }
    return this.bb84Discarded() ? 'Sessão ativa · BB84 descartado' : 'Sessão segura ativa';
  });

  /** Por que a sessao terminou, dito no rodape da conversa. */
  readonly closedMessage = computed(() => {
    if (this.rejected()) {
      return 'O convite foi recusado. Nenhuma chave foi estabelecida.';
    }
    if (this.aborted()) {
      return 'Sessão abortada: espionagem detectada no canal quântico. Nenhuma chave foi gerada.';
    }
    return 'Sessão encerrada. As mensagens eram efêmeras e foram descartadas.';
  });

  /** O QBER mede perturbacao, nao seguranca: o veredicto diz exatamente isso. */
  readonly verdictLabel = computed(() =>
    this.qberExceeded() ? 'Espionagem detectada' : 'Nenhuma perturbação detectada',
  );

  /** A divisao de feixe nao perturba os qubits, entao o QBER nao a denuncia. */
  readonly beamSplittingUndetected = computed(
    () => this.adversaryAtKey() === 'BEAM_SPLITTING' && !this.qberExceeded(),
  );

  /** Os tres numeros que resumem o estabelecimento, em destaque. */
  readonly statTiles = computed<StatTile[]>(() => {
    const metrics = this.metrics();
    if (!metrics) {
      return [];
    }
    const tiles: StatTile[] = [];
    const elapsed = metrics['elapsed_ms'];
    if (typeof elapsed === 'number') {
      tiles.push({
        label: 'Estabelecimento',
        value: elapsed < 1000 ? formatNumber(elapsed) : formatNumber(elapsed / 1000, 2),
        unit: elapsed < 1000 ? 'ms' : 's',
      });
    }
    const bytes = metrics['bytes_exchanged'];
    if (typeof bytes === 'number' && bytes > 0) {
      tiles.push({ label: 'Trocados', value: formatNumber(bytes), unit: 'bytes' });
    }
    const bits = metrics['key_size_bits'];
    if (typeof bits === 'number') {
      tiles.push({ label: 'Chave', value: formatNumber(bits), unit: 'bits' });
    }
    return tiles;
  });

  /** Destilacao da chave no BB84: de qubits transmitidos a chave de sessao. */
  readonly funnelStages = computed<FunnelStage[]>(() => {
    const metrics = this.metrics();
    if (!metrics || this.session()?.mode !== 'BB84') {
      return [];
    }
    const num = (key: string): number | null =>
      typeof metrics[key] === 'number' ? (metrics[key] as number) : null;

    const qubits = num('n_qubits');
    const sifted = num('sifted_length');
    const reconciled = num('reconciled_length');
    const amplified = num('amplified_length');
    const keyBits = num('key_size_bits');
    if (qubits === null || sifted === null) {
      return [];
    }

    const stages: FunnelStage[] = [
      {
        label: 'Qubits transmitidos',
        value: qubits,
        note: 'Alice envia cada bit em uma base escolhida ao acaso.',
      },
      {
        label: 'Após o sifting',
        value: sifted,
        note: 'Sobram os bits em que Alice e Bob acertaram a mesma base — cerca de metade.',
      },
    ];
    if (reconciled !== null) {
      stages.push({
        label: 'Após a reconciliação',
        value: reconciled,
        note: 'O Cascade corrige as divergências restantes trocando paridades.',
      });
    }
    if (amplified !== null) {
      stages.push({
        label: 'Após a amplificação',
        value: amplified,
        note: 'A chave é comprimida para destruir a informação que um espião possa ter.',
      });
    }
    if (keyBits !== null) {
      stages.push({
        label: 'Chave de sessão',
        value: keyBits,
        note: 'É esta chave que cifra as mensagens em AES-256-GCM.',
        final: true,
      });
    }
    return stages;
  });

  /** Detalhes que nao cabem nos numeros em destaque nem no funil. */
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

    switch (this.session()?.mode) {
      case 'RSA':
        push('Par de chaves', this.formatBits(metrics['rsa_key_bits']), 'controle experimental');
        break;
      case 'MLKEM':
        push('Nível', metrics['mlkem_level'], 'NIST FIPS 203');
        break;
      case 'BB84':
        push(
          'Bits de paridade vazados',
          this.formatCount(metrics['parity_bits_leaked']),
          'expostos no canal público durante a reconciliação',
        );
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
    const qber = this.qber();
    const threshold = this.qberThreshold();
    return Object.entries(components as Record<string, Record<string, unknown>>).map(
      ([name, detail]) => {
        const ok = detail?.['ok'] === true;
        let error = (detail?.['error'] as string | null) ?? null;
        // A mensagem crua do backend vem como "QBER 0.2635 acima do limiar
        // 0.1500"; com os valores em maos, apresenta-se no formato da tela.
        if (!ok && name === 'bb84' && qber !== null && threshold !== null) {
          error = `QBER de ${formatPercent(qber)} acima do limiar de ${formatPercent(threshold)} — possível espionagem`;
        }
        return {
          name: name === 'bb84' ? 'BB84 · quântico' : 'ML-KEM · pós-quântico',
          ok,
          error,
        };
      },
    );
  });

  private readonly messageList = viewChild<ElementRef<HTMLDivElement>>('messageList');

  private sessionId = '';
  private cryptoKey: CryptoKey | null = null;
  /** Alerta que chegou antes de a sessao carregar: o desfecho depende do modo. */
  private pendingAlert: QberAlert | null = null;
  private alertHandled = false;
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
        if (session.qber !== null) {
          this.qber.set(session.qber);
        }
        if (session.state === 'rejected') {
          this.rejected.set(true);
          this.sessionClosed.set(true);
        } else if (session.state === 'aborted') {
          // O backend so' aborta sessoes por espionagem (reason="eve_detected").
          this.aborted.set(true);
          this.sessionClosed.set(true);
        } else if (session.state === 'closed') {
          this.sessionClosed.set(true);
        } else if (session.state === 'active') {
          // Sessao ja ativa (ex.: apos recarregar a pagina): recupera a chave.
          this.loadKey();
        }
        // pending/establishing: a chave chegara via WS (key_established).

        // Alerta que chegou enquanto a tela carregava, ou ainda no lobby.
        const alert = this.pendingAlert ?? this.cryptoMetrics.getQberAlert(this.sessionId);
        this.pendingAlert = null;
        if (alert) {
          this.applyQberAlert(alert);
        }
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

  toggleEvidence(): void {
    this.evidenceOpen.update((open) => !open);
  }

  toggleKeyReveal(): void {
    this.keyRevealed.update((revealed) => !revealed);
  }

  backToLobby(): void {
    void this.router.navigate(['/lobby']);
  }

  /** Registra o alerta de QBER e aplica o desfecho que o backend deu a sessao.
   *
   * BB84: sem canal quantico integro nao ha chave, entao a sessao e' abortada.
   * Hibrido: o backend descarta o componente BB84 e deriva a chave do ML-KEM
   * (ver `_build_qber_monitor` em key_exchange.py) — a sessao continua.
   */
  private applyQberAlert(alert: QberAlert): void {
    const mode = this.session()?.mode;
    if (!mode) {
      this.pendingAlert = alert;
      return;
    }
    this.qber.set(alert.qber);
    if (this.alertHandled) {
      return;
    }
    this.alertHandled = true;

    const sessionContinues = mode === 'HYBRID';
    if (sessionContinues) {
      this.bb84Discarded.set(true);
    } else {
      this.aborted.set(true);
      this.sessionClosed.set(true);
    }
    const data: QberAlertDialogData = { ...alert, sessionContinues };
    this.dialog.open(QberAlertDialogComponent, { data });
  }

  private async applyKey(keyBase64: string, qber: number | null): Promise<void> {
    this.cryptoKey = await this.messageCrypto.importKey(keyBase64);
    this.adversary.fetch().subscribe({ next: (state) => this.adversaryAtKey.set(state.mode) });
    this.sessionKey.set(keyBase64);
    this.keyFingerprint.set(await this.messageCrypto.fingerprint(keyBase64));
    this.ready.set(true);
    if (qber !== null) {
      this.qber.set(qber);
    }
  }

  private formatBits(value: unknown): string | null {
    return typeof value === 'number' ? `${formatNumber(value)} bits` : null;
  }

  private formatCount(value: unknown): string | null {
    return typeof value === 'number' ? formatNumber(value) : null;
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
        this.applyQberAlert(message.payload as unknown as QberAlert);
        break;
      case 'session_rejected':
        this.rejected.set(true);
        this.sessionClosed.set(true);
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

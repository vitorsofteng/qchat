import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';

import { PROTOCOL_MODES, ProtocolMode } from '../../core/models/protocol-mode';
import { UserProfile } from '../../core/models/user';
import { WSMessage } from '../../core/models/ws-message';
import { AuthService } from '../../core/services/auth.service';
import { CryptoMetricsService } from '../../core/services/crypto-metrics.service';
import { SessionService } from '../../core/services/session.service';
import { UserService } from '../../core/services/user.service';
import { WebSocketService } from '../../core/services/websocket.service';
import { ToolbarComponent } from '../../shared/toolbar/toolbar.component';

interface PendingRequest {
  sessionId: string;
  from: string;
  mode: string;
}

/** Tela de lobby — usuarios online e solicitacoes de sessao (F14.3). */
@Component({
  selector: 'app-lobby',
  imports: [
    ToolbarComponent,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatSelectModule,
  ],
  templateUrl: './lobby.component.html',
  styleUrl: './lobby.component.scss',
})
export class LobbyComponent implements OnInit, OnDestroy {
  private readonly auth = inject(AuthService);
  private readonly ws = inject(WebSocketService);
  private readonly users = inject(UserService);
  private readonly sessions = inject(SessionService);
  private readonly router = inject(Router);
  private readonly snackBar = inject(MatSnackBar);
  // Injetado para manter o servico vivo capturando os eventos key_established.
  private readonly cryptoMetrics = inject(CryptoMetricsService);

  readonly protocolModes = PROTOCOL_MODES;
  readonly selectedMode = signal<ProtocolMode>('RSA');
  readonly onlineUsers = signal<UserProfile[]>([]);
  readonly pendingRequests = signal<PendingRequest[]>([]);
  readonly connectionStatus = this.ws.status;

  private subscription?: Subscription;

  ngOnInit(): void {
    const token = this.auth.token;
    if (token) {
      this.ws.connect(token);
    }
    if (!this.auth.currentUser()) {
      this.auth.loadCurrentUser().subscribe();
    }
    this.refreshUsers();
    this.subscription = this.ws.messages$.subscribe((message) => this.handle(message));
  }

  ngOnDestroy(): void {
    this.subscription?.unsubscribe();
  }

  refreshUsers(): void {
    this.users.listOnline().subscribe({
      next: (users) => this.onlineUsers.set(users),
      error: () => this.onlineUsers.set([]),
    });
  }

  modeDescription(): string {
    return this.protocolModes.find((option) => option.value === this.selectedMode())?.description ?? '';
  }

  startSession(user: UserProfile): void {
    this.sessions.request(user.username, this.selectedMode()).subscribe({
      next: (session) => void this.router.navigate(['/chat', session.id]),
      error: () => this.notify('Não foi possível iniciar a sessão.'),
    });
  }

  acceptRequest(request: PendingRequest): void {
    this.sessions.accept(request.sessionId).subscribe({
      next: () => void this.router.navigate(['/chat', request.sessionId]),
      error: () => this.notify('Não foi possível aceitar a solicitação.'),
    });
  }

  rejectRequest(request: PendingRequest): void {
    this.sessions.reject(request.sessionId).subscribe({
      error: () => this.notify('Não foi possível recusar a solicitação.'),
    });
    this.removeRequest(request.sessionId);
  }

  private handle(message: WSMessage): void {
    if (message.type === 'session_request' && message.session_id) {
      this.pendingRequests.update((list) => [
        ...list,
        {
          sessionId: message.session_id as string,
          from: (message.payload['from'] as string) ?? 'desconhecido',
          mode: (message.payload['mode'] as string) ?? '',
        },
      ]);
    } else if (message.type === 'session_accepted' && message.session_id) {
      void this.router.navigate(['/chat', message.session_id]);
    }
  }

  private removeRequest(sessionId: string): void {
    this.pendingRequests.update((list) => list.filter((r) => r.sessionId !== sessionId));
  }

  private notify(text: string): void {
    this.snackBar.open(text, 'OK', { duration: 4000 });
  }
}

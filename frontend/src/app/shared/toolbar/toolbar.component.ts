import { Component, computed, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { WebSocketService } from '../../core/services/websocket.service';

/** Barra superior compartilhada pelas telas autenticadas. */
@Component({
  selector: 'app-toolbar',
  imports: [MatToolbarModule, MatButtonModule, MatIconModule, RouterLink],
  template: `
    <mat-toolbar color="primary">
      <span class="brand" routerLink="/lobby">QChat</span>
      <span class="spacer"></span>
      @if (username()) {
        <span class="username">{{ username() }}</span>
      }
      <button mat-icon-button routerLink="/lobby" aria-label="Lobby">
        <mat-icon>home</mat-icon>
      </button>
      <button mat-icon-button routerLink="/settings" aria-label="Configurações">
        <mat-icon>settings</mat-icon>
      </button>
      <button mat-icon-button (click)="logout()" aria-label="Sair">
        <mat-icon>logout</mat-icon>
      </button>
    </mat-toolbar>
  `,
  styles: `
    .brand {
      font-weight: 600;
      cursor: pointer;
    }
    .spacer {
      flex: 1 1 auto;
    }
    .username {
      margin-right: 0.5rem;
      opacity: 0.85;
    }
  `,
})
export class ToolbarComponent {
  private readonly auth = inject(AuthService);
  private readonly ws = inject(WebSocketService);
  private readonly router = inject(Router);

  readonly username = computed(() => this.auth.currentUser()?.username ?? '');

  logout(): void {
    this.ws.disconnect();
    this.auth.logout();
    void this.router.navigate(['/login']);
  }
}

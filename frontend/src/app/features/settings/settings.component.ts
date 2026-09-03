import { HttpClient } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

import { environment } from '../../../environments/environment';
import { PROTOCOL_MODES } from '../../core/models/protocol-mode';
import { ToolbarComponent } from '../../shared/toolbar/toolbar.component';

interface SystemConfig {
  bb84_qubits: number;
  qber_threshold: number;
  cascade_passes: number;
  mlkem_level: string;
  session_timeout_minutes: number;
}

/** Tela de configuracoes — parametros do sistema em modo leitura (F14.7). */
@Component({
  selector: 'app-settings',
  imports: [ToolbarComponent, MatCardModule, MatIconModule],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss',
})
export class SettingsComponent implements OnInit {
  private readonly http = inject(HttpClient);

  readonly config = signal<SystemConfig | null>(null);
  readonly protocolModes = PROTOCOL_MODES;

  ngOnInit(): void {
    this.http
      .get<SystemConfig>(`${environment.apiBaseUrl}/config`)
      .subscribe({ next: (config) => this.config.set(config) });
  }
}

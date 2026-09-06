import { Component, OnInit, inject, signal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

import { PROTOCOL_MODES } from '../../core/models/protocol-mode';
import { SystemConfig } from '../../core/models/system-config';
import { ConfigService } from '../../core/services/config.service';
import { ToolbarComponent } from '../../shared/toolbar/toolbar.component';

/** Tela de configuracoes — parametros do sistema em modo leitura (F14.7). */
@Component({
  selector: 'app-settings',
  imports: [ToolbarComponent, MatCardModule, MatIconModule],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss',
})
export class SettingsComponent implements OnInit {
  private readonly configService = inject(ConfigService);

  readonly config = signal<SystemConfig | null>(null);
  readonly protocolModes = PROTOCOL_MODES;

  ngOnInit(): void {
    this.configService.get().subscribe({ next: (config) => this.config.set(config) });
  }
}

import { Component, OnInit, computed, inject, input, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar } from '@angular/material/snack-bar';

import { EVE_MODE_LABELS, EveMode } from '../../core/models/adversary';
import { AdversaryService } from '../../core/services/adversary.service';

/** Controle do adversario simulado, usado no lobby e no painel de evidencias.
 *
 * A troca vale a partir da proxima sessao: a interferencia de Eve acontece
 * durante o estabelecimento da chave, nao durante a conversa.
 */
@Component({
  selector: 'app-adversary-control',
  imports: [MatButtonModule, MatIconModule],
  templateUrl: './adversary-control.component.html',
  styleUrl: './adversary-control.component.scss',
})
export class AdversaryControlComponent implements OnInit {
  private readonly adversary = inject(AdversaryService);
  private readonly snackBar = inject(MatSnackBar);

  /** `compact` encolhe o controle para caber na coluna lateral do chat. */
  readonly compact = input(false);

  readonly state = this.adversary.state;
  readonly busy = signal(false);
  readonly labels = EVE_MODE_LABELS;

  readonly active = computed(() => {
    const mode = this.state()?.mode;
    return mode !== undefined && mode !== 'PASSIVE';
  });

  ngOnInit(): void {
    this.adversary.refresh();
  }

  select(mode: EveMode): void {
    if (this.busy() || this.state()?.mode === mode) {
      return;
    }
    this.busy.set(true);
    this.adversary.setMode(mode).subscribe({
      next: () => {
        this.busy.set(false);
        this.snackBar.open(
          mode === 'PASSIVE'
            ? 'Espião desligado. Vale a partir da próxima sessão.'
            : `Espião ativado: ${this.labels[mode]}. Vale a partir da próxima sessão.`,
          'OK',
          { duration: 4000 },
        );
      },
      error: () => {
        this.busy.set(false);
        this.snackBar.open('Não foi possível alterar o adversário simulado.', 'OK', {
          duration: 5000,
        });
      },
    });
  }
}

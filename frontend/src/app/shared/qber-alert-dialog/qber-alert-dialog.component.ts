import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

import { QberAlert } from '../../core/services/crypto-metrics.service';
import { formatPercent } from '../format';

/** Dados do alerta, com o desfecho da sessao. */
export interface QberAlertDialogData extends QberAlert {
  /** `true` no hibrido: o BB84 cai, mas a sessao segue protegida pelo ML-KEM. */
  sessionContinues: boolean;
}

/** Modal de alerta de espionagem exibido quando o QBER ultrapassa o limiar (F14.6).
 *
 * O desfecho depende do modo. No BB84 puro nao ha chave sem o canal quantico, e
 * a sessao e abortada. No hibrido o backend descarta apenas o componente BB84 e
 * deriva a chave do ML-KEM — afirmar que a sessao "foi encerrada" ali seria falso.
 */
@Component({
  selector: 'app-qber-alert-dialog',
  imports: [MatDialogModule, MatButtonModule, MatIconModule],
  template: `
    <h2 mat-dialog-title class="title">
      <mat-icon class="icon">gpp_maybe</mat-icon>
      {{
        data.sessionContinues ? 'Espionagem detectada no canal quântico' : 'Espionagem detectada'
      }}
    </h2>
    <mat-dialog-content>
      <p>
        O QBER medido é de <strong>{{ qber }}</strong>, acima do limiar de
        <strong>{{ threshold }}</strong>. Medir um qubit o perturba: um erro dessa magnitude
        indica que alguém interceptou o canal.
      </p>
      @if (data.sessionContinues) {
        <p class="outcome continues">
          O componente BB84 foi descartado. A chave da sessão foi derivada apenas do ML-KEM, que
          não depende do canal quântico — a conversa continua protegida.
        </p>
      } @else {
        <p class="outcome aborted">
          Nenhuma chave foi gerada e a sessão foi abortada. No BB84 puro não há como seguir sem um
          canal quântico íntegro.
        </p>
      }
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-flat-button mat-dialog-close>Entendi</button>
    </mat-dialog-actions>
  `,
  styles: `
    .title {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .icon {
      color: var(--qc-danger);
    }

    .outcome {
      padding: 0.6rem 0.75rem;
      border-radius: var(--qc-radius-sm);
      line-height: 1.45;
    }

    .continues {
      background: var(--qc-safe-soft);
    }

    .aborted {
      background: var(--qc-danger-soft);
    }
  `,
})
export class QberAlertDialogComponent {
  readonly data = inject<QberAlertDialogData>(MAT_DIALOG_DATA);

  readonly qber = formatPercent(this.data.qber);
  readonly threshold = formatPercent(this.data.threshold);
}

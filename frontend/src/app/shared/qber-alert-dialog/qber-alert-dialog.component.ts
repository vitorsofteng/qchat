import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

import { QberAlert } from '../../core/services/crypto-metrics.service';

/** Modal de alerta de espionagem exibido quando o QBER ultrapassa o limiar (F14.6). */
@Component({
  selector: 'app-qber-alert-dialog',
  imports: [MatDialogModule, MatButtonModule, MatIconModule],
  template: `
    <h2 mat-dialog-title class="title">
      <mat-icon color="warn">gpp_maybe</mat-icon>
      Possível espionagem detectada
    </h2>
    <mat-dialog-content>
      <p>
        O QBER medido nesta sessão é de
        <strong>{{ (data.qber * 100).toFixed(1) }}%</strong>, acima do limiar de
        <strong>{{ (data.threshold * 100).toFixed(1) }}%</strong>.
      </p>
      <p>
        Conforme os princípios da mecânica quântica, essa perturbação indica que o
        canal pode ter sido interceptado. A sessão foi encerrada por segurança.
      </p>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-flat-button color="warn" mat-dialog-close>Entendi</button>
    </mat-dialog-actions>
  `,
  styles: `
    .title {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
  `,
})
export class QberAlertDialogComponent {
  readonly data = inject<QberAlert>(MAT_DIALOG_DATA);
}

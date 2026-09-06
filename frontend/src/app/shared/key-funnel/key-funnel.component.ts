import { Component, computed, input } from '@angular/core';

/** Um estagio da destilacao da chave. */
export interface FunnelStage {
  label: string;
  /** Quantidade de bits (ou qubits, no primeiro estagio). */
  value: number;
  /** O que aconteceu neste estagio, em uma linha. */
  note: string;
  /** Destaca o estagio final: a chave efetivamente usada. */
  final?: boolean;
}

interface RenderedStage extends FunnelStage {
  widthPercent: number;
  retained: string | null;
}

/** Funil de destilacao: de qubits transmitidos ate a chave de sessao.
 *
 * Cada barra e' proporcional ao primeiro estagio, e a etiqueta a direita mostra
 * quanto sobreviveu do estagio anterior — e' onde se ve, por exemplo, que o
 * sifting descarta cerca de metade dos qubits do BB84.
 */
@Component({
  selector: 'app-key-funnel',
  imports: [],
  templateUrl: './key-funnel.component.html',
  styleUrl: './key-funnel.component.scss',
})
export class KeyFunnelComponent {
  readonly stages = input.required<FunnelStage[]>();

  readonly rendered = computed<RenderedStage[]>(() => {
    const stages = this.stages();
    const base = stages[0]?.value ?? 0;
    if (base <= 0) {
      return [];
    }
    return stages.map((stage, index) => {
      const previous = index > 0 ? stages[index - 1].value : null;
      return {
        ...stage,
        // Piso de 2% para que um estagio pequeno continue visivel.
        widthPercent: Math.max(2, (stage.value / base) * 100),
        retained:
          previous && previous > 0 ? `${((stage.value / previous) * 100).toFixed(0)}%` : null,
      };
    });
  });

  format(value: number): string {
    return value.toLocaleString('pt-BR');
  }
}

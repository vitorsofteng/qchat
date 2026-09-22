import { Component, computed, input } from '@angular/core';

import { formatNumber, formatPercent } from '../format';

/** Geometria do arco: semicirculo de 180 graus, desenhado em sentido horario. */
const CX = 100;
const CY = 100;
const R = 78;
const STROKE = 16;

function polar(angleDeg: number): { x: number; y: number } {
  // 180 graus = extremidade esquerda; 0 grau = extremidade direita.
  const rad = (Math.PI * angleDeg) / 180;
  return { x: CX + R * Math.cos(rad), y: CY - R * Math.sin(rad) };
}

/** Caminho SVG do arco entre duas fracoes (0 = esquerda, 1 = direita). */
function arc(fromFraction: number, toFraction: number): string {
  const start = polar(180 - 180 * fromFraction);
  const end = polar(180 - 180 * toFraction);
  // O large-arc-flag do SVG vale 1 so para arcos acima de 180 graus. Como o
  // medidor inteiro e um semicirculo, a fracao 0,5 corresponde a 90 graus, e
  // compara-la com 0,5 forcava o "arco grande": para atende-lo com o mesmo
  // raio, o SVG desenhava o arco em outro centro, fora do trilho. O defeito
  // aparecia justamente acima do limiar (15% numa escala de 30%).
  const large = 180 * (toFraction - fromFraction) > 180 ? 1 : 0;
  return `M ${start.x} ${start.y} A ${R} ${R} 0 ${large} 1 ${end.x} ${end.y}`;
}

/** Medidor em arco da taxa de erro quantico, com a zona de limiar destacada.
 *
 * A escala vai de 0 ate `max`; a marca do limiar separa a faixa tolerada da
 * faixa que aborta a sessao. O arco preenchido muda de cor ao cruzar o limiar.
 */
@Component({
  selector: 'app-qber-gauge',
  imports: [],
  templateUrl: './qber-gauge.component.html',
  styleUrl: './qber-gauge.component.scss',
})
export class QberGaugeComponent {
  /** Valor medido, em fracao (0 a 1). `null` = ainda nao medido. */
  readonly value = input<number | null>(null);
  /** Limiar de aborto, em fracao. */
  readonly threshold = input<number>(0.15);
  /** Fim da escala, em fracao. */
  readonly max = input<number>(0.3);

  private readonly clampedMax = computed(() => Math.max(this.max(), this.threshold() * 1.5));

  readonly fraction = computed(() => {
    const value = this.value();
    return value === null ? 0 : Math.min(1, Math.max(0, value / this.clampedMax()));
  });

  readonly thresholdFraction = computed(() =>
    Math.min(1, this.threshold() / this.clampedMax()),
  );

  readonly exceeded = computed(() => {
    const value = this.value();
    return value !== null && value > this.threshold();
  });

  readonly display = computed(() => {
    const value = this.value();
    return value === null ? '—' : formatNumber(value * 100, 1);
  });

  readonly thresholdLabel = computed(() => formatPercent(this.threshold(), 0));
  readonly maxLabel = computed(() => formatPercent(this.clampedMax(), 0));

  // Trilho completo, zona tolerada, zona de alarme e arco do valor medido.
  readonly trackPath = arc(0, 1);
  readonly safeZonePath = computed(() => arc(0, this.thresholdFraction()));
  readonly dangerZonePath = computed(() => arc(this.thresholdFraction(), 1));
  readonly valuePath = computed(() => (this.fraction() > 0 ? arc(0, this.fraction()) : ''));

  readonly thresholdTick = computed(() => {
    const angle = 180 - 180 * this.thresholdFraction();
    const rad = (Math.PI * angle) / 180;
    const inner = R - STROKE / 2 - 3;
    const outer = R + STROKE / 2 + 3;
    return {
      x1: CX + inner * Math.cos(rad),
      y1: CY - inner * Math.sin(rad),
      x2: CX + outer * Math.cos(rad),
      y2: CY - outer * Math.sin(rad),
    };
  });

  readonly strokeWidth = STROKE;
}

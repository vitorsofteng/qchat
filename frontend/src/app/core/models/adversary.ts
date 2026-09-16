export type EveMode = 'PASSIVE' | 'INTERCEPT_RESEND' | 'BEAM_SPLITTING';

export interface AdversaryOption {
  mode: EveMode;
  description: string;
}

/** Situacao do adversario simulado, exposta por `/adversary`. */
export interface AdversaryState {
  mode: EveMode;
  description: string;
  beam_split_fraction: number;
  /** Em producao o controle e somente leitura. */
  locked: boolean;
  options: AdversaryOption[];
}

/** Rotulos curtos para os botoes do controle. */
export const EVE_MODE_LABELS: Record<EveMode, string> = {
  PASSIVE: 'Desligado',
  INTERCEPT_RESEND: 'Interceptar e reenviar',
  BEAM_SPLITTING: 'Divisão de feixe',
};

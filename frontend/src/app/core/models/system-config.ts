/** Parametros do sistema expostos pelo endpoint publico `/config`. */
export interface SystemConfig {
  bb84_qubits: number;
  qber_threshold: number;
  cascade_passes: number;
  mlkem_level: string;
  session_timeout_minutes: number;
}

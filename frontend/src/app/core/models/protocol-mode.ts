export type ProtocolMode = 'RSA' | 'MLKEM' | 'BB84' | 'HYBRID';

export interface ProtocolModeOption {
  value: ProtocolMode;
  label: string;
  /** Nome curto, para chips e cabecalhos. */
  short: string;
  /** Familia a que o modo pertence, exibida como etiqueta no card. */
  family: string;
  description: string;
  icon: string;
  /** Indica se o modo expoe metrica de QBER. */
  hasQber: boolean;
  /** O modo percebe um espiao no canal? Apenas os quanticos percebem. */
  detectsEavesdropping: boolean;
  /** Resiste a um computador quantico rodando o algoritmo de Shor? */
  quantumResistant: boolean;
}

export const PROTOCOL_MODES: ProtocolModeOption[] = [
  {
    value: 'RSA',
    label: 'RSA (clássico)',
    short: 'RSA',
    family: 'Clássico',
    description: 'Criptografia clássica de chave pública — controle experimental.',
    icon: 'vpn_key',
    hasQber: false,
    detectsEavesdropping: false,
    quantumResistant: false,
  },
  {
    value: 'MLKEM',
    label: 'ML-KEM (pós-quântico)',
    short: 'ML-KEM',
    family: 'Pós-quântico',
    description: 'Encapsulamento de chave pós-quântico — NIST FIPS 203.',
    icon: 'lock',
    hasQber: false,
    detectsEavesdropping: false,
    quantumResistant: true,
  },
  {
    value: 'BB84',
    label: 'BB84 (QKD)',
    short: 'BB84',
    family: 'Quântico',
    description: 'Distribuição de chaves quânticas com detecção de espionagem.',
    icon: 'blur_on',
    hasQber: true,
    detectsEavesdropping: true,
    quantumResistant: true,
  },
  {
    value: 'HYBRID',
    label: 'Híbrido (BB84 + ML-KEM)',
    short: 'Híbrido',
    family: 'Quântico + pós-quântico',
    description: 'Combina QKD e PQC via HKDF — seguro enquanto um componente resistir.',
    icon: 'shield',
    hasQber: true,
    detectsEavesdropping: true,
    quantumResistant: true,
  },
];

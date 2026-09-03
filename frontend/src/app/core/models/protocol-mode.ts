export type ProtocolMode = 'RSA' | 'MLKEM' | 'BB84' | 'HYBRID';

export interface ProtocolModeOption {
  value: ProtocolMode;
  label: string;
  description: string;
  /** Indica se o modo expoe metrica de QBER. */
  hasQber: boolean;
}

export const PROTOCOL_MODES: ProtocolModeOption[] = [
  {
    value: 'RSA',
    label: 'RSA (clássico)',
    description: 'Criptografia clássica de chave pública — controle experimental.',
    hasQber: false,
  },
  {
    value: 'MLKEM',
    label: 'ML-KEM (pós-quântico)',
    description: 'Encapsulamento de chave pós-quântico — NIST FIPS 203.',
    hasQber: false,
  },
  {
    value: 'BB84',
    label: 'BB84 (QKD)',
    description: 'Distribuição de chaves quânticas com detecção de espionagem.',
    hasQber: true,
  },
  {
    value: 'HYBRID',
    label: 'Híbrido (BB84 + ML-KEM)',
    description: 'Combina QKD e PQC via HKDF — seguro enquanto um componente resistir.',
    hasQber: true,
  },
];

export type WSMessageType =
  | 'session_request'
  | 'session_accepted'
  | 'session_rejected'
  | 'session_closed'
  | 'key_exchange'
  | 'key_established'
  | 'chat_message'
  | 'qber_alert'
  | 'typing'
  | 'ping'
  | 'pong'
  | 'error';

export interface WSMessage {
  type: WSMessageType;
  session_id?: string | null;
  payload: Record<string, unknown>;
}

/** Envelope cifrado AES-256-GCM, espelha o EncryptedEnvelope do backend. */
export interface EncryptedEnvelope {
  nonce: string;
  ciphertext: string;
  tag: string;
  sequence_number: number;
  timestamp: string;
}

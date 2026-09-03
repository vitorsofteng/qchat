export interface ChatMessage {
  text: string;
  /** true = enviada pelo usuario local; false = recebida do interlocutor. */
  outgoing: boolean;
  timestamp: string;
}

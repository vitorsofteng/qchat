import { Injectable } from '@angular/core';

import { EncryptedEnvelope } from '../models/ws-message';

/** Cifragem AES-256-GCM de mensagens via Web Crypto API.
 *
 * Espelha o `MessageCipher` do backend: nonce de 96 bits, tag de 128 bits e
 * associated data `session_id|sequence_number|timestamp`. As mensagens sao
 * cifradas no cliente com a chave de sessao distribuida pelo servidor.
 */
@Injectable({ providedIn: 'root' })
export class MessageCryptoService {
  private readonly encoder = new TextEncoder();
  private readonly decoder = new TextDecoder();

  async importKey(keyBase64: string): Promise<CryptoKey> {
    return crypto.subtle.importKey(
      'raw',
      this.fromBase64(keyBase64),
      { name: 'AES-GCM' },
      false,
      ['encrypt', 'decrypt'],
    );
  }

  async encrypt(
    key: CryptoKey,
    plaintext: string,
    sessionId: string,
    sequenceNumber: number,
    timestamp: string,
  ): Promise<EncryptedEnvelope> {
    const nonce = crypto.getRandomValues(new Uint8Array(12));
    const aad = this.encoder.encode(`${sessionId}|${sequenceNumber}|${timestamp}`);
    const output = new Uint8Array(
      await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv: nonce, additionalData: aad },
        key,
        this.encoder.encode(plaintext),
      ),
    );
    // O Web Crypto anexa a tag de 16 bytes ao final do ciphertext.
    return {
      nonce: this.toBase64(nonce),
      ciphertext: this.toBase64(output.slice(0, output.length - 16)),
      tag: this.toBase64(output.slice(output.length - 16)),
      sequence_number: sequenceNumber,
      timestamp,
    };
  }

  async decrypt(key: CryptoKey, envelope: EncryptedEnvelope, sessionId: string): Promise<string> {
    const aad = this.encoder.encode(
      `${sessionId}|${envelope.sequence_number}|${envelope.timestamp}`,
    );
    const combined = this.concat(
      this.fromBase64(envelope.ciphertext),
      this.fromBase64(envelope.tag),
    );
    const plaintext = await crypto.subtle.decrypt(
      { name: 'AES-GCM', iv: this.fromBase64(envelope.nonce), additionalData: aad },
      key,
      combined,
    );
    return this.decoder.decode(plaintext);
  }

  private toBase64(bytes: Uint8Array): string {
    let binary = '';
    for (const byte of bytes) {
      binary += String.fromCharCode(byte);
    }
    return btoa(binary);
  }

  private fromBase64(value: string): Uint8Array<ArrayBuffer> {
    const binary = atob(value);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes;
  }

  private concat(first: Uint8Array, second: Uint8Array): Uint8Array<ArrayBuffer> {
    const result = new Uint8Array(first.length + second.length);
    result.set(first, 0);
    result.set(second, first.length);
    return result;
  }
}

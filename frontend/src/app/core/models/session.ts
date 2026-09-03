import { ProtocolMode } from './protocol-mode';

export type SessionState =
  | 'pending'
  | 'establishing'
  | 'active'
  | 'rejected'
  | 'closed'
  | 'aborted';

export interface SessionView {
  id: string;
  alice_id: string;
  bob_id: string;
  mode: ProtocolMode;
  state: SessionState;
  qber: number | null;
  created_at: string;
}

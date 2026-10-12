export interface Session {
  sessionId: string;
  machineId: string;
  startTime: string;
  endTime?: string | null;
  status: 'ACTIVE' | 'IDLE' | 'LOCKED' | 'COMPLETED' | 'PANIC_LOCKED';
  eventCount?: number;
  integrityValid?: boolean;
}

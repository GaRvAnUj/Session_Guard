export interface SessionEventData {
  // Process
  process_name?: string;
  cpu_percent?: number;
  memory_mb?: number;
  exe_path_hash?: string;
  exe_path_hash_short?: string;

  // File
  operation?: string;
  extension?: string;
  size_bytes?: number;
  path_hash?: string;
  path_hash_short?: string;

  // Network
  protocol?: string;
  remote_port?: number;
  bytes_sent?: number;
  bytes_received?: number;
  remote_ip_hash?: string;
  remote_ip_hash_short?: string;

  // Lifecycle
  action?: string;
  machine_id?: string;
  status?: string;

  [key: string]: any;
}

export interface SessionEvent {
  id: number;
  sessionId: string;
  timestamp: string;
  eventType: string;
  eventData: SessionEventData;
  integrityHash: string;
  previousEventHash: string;
  verified: boolean;
}

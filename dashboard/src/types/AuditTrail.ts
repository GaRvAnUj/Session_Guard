import { SessionEvent } from './SessionEvent';

export interface AuditTrailResponse {
  sessionId: string;
  totalEvents: number;
  chainValid: boolean;
  events: SessionEvent[];
}

export interface IntegrityVerificationReport {
  sessionId: string;
  valid: boolean;
  totalEventsEvaluated: number;
  verifiedEventsCount: number;
  brokenLinks: number[];
  issues: string[];
  verificationTimestamp: string;
}

export interface ComplianceStats {
  gdprCompliant: boolean;
  retentionDays: number;
  screenRecordingActive: boolean;
  keyloggingActive: boolean;
  contentInspectionActive: boolean;
  metadataHashingActive: boolean;
  hmacChainVerificationActive: boolean;
  adminManagedQuarantineActive: boolean;
}

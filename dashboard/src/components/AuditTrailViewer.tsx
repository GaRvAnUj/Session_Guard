import React, { useState, useEffect, useMemo, useRef } from 'react';
import { api } from '../services/api';
import { SessionEvent } from '../types/SessionEvent';
import { IntegrityVerificationReport } from '../types/AuditTrail';
import { SessionTimeline } from './SessionTimeline';
import {
  IconFileText,
  IconShieldCheck,
  IconShieldAlert,
  IconSearch,
  IconCheck,
  IconAlertTriangle,
  IconEye,
  IconTerminal,
} from './Icons';

interface Props {
  accessToken: string;
  selectedSessionId: string | null;
}

export const AuditTrailViewer: React.FC<Props> = ({ accessToken, selectedSessionId }) => {
  const [sessionId, setSessionId] = useState<string>(selectedSessionId || '');
  const [machineId, setMachineId] = useState<string>('');
  const [events, setEvents] = useState<SessionEvent[]>([]);
  const [chainValid, setChainValid] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [verificationReport, setVerificationReport] = useState<IntegrityVerificationReport | null>(null);
  const [viewMode, setViewMode] = useState<'timeline' | 'json'>('timeline');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const auditRequestId = useRef(0);

  useEffect(() => {
    if (selectedSessionId) {
      setSessionId(selectedSessionId);
      loadAudit(selectedSessionId);
    }
    return () => {
      auditRequestId.current += 1;
    };
  }, [accessToken, selectedSessionId]);

  const loadAudit = async (targetId?: string) => {
    const sid = targetId || sessionId;
    const requestId = ++auditRequestId.current;
    setLoading(true);
    try {
      const res = await api.getAuditTrail(accessToken, sid, machineId);
      if (requestId !== auditRequestId.current) return;
      setEvents(res.events);
      setChainValid(res.chainValid);

      if (sid) {
        const report = await api.verifyIntegrity(accessToken, sid);
        if (requestId !== auditRequestId.current) return;
        setVerificationReport(report);
      }
    } catch (e) {
      if (requestId !== auditRequestId.current) return;
      console.error('Error loading audit trail:', e);
    } finally {
      if (requestId === auditRequestId.current) setLoading(false);
    }
  };

  const handleVerifyChain = async () => {
    console.log('Verifying chain for session:', sessionId);
    console.log('Using token:', accessToken);
    if (!sessionId) {
      alert('Please enter a session ID to verify');
      return;
    }
    const requestId = ++auditRequestId.current;
    setLoading(true);
    try {
      const report = await api.verifyIntegrity(accessToken, sessionId);
      if (requestId !== auditRequestId.current) return;
      console.log('Verification report received:', report);
      setVerificationReport(report);
      setChainValid(report.valid);
    } catch (e) {
      if (requestId !== auditRequestId.current) return;
      console.error('Verification failure:', e);
      // Create error report for display
      const errorReport: IntegrityVerificationReport = {
        sessionId: sessionId,
        valid: false,
        totalEventsEvaluated: 0,
        verifiedEventsCount: 0,
        brokenLinks: [],
        issues: [`Network error: ${e instanceof Error ? e.message : 'Unknown error'}`],
        verificationTimestamp: new Date().toISOString()
      };
      setVerificationReport(errorReport);
      setChainValid(false);
    } finally {
      if (requestId === auditRequestId.current) setLoading(false);
    }
  };


  const filteredEvents = useMemo(() => {
    if (categoryFilter === 'all') return events;
    return events.filter((ev) => ev.eventType === categoryFilter);
  }, [events, categoryFilter]);

  return (
    <div className="card audit-trail-viewer">
      <div className="viewer-header">
        <div className="title-row">
          <div className="title-left">
            <IconFileText size={20} className="text-accent" />
            <div>
              <h2>Audit Ledger & Hash Continuity</h2>
            </div>
          </div>

          <div className="title-right">
            <span className={`status-badge-chip ${chainValid ? 'badge-verified' : 'badge-tampered'}`}>
              {chainValid ? (
                <>
                  <IconShieldCheck size={14} />
                  <span>Hash Chain Intact</span>
                </>
              ) : (
                <>
                  <IconShieldAlert size={14} />
                  <span>Tamper Detected</span>
                </>
              )}
            </span>
          </div>
        </div>

        <div className="controls-row">
          <input
            type="text"
            placeholder="Session ID (e.g. sess_PC_LAB_01)..."
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            className="form-input"
            style={{ minWidth: '220px' }}
          />

          <input
            type="text"
            placeholder="Station ID (e.g. PC_LAB_01)..."
            value={machineId}
            onChange={(e) => setMachineId(e.target.value)}
            className="form-input"
            style={{ width: '180px' }}
          />

          <button className="btn btn-primary" onClick={() => loadAudit()} disabled={loading}>
            <IconSearch size={14} />
            {loading ? 'Querying...' : 'Filter Ledger'}
          </button>

          {sessionId && (
            <button className="btn btn-secondary" onClick={handleVerifyChain} disabled={loading}>
              <IconShieldCheck size={14} />
              {loading ? 'Verifying...' : 'Verify Chain Integrity'}
            </button>
          )}

          <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.35rem' }}>
            <button
              className={`btn btn-sm ${categoryFilter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setCategoryFilter('all')}
            >
              All ({events.length})
            </button>
            <button
              className={`btn btn-sm ${categoryFilter === 'process_start' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setCategoryFilter('process_start')}
            >
              Processes
            </button>
            <button
              className={`btn btn-sm ${categoryFilter === 'network_connection' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setCategoryFilter('network_connection')}
            >
              Network
            </button>
            <button
              className={`btn btn-sm ${categoryFilter === 'file_operation' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setCategoryFilter('file_operation')}
            >
              Files
            </button>
          </div>
        </div>
      </div>

      {/* Privacy Guarantee Banner */}
      <div className="privacy-guarantee-banner">
        <div className="guarantee-col">
          <IconShieldCheck size={15} style={{ color: 'var(--color-success)', flexShrink: 0 }} />
          <div>
            <strong>Privacy Enforcement:</strong> Metadata Only • Keystroke Logging Disabled • Screen Capture Prohibited • Paths & IPs Pseudonymized
          </div>
        </div>

        <div className="view-toggle">
          <button
            className={`toggle-btn ${viewMode === 'timeline' ? 'active' : ''}`}
            onClick={() => setViewMode('timeline')}
          >
            <IconEye size={12} style={{ marginRight: '4px', verticalAlign: '-1px' }} />
            Timeline View
          </button>
          <button
            className={`toggle-btn ${viewMode === 'json' ? 'active' : ''}`}
            onClick={() => setViewMode('json')}
          >
            <IconTerminal size={12} style={{ marginRight: '4px', verticalAlign: '-1px' }} />
            Raw Ledger JSON
          </button>
        </div>
      </div>

      {/* Verification status report */}
      {verificationReport && (
        <div className={`verification-summary-banner ${verificationReport.valid ? 'valid' : 'invalid'}`}>
          <div className="summary-col">
            {verificationReport.valid ? (
              <IconCheck size={18} style={{ color: 'var(--color-success)', marginTop: '2px', flexShrink: 0 }} />
            ) : (
              <IconAlertTriangle size={18} style={{ color: 'var(--color-danger)', marginTop: '2px', flexShrink: 0 }} />
            )}
            <div>
              <strong>
                {verificationReport.valid
                  ? 'Cryptographic Hash Chain Validated'
                  : 'INTEGRITY ALERT: Broken Cryptographic Linkage Detected!'}
              </strong>
              {verificationReport.issues.length > 0 && (
                <div className="issue-text">Mismatch: {verificationReport.issues.join('; ')}</div>
              )}
            </div>
          </div>
          <div className="timestamp-badge">
            Verified: {new Date(verificationReport.verificationTimestamp).toLocaleTimeString()}
          </div>
        </div>
      )}

      {/* Events Viewer */}
      <div className="viewer-content">
        {loading ? (
          <div className="loading-state">Decrypting and validating session audit trail...</div>
        ) : filteredEvents.length === 0 ? (
          <div className="empty-state">No audit ledger records match the selected filter.</div>
        ) : viewMode === 'timeline' ? (
          <SessionTimeline events={filteredEvents} />
        ) : (
          <div className="json-container">
            <pre className="code-block">
              {JSON.stringify(filteredEvents, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

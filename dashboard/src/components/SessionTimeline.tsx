import React from 'react';
import { SessionEvent } from '../types/SessionEvent';
import { IntegrityVerificationBadge } from './IntegrityVerificationBadge';
import {
  IconCpu,
  IconFileText,
  IconGlobe,
  IconLock,
  IconActivity,
  IconLink,
  IconTerminal,
} from './Icons';

interface Props {
  events: SessionEvent[];
}

export const SessionTimeline: React.FC<Props> = ({ events }) => {
  if (events.length === 0) {
    return <div className="timeline-empty">Select a session to inspect chronological metadata events.</div>;
  }

  const renderEventIcon = (type: string) => {
    switch (type) {
      case 'process_start':
        return <IconCpu size={13} />;
      case 'process_terminate':
        return <IconTerminal size={13} />;
      case 'file_operation':
        return <IconFileText size={13} />;
      case 'network_connection':
        return <IconGlobe size={13} />;
      case 'session_lifecycle':
        return <IconLock size={13} />;
      default:
        return <IconActivity size={13} />;
    }
  };

  const getEventBadgeClass = (type: string) => {
    switch (type) {
      case 'process_start':
      case 'process_terminate':
        return 'badge-proc';
      case 'file_operation':
        return 'badge-file';
      case 'network_connection':
        return 'badge-net';
      default:
        return 'badge-lifecycle';
    }
  };

  return (
    <div className="session-timeline">
      <div className="timeline-flow">
        {events.map((ev, index) => {
          const isTampered = !ev.verified;
          return (
            <div key={ev.id || index} className={`timeline-entry ${isTampered ? 'tampered-entry' : ''}`}>
              <div className="timeline-rail">
                <div className="rail-icon-wrapper">
                  {renderEventIcon(ev.eventType)}
                </div>
                {index < events.length - 1 && <div className="rail-line"></div>}
              </div>

              <div className="timeline-card">
                <div className="entry-header">
                  <div className="header-left">
                    <span className={`event-type-badge ${getEventBadgeClass(ev.eventType)}`}>
                      {ev.eventType.replace('_', ' ').toUpperCase()}
                    </span>
                    <IntegrityVerificationBadge verified={ev.verified} compact />
                  </div>
                  <span className="entry-time">{new Date(ev.timestamp).toLocaleTimeString()}</span>
                </div>

                <div className="entry-body">
                  {ev.eventType === 'process_start' && (
                    <div className="metadata-grid">
                      <div className="meta-pill">
                        <strong>Process:</strong> {ev.eventData.process_name}
                      </div>
                      <div className="meta-pill">
                        <strong>CPU Load:</strong> {ev.eventData.cpu_percent}%
                      </div>
                      <div className="meta-pill">
                        <strong>Memory:</strong> {ev.eventData.memory_mb} MB
                      </div>
                      {ev.eventData.exe_path_hash_short && (
                        <div className="meta-pill privacy-pill" title="Executable full path SHA-256 hashed">
                          <strong>Path Digest:</strong> {ev.eventData.exe_path_hash_short}...
                        </div>
                      )}
                    </div>
                  )}

                  {ev.eventType === 'file_operation' && (
                    <div className="metadata-grid">
                      <div className="meta-pill">
                        <strong>Operation:</strong> {ev.eventData.operation}
                      </div>
                      <div className="meta-pill">
                        <strong>Extension:</strong> {ev.eventData.extension || 'N/A'}
                      </div>
                      <div className="meta-pill">
                        <strong>Size:</strong> {(ev.eventData.size_bytes || 0).toLocaleString()} bytes
                      </div>
                      {ev.eventData.path_hash_short && (
                        <div className="meta-pill privacy-pill" title="Actual filename & directory cryptographically hashed">
                          <strong>Path Digest:</strong> {ev.eventData.path_hash_short}...
                        </div>
                      )}
                    </div>
                  )}

                  {ev.eventType === 'network_connection' && (
                    <div className="metadata-grid">
                      <div className="meta-pill">
                        <strong>Protocol:</strong> {ev.eventData.protocol}
                      </div>
                      <div className="meta-pill">
                        <strong>Remote Port:</strong> {ev.eventData.remote_port}
                      </div>
                      <div className="meta-pill">
                        <strong>Traffic Vol:</strong> ↓ {ev.eventData.bytes_received} B / ↑ {ev.eventData.bytes_sent} B
                      </div>
                      {ev.eventData.remote_ip_hash_short && (
                        <div className="meta-pill privacy-pill" title="Remote IP and domain address SHA-256 hashed">
                          <strong>Host Digest:</strong> {ev.eventData.remote_ip_hash_short}...
                        </div>
                      )}
                    </div>
                  )}

                  {ev.eventType === 'session_lifecycle' && (
                    <div className="metadata-grid">
                      <div className="meta-pill">
                        <strong>Action:</strong> {ev.eventData.action}
                      </div>
                      <div className="meta-pill">
                        <strong>Workstation:</strong> {ev.eventData.machine_id}
                      </div>
                      <div className="meta-pill">
                        <strong>State:</strong> {ev.eventData.status}
                      </div>
                    </div>
                  )}
                </div>

                <div className="entry-cryptography">
                  <div className="hash-chain-info">
                    <span className="hash-label">HMAC:</span>
                    <code>{ev.integrityHash.substring(0, 18)}...</code>
                    <IconLink size={12} style={{ color: 'var(--text-muted)' }} />
                    <span className="hash-label">Prev:</span>
                    <code>{ev.previousEventHash.substring(0, 18)}...</code>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

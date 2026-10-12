import React, { useState } from 'react';
import { Session } from '../types/Session';
import { IconMonitor, IconSearch, IconZap, IconLock } from './Icons';

interface Props {
  sessions: Session[];
  selectedSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onPanicLock: (machineId: string) => void;
  loading: boolean;
  isolatingMachineId?: string | null;
}

export const ActiveSessionsPanel: React.FC<Props> = ({
  sessions,
  selectedSessionId,
  onSelectSession,
  onPanicLock,
  loading,
  isolatingMachineId,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const formatDuration = (startTime: string) => {
    const diff = Math.floor((Date.now() - new Date(startTime).getTime()) / 1000);
    if (diff < 60) return `${diff}s`;
    const mins = Math.floor(diff / 60);
    const hrs = Math.floor(mins / 60);
    return hrs > 0 ? `${hrs}h ${mins % 60}m` : `${mins}m`;
  };

  const filteredSessions = sessions.filter(
    (s) =>
      s.machineId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.sessionId.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="card active-sessions-panel">
      <div className="panel-header">
        <div>
          <h3>
            <IconMonitor size={17} className="text-accent" />
            Lab Computers
          </h3>
          <span className="item-path" style={{ fontSize: '0.75rem', color: 'var(--ink-faint)', marginTop: '2px' }}>
            Real-time monitoring
          </span>
        </div>
        <span className="live-indicator">
          <span className="pulse-dot"></span> LIVE
        </span>
      </div>

      <div style={{ padding: '0.65rem 1.25rem 0', display: 'flex' }}>
        <input
          type="text"
          placeholder="Search computers..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="form-input"
          style={{ width: '100%', fontSize: '0.78rem', padding: '0.35rem 0.65rem' }}
        />
      </div>

      {loading ? (
        <div className="loading-state">Checking computer status...</div>
      ) : filteredSessions.length === 0 ? (
        <div className="empty-state">No computers found matching your search.</div>
      ) : (
        <div className="sessions-grid">
          {filteredSessions.map((s) => {
            const isSelected = s.sessionId === selectedSessionId;
            const isLocked = s.status === 'PANIC_LOCKED' || s.status === 'LOCKED';
            const isBusy = isolatingMachineId === s.machineId;

            return (
              <div
                key={s.sessionId}
                className={`session-card ${isSelected ? 'selected' : ''} ${isLocked ? 'panic-active' : ''}`}
                onClick={() => onSelectSession(s.sessionId)}
              >
                <div className="card-top">
                  <div className="machine-info">
                    <IconMonitor size={16} className="machine-icon" />
                    <strong className="machine-title">{s.machineId}</strong>
                  </div>
                  <span className={`status-pill pill-${s.status.toLowerCase()}`}>
                    {s.status}
                  </span>
                </div>

                <div className="card-meta">
                  <div className="meta-row">
                    <span className="meta-label">Session ID:</span>
                    <span className="meta-val monospace">{s.sessionId.substring(0, 16)}...</span>
                  </div>
                  <div className="meta-row">
                    <span className="meta-label">Active Time:</span>
                    <span className="meta-val">{formatDuration(s.startTime)}</span>
                  </div>
                  <div className="meta-row">
                    <span className="meta-label">Audit Events:</span>
                    <span className="meta-val" style={{ fontWeight: 600 }}>{s.eventCount || 0}</span>
                  </div>
                </div>

                <div className="card-actions" onClick={(e) => e.stopPropagation()}>
                  <button
                    className="btn btn-secondary btn-sm"
                    style={{ flex: 1 }}
                    onClick={() => onSelectSession(s.sessionId)}
                  >
                    <IconSearch size={12} />
                    View Details
                  </button>
                  {s.status === 'ACTIVE' && (
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onPanicLock(s.machineId);
                      }}
                      disabled={isBusy}
                      title="Lock this computer and clean up user data"
                    >
                      <IconZap size={12} />
                      {isBusy ? 'Locking...' : 'Lock Now'}
                    </button>
                  )}
                  {s.status === 'PANIC_LOCKED' && (
                    <span
                      className="status-pill pill-panic_locked"
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', padding: '0.35rem 0.6rem' }}
                    >
                      <IconLock size={12} /> Locked
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

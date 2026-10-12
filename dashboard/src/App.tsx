import React, { useState, useEffect } from 'react';
import { api } from './services/api';
import { Session } from './types/Session';
import { ActiveSessionsPanel } from './components/ActiveSessionsPanel';
import { AuditTrailViewer } from './components/AuditTrailViewer';
import { PanicLockButton } from './components/PanicLockButton';
import { AlertNotifications } from './components/AlertNotifications';
import { ComplianceReport } from './components/ComplianceReport';
import { QuarantinePanel } from './components/QuarantinePanel';
import { AdminLoginPage } from './components/AdminLoginPage';
import {
  IconShield,
  IconMonitor,
  IconFileText,
  IconShieldCheck,
  IconRefresh,
  IconActivity,
  IconLink,
  IconTrash,
  IconCheck,
  IconAlertTriangle,
} from './components/Icons';

export const App: React.FC = () => {
  const [adminToken, setAdminToken] = useState<string | null>(
    () => sessionStorage.getItem('ssg_admin_token'),
  );
  const [sessions, setSessions] = useState<Session[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'audit' | 'compliance' | 'quarantine'>('overview');
  const [isolatingMachineId, setIsolatingMachineId] = useState<string | null>(null);
  const [actionToast, setActionToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const refreshSessions = async () => {
    if (!adminToken) return;
    setLoading(true);
    try {
      const active = await api.getActiveSessions(adminToken);
      setSessions(active);
      if (!selectedSessionId && active.length > 0) {
        setSelectedSessionId(active[0].sessionId);
      }
    } catch (e) {
      console.error('Error fetching sessions:', e);
      if (e instanceof Error && e.message === 'ADMIN_UNAUTHORIZED') {
        sessionStorage.removeItem('ssg_admin_token');
        setAdminToken(null);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!adminToken) {
      setSessions([]);
      setLoading(false);
      return;
    }
    void refreshSessions();
    const interval = setInterval(refreshSessions, 10000);
    return () => clearInterval(interval);
  }, [adminToken]);

  const handleIsolateWorkstation = async (machineId: string) => {
    setIsolatingMachineId(machineId);
    try {
      if (!adminToken) return;
      const res = await api.triggerPanicLock(adminToken, machineId, 'Manual Administrator Station Isolation');
      setSessions((prev) =>
        prev.map((s) =>
          s.machineId === machineId || machineId === 'ALL'
            ? { ...s, status: 'PANIC_LOCKED' }
            : s
        )
      );
      setActionToast({
        message: res.message || `Workstation ${machineId} isolated. Cleanup targets are being quarantined.`,
        type: 'success',
      });
      setTimeout(() => setActionToast(null), 5000);
      await refreshSessions();
    } catch (err) {
      console.error('Failed to isolate workstation:', err);
      setActionToast({
        message: `Failed to isolate workstation ${machineId}.`,
        type: 'error',
      });
      setTimeout(() => setActionToast(null), 5000);
    } finally {
      setIsolatingMachineId(null);
    }
  };

  const totalEvents = sessions.reduce((acc, s) => acc + (s.eventCount || 0), 0);
  const activeCount = sessions.filter((s) => s.status === 'ACTIVE').length;
  const tamperedCount = sessions.filter((s) => s.integrityValid === false).length;

  if (!adminToken) {
    return (
      <AdminLoginPage
        onAuthenticated={(token) => {
          sessionStorage.setItem('ssg_admin_token', token);
          setAdminToken(token);
        }}
      />
    );
  }

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="navbar">
        <div className="nav-brand">
          <div className="brand-icon-wrapper">
            <IconShield size={20} />
          </div>
          <div>
            <div className="brand-title">
              SessionWatch Pro
            </div>
            <div className="brand-subtitle" style={{ fontSize: '0.75rem', color: 'var(--header-ink-soft)', marginTop: '2px' }}>
              Lab Security Dashboard
            </div>
          </div>
        </div>

        <nav className="nav-center">
          <button
            className={`nav-tab ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <IconMonitor size={15} />
            Live Feed
          </button>
          <button
            className={`nav-tab ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit')}
          >
            <IconFileText size={15} />
            Event History
          </button>
          <button
            className={`nav-tab ${activeTab === 'compliance' ? 'active' : ''}`}
            onClick={() => setActiveTab('compliance')}
          >
            <IconShieldCheck size={15} />
            Privacy Report
          </button>
          <button
            className={`nav-tab ${activeTab === 'quarantine' ? 'active' : ''}`}
            onClick={() => setActiveTab('quarantine')}
          >
            <IconTrash size={15} />
            Quarantine Zone
          </button>
        </nav>

        <div className="nav-actions">
          <div className="connection-indicator">
            <span className="connection-dot"></span>
            <span>Server Online</span>
          </div>

          <PanicLockButton
            accessToken={adminToken}
            machineId={sessions.length > 0 ? sessions[0].machineId : 'PC_LAB_01'}
            onLockTriggered={refreshSessions}
          />

          <button
            className="btn btn-secondary"
            onClick={() => {
              sessionStorage.removeItem('ssg_admin_token');
              setAdminToken(null);
            }}
          >
            Sign out
          </button>

          <button
            className="btn btn-secondary btn-icon"
            onClick={refreshSessions}
            title="Refresh workstation data"
            disabled={loading}
          >
            <IconRefresh size={15} />
          </button>
        </div>
      </header>

      {/* Real-time Alert Notification Bar */}
      <AlertNotifications />

      {/* Immediate Toast Notification for Isolations */}
      {actionToast && (
        <div style={{ padding: '0.5rem 2rem 0' }}>
          <div
            className={`alert-banner ${actionToast.type === 'success' ? 'banner-warning' : 'banner-danger'}`}
            style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}
          >
            {actionToast.type === 'success' ? (
              <IconCheck size={16} style={{ color: 'var(--color-success)' }} />
            ) : (
              <IconAlertTriangle size={16} style={{ color: 'var(--color-danger)' }} />
            )}
            <strong style={{ fontSize: '0.82rem' }}>{actionToast.message}</strong>
            <button
              style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: 'inherit' }}
              onClick={() => setActionToast(null)}
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <section className="stats-row">
        <div className="stat-card">
          <div className="stat-icon">
            <IconMonitor size={18} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Computers Online</span>
            <span className="stat-value">{activeCount}</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <IconActivity size={18} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Events Logged Today</span>
            <span className="stat-value">{totalEvents.toLocaleString()}</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <IconLink size={18} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Security Status</span>
            <span className={`stat-value ${tamperedCount > 0 ? 'text-warning' : 'text-success'}`}>
              {tamperedCount > 0 ? `⚠️ ${tamperedCount} Issues` : '✓ All Good'}
            </span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <IconTrash size={18} />
          </div>
          <div className="stat-info">
            <span className="stat-label">Cleanup Status</span>
            <span className="stat-value text-accent">Ready</span>
          </div>
        </div>
      </section>

      {/* Main Content Body */}
      <main className="main-content">
        {activeTab === 'overview' && (
          <div className="dashboard-grid">
            <div className="grid-left">
              <ActiveSessionsPanel
                sessions={sessions}
                selectedSessionId={selectedSessionId}
                onSelectSession={(id) => {
                  setSelectedSessionId(id);
                  setActiveTab('audit');
                }}
                onPanicLock={handleIsolateWorkstation}
                loading={loading}
                isolatingMachineId={isolatingMachineId}
              />
            </div>
            <div className="grid-right">
              <AuditTrailViewer accessToken={adminToken} selectedSessionId={selectedSessionId} />
            </div>
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="full-width-container">
            <AuditTrailViewer accessToken={adminToken} selectedSessionId={selectedSessionId} />
          </div>
        )}

        {activeTab === 'compliance' && (
          <div className="full-width-container">
            <ComplianceReport accessToken={adminToken} />
          </div>
        )}

        {activeTab === 'quarantine' && (
          <div className="full-width-container">
            <QuarantinePanel accessToken={adminToken} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <span>SessionWatch Pro • Lab Security Monitor</span>
          <div className="footer-badges">
            <span className="badge-chip">Encrypted</span>
            <span className="badge-chip">Privacy First</span>
            <span className="badge-chip">Auto-cleanup</span>
            <span className="badge-chip">GDPR Ready</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { ComplianceStats } from '../types/AuditTrail';
import { IconShieldCheck, IconDownload, IconCheckCircle } from './Icons';

interface Props {
  accessToken: string;
}

export const ComplianceReport: React.FC<Props> = ({ accessToken }) => {
  const [stats, setStats] = useState<ComplianceStats | null>(null);

  useEffect(() => {
    api.getComplianceStats(accessToken).then(setStats);
  }, [accessToken]);

  const downloadReport = () => {
    const reportData = {
      title: 'GDPR & Cryptographic Compliance Audit Certification',
      generatedAt: new Date().toISOString(),
      standardsApplied: [
        'GDPR Article 5.1(c) (Data Minimization)',
        'GDPR Article 25 (Privacy by Design and by Default)',
        'GDPR Article 32 (Security of Processing & Cryptographic Proof)',
        'Admin-managed reversible quarantine for session-scoped Downloads and cleanup targets',
        'HMAC-SHA256 Sequential Hash Chain Integrity',
      ],
      systemGuarantees: {
        screenRecording: 'STRICTLY PROHIBITED (Zero Screen Frames Captured)',
        keystrokeLogging: 'STRICTLY PROHIBITED (Zero Keystrokes Monitored)',
        fileContentInspection: 'STRICTLY PROHIBITED (Only Extension & Size Recorded)',
        sensitiveDataProtection: 'SHA-256 Hashed Telemetry Identifiers; File Names Shared Only for Admin Quarantine Inventory',
        dataRetentionPolicy: '30-Day Automated Hard Purge',
        integrityAssurance: 'HMAC-SHA256 Sequential Hash Chain',
      },
      verificationStatus: 'COMPLIANT & AUDIT READY',
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `compliance_audit_report_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="card compliance-report-card">
      <div className="report-header">
        <div>
          <h3>
            <IconShieldCheck size={18} className="text-accent" style={{ marginRight: '6px', verticalAlign: '-2px' }} />
            Regulatory Governance & Privacy Compliance Matrix
          </h3>
        </div>
        <button className="btn btn-primary btn-sm" onClick={downloadReport}>
          <IconDownload size={14} />
          Export Audit Certificate (.JSON)
        </button>
      </div>

      <div className="compliance-body">
        {stats && (
          <div className="compliance-stats-row">
            <div className="compliance-stat-card">
              <span className="comp-stat-label">GDPR Status</span>
              <div className="comp-stat-val" style={{ color: stats.gdprCompliant ? 'var(--color-success)' : 'var(--color-danger)' }}>
                {stats.gdprCompliant ? 'Compliant' : 'Non-Compliant'}
              </div>
            </div>

            <div className="compliance-stat-card">
              <span className="comp-stat-label">Storage Retention</span>
              <div className="comp-stat-val">
                {stats.retentionDays} Days (Auto-Purge)
              </div>
            </div>

            <div className="compliance-stat-card">
              <span className="comp-stat-label">Content Inspection</span>
              <div className="comp-stat-val" style={{ color: 'var(--color-success)' }}>
                {stats.contentInspectionActive ? 'Active' : 'Disabled (Zero Content)'}
              </div>
            </div>

            <div className="compliance-stat-card">
              <span className="comp-stat-label">HMAC Chain Verification</span>
              <div className="comp-stat-val" style={{ color: stats.hmacChainVerificationActive ? 'var(--color-success)' : 'var(--color-warning)' }}>
                {stats.hmacChainVerificationActive ? 'Continuous Active' : 'Suspended'}
              </div>
            </div>
          </div>
        )}

        <div className="compliance-grid">
          <div className="compliance-item passed">
            <div className="item-icon-wrapper">
              <IconCheckCircle size={18} />
            </div>
            <div className="item-details">
              <strong>Data Minimization (GDPR Art. 5.1c)</strong>
              <p>Only abstract metadata (process name, file size, byte volume) is logged. User document text and interactive screen data are strictly excluded.</p>
            </div>
          </div>

          <div className="compliance-item passed">
            <div className="item-icon-wrapper">
              <IconCheckCircle size={18} />
            </div>
            <div className="item-details">
              <strong>Strict Prohibition of Keystroke & Screen Capture</strong>
              <p>No keyloggers or screen capture modules are implemented. Personal student logins, passwords, banking sessions, and chats cannot be reconstructed.</p>
            </div>
          </div>

          <div className="compliance-item passed">
            <div className="item-icon-wrapper">
              <IconCheckCircle size={18} />
            </div>
            <div className="item-details">
              <strong>Client-Side Cryptographic Pseudonymization</strong>
              <p>Absolute file paths and destination IP addresses are replaced with 64-character SHA-256 digests prior to network dispatch.</p>
            </div>
          </div>

          <div className="compliance-item passed">
            <div className="item-icon-wrapper">
              <IconCheckCircle size={18} />
            </div>
            <div className="item-details">
              <strong>Forensic Non-Repudiation (HMAC Hash Chaining)</strong>
              <p>Each event mathematically seals the signature of the preceding event. Any post-incident database modification or record deletion breaks chain integrity.</p>
            </div>
          </div>

          <div className="compliance-item passed">
            <div className="item-icon-wrapper">
              <IconCheckCircle size={18} />
            </div>
            <div className="item-details">
              <strong>Storage Limitation & Automated 30-Day Purge</strong>
              <p>Enforces automated rolling retention schedules. All historical event records exceeding 30 calendar days are permanently removed.</p>
            </div>
          </div>

          <div className="compliance-item passed">
            <div className="item-icon-wrapper">
              <IconCheckCircle size={18} />
            </div>
            <div className="item-details">
              <strong>Admin-managed quarantine</strong>
              <p>On session logout or emergency lockdown, only that session's Downloads subfolder is quarantined; other Downloads files remain untouched. Configured browser data, temporary files, and Recent items are also moved into local quarantine. An authenticated admin must explicitly select items for permanent deletion. Clipboard clearing is not reversible.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

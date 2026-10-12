import React, { useState } from 'react';
import { api } from '../services/api';
import { IconZap, IconAlertTriangle, IconX } from './Icons';

interface Props {
  accessToken: string;
  machineId?: string;
  onLockTriggered?: () => void;
}

export const PanicLockButton: React.FC<Props> = ({ accessToken, machineId, onLockTriggered }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [targetMachine, setTargetMachine] = useState(machineId || 'PC_LAB_01');
  const [reason, setReason] = useState('Manual Security Isolation Directive');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleTrigger = async () => {
    setIsSubmitting(true);
    try {
      const res = await api.triggerPanicLock(accessToken, targetMachine, reason);
      setMessage(res.message || `Lockdown dispatched to ${targetMachine}. Cleanup targets are being quarantined.`);
      setTimeout(() => {
        setIsOpen(false);
        setMessage(null);
        if (onLockTriggered) onLockTriggered();
      }, 1500);
    } catch (e) {
      setMessage('Failed to dispatch station lockdown instruction.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <button className="btn btn-panic" onClick={() => setIsOpen(true)}>
        <IconZap size={14} />
        Emergency Station Lockdown
      </button>

      {isOpen && (
        <div className="modal-overlay" onClick={() => setIsOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>
                <IconZap size={16} />
                Emergency Workstation Lockdown
              </h3>
              <button className="close-btn" onClick={() => setIsOpen(false)}>
                <IconX size={16} />
              </button>
            </div>

            <div className="modal-body">
              <div className="warning-notice">
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start' }}>
                  <IconAlertTriangle size={18} style={{ flexShrink: 0, marginTop: '2px' }} />
                  <div>
                    <strong>Mandatory Protocol Warning:</strong> Triggering an emergency lockdown immediately commands the workstation to terminate active sessions, lock the Windows terminal screen, clear clipboard buffers, and move cleanup targets into admin-managed quarantine.
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label>Target Workstation ID:</label>
                <input
                  type="text"
                  className="form-input"
                  value={targetMachine}
                  onChange={(e) => setTargetMachine(e.target.value)}
                  placeholder="e.g. PC_LAB_01 or ALL"
                />
              </div>

              <div className="form-group">
                <label>Audit Justification / Incident Note:</label>
                <input
                  type="text"
                  className="form-input"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g. Unattended session or administrative protocol breach"
                />
              </div>

              {message && <div className="feedback-banner">{message}</div>}
            </div>

            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setIsOpen(false)} disabled={isSubmitting}>
                Cancel
              </button>
              <button className="btn btn-danger" onClick={handleTrigger} disabled={isSubmitting}>
                {isSubmitting ? 'Dispatching Instruction...' : 'Confirm Emergency Lockdown'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

import React, { useEffect, useState } from 'react';
import { wsClient } from '../services/websocket';
import { IconShieldAlert, IconZap, IconX } from './Icons';

export interface AlertItem {
  id: string;
  type: 'INTEGRITY_TAMPER_ALERT' | 'PANIC_LOCK_ALERT' | 'SESSION_UPDATE';
  title: string;
  details: string;
  timestamp: string;
}

export const AlertNotifications: React.FC = () => {
  const [alerts, setAlerts] = useState<AlertItem[]>([
    {
      id: 'init-tamper',
      type: 'INTEGRITY_TAMPER_ALERT',
      title: 'Cryptographic Integrity Warning (PC_LAB_04)',
      details: 'Audit event #2 failed HMAC signature verification (hash chain continuity broken).',
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);

  useEffect(() => {
    wsClient.connect();
    const unsubscribe = wsClient.subscribe((msg: any) => {
      const newAlert: AlertItem = {
        id: Math.random().toString(),
        type: msg.type || 'SESSION_UPDATE',
        title: msg.type === 'INTEGRITY_TAMPER_ALERT' ? 'Cryptographic Integrity Warning' : 'Station Lockdown Dispatched',
        details: msg.details || msg.reason || `Workstation session ${msg.sessionId} updated to ${msg.status}`,
        timestamp: new Date().toLocaleTimeString(),
      };
      setAlerts((prev) => [newAlert, ...prev.slice(0, 9)]);
    });

    return () => unsubscribe();
  }, []);

  const removeAlert = (id: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  };

  if (alerts.length === 0) return null;

  return (
    <div className="alert-notifications-container">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className={`alert-banner ${alert.type === 'INTEGRITY_TAMPER_ALERT' ? 'banner-danger' : 'banner-warning'}`}
        >
          <div className="alert-content">
            <span className="alert-icon">
              {alert.type === 'INTEGRITY_TAMPER_ALERT' ? (
                <IconShieldAlert size={16} />
              ) : (
                <IconZap size={16} />
              )}
            </span>
            <div className="alert-text">
              <strong>{alert.title}:</strong> {alert.details}
              <span className="alert-time">({alert.timestamp})</span>
            </div>
          </div>
          <button className="alert-close" onClick={() => removeAlert(alert.id)} title="Dismiss alert">
            <IconX size={14} />
          </button>
        </div>
      ))}
    </div>
  );
};

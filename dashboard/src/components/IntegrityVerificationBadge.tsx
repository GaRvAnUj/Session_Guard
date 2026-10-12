import React from 'react';
import { IconShieldCheck, IconShieldAlert } from './Icons';

interface Props {
  verified: boolean;
  hash?: string;
  previousHash?: string;
  compact?: boolean;
}

export const IntegrityVerificationBadge: React.FC<Props> = ({
  verified,
  hash,
  previousHash,
  compact = false,
}) => {
  if (compact) {
    return (
      <span
        className={`status-badge-chip ${verified ? 'badge-verified' : 'badge-tampered'}`}
        title={verified ? 'Cryptographic HMAC Hash Chain Intact' : 'Broken Hash Link Detected!'}
      >
        {verified ? (
          <>
            <IconShieldCheck size={12} />
            <span>Verified</span>
          </>
        ) : (
          <>
            <IconShieldAlert size={12} />
            <span>Tamper Alert</span>
          </>
        )}
      </span>
    );
  }

  return (
    <div className={`verification-summary-banner ${verified ? 'valid' : 'invalid'}`}>
      <div className="summary-col">
        {verified ? (
          <IconShieldCheck size={18} style={{ color: 'var(--color-success)', marginTop: '2px' }} />
        ) : (
          <IconShieldAlert size={18} style={{ color: 'var(--color-danger)', marginTop: '2px' }} />
        )}
        <div>
          <span style={{ fontWeight: 600 }}>
            {verified ? 'HMAC Integrity Chain Validated' : 'Cryptographic Integrity Failure (Tampering Detected)'}
          </span>
          {hash && (
            <div style={{ marginTop: '0.35rem', display: 'flex', gap: '0.85rem', fontSize: '0.72rem' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Event HMAC: </span>
                <code>{hash.substring(0, 20)}...</code>
              </div>
              {previousHash && (
                <div>
                  <span style={{ color: 'var(--text-muted)' }}>Chained Prev: </span>
                  <code>{previousHash.substring(0, 20)}...</code>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

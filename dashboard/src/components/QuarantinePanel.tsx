import React, { useEffect, useMemo, useState } from 'react';
import { api, QuarantineItem } from '../services/api';

const formatSize = (size: number) => {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
};

interface Props {
  accessToken: string;
}

export const QuarantinePanel: React.FC<Props> = ({ accessToken }) => {
  const [items, setItems] = useState<QuarantineItem[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadItems = async (accessToken: string) => {
    setLoading(true);
    try {
      const inventory = await api.getQuarantineItems(accessToken);
      setItems(inventory);
      setSelected((current) => new Set([...current].filter((id) => inventory.some((item) => item.itemId === id))));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load quarantine inventory.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadItems(accessToken);
    const interval = window.setInterval(() => void loadItems(accessToken), 5000);
    return () => window.clearInterval(interval);
  }, [accessToken]);

  const groupedItems = useMemo(
    () => items.reduce<Record<string, QuarantineItem[]>>((groups, item) => {
      (groups[item.machineId] ||= []).push(item);
      return groups;
    }, {}),
    [items],
  );

  const toggleSelected = (itemId: string) => {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(itemId)) next.delete(itemId);
      else next.add(itemId);
      return next;
    });
  };

  const runAction = async (action: 'restore' | 'permanently-delete') => {
    if (selected.size === 0) return;
    const actionLabel = action === 'restore' ? 'restore' : 'permanently delete';
    if (action === 'permanently-delete' &&
        !window.confirm(`Permanently delete ${selected.size} selected quarantined item(s)? This cannot be undone.`)) {
      return;
    }

    const selectedItems = items.filter((item) => selected.has(item.itemId));
    const idsByMachine = selectedItems.reduce<Record<string, string[]>>((groups, item) => {
      (groups[item.machineId] ||= []).push(item.itemId);
      return groups;
    }, {});

    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      for (const [machineId, itemIds] of Object.entries(idsByMachine)) {
        await api.queueQuarantineAction(accessToken, machineId, itemIds, action);
      }
      setSelected(new Set());
      setNotice(`Admin-approved ${actionLabel} request queued. The workstation client will apply it when it checks in.`);
      await loadItems(accessToken);
    } catch (e) {
      setError(e instanceof Error ? e.message : `Could not ${actionLabel} selected files.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card" style={{ padding: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <div>
          <h2>Quarantined files</h2>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-secondary" disabled={loading} onClick={() => void loadItems(accessToken)}>Refresh</button>
        </div>
      </div>

      <div className="alert-banner banner-warning" style={{ margin: '1rem 0' }}>
        Restore moves items back to their original paths and will not overwrite existing files. Permanent deletion requires an authenticated admin and an explicit confirmation.
      </div>
      {notice && <p role="status" style={{ color: 'var(--color-success)', marginBottom: '0.75rem' }}>{notice}</p>}
      {error && <p role="alert" style={{ color: 'var(--color-danger)', marginBottom: '0.75rem' }}>{error}</p>}

      {loading && items.length === 0 ? (
        <div className="loading-state">Loading quarantine inventory...</div>
      ) : items.length === 0 ? (
        <div className="empty-state">No quarantined files are currently reported by connected workstations.</div>
      ) : (
        <>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.9rem', flexWrap: 'wrap' }}>
            <button className="btn btn-secondary" disabled={!selected.size || loading} onClick={() => void runAction('restore')}>
              Restore selected ({selected.size})
            </button>
            <button className="btn btn-danger" disabled={!selected.size || loading} onClick={() => void runAction('permanently-delete')}>
              Permanently delete selected
            </button>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr>
                  <th style={{ padding: '0.65rem' }}>Select</th>
                  <th style={{ padding: '0.65rem' }}>Workstation</th>
                  <th style={{ padding: '0.65rem' }}>File</th>
                  <th style={{ padding: '0.65rem' }}>Category</th>
                  <th style={{ padding: '0.65rem' }}>Size</th>
                  <th style={{ padding: '0.65rem' }}>Quarantined</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(groupedItems).flatMap(([machineId, machineItems]) =>
                  machineItems.map((item) => (
                    <tr key={`${machineId}:${item.itemId}`} style={{ borderTop: '1px solid var(--border-subtle)' }}>
                      <td style={{ padding: '0.65rem' }}>
                        <input
                          type="checkbox"
                          checked={selected.has(item.itemId)}
                          onChange={() => toggleSelected(item.itemId)}
                          aria-label={`Select ${item.fileName}`}
                        />
                      </td>
                      <td style={{ padding: '0.65rem' }}>{machineId}</td>
                      <td style={{ padding: '0.65rem', overflowWrap: 'anywhere' }}>
                        <strong>{item.fileName}</strong>
                        {item.relativePath !== item.fileName && <><br /><span className="item-path">{item.relativePath}</span></>}
                      </td>
                      <td style={{ padding: '0.65rem' }}>{item.category}</td>
                      <td style={{ padding: '0.65rem', whiteSpace: 'nowrap' }}>{formatSize(item.sizeBytes)}</td>
                      <td style={{ padding: '0.65rem', whiteSpace: 'nowrap' }}>{new Date(item.quarantinedAt).toLocaleString()}</td>
                    </tr>
                  )),
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
};

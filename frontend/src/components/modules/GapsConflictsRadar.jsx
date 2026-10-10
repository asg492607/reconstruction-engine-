import React, { useState } from 'react';
import { 
  AlertTriangle, 
  AlertCircle, 
  CheckCircle, 
  Search, 
  RefreshCw,
  Sparkles,
  ArrowRight,
  Clock,
  FileQuestion,
  CheckCircle2,
  Filter,
  Plus,
  Edit3
} from 'lucide-react';
import { api } from '../../api';

export default function GapsConflictsRadar({ caseId, gapsConflicts = [], onRefresh }) {
  const [detecting, setDetecting] = useState(false);
  const [error, setError] = useState(null);
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [mitigations, setMitigations] = useState(() => {
    try {
      const saved = localStorage.getItem(`rre_mitigations_${caseId}`);
      return saved ? JSON.parse(saved) : {};
    } catch (e) {
      return {};
    }
  });

  const [activeMitigateId, setActiveMitigateId] = useState(null);
  const [mitigationNote, setMitigationNote] = useState('');

  const saveMitigations = (next) => {
    setMitigations(next);
    try {
      localStorage.setItem(`rre_mitigations_${caseId}`, JSON.stringify(next));
    } catch (e) {
      console.warn("Could not save mitigations:", e);
    }
  };

  const handleRunDetect = async () => {
    setDetecting(true);
    setError(null);
    try {
      await api.gapsConflicts.detect(caseId);
      onRefresh();
    } catch (err) {
      setError(err.message || "Detection failed.");
    } finally {
      setDetecting(false);
    }
  };

  const handleToggleMitigate = (itemId) => {
    const isMitigated = mitigations[itemId]?.status === 'RESOLVED';
    const next = {
      ...mitigations,
      [itemId]: {
        status: isMitigated ? 'OPEN' : 'RESOLVED',
        note: mitigations[itemId]?.note || 'Mitigated by investigating detective',
        updated_at: new Date().toLocaleDateString()
      }
    };
    saveMitigations(next);
  };

  const handleSaveMitigationNote = (itemId) => {
    if (!mitigationNote.trim()) return;
    const next = {
      ...mitigations,
      [itemId]: {
        status: 'RESOLVED',
        note: mitigationNote.trim(),
        updated_at: new Date().toLocaleDateString()
      }
    };
    saveMitigations(next);
    setActiveMitigateId(null);
    setMitigationNote('');
  };

  const gaps = gapsConflicts.filter(item => item.item_type === 'GAP' || !item.item_type).filter(g => {
    if (severityFilter === 'RESOLVED') return mitigations[g.id]?.status === 'RESOLVED';
    if (severityFilter === 'OPEN') return mitigations[g.id]?.status !== 'RESOLVED';
    if (severityFilter !== 'ALL' && g.severity !== severityFilter) return false;
    return true;
  });

  const conflicts = gapsConflicts.filter(item => item.item_type === 'CONFLICT').filter(c => {
    if (severityFilter === 'RESOLVED') return mitigations[c.id]?.status === 'RESOLVED';
    if (severityFilter === 'OPEN') return mitigations[c.id]?.status !== 'RESOLVED';
    return true;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div className="card" style={{ padding: '20px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '14px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-red">Evidentiary Radar</span>
            <span className="badge badge-slate">Anomaly Detection</span>
          </div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
            Gaps & Conflicts Radar & Mitigation Ledger
          </h2>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', margin: 0, marginTop: '4px' }}>
            Surfaces sensor blind spots, contradictory witness claims, and provides detective mitigation sign-offs.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="form-select"
            style={{ fontSize: '0.825rem', padding: '6px 12px', width: 'auto' }}
          >
            <option value="ALL">All Items</option>
            <option value="OPEN">Open Voids Only</option>
            <option value="RESOLVED">Mitigated Items Only</option>
            <option value="HIGH">High Severity Only</option>
            <option value="MEDIUM">Medium Severity Only</option>
          </select>

          <button
            onClick={handleRunDetect}
            disabled={detecting}
            className="btn btn-primary btn-sm"
            style={{ fontSize: '0.825rem' }}
          >
            <Sparkles size={15} />
            {detecting ? 'Scanning Evidence...' : 'Detect Gaps & Conflicts'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          padding: '12px 16px',
          backgroundColor: 'var(--danger-bg)',
          border: '1px solid var(--danger-border)',
          borderRadius: 'var(--radius-md)',
          color: 'var(--danger-text)',
          fontSize: '0.85rem'
        }}>
          {error}
        </div>
      )}

      {/* Grid: Gaps on Left, Conflicts on Right */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
        {/* Evidentiary Gaps */}
        <div className="card" style={{ padding: '22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock size={18} color="var(--primary)" />
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>
                Evidentiary Coverage Gaps ({gaps.length})
              </h3>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {gaps.length === 0 ? (
              <div style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                <CheckCircle2 size={32} color="#16a34a" style={{ margin: '0 auto 8px auto' }} />
                <div>No active evidentiary coverage voids matching filter.</div>
              </div>
            ) : (
              gaps.map((gap, idx) => {
                const isMitigated = mitigations[gap.id]?.status === 'RESOLVED';
                return (
                  <div 
                    key={gap.id || idx}
                    style={{
                      padding: '16px',
                      borderRadius: 'var(--radius-md)',
                      border: isMitigated ? '1px solid #bbf7d0' : (gap.severity === 'HIGH' ? '1px solid var(--danger-border)' : '1px solid var(--border-light)'),
                      backgroundColor: isMitigated ? '#f0fdf4' : (gap.severity === 'HIGH' ? '#fff1f2' : '#ffffff'),
                      boxShadow: 'var(--shadow-sm)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.9rem', color: isMitigated ? '#166534' : (gap.severity === 'HIGH' ? 'var(--danger-text)' : 'var(--text-main)') }}>
                        {gap.title || `Coverage Gap #${idx + 1}`}
                      </span>
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        {isMitigated ? (
                          <span className="badge badge-green" style={{ fontSize: '0.68rem' }}>
                            ✓ MITIGATED
                          </span>
                        ) : (
                          <span className={gap.severity === 'HIGH' ? 'badge badge-red' : 'badge badge-amber'} style={{ fontSize: '0.68rem' }}>
                            {gap.severity || 'MEDIUM'}
                          </span>
                        )}
                      </div>
                    </div>

                    <p style={{ fontSize: '0.825rem', color: 'var(--text-main)', lineHeight: 1.5, marginBottom: '8px' }}>
                      {gap.description}
                    </p>

                    {gap.recommended_action && (
                      <div style={{
                        padding: '8px 10px',
                        backgroundColor: isMitigated ? '#ffffff' : 'rgba(255, 255, 255, 0.75)',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: '0.78rem',
                        color: 'var(--text-muted)',
                        marginBottom: '8px',
                        border: '1px solid rgba(0,0,0,0.05)'
                      }}>
                        <strong style={{ color: 'var(--primary)' }}>Investigative Action:</strong> {gap.recommended_action}
                      </div>
                    )}

                    {/* Mitigation Note display */}
                    {mitigations[gap.id]?.note && (
                      <div style={{ fontSize: '0.75rem', color: '#15803d', backgroundColor: '#dcfce7', padding: '6px 8px', borderRadius: '4px', marginBottom: '8px' }}>
                        <strong>Detective Note:</strong> {mitigations[gap.id].note} ({mitigations[gap.id].updated_at})
                      </div>
                    )}

                    {/* Action Bar */}
                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px', marginTop: '6px' }}>
                      <button
                        onClick={() => {
                          setActiveMitigateId(activeMitigateId === gap.id ? null : gap.id);
                          setMitigationNote(mitigations[gap.id]?.note || '');
                        }}
                        className="btn btn-secondary btn-sm"
                        style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                      >
                        <Edit3 size={11} />
                        {mitigations[gap.id]?.note ? 'Edit Note' : 'Add Mitigation Note'}
                      </button>
                      <button
                        onClick={() => handleToggleMitigate(gap.id)}
                        className={`btn btn-sm ${isMitigated ? 'btn-outline' : 'btn-primary'}`}
                        style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                      >
                        {isMitigated ? 'Reopen Void' : 'Mark Mitigated'}
                      </button>
                    </div>

                    {/* Inline Mitigation Note Form */}
                    {activeMitigateId === gap.id && (
                      <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px dashed var(--border-light)' }}>
                        <textarea
                          rows={2}
                          placeholder="Document investigative resolution: e.g. Cross-referenced external delivery camera; accounted for blind spot..."
                          value={mitigationNote}
                          onChange={(e) => setMitigationNote(e.target.value)}
                          className="form-input"
                          style={{ fontSize: '0.78rem', width: '100%', marginBottom: '6px' }}
                        />
                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px' }}>
                          <button onClick={() => setActiveMitigateId(null)} className="btn btn-secondary btn-sm" style={{ fontSize: '0.7rem' }}>
                            Cancel
                          </button>
                          <button onClick={() => handleSaveMitigationNote(gap.id)} className="btn btn-primary btn-sm" style={{ fontSize: '0.7rem' }}>
                            Save Mitigation
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Evidentiary Conflicts */}
        <div className="card" style={{ padding: '22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={18} color="#dc2626" />
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0 }}>
                Telemetry & Statement Conflicts ({conflicts.length})
              </h3>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {conflicts.length === 0 ? (
              <div style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                <CheckCircle2 size={32} color="#16a34a" style={{ margin: '0 auto 8px auto' }} />
                <div>No contradictory testimony or sensor conflicts detected.</div>
              </div>
            ) : (
              conflicts.map((conf, idx) => {
                const isMitigated = mitigations[conf.id]?.status === 'RESOLVED';
                return (
                  <div 
                    key={conf.id || idx}
                    style={{
                      padding: '16px',
                      borderRadius: 'var(--radius-md)',
                      border: isMitigated ? '1px solid #bbf7d0' : '1px solid var(--warning-border)',
                      backgroundColor: isMitigated ? '#f0fdf4' : 'var(--warning-bg)',
                      boxShadow: 'var(--shadow-sm)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                      <span style={{ fontWeight: 700, fontSize: '0.9rem', color: isMitigated ? '#166534' : 'var(--warning-text)' }}>
                        {conf.title || `Conflict #${idx + 1}`}
                      </span>
                      <span className={isMitigated ? 'badge badge-green' : 'badge badge-amber'} style={{ fontSize: '0.68rem' }}>
                        {isMitigated ? '✓ RECONCILED' : 'CONFLICT'}
                      </span>
                    </div>

                    <p style={{ fontSize: '0.825rem', color: 'var(--text-main)', lineHeight: 1.5, marginBottom: '8px' }}>
                      {conf.description}
                    </p>

                    {conf.claims_involved && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                        <strong>Involves:</strong> {conf.claims_involved}
                      </div>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '6px' }}>
                      <button
                        onClick={() => handleToggleMitigate(conf.id)}
                        className={`btn btn-sm ${isMitigated ? 'btn-outline' : 'btn-primary'}`}
                        style={{ fontSize: '0.72rem', padding: '3px 8px' }}
                      >
                        {isMitigated ? 'Reopen Conflict' : 'Mark Reconciled'}
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

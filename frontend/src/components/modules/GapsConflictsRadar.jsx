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
  FileQuestion
} from 'lucide-react';
import { api } from '../../api';

export default function GapsConflictsRadar({ caseId, gapsConflicts = [], onRefresh }) {
  const [detecting, setDetecting] = useState(false);
  const [error, setError] = useState(null);

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

  const gaps = gapsConflicts.filter(item => item.item_type === 'GAP' || !item.item_type);
  const conflicts = gapsConflicts.filter(item => item.item_type === 'CONFLICT');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header */}
      <div className="card" style={{ padding: '20px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '14px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-red">Evidentiary Radar</span>
            <span className="badge badge-slate">Anomaly Detection</span>
          </div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-main)' }}>
            Gaps & Conflicts Radar
          </h2>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
            Surfaces temporal coverage voids, contradictory witness testimony, and telemetry inconsistencies.
          </p>
        </div>

        <button
          onClick={handleRunDetect}
          disabled={detecting}
          className="btn btn-primary"
        >
          <Sparkles size={16} />
          {detecting ? 'Scanning Evidence...' : 'Detect Gaps & Conflicts'}
        </button>
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
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Clock size={18} color="var(--primary)" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Evidentiary Coverage Gaps ({gaps.length})</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {gaps.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No active evidentiary gaps flagged.
              </div>
            ) : (
              gaps.map((gap, idx) => (
                <div 
                  key={gap.id || idx}
                  style={{
                    padding: '16px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-light)',
                    backgroundColor: gap.severity === 'HIGH' ? 'var(--danger-bg)' : '#ffffff',
                    borderColor: gap.severity === 'HIGH' ? 'var(--danger-border)' : 'var(--border-light)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.9rem', color: gap.severity === 'HIGH' ? 'var(--danger-text)' : 'var(--text-main)' }}>
                      {gap.title || `Coverage Gap #${idx + 1}`}
                    </span>
                    <span className={gap.severity === 'HIGH' ? 'badge badge-red' : 'badge badge-amber'}>
                      {gap.severity || 'MEDIUM'}
                    </span>
                  </div>

                  <p style={{ fontSize: '0.825rem', color: 'var(--text-main)', lineHeight: 1.5, marginBottom: '8px' }}>
                    {gap.description}
                  </p>

                  {gap.recommended_action && (
                    <div style={{
                      padding: '8px 10px',
                      backgroundColor: 'rgba(255, 255, 255, 0.7)',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: '0.78rem',
                      color: 'var(--text-muted)'
                    }}>
                      <strong style={{ color: 'var(--primary)' }}>Action Item:</strong> {gap.recommended_action}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Evidentiary Conflicts */}
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <AlertTriangle size={18} color="#dc2626" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Telemetry & Statement Conflicts ({conflicts.length})</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {conflicts.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No direct statement or telemetry conflicts detected.
              </div>
            ) : (
              conflicts.map((conf, idx) => (
                <div 
                  key={conf.id || idx}
                  style={{
                    padding: '16px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--warning-border)',
                    backgroundColor: 'var(--warning-bg)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--warning-text)' }}>
                      {conf.title || `Conflict #${idx + 1}`}
                    </span>
                    <span className="badge badge-amber">
                      CONFLICT
                    </span>
                  </div>

                  <p style={{ fontSize: '0.825rem', color: 'var(--text-main)', lineHeight: 1.5, marginBottom: '8px' }}>
                    {conf.description}
                  </p>

                  {conf.claims_involved && (
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Involves: {conf.claims_involved}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

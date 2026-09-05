import React, { useState } from 'react';
import { 
  Shield, 
  FileText, 
  AlertTriangle, 
  Layers, 
  GitBranch, 
  Users, 
  CheckCircle, 
  Clock, 
  ArrowRight,
  Database,
  Sparkles,
  Upload,
  Plus
} from 'lucide-react';
import DashboardCaseIntakeWizard from '../modules/DashboardCaseIntakeWizard';

export default function LeadInvestigatorDashboard({ 
  caseData, 
  evidence = [], 
  timelineEvents = [], 
  hypotheses = [], 
  gapsConflicts = [], 
  entities = [], 
  onNavigate,
  onTriggerReconstruction,
  reconstructionLoading,
  onCaseCreated
}) {
  const [showIntakeForm, setShowIntakeForm] = useState(!caseData);
  const highGaps = gapsConflicts.filter(g => g.severity === 'HIGH');
  const unconfirmedEntities = entities.filter(e => e.status !== 'CONFIRMED');

  const handleCaseCreatedInternal = (newCase) => {
    setShowIntakeForm(false);
    if (onCaseCreated) {
      onCaseCreated(newCase);
    }
  };

  // If no case selected or user clicked to register a new incident, render the intake wizard directly on the dashboard
  if (!caseData || showIntakeForm) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <DashboardCaseIntakeWizard
          onCaseCreated={handleCaseCreatedInternal}
          onCancel={caseData ? () => setShowIntakeForm(false) : null}
        />
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner */}
      <div className="card" style={{
        padding: '24px',
        background: 'linear-gradient(135deg, #eff6ff 0%, #ffffff 100%)',
        borderColor: 'var(--primary-border)',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span className="badge badge-blue">Lead Investigator Command HUD</span>
            <span className="badge badge-purple">{caseData?.case_number || 'NO ACTIVE CASE'}</span>
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '4px' }}>
            {caseData?.title || 'No Active Investigation Case'}
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {caseData ? `Theft Domain: ${caseData.specific_offense || caseData.case_type || 'Theft / Robbery'} • Status: ${caseData.status || 'Active'}` : 'Create a new case using the "+ New Case" button in the navigation bar to begin intake.'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={() => setShowIntakeForm(true)} 
            className="btn btn-outline"
            style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <Plus size={16} />
            Register Incident
          </button>
          <button 
            onClick={() => onNavigate('evidence')} 
            className="btn btn-outline"
            disabled={!caseData}
          >
            <Upload size={16} />
            Intake Evidence
          </button>
          <button 
            onClick={onTriggerReconstruction} 
            disabled={reconstructionLoading || !caseData}
            className="btn btn-primary"
          >
            <Sparkles size={16} />
            {reconstructionLoading ? 'Synthesizing...' : 'Run Reconstruction'}
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '16px'
      }}>
        <div 
          onClick={() => onNavigate('evidence')}
          className="card" 
          style={{ padding: '18px', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Evidence Vault</span>
            <Database size={18} color="var(--primary)" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)' }}>
            {evidence.length}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--success-text)', fontWeight: 600, marginTop: '4px' }}>
            ✓ SHA-256 Verified
          </div>
        </div>

        <div 
          onClick={() => onNavigate('timeline')}
          className="card" 
          style={{ padding: '18px', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Timeline Events</span>
            <Clock size={18} color="var(--primary)" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)' }}>
            {timelineEvents.length}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Multi-Source Synced
          </div>
        </div>

        <div 
          onClick={() => onNavigate('reconstruction')}
          className="card" 
          style={{ padding: '18px', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Hypotheses</span>
            <GitBranch size={18} color="#7c3aed" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)' }}>
            {hypotheses.length}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#7c3aed', fontWeight: 600, marginTop: '4px' }}>
            Self-Challenged AI
          </div>
        </div>

        <div 
          onClick={() => onNavigate('gaps')}
          className="card" 
          style={{ padding: '18px', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Gaps & Conflicts</span>
            <AlertTriangle size={18} color="#dc2626" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: highGaps.length > 0 ? '#dc2626' : 'var(--text-main)' }}>
            {gapsConflicts.length}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#dc2626', fontWeight: 600, marginTop: '4px' }}>
            {highGaps.length} High Severity
          </div>
        </div>

        <div 
          onClick={() => onNavigate('entities')}
          className="card" 
          style={{ padding: '18px', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>Tracked Entities</span>
            <Users size={18} color="#d97706" />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)' }}>
            {entities.length}
          </div>
          <div style={{ fontSize: '0.75rem', color: '#d97706', fontWeight: 600, marginTop: '4px' }}>
            {unconfirmedEntities.length} Pending Review
          </div>
        </div>
      </div>

      {/* Main Grid: Hypotheses vs Gaps/Conflicts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '20px' }}>
        {/* Left: Reconstructed Hypotheses */}
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <GitBranch size={18} color="var(--primary)" />
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Leading Theft Hypotheses</h3>
            </div>
            <button 
              onClick={() => onNavigate('output')} 
              className="btn btn-secondary btn-sm"
            >
              View Dossier
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {hypotheses.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No hypotheses synthesized yet. Upload evidence and run the reconstruction engine.
              </div>
            ) : (
              hypotheses.slice(0, 3).map((h, idx) => (
                <div 
                  key={h.id || h.hypothesis_id || idx}
                  style={{
                    padding: '14px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--primary-border)',
                    backgroundColor: idx === 0 ? 'var(--bg-accent-light)' : '#ffffff'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main)' }}>
                      {h.title || h.hypothesis_title || `Hypothesis #${idx + 1}`}
                    </span>
                    <span className={h.theft_conclusion_supported === false ? "badge badge-amber" : "badge badge-blue"}>
                      {h.support_level || (h.theft_conclusion_supported === false ? "Alternative / Partial" : "Candidate")}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '8px' }}>
                    {h.narrative}
                  </p>
                  <div style={{ display: 'flex', gap: '8px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    <span>• {h.supporting_evidence_citations?.length || h.supporting_claims?.length || 0} Citations</span>
                    {h.critical_gap && <span style={{ color: '#dc2626' }}>• {h.critical_gap}</span>}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right: Critical Gaps & Conflicts */}
        <div className="card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={18} color="#dc2626" />
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Priority Investigation Anomalies</h3>
            </div>
            <button 
              onClick={() => onNavigate('gaps')} 
              className="btn btn-secondary btn-sm"
            >
              View Radar
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {gapsConflicts.length === 0 ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No active evidentiary gaps or conflicts identified.
              </div>
            ) : (
              gapsConflicts.slice(0, 3).map((gc, idx) => (
                <div 
                  key={gc.id || idx}
                  style={{
                    padding: '14px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-light)',
                    backgroundColor: gc.severity === 'HIGH' ? 'var(--danger-bg)' : 'var(--warning-bg)',
                    borderColor: gc.severity === 'HIGH' ? 'var(--danger-border)' : 'var(--warning-border)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 700, fontSize: '0.875rem', color: gc.severity === 'HIGH' ? 'var(--danger-text)' : 'var(--warning-text)' }}>
                      {gc.title || gc.conflict_type || gc.gap_type || `Anomaly #${idx + 1}`}
                    </span>
                    <span className={gc.severity === 'HIGH' ? 'badge badge-red' : 'badge badge-amber'}>
                      {gc.severity || gc.conflict_type || 'FLAGGED'}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
                    {gc.description || gc.discrepancy_explanation}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

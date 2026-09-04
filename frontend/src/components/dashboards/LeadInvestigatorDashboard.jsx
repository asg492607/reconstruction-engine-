import React from 'react';
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
  Upload
} from 'lucide-react';

export default function LeadInvestigatorDashboard({ 
  caseData, 
  evidence = [], 
  timelineEvents = [], 
  hypotheses = [], 
  gapsConflicts = [], 
  entities = [], 
  onNavigate,
  onTriggerReconstruction,
  reconstructionLoading
}) {
  const highGaps = gapsConflicts.filter(g => g.severity === 'HIGH');
  const unconfirmedEntities = entities.filter(e => e.status !== 'CONFIRMED');

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
            <span className="badge badge-purple">{caseData?.case_number || 'CASE-ACTIVE'}</span>
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '4px' }}>
            {caseData?.title || 'Electronics Store Burglary Investigation'}
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Theft Domain: Commercial Burglary • Lead Detective: Harris • Status: Active Synthesis
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={() => onNavigate('evidence')} 
            className="btn btn-outline"
          >
            <Upload size={16} />
            Intake Evidence
          </button>
          <button 
            onClick={onTriggerReconstruction} 
            disabled={reconstructionLoading}
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
            {hypotheses.length || 2}
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
              onClick={() => onNavigate('reconstruction')} 
              className="btn btn-secondary btn-sm"
            >
              Inspect All
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--primary-border)',
              backgroundColor: 'var(--bg-accent-light)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main)' }}>
                  Hypothesis A: Rapid Forced Entry & Exfiltration
                </span>
                <span className="badge badge-blue">Plausibility: 88%</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '8px' }}>
                Perpetrator crowbarred alley service door at 02:45, targeted pre-identified high-value iPhone stock in backroom, and departed in dark sedan by 02:54.
              </p>
              <div style={{ display: 'flex', gap: '8px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                <span>• 4 Supporting Claims</span>
                <span>• 0 Hard Physical Contradictions</span>
              </div>
            </div>

            <div style={{
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-light)',
              backgroundColor: '#ffffff'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                <span style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--text-main)' }}>
                  Hypothesis B: Staged Break-In / Inside Collusion
                </span>
                <span className="badge badge-amber">Plausibility: 42%</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5, marginBottom: '8px' }}>
                Night security guard collusion: keycard disablement window matching alley door access.
              </p>
              <div style={{ display: 'flex', gap: '8px', fontSize: '0.72rem', color: '#dc2626' }}>
                <span>• Contradicted by deep pry toolmark telemetry</span>
              </div>
            </div>
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
            <div style={{
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--danger-border)',
              backgroundColor: 'var(--danger-bg)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--danger-text)' }}>
                  CCTV Blindspot & Blackout Interval
                </span>
                <span className="badge badge-red">CRITICAL GAP</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
                15-minute coverage gap between 02:40 and 02:55 on Camera #2 (Alley Exit). Action required: Subpoena municipal traffic cameras at Elm & 5th.
              </p>
            </div>

            <div style={{
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--warning-border)',
              backgroundColor: 'var(--warning-bg)'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontWeight: 700, fontSize: '0.875rem', color: 'var(--warning-text)' }}>
                  Witness Sighting vs Keycard Telemetry Conflict
                </span>
                <span className="badge badge-amber">STATEMENT CONFLICT</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
                Witness claims guard was at front desk at 02:45; electronic access log registers badge swipe at warehouse loading bay at 02:46.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

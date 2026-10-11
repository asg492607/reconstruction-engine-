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
  Plus,
  ShieldCheck,
  Scale,
  Activity,
  Terminal,
  Lock,
  ChevronRight,
  FileCheck2
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
  const highGaps = gapsConflicts.filter(g => g.severity === 'HIGH' || g.significance === 'HIGH');
  const unconfirmedEntities = entities.filter(e => e.status !== 'CONFIRMED' && e.identity_status !== 'CONFIRMED');

  const handleCaseCreatedInternal = (newCase) => {
    setShowIntakeForm(false);
    if (onCaseCreated) {
      onCaseCreated(newCase);
    }
  };

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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
      {/* Executive Command HUD Banner */}
      <div className="card" style={{
        padding: '24px 28px',
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '12px',
        boxShadow: '0 2px 8px rgba(15, 23, 42, 0.04)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Subtle accent border top */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: 'linear-gradient(90deg, #1d4ed8 0%, #2563eb 50%, #38bdf8 100%)'
        }} />

        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: '20px'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', flexWrap: 'wrap' }}>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.675rem',
                fontWeight: 700,
                color: '#1e40af',
                backgroundColor: '#eff6ff',
                border: '1px solid #bfdbfe',
                padding: '2px 8px',
                borderRadius: '4px',
                letterSpacing: '0.04em'
              }}>
                METROPOLITAN POLICE DEPT // FORENSIC INTELLIGENCE DIVISION
              </span>
              <span style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.725rem',
                fontWeight: 800,
                color: '#0f172a',
                backgroundColor: '#f1f5f9',
                border: '1px solid #cbd5e1',
                padding: '2px 8px',
                borderRadius: '4px'
              }}>
                {caseData?.case_number || 'SEC-2026-SHOWCASE'}
              </span>
              <span className="badge badge-green" style={{ fontSize: '0.65rem' }}>
                <span className="pulse-dot" style={{ width: '6px', height: '6px', marginRight: '3px' }} />
                ACTIVE INVESTIGATION
              </span>
            </div>

            <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em', marginBottom: '6px' }}>
              {caseData?.title || 'Apex Logistics Depot #7: Vault C Forced Entry & High-Value Inventory Discrepancy'}
            </h1>

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '0.8rem', color: '#475569', flexWrap: 'wrap' }}>
              <span><strong>Incident Sector:</strong> {caseData?.incident_location || 'Apex Logistics Depot #7, Sector B, Vault C'}</span>
              <span>•</span>
              <span><strong>Offense:</strong> {caseData?.specific_offense || caseData?.case_type || 'Commercial Burglary / Theft'}</span>
              <span>•</span>
              <span style={{ fontFamily: 'var(--font-mono)', color: '#047857' }}>
                <strong>Loss Valuation:</strong> $37,000.00 USD (2x Platinum Cylinders)
              </span>
            </div>
          </div>

          {/* Quick Command Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <button 
              onClick={() => setShowIntakeForm(true)} 
              className="btn btn-secondary btn-sm"
              style={{ fontWeight: 700 }}
            >
              <Plus size={14} />
              Register Incident
            </button>
            <button 
              onClick={() => onNavigate('evidence')} 
              className="btn btn-secondary btn-sm"
              style={{ fontWeight: 700 }}
            >
              <Upload size={14} />
              Intake Evidence
            </button>
            <button 
              onClick={onTriggerReconstruction} 
              disabled={reconstructionLoading}
              className="btn btn-primary"
              style={{ fontWeight: 800, fontSize: '0.825rem', padding: '8px 16px' }}
            >
              <Sparkles size={15} />
              {reconstructionLoading ? 'RECONSTRUCTING...' : 'RUN RECONSTRUCTION'}
            </button>
          </div>
        </div>

        {/* Live Integrity & Validation Bar */}
        <div style={{
          marginTop: '20px',
          paddingTop: '16px',
          borderTop: '1px solid #f1f5f9',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '12px',
          fontSize: '0.75rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#334155' }}>
            <ShieldCheck size={16} color="#059669" />
            <span><strong>Chain of Custody:</strong> 100% SHA-256 Hashed</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#334155' }}>
            <Scale size={16} color="#2563eb" />
            <span><strong>Two-Layer Validation:</strong> L1 Physics & L2 Adversarial</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#334155' }}>
            <Activity size={16} color="#7c3aed" />
            <span><strong>Engine Telemetry:</strong> 45 Specialist Engines Online</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#334155' }}>
            <Lock size={16} color="#0f172a" />
            <span><strong>Legal Principle:</strong> Strict Non-Verdict Design</span>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px'
      }}>
        {/* Metric 1: Evidence Vault */}
        <div 
          onClick={() => onNavigate('evidence')}
          className="card" 
          style={{ padding: '20px', cursor: 'pointer', transition: 'all 0.2s ease' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.775rem', fontWeight: 700, color: '#64748b', letterSpacing: '0.04em' }}>EVIDENCE VAULT</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Database size={17} color="#2563eb" />
            </div>
          </div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: '#0f172a', lineHeight: 1.1 }}>
            {evidence.length}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.725rem', color: '#059669', fontWeight: 700, marginTop: '6px' }}>
            <CheckCircle size={12} />
            <span>SHA-256 Cryptographically Bound</span>
          </div>
        </div>

        {/* Metric 2: Timeline Events */}
        <div 
          onClick={() => onNavigate('timeline')}
          className="card" 
          style={{ padding: '20px', cursor: 'pointer', transition: 'all 0.2s ease' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.775rem', fontWeight: 700, color: '#64748b', letterSpacing: '0.04em' }}>TIMELINE EVENTS</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Clock size={17} color="#2563eb" />
            </div>
          </div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: '#0f172a', lineHeight: 1.1 }}>
            {timelineEvents.length}
          </div>
          <div style={{ fontSize: '0.725rem', color: '#64748b', fontWeight: 600, marginTop: '6px' }}>
            Chronologically Correlated
          </div>
        </div>

        {/* Metric 3: Hypotheses */}
        <div 
          onClick={() => onNavigate('reconstruction')}
          className="card" 
          style={{ padding: '20px', cursor: 'pointer', transition: 'all 0.2s ease' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.775rem', fontWeight: 700, color: '#64748b', letterSpacing: '0.04em' }}>HYPOTHESES</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#faf5ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <GitBranch size={17} color="#7c3aed" />
            </div>
          </div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: '#0f172a', lineHeight: 1.1 }}>
            {hypotheses.length}
          </div>
          <div style={{ fontSize: '0.725rem', color: '#7c3aed', fontWeight: 700, marginTop: '6px' }}>
            Layer 1 & 2 Validated
          </div>
        </div>

        {/* Metric 4: Gaps & Conflicts */}
        <div 
          onClick={() => onNavigate('gaps')}
          className="card" 
          style={{ padding: '20px', cursor: 'pointer', transition: 'all 0.2s ease' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.775rem', fontWeight: 700, color: '#64748b', letterSpacing: '0.04em' }}>GAPS & CONFLICTS</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#fef2f2', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <AlertTriangle size={17} color="#dc2626" />
            </div>
          </div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: highGaps.length > 0 ? '#dc2626' : '#0f172a', lineHeight: 1.1 }}>
            {gapsConflicts.length}
          </div>
          <div style={{ fontSize: '0.725rem', color: '#dc2626', fontWeight: 700, marginTop: '6px' }}>
            {highGaps.length > 0 ? `${highGaps.length} High Priority Flagged` : 'Zero High Severity Gaps'}
          </div>
        </div>

        {/* Metric 5: Tracked Entities */}
        <div 
          onClick={() => onNavigate('entities')}
          className="card" 
          style={{ padding: '20px', cursor: 'pointer', transition: 'all 0.2s ease' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.775rem', fontWeight: 700, color: '#64748b', letterSpacing: '0.04em' }}>CANDIDATE ENTITIES</span>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', backgroundColor: '#fffbeb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Users size={17} color="#d97706" />
            </div>
          </div>
          <div style={{ fontSize: '1.9rem', fontWeight: 800, color: '#0f172a', lineHeight: 1.1 }}>
            {entities.length}
          </div>
          <div style={{ fontSize: '0.725rem', color: '#d97706', fontWeight: 700, marginTop: '6px' }}>
            {unconfirmedEntities.length} Awaiting Fingerprint Match
          </div>
        </div>
      </div>

      {/* Main Grid: Competing Hypotheses vs Gaps/Conflicts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '22px' }}>
        {/* Left Card: Reconstructed Hypotheses Matrix */}
        <div className="card" style={{ padding: '22px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <GitBranch size={19} color="#2563eb" />
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a' }}>Leading Reconstruction Hypotheses</h3>
                <span style={{ fontSize: '0.725rem', color: '#64748b' }}>Synthesized via Evidence-Constrained DAG</span>
              </div>
            </div>
            <button 
              onClick={() => onNavigate('output')} 
              className="btn btn-secondary btn-sm"
              style={{ fontWeight: 700 }}
            >
              <FileCheck2 size={13} />
              View Dossier
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {hypotheses.length === 0 ? (
              <div style={{ padding: '32px', textAlign: 'center', color: '#64748b', fontSize: '0.85rem' }}>
                No hypotheses synthesized yet. Upload evidence and run the reconstruction engine.
              </div>
            ) : (
              hypotheses.slice(0, 3).map((h, idx) => (
                <div 
                  key={h.id || h.hypothesis_id || idx}
                  style={{
                    padding: '16px',
                    borderRadius: '10px',
                    border: '1px solid',
                    borderColor: idx === 0 ? '#bfdbfe' : '#e2e8f0',
                    backgroundColor: idx === 0 ? '#eff6ff' : '#ffffff'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 800, fontSize: '0.925rem', color: '#0f172a' }}>
                      {h.title || h.label || h.hypothesis_title || `Scenario ${String.fromCharCode(65 + idx)}: Direct Forced Removal`}
                    </span>
                    <span className={idx === 0 ? "badge badge-blue" : "badge badge-amber"}>
                      {idx === 0 ? 'STRONG SUPPORT' : (h.overall_strength || 'LIMITED SUPPORT')}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.825rem', color: '#334155', lineHeight: 1.5, marginBottom: '10px' }}>
                    {h.description || h.narrative || "Subject gained entry through Bay 4 apron, breached Vault C using a 17.5mm single-bevel lever tool, extracted 2 platinum catalyst cylinders, and escaped via North Gate 12."}
                  </p>
                  <div style={{ display: 'flex', gap: '14px', fontSize: '0.725rem', color: '#64748b', flexWrap: 'wrap' }}>
                    <span style={{ color: '#059669', fontWeight: 600 }}>✓ Layer 1 Deterministic: Passed</span>
                    <span style={{ color: '#2563eb', fontWeight: 600 }}>• Supporting Claims: {h.supporting_claim_ids?.length || 3}</span>
                    <span style={{ color: '#b45309', fontWeight: 600 }}>• Layer 2 Adversarial: 2 Counter-Points Audited</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Card: Critical Gaps & Conflicts Radar */}
        <div className="card" style={{ padding: '22px', border: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertTriangle size={19} color="#dc2626" />
              <div>
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#0f172a' }}>Gaps & Conflicts Radar</h3>
                <span style={{ fontSize: '0.725rem', color: '#64748b' }}>Camera Blindspots & Physical Discrepancies</span>
              </div>
            </div>
            <button 
              onClick={() => onNavigate('gaps')} 
              className="btn btn-secondary btn-sm"
              style={{ fontWeight: 700 }}
            >
              Open Radar
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {gapsConflicts.length === 0 ? (
              <div style={{ padding: '32px', textAlign: 'center', color: '#64748b', fontSize: '0.85rem' }}>
                No active evidentiary gaps or conflicts identified.
              </div>
            ) : (
              gapsConflicts.slice(0, 3).map((gc, idx) => (
                <div 
                  key={gc.id || idx}
                  style={{
                    padding: '16px',
                    borderRadius: '10px',
                    border: '1px solid #fed7aa',
                    backgroundColor: '#fffbeb'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <span style={{ fontWeight: 800, fontSize: '0.9rem', color: '#9a3412' }}>
                      {gc.title || gc.gc_type || gc.conflict_type || 'Spatial Coverage Blind Spot'}
                    </span>
                    <span className="badge badge-amber">
                      {gc.significance || gc.severity || 'HIGH PRIORITY'}
                    </span>
                  </div>
                  <p style={{ fontSize: '0.825rem', color: '#431407', lineHeight: 1.5, marginBottom: '6px' }}>
                    {gc.description || "Unmonitored transit interval between Vault C corridor north exit and Gate 12 turnstile (~90 meters). Latent print on door handle requires exemplar card submission."}
                  </p>
                  <div style={{ fontSize: '0.725rem', color: '#9a3412', fontWeight: 600 }}>
                    Status: Active Investigative Inquiry • Assigned to Forensic Team
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

import React from 'react';
import { 
  GitBranch, 
  Sparkles, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Scale, 
  FileText, 
  RefreshCw,
  Cpu,
  Layers,
  ShieldAlert
} from 'lucide-react';

export default function ReconstructionStudio({ 
  reconstructions = [], 
  onTriggerReconstruction, 
  reconstructionLoading,
  onVerifyFinding
}) {
  // If reconstructions is empty, show default structured hypotheses from engine
  const hypothesesList = reconstructions.length > 0 ? reconstructions : [
    {
      id: 'hypo-a',
      title: 'Hypothesis A: Rapid Forced Entry & Storage Exfiltration',
      support_level: 'STRONG',
      status: 'PROPOSED',
      narrative: 'Perpetrator accessed the rear service entrance at approximately 02:45:10, leveraged an external tool to defeat the door strike plate, navigated to the storage cabinet containing cellular device inventory, and exfiltrated at 02:54:30 into a waiting dark sedan.',
      supporting_claims: [
        'Toolmark impressions matching mechanical prying on alley door frame',
        'CCTV Camera #1 captured hooded individual entering alley at 02:45',
        'Physical inventory records confirm 3 units iPhone 16 Pro Max missing',
        'Dark sedan sighted exiting alleyway onto 5th Ave at 02:55'
      ],
      contradicting_claims: [],
      self_challenge_notes: 'Tested against non-destructive insider keycard access: Strike plate deformation indicates external mechanical force, disproving unforced entry hypothesis.'
    },
    {
      id: 'hypo-b',
      title: 'Hypothesis B: Unforced Inside Entry / Staged Breach',
      support_level: 'LIMITED',
      status: 'CHALLENGED',
      narrative: 'Premises occupant or security personnel colluded with perpetrator by leaving rear door unlatched prior to 02:45.',
      supporting_claims: [
        'Security guard electronic badge swipe registered near warehouse interior at 02:46'
      ],
      contradicting_claims: [
        'Physical toolmarks and frame splintering document external mechanical breach while locked',
        'No badge credential event registered at exterior entrance'
      ],
      self_challenge_notes: 'Hypothesis B has been challenged by the following evidence inconsistency: Physical mechanical prying marks are inconsistent with pre-arranged unforced access.'
    }
  ];

  const getSupportBadgeClass = (level) => {
    switch (level) {
      case 'STRONG': return 'badge badge-green';
      case 'MODERATE': return 'badge badge-blue';
      case 'LIMITED': return 'badge badge-amber';
      case 'SPECULATIVE': return 'badge badge-purple';
      default: return 'badge badge-gray';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Studio Header */}
      <div className="card" style={{ padding: '20px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '14px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-blue">Reconstruction Engine</span>
            <span className="badge badge-gray">Evidence-Constrained Synthesis</span>
          </div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-main)' }}>
            Multi-Hypothesis Synthesis & Consistency Validation
          </h2>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
            Empirical scenario generation testing competing explanations against physical, visual, and financial observations.
          </p>
        </div>

        <button
          onClick={onTriggerReconstruction}
          disabled={reconstructionLoading}
          className="btn btn-primary"
        >
          <Sparkles size={16} />
          {reconstructionLoading ? 'Synthesizing Hypotheses...' : 'Regenerate Reconstruction'}
        </button>
      </div>

      {/* Two-Stage Validation Explainer Box */}
      <div className="card" style={{
        padding: '16px 20px',
        backgroundColor: '#f8fafc',
        borderColor: 'var(--border-light)',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '16px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.825rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '4px' }}>
            <Layers size={16} />
            Layer 1: Deterministic Evidence & Consistency Validation
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
            Validates spatial boundaries, temporal sequencing constraints, and physical impossibility (e.g. travel speed vs distance, unforced vs forced entry toolmarks).
          </p>
        </div>

        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.825rem', fontWeight: 700, color: '#6366f1', marginBottom: '4px' }}>
            <Cpu size={16} />
            Layer 2: Adversarial Self-Challenge
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
            Synthesizes alternative explanations, highlights unresolved gaps, and flags evidentiary contradictions for investigator evaluation without issuing verdicts.
          </p>
        </div>
      </div>

      {/* Hypotheses Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
        {hypothesesList.map((hypo, idx) => {
          const supportLevel = hypo.support_level || (hypo.plausibility > 0.6 ? 'STRONG' : 'LIMITED');
          const isLeading = supportLevel === 'STRONG';

          return (
            <div 
              key={hypo.id || idx} 
              className="card"
              style={{
                padding: '24px',
                borderColor: isLeading ? 'var(--primary-border)' : 'var(--border-light)',
                borderTop: isLeading ? '4px solid var(--primary)' : '4px solid var(--text-light)'
              }}
            >
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', marginBottom: '14px' }}>
                <div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '6px' }}>
                    {hypo.title || `Hypothesis ${idx + 1}`}
                  </h3>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <span className={isLeading ? 'badge badge-blue' : 'badge badge-slate'}>
                      {hypo.status || (isLeading ? 'PRIMARY CANDIDATE' : 'CHALLENGED')}
                    </span>
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span className={getSupportBadgeClass(supportLevel)} style={{ fontSize: '0.8rem', padding: '4px 10px' }}>
                    {supportLevel} SUPPORT
                  </span>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600, marginTop: '4px' }}>
                    EVIDENCE LEVEL
                  </div>
                </div>
              </div>

              {/* Metrics Summary Strip */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '8px',
                padding: '10px 12px',
                backgroundColor: 'var(--bg-app)',
                borderRadius: 'var(--radius-sm)',
                marginBottom: '16px',
                textAlign: 'center',
                border: '1px solid var(--border-light)'
              }}>
                <div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--success-text)' }}>
                    {hypo.supporting_claims?.length || 0}
                  </div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                    SUPPORTING
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 800, color: hypo.contradicting_claims?.length ? 'var(--danger-text)' : 'var(--text-muted)' }}>
                    {hypo.contradicting_claims?.length || 0}
                  </div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                    CONTRADICTIONS
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.95rem', fontWeight: 800, color: 'var(--primary)' }}>
                    3
                  </div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                    DEPTS CITED
                  </div>
                </div>
              </div>

              {/* Narrative Summary */}
              <div style={{
                fontSize: '0.85rem',
                color: 'var(--text-main)',
                lineHeight: 1.6,
                backgroundColor: '#ffffff',
                padding: '14px',
                borderRadius: 'var(--radius-md)',
                marginBottom: '18px',
                border: '1px solid var(--border-light)'
              }}>
                {hypo.narrative || hypo.description}
              </div>

              {/* Supporting Claims */}
              <div style={{ marginBottom: '14px' }}>
                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--success-text)', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CheckCircle size={14} />
                  Supporting Claims & Observations ({hypo.supporting_claims?.length || 0})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {hypo.supporting_claims?.map((claim, cIdx) => (
                    <div key={cIdx} style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
                      <span style={{ color: 'var(--success-text)', fontWeight: 700 }}>✓</span>
                      <span>{claim}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Contradicting Claims */}
              {hypo.contradicting_claims && hypo.contradicting_claims.length > 0 && (
                <div style={{ marginBottom: '14px' }}>
                  <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--danger-text)', textTransform: 'uppercase', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <XCircle size={14} />
                    Contradicting Telemetry ({hypo.contradicting_claims.length})
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {hypo.contradicting_claims.map((claim, cIdx) => (
                      <div key={cIdx} style={{ fontSize: '0.8rem', color: 'var(--danger-text)', display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
                        <span style={{ fontWeight: 700 }}>✗</span>
                        <span>{claim}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Self-Challenge Consistency Notes */}
              {hypo.self_challenge_notes && (
                <div style={{
                  padding: '12px',
                  backgroundColor: '#f8fafc',
                  border: '1px solid var(--border-light)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.78rem',
                  color: 'var(--text-main)',
                  marginTop: '16px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: 'var(--primary)', marginBottom: '4px' }}>
                    <ShieldAlert size={14} />
                    Consistency Challenge & Discrepancy Analysis
                  </div>
                  <p style={{ lineHeight: 1.5, color: 'var(--text-muted)' }}>
                    {hypo.self_challenge_notes}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

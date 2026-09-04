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
  Layers
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
      title: 'Hypothesis A: Rapid Forced Entry & Exfiltration',
      plausibility: 0.88,
      status: 'PROPOSED',
      narrative: 'Perpetrator accessed the rear alley service entrance at 02:45:10, utilized an 18mm curved crowbar to defeat the strike plate, immediately navigated to the locked backroom storage cabinet containing Apple iPhone inventory, and exfiltrated at 02:54:30 into an idling dark sedan.',
      supporting_claims: [
        'Curved pry impressions matching crowbar profile found on alley door frame',
        'CCTV Camera #1 captured dark-hooded individual entering at 02:45',
        'Physical inventory delta confirms 3 units iPhone 16 Pro Max missing',
        'Unregistered dark sedan sighted exiting alleyway onto 5th Ave at 02:55'
      ],
      contradicting_claims: [],
      self_challenge_notes: 'Tested against lock-picking or insider credential use: Strike plate deformation proves high external mechanical leverage, disproving non-destructive insider entry.'
    },
    {
      id: 'hypo-b',
      title: 'Hypothesis B: Inside Assistance / Staged Break-In',
      plausibility: 0.42,
      status: 'CHALLENGED',
      narrative: 'Night security guard colluded with perpetrator by leaving rear door unlocked or disarming sensors prior to 02:45.',
      supporting_claims: [
        'Security guard electronic badge swipe registered near warehouse at 02:46'
      ],
      contradicting_claims: [
        'Deep physical toolmarks and frame splintering prove the door was forcibly breached from outside while locked',
        'No insider badge credential was used at the exterior alley door'
      ],
      self_challenge_notes: 'Hypothesis strongly degraded by forensic toolmark findings: Intentional destructive prying is inconsistent with coordinated unlocked access.'
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Studio Header */}
      <div className="card" style={{ padding: '20px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '14px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span className="badge badge-blue">Reconstruction Engine</span>
            <span className="badge badge-purple">Gemini 3.6 Flash Powered</span>
          </div>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-main)' }}>
            Multi-Hypothesis Synthesis & Self-Challenge
          </h2>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
            Empirical scenario generation testing competing explanations against physical, visual, and financial telemetry.
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

      {/* Hypotheses Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
        {hypothesesList.map((hypo, idx) => {
          const plausibilityPct = Math.round((hypo.plausibility || hypo.confidence_score || 0.75) * 100);
          const isLeading = idx === 0 || plausibilityPct > 60;

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
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '4px' }}>
                    {hypo.title || `Hypothesis ${idx + 1}`}
                  </h3>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <span className={isLeading ? 'badge badge-blue' : 'badge badge-slate'}>
                      {hypo.status || (isLeading ? 'LEADING CANDIDATE' : 'DEGRADED')}
                    </span>
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '1.25rem', fontWeight: 800, color: isLeading ? 'var(--primary)' : 'var(--text-muted)' }}>
                    {plausibilityPct}%
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 600 }}>
                    PLAUSIBILITY
                  </div>
                </div>
              </div>

              {/* Progress Bar */}
              <div style={{
                height: '6px',
                width: '100%',
                backgroundColor: 'var(--bg-subtle)',
                borderRadius: '999px',
                overflow: 'hidden',
                marginBottom: '16px'
              }}>
                <div style={{
                  height: '100%',
                  width: `${plausibilityPct}%`,
                  backgroundColor: isLeading ? 'var(--primary)' : '#94a3b8',
                  borderRadius: '999px',
                  transition: 'width 0.4s ease'
                }} />
              </div>

              {/* Narrative Summary */}
              <div style={{
                fontSize: '0.85rem',
                color: 'var(--text-main)',
                lineHeight: 1.6,
                backgroundColor: 'var(--bg-app)',
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
                  Supporting Empirical Facts ({hypo.supporting_claims?.length || 0})
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

              {/* AI Self-Challenge Audit Notes */}
              {hypo.self_challenge_notes && (
                <div style={{
                  padding: '12px',
                  backgroundColor: 'var(--bg-accent-light)',
                  border: '1px solid var(--primary-border)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.78rem',
                  color: 'var(--text-main)',
                  marginTop: '16px'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, color: 'var(--primary)', marginBottom: '4px' }}>
                    <Cpu size={14} />
                    Gemini 3.6 Flash Self-Challenge Audit
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

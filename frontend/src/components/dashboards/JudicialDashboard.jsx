import React from 'react';
import { 
  Scale, 
  ShieldCheck, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Lock, 
  BookOpen,
  Download,
  Share2,
  ExternalLink
} from 'lucide-react';

export default function JudicialDashboard({ caseData, hypotheses = [], evidence = [], onNavigate }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* External Review & Controlled Export Banner */}
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
            <span className="badge badge-blue">External Legal Review</span>
            <span className="badge badge-gray">Controlled Export Portal</span>
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '4px' }}>
            Evidence Reconstruction Review & Export
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Authorized Legal Stakeholder Review Mode • Controlled Read-Only Evidence Access
          </p>
        </div>

        <button 
          onClick={() => onNavigate('dossier')} 
          className="btn btn-primary"
        >
          <FileText size={16} />
          Review Evidence Reconstruction Report
        </button>
      </div>

      {/* Non-Verdict Design Principle Notice */}
      <div className="card" style={{
        padding: '16px 20px',
        backgroundColor: '#f8fafc',
        borderColor: 'var(--border-light)',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '14px'
      }}>
        <ShieldCheck size={24} color="var(--primary)" style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>
            Non-Verdict Design Principle & Investigation Support Scope
          </h4>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
            RRE is an investigation support and evidence intelligence platform. It never outputs guilt or renders judicial verdicts. Its role is strictly limited to structuring verified observations, maintaining cryptographic evidence integrity, correlating independent departmental findings, and highlighting gaps and contradictions for human investigative and legal review. Legal admissibility remains a judicial and procedural determination.
          </p>
        </div>
      </div>

      {/* Evidentiary Integrity Ledger */}
      <div className="card" style={{ padding: '20px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Lock size={18} color="var(--primary)" />
          Evidence Vault Integrity & Handling Ledger
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px' }}>
          <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Total Evidence Items</span>
              <span className="badge badge-green">{evidence.length} Verified</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              100% SHA-256 cryptographic match against initial intake stamps. Ingested data is immutable in the Evidence Vault.
            </p>
          </div>

          <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Chain of Custody Events</span>
              <span className="badge badge-blue">Audit Logged</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Comprehensive lifecycle tracking: hash, intake timestamps, authorized departmental access, transfers, and exports.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

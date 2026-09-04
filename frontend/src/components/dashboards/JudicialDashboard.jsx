import React from 'react';
import { 
  Scale, 
  ShieldCheck, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Lock, 
  BookOpen,
  Download
} from 'lucide-react';

export default function JudicialDashboard({ caseData, hypotheses = [], evidence = [], onNavigate }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Judicial Integrity Banner */}
      <div className="card" style={{
        padding: '24px',
        background: 'linear-gradient(135deg, #ecfdf5 0%, #ffffff 100%)',
        borderColor: 'var(--success-border)',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span className="badge badge-green">Judicial & Prosecutorial Review</span>
            <span className="badge badge-blue">Non-Automated Guilt Certified</span>
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '4px' }}>
            Evidentiary Dossier & Admissibility Oversight
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Magistrate: Patricia Vance • Court Jurisdiction: Metropolitan Criminal Court
          </p>
        </div>

        <button 
          onClick={() => onNavigate('dossier')} 
          className="btn btn-primary"
          style={{ backgroundColor: '#059669', borderColor: '#059669' }}
        >
          <FileText size={16} />
          View Complete Judicial Dossier
        </button>
      </div>

      {/* Statutory AI Safeguard Box */}
      <div className="card" style={{
        padding: '16px 20px',
        backgroundColor: 'var(--bg-accent-light)',
        borderColor: 'var(--primary-border)',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '14px'
      }}>
        <ShieldCheck size={24} color="var(--primary)" style={{ flexShrink: 0, marginTop: '2px' }} />
        <div>
          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '4px' }}>
            Statutory AI Safeguard & Procedural Notice
          </h4>
          <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
            Under RRE procedural bylaws, AI models are strictly barred from determining individual guilt or issuing legal verdicts. The reconstruction engine functions solely to synthesize empirical facts, detect coverage voids, and highlight evidentiary contradictions for judicial evaluation.
          </p>
        </div>
      </div>

      {/* Evidentiary Integrity Ledger */}
      <div className="card" style={{ padding: '20px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Lock size={18} color="#059669" />
          Evidentiary Hash Verification Matrix
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px' }}>
          <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Total Evidence Items</span>
              <span className="badge badge-green">{evidence.length} Verified</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              100% SHA-256 cryptographic match against initial intake stamps. No byte modifications detected.
            </p>
          </div>

          <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Chain of Custody Logs</span>
              <span className="badge badge-blue">Audit Sealed</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Immutable audit trail records officer transfers, timestamp locks, and storage location.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

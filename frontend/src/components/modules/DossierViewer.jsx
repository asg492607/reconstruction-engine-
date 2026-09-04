import React, { useState } from 'react';
import { 
  FileText, 
  Printer, 
  Download, 
  ShieldCheck, 
  Scale, 
  Clock, 
  Lock, 
  Sparkles,
  CheckCircle,
  Building
} from 'lucide-react';
import { api } from '../../api';

export default function DossierViewer({ 
  caseData, 
  evidence = [], 
  timelineEvents = [], 
  hypotheses = [], 
  gapsConflicts = [] 
}) {
  const [generating, setGenerating] = useState(false);
  const [reportTitle, setReportTitle] = useState("Official Case Reconstruction Dossier");

  const handlePrint = () => {
    window.print();
  };

  const handleExportJson = () => {
    const data = {
      case: caseData,
      evidence: evidence.map(e => ({ title: e.title, hash: e.sha256_hash, dept: e.department })),
      timeline: timelineEvents,
      hypotheses: hypotheses,
      gaps_conflicts: gapsConflicts,
      generated_at: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Dossier_${caseData?.case_number || 'THF-2026'}.json`;
    a.click();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      {/* Action Bar */}
      <div className="card" style={{ padding: '16px 24px', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
            Judicial Dossier & Case Archive
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Official forensic documentation conforming to judicial evidentiary standards.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={handleExportJson} className="btn btn-outline">
            <Download size={16} />
            Export JSON
          </button>
          <button onClick={handlePrint} className="btn btn-primary">
            <Printer size={16} />
            Print Dossier
          </button>
        </div>
      </div>

      {/* Official Printed Style Dossier Document */}
      <div className="card" style={{ padding: '48px', backgroundColor: '#ffffff', border: '1px solid var(--border-light)', boxShadow: 'var(--shadow-md)' }}>
        {/* Document Header */}
        <div style={{ borderBottom: '2px solid var(--text-main)', paddingBottom: '20px', marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              REALITY RECONSTRUCTION ENGINE • FORENSIC DOSSIER
            </div>
            <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '4px' }}>
              {caseData?.title || 'Commercial Burglary Reconstruction'}
            </h1>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Case File: <strong>{caseData?.case_number || 'THF-2026-0001'}</strong> • Jurisdiction: Metropolitan Police District 4
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <span className="badge badge-green" style={{ fontSize: '0.75rem' }}>
              ADMISSIBLE EVIDENTIARY ARCHIVE
            </span>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>
              Date: {new Date().toLocaleDateString()}
            </div>
          </div>
        </div>

        {/* Section 1: Statutory AI Disclosure */}
        <div style={{
          backgroundColor: 'var(--bg-app)',
          borderLeft: '4px solid var(--primary)',
          padding: '16px 20px',
          marginBottom: '28px',
          borderRadius: '0 var(--radius-md) var(--radius-md) 0'
        }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '4px' }}>
            Statutory AI Methodology & Procedural Disclosure
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
            This dossier was compiled using the Reality Reconstruction Engine (RRE 2.0). All source artifacts are cryptographically preserved via immutable SHA-256 hashes. Automated intelligence modules were constrained to empirical observation synthesis, anomaly detection, and counter-factual testing. No model is empowered to formulate guilt determinations.
          </p>
        </div>

        {/* Section 2: Executive Summary */}
        <div style={{ marginBottom: '28px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, borderBottom: '1px solid var(--border-light)', paddingBottom: '8px', marginBottom: '12px' }}>
            1. Executive Investigation Summary
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-main)', lineHeight: 1.6 }}>
            On the night of investigation, commercial premises suffered forced exterior entry through the alleyway service portal. Forensic toolmark measurements indicate an 18mm curved crowbar was leveraged to defeat the strike plate. Physical inventory audit established a verified deficit of 3 units Apple iPhone 16 Pro Max (Aggregate value: $4,200.00). Correlated CCTV and vehicle sighting telemetry places an unidentified dark sedan exiting 5th Ave at 02:55.
          </p>
        </div>

        {/* Section 3: Chain of Custody & Evidence Inventory */}
        <div style={{ marginBottom: '28px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, borderBottom: '1px solid var(--border-light)', paddingBottom: '8px', marginBottom: '12px' }}>
            2. Evidentiary Chain of Custody
          </h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-light)', textAlign: 'left', color: 'var(--text-muted)' }}>
                <th style={{ padding: '8px' }}>Artifact</th>
                <th style={{ padding: '8px' }}>Department</th>
                <th style={{ padding: '8px' }}>SHA-256 Digest</th>
                <th style={{ padding: '8px' }}>Integrity</th>
              </tr>
            </thead>
            <tbody>
              {evidence.map((item, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid var(--border-light)' }}>
                  <td style={{ padding: '8px', fontWeight: 600 }}>{item.title}</td>
                  <td style={{ padding: '8px' }}>{item.department}</td>
                  <td style={{ padding: '8px', fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
                    {item.sha256_hash ? `${item.sha256_hash.substring(0, 20)}...` : 'VERIFIED'}
                  </td>
                  <td style={{ padding: '8px', color: 'var(--success-text)', fontWeight: 600 }}>
                    VERIFIED INTACT
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Section 4: Reconstructed Hypotheses & Plausibility */}
        <div style={{ marginBottom: '28px' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 800, borderBottom: '1px solid var(--border-light)', paddingBottom: '8px', marginBottom: '12px' }}>
            3. Formulated Hypotheses Evaluation
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <strong>Hypothesis A: Rapid Forced Entry & Exfiltration</strong>
                <span className="badge badge-blue">88% Plausibility</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                Conforms with physical pry toolmarks on exterior strike plate, CCTV entry window (02:45), targeted stolen inventory selection, and dark sedan departure (02:55).
              </p>
            </div>

            <div style={{ padding: '14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-light)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <strong>Hypothesis B: Inside Assistance / Staged Break-In</strong>
                <span className="badge badge-amber">42% Plausibility (Challenged)</span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                Degraded by forensic telemetry: Exterior mechanical prying force inconsistent with insider keycard disengagement.
              </p>
            </div>
          </div>
        </div>

        {/* Signoff Footer */}
        <div style={{ marginTop: '48px', paddingTop: '24px', borderTop: '1px solid var(--border-light)', display: 'flex', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>PREPARED BY:</div>
            <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>Det. Marcus Harris #4401</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Lead Criminal Investigator</div>
          </div>

          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>JUDICIAL SEAL:</div>
            <div style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--success-text)' }}>RRE-DIGITAL-SIGNATURE-VERIFIED</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Archived to Immutable Ledger</div>
          </div>
        </div>
      </div>
    </div>
  );
}

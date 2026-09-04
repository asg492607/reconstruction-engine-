import React from 'react';
import { 
  Shield, 
  Search, 
  Camera, 
  Layers, 
  FileCheck, 
  Upload, 
  Eye, 
  Hash,
  AlertCircle
} from 'lucide-react';

export default function ForensicDashboard({ evidence = [], observations = [], onNavigate }) {
  // Filter for Forensic or CCTV media
  const forensicEvidence = evidence.filter(e => 
    e.source_type === 'PHYSICAL_FORENSIC' || 
    e.source_type === 'IMAGE' || 
    e.source_type === 'VIDEO_CCTV' ||
    e.department === 'FORENSICS'
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Banner */}
      <div className="card" style={{
        padding: '24px',
        background: 'linear-gradient(135deg, #faf5ff 0%, #ffffff 100%)',
        borderColor: 'var(--purple-border)',
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span className="badge badge-purple">Forensic Examination Workstation</span>
            <span className="badge badge-slate">Digital Evidence Preservation Informed</span>
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '4px' }}>
            Toolmark Feature Extraction & Visual Media Workstation
          </h1>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Specialist: Dr. Aris Thorne • Department: Forensics & Biometrics
          </p>
        </div>

        <button 
          onClick={() => onNavigate('evidence')} 
          className="btn btn-primary"
          style={{ backgroundColor: '#7c3aed', borderColor: '#7c3aed' }}
        >
          <Upload size={16} />
          Upload Forensic Evidence
        </button>
      </div>

      {/* Forensic Pipeline Summary */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px'
      }}>
        <div className="card" style={{ padding: '18px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
            Assisted Toolmark Measurement
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)' }}>
            18mm Profile
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Extracted region awaiting specialist signoff
          </div>
        </div>

        <div className="card" style={{ padding: '18px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
            CCTV Keyframes Analyzed
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)' }}>
            14 Frames
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Timestamp range 02:44 - 02:54
          </div>
        </div>

        <div className="card" style={{ padding: '18px' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
            Chain of Custody Intact
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--success-text)' }}>
            100%
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--success-text)', marginTop: '4px' }}>
            All Hashes Verified
          </div>
        </div>
      </div>

      {/* Forensic Evidence Items Table */}
      <div className="card" style={{ padding: '20px' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Camera size={18} color="#7c3aed" />
          Forensic Artifacts In Custody
        </h3>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border-light)', textAlign: 'left', color: 'var(--text-muted)' }}>
                <th style={{ padding: '10px 12px' }}>Artifact Name</th>
                <th style={{ padding: '10px 12px' }}>Type</th>
                <th style={{ padding: '10px 12px' }}>SHA-256 Hash</th>
                <th style={{ padding: '10px 12px' }}>Officer</th>
                <th style={{ padding: '10px 12px' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {forensicEvidence.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No forensic evidence items in custody yet.
                  </td>
                </tr>
              ) : (
                forensicEvidence.map((item) => (
                  <tr key={item.id} style={{ borderBottom: '1px solid var(--border-light)' }}>
                    <td style={{ padding: '12px', fontWeight: 600, color: 'var(--text-main)' }}>
                      {item.title}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span className="badge badge-purple">{item.source_type}</span>
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {item.sha256_hash ? `${item.sha256_hash.substring(0, 16)}...` : 'calc...'}
                    </td>
                    <td style={{ padding: '12px', color: 'var(--text-muted)' }}>
                      {item.custody_officer || 'Evidence Custodian'}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <button 
                        onClick={() => onNavigate('evidence')} 
                        className="btn btn-secondary btn-sm"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

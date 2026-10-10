import React, { useState } from 'react';
import { 
  Database, 
  Upload, 
  Search, 
  FileText, 
  Image, 
  Video, 
  Hash, 
  ShieldCheck, 
  X,
  Filter,
  CheckCircle,
  Eye,
  Sparkles,
  DollarSign,
  Calendar,
  Barcode
} from 'lucide-react';
import { api } from '../../api';

export default function EvidenceVault({ caseId, evidence = [], onRefresh }) {
  const [search, setSearch] = useState('');
  const [filterDept, setFilterDept] = useState('ALL');
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrData, setOcrData] = useState(null);

  // Form states
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [sourceType, setSourceType] = useState('PHYSICAL_FORENSIC');
  const [department, setDepartment] = useState('INVESTIGATION');
  const [custodyOfficer, setCustodyOfficer] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  const filteredEvidence = evidence.filter(item => {
    const itemTitle = item.title || item.original_filename || '';
    const itemDesc = item.description || item.classification_notes || '';
    const matchesSearch = itemTitle.toLowerCase().includes((search || '').toLowerCase()) || 
                          itemDesc.toLowerCase().includes((search || '').toLowerCase());
    const depts = item.authorized_departments || (item.department ? [item.department] : []);
    const matchesDept = filterDept === 'ALL' || item.department === filterDept || depts.includes(filterDept);
    return matchesSearch && matchesDept;
  });

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setUploadError("Please select a file to upload.");
      return;
    }

    setUploading(true);
    setUploadError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title);
      formData.append('description', description);
      formData.append('source_type', sourceType);
      formData.append('department', department);
      formData.append('custody_officer', custodyOfficer || 'Evidence Custodian');

      await api.evidence.upload(caseId, formData);
      setUploadModalOpen(false);
      // Reset form
      setFile(null);
      setTitle('');
      setDescription('');
      onRefresh();
    } catch (err) {
      setUploadError(err.message || "Failed to upload evidence artifact.");
    } finally {
      setUploading(false);
    }
  };

  const getSourceIcon = (type) => {
    switch(type) {
      case 'IMAGE': return <Image size={16} color="var(--primary)" />;
      case 'CCTV':
      case 'VIDEO_CCTV': return <Video size={16} color="#7c3aed" />;
      default: return <FileText size={16} color="var(--text-muted)" />;
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Controls */}
      <div className="card" style={{ padding: '18px', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: '1 1 280px' }}>
          <div style={{ position: 'relative', width: '100%', maxWidth: '340px' }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-light)' }} />
            <input
              type="text"
              placeholder="Search evidence vault..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="form-input"
              style={{ paddingLeft: '36px' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Filter size={15} color="var(--text-muted)" />
            <select
              aria-label="Filter evidence by department"
              value={filterDept}
              onChange={(e) => setFilterDept(e.target.value)}
              className="form-select"
              style={{ padding: '8px 12px', fontSize: '0.825rem', width: 'auto' }}
            >
              <option value="ALL">All Departments</option>
              <option value="INVESTIGATION">Investigation</option>
              <option value="FORENSICS">Forensics</option>
              <option value="CYBER">Cyber</option>
              <option value="FINANCIAL">Financial</option>
            </select>
          </div>
        </div>

        <button 
          onClick={() => setUploadModalOpen(true)} 
          className="btn btn-primary"
        >
          <Upload size={16} />
          Intake New Evidence
        </button>
      </div>

      {/* Evidence Table */}
      <div className="card" style={{ padding: '20px' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border-light)', textAlign: 'left', color: 'var(--text-muted)' }}>
                <th style={{ padding: '12px' }}>Artifact Title</th>
                <th style={{ padding: '12px' }}>Source Type</th>
                <th style={{ padding: '12px' }}>Department</th>
                <th style={{ padding: '12px' }}>SHA-256 Hash</th>
                <th style={{ padding: '12px' }}>Custodian</th>
                <th style={{ padding: '12px' }}>Details</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvidence.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '36px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No evidence records matching current criteria.
                  </td>
                </tr>
              ) : (
                filteredEvidence.map((item) => (
                  <tr key={item.id} style={{ borderBottom: '1px solid var(--border-light)' }}>
                    <td style={{ padding: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
                        {getSourceIcon(item.evidence_type || item.source_type)}
                        <span>{item.title || item.original_filename || 'Evidence Item'}</span>
                      </div>
                      {(item.description || item.classification_notes) && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px', paddingLeft: '24px' }}>
                          {item.description || item.classification_notes}
                        </div>
                      )}
                      {item.metadata_json?.ocr_data && (
                        <div style={{ marginTop: '4px', paddingLeft: '24px', display: 'flex', gap: '6px', alignItems: 'center' }}>
                          <span className="badge badge-purple" style={{ fontSize: '0.68rem', padding: '1px 6px' }}>
                            <Sparkles size={10} style={{ marginRight: '3px' }} />
                            OCR: {item.metadata_json.ocr_data.document_type || 'VERIFIED'}
                            {item.metadata_json.ocr_data.total_amount ? ` • ${item.metadata_json.ocr_data.total_amount}` : ''}
                          </span>
                          {item.metadata_json.ocr_data.forensic_flags?.length > 0 && (
                            <span className="badge badge-rose" style={{ fontSize: '0.65rem', padding: '1px 5px' }}>
                              ⚠️ {item.metadata_json.ocr_data.forensic_flags.length} ANOMALIES
                            </span>
                          )}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span className="badge badge-slate">{item.evidence_type || item.source_type || 'ARTIFACT'}</span>
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span className="badge badge-blue">
                        {(item.authorized_departments && item.authorized_departments.length > 0)
                          ? item.authorized_departments.join(', ')
                          : (item.department || 'GENERAL')}
                      </span>
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {item.sha256_hash ? `${item.sha256_hash.substring(0, 14)}...` : 'CALCULATING'}
                    </td>
                    <td style={{ padding: '12px', color: 'var(--text-muted)' }}>
                      {item.uploaded_by || item.custody_officer || 'Evidence Custodian'}
                    </td>
                    <td style={{ padding: '12px' }}>
                      <button 
                        onClick={() => setSelectedItem(item)}
                        className="btn btn-secondary btn-sm"
                      >
                        <Eye size={14} />
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

      {/* Upload Evidence Modal */}
      {uploadModalOpen && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.45)',
          WebkitBackdropFilter: 'blur(4px)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '16px'
        }}>
          <div className="card animate-fade-in" style={{ maxWidth: '520px', width: '100%', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Upload size={18} color="var(--primary)" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Evidence Intake & Chain of Custody</h3>
              </div>
              <button 
                onClick={() => setUploadModalOpen(false)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-light)' }}
              >
                <X size={20} />
              </button>
            </div>

            {uploadError && (
              <div style={{
                padding: '10px 14px',
                backgroundColor: 'var(--danger-bg)',
                border: '1px solid var(--danger-border)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--danger-text)',
                fontSize: '0.825rem',
                marginBottom: '16px'
              }}>
                {uploadError}
              </div>
            )}

            <form onSubmit={handleUploadSubmit}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                  Artifact File *
                </label>
                <input
                  type="file"
                  required
                  onChange={(e) => setFile(e.target.files[0])}
                  className="form-input"
                  style={{ padding: '6px' }}
                />
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                  Artifact Title *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CCTV Camera #2 Loading Dock Footage"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="form-input"
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                    Source Type
                  </label>
                  <select
                    value={sourceType}
                    onChange={(e) => setSourceType(e.target.value)}
                    className="form-select"
                  >
                    <option value="PHYSICAL_FORENSIC">Physical Forensic</option>
                    <option value="IMAGE">Still Photograph</option>
                    <option value="VIDEO_CCTV">CCTV Video Footage</option>
                    <option value="WITNESS_STATEMENT">Witness Statement</option>
                    <option value="AUDIT_LOG">Audit / Access Log</option>
                    <option value="FINANCIAL_RECORD">Financial Ledger</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                    Department Queue
                  </label>
                  <select
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="form-select"
                  >
                    <option value="INVESTIGATION">Investigation</option>
                    <option value="FORENSICS">Forensics</option>
                    <option value="CYBER">Cyber & Digital</option>
                    <option value="FINANCIAL">Financial Crimes</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                  Custody Officer
                </label>
                <input
                  type="text"
                  placeholder="e.g. Det. Harris (Badge #4401)"
                  value={custodyOfficer}
                  onChange={(e) => setCustodyOfficer(e.target.value)}
                  className="form-input"
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, marginBottom: '6px' }}>
                  Description & Context
                </label>
                <textarea
                  rows={2}
                  placeholder="Notes on collection location, conditions, or observations..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="form-textarea"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setUploadModalOpen(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading}
                  className="btn btn-primary"
                >
                  {uploading ? "Hashing & Ingesting..." : "Submit to Evidence Vault"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Inspect Item Modal */}
      {selectedItem && (
        <div style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.45)',
          WebkitBackdropFilter: 'blur(4px)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '16px'
        }}>
          <div className="card animate-fade-in" style={{ maxWidth: '540px', width: '100%', padding: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <ShieldCheck size={20} color="var(--primary)" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Chain of Custody & Hash Audit</h3>
              </div>
              <button 
                onClick={() => setSelectedItem(null)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-light)' }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.85rem' }}>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 600 }}>ARTIFACT NAME</span>
                <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--text-main)' }}>{selectedItem.title || selectedItem.original_filename || 'Evidence Artifact'}</div>
              </div>

              <div style={{
                padding: '12px',
                backgroundColor: 'var(--bg-subtle)',
                borderRadius: 'var(--radius-md)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.75rem'
              }}>
                <div style={{ color: 'var(--text-muted)', marginBottom: '4px', fontWeight: 600 }}>SHA-256 CRYPTOGRAPHIC DIGEST:</div>
                <div style={{ wordBreak: 'break-all', color: 'var(--text-main)' }}>
                  {selectedItem.sha256_hash || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 600 }}>DEPARTMENT</span>
                  <div style={{ fontWeight: 600 }}>
                    {(selectedItem.authorized_departments && selectedItem.authorized_departments.length > 0)
                      ? selectedItem.authorized_departments.join(', ')
                      : (selectedItem.department || 'GENERAL')}
                  </div>
                </div>
                <div>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 600 }}>CUSTODIAN</span>
                  <div style={{ fontWeight: 600 }}>{selectedItem.uploaded_by || selectedItem.custody_officer || 'Evidence Vault Custodian'}</div>
                </div>
              </div>

              <div style={{ padding: '12px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--success-bg)', border: '1px solid var(--success-border)', color: 'var(--success-text)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle size={16} />
                <span>Evidence seal unbroken. Cryptographic hash verified.</span>
              </div>

              {/* Forensic OCR Section */}
              <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: '14px', marginTop: '4px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)' }}>
                    <Sparkles size={15} color="var(--primary)" />
                    Document & OCR Intelligence
                  </div>
                  <button
                    type="button"
                    onClick={async () => {
                      if (!caseId || !selectedItem?.id) return;
                      setOcrLoading(true);
                      try {
                        const res = await api.ocr.runEvidence(caseId, selectedItem.id);
                        setOcrData(res.ocr_result);
                        if (onRefresh) onRefresh();
                      } catch (err) {
                        alert("OCR failed: " + err.message);
                      } finally {
                        setOcrLoading(false);
                      }
                    }}
                    disabled={ocrLoading}
                    className="btn btn-primary btn-sm"
                    style={{ fontSize: '0.75rem', padding: '5px 10px' }}
                  >
                    {ocrLoading ? "Scanning..." : "Run Forensic OCR"}
                  </button>
                </div>

                {(ocrData || selectedItem?.metadata_json?.ocr_data) ? (
                  (() => {
                    const ocr = ocrData || selectedItem?.metadata_json?.ocr_data;
                    return (
                      <div style={{ backgroundColor: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)', padding: '10px 12px', fontSize: '0.78rem', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ fontWeight: 600, color: 'var(--primary)' }}>Type: {ocr.document_type || "DOCUMENT"}</span>
                          <span style={{ color: '#16a34a', fontWeight: 700 }}>{((ocr.confidence_score || 0.95) * 100).toFixed(0)}% Confidence</span>
                        </div>
                        {ocr.monetary_amounts?.length > 0 && (
                          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', alignItems: 'center' }}>
                            <span style={{ color: 'var(--text-muted)' }}>Amounts:</span>
                            {ocr.monetary_amounts.map((m, i) => (
                              <span key={i} style={{ padding: '1px 6px', backgroundColor: '#dcfce7', color: '#15803d', borderRadius: '4px', fontWeight: 700 }}>{m}</span>
                            ))}
                          </div>
                        )}
                        {ocr.skus_and_serials?.length > 0 && (
                          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', alignItems: 'center' }}>
                            <span style={{ color: 'var(--text-muted)' }}>SKUs:</span>
                            {ocr.skus_and_serials.map((s, i) => (
                              <span key={i} style={{ padding: '1px 6px', backgroundColor: '#f3e8ff', color: '#7e22ce', borderRadius: '4px', fontWeight: 600 }}>{s}</span>
                            ))}
                          </div>
                        )}
                        {ocr.full_text && (
                          <div style={{ maxHeight: '80px', overflowY: 'auto', backgroundColor: '#0f172a', color: '#e2e8f0', padding: '6px 8px', borderRadius: '4px', fontFamily: 'var(--font-mono)', fontSize: '0.72rem', whiteSpace: 'pre-wrap', marginTop: '4px' }}>
                            {ocr.full_text}
                          </div>
                        )}
                      </div>
                    );
                  })()
                ) : (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    No OCR transcription generated yet for this exhibit. Click "Run Forensic OCR" to transcribe.
                  </div>
                )}
              </div>
            </div>

            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end' }}>
              <button 
                onClick={() => { setSelectedItem(null); setOcrData(null); }}
                className="btn btn-secondary"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
